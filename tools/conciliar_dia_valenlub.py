#!/usr/bin/env python3
"""Conciliação do caixa 4 ValenLub — skill 1.33.0.

Função principal: conciliar_dia_valenlub(...)

Variáveis de ambiente (nunca hardcode):
  QUERY_API_BASE   (default https://backend.acessoquery.com/api)
  QUERY_TOKEN      Bearer já obtido (opcional se USER/PASS)
  QUERY_TENANT     token do tenant (path login mgerencia + X-Tenant API)
  QUERY_USER / QUERY_PASS  login API e mgerencia
  QUERY_CAIXA      id do caixa (default = arg caixa)
  QUERY_MGERENCIA_BASE  (default https://acessoquery.com/mgerencia)
  QUERY_MGERENCIA_HOST  (default valenlub.com.br) — host no path /login/{host}/{tenant}

Também lê .env na raiz do cérebro e em ~/.hermes/.env se existirem
(sem sobrescrever o ambiente já setado).

Uso CLI:
  python3 tools/conciliar_dia_valenlub.py \\
    --data 2026-10-21 --ofx /path/dia.ofx --modo simular
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor
from http.cookiejar import CookieJar

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "conciliacao-bancaria-valenlub"
REL_DIR = ROOT / "skills" / "relatorio-conciliacao"
sys.path.insert(0, str(SKILL_DIR))
from decidir import decidir  # noqa: E402


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass
class ResultadoConciliacao:
    status: str
    data: str
    caixa: int
    modo: str
    contagens: dict[str, int] = field(default_factory=dict)
    criados: list[dict[str, Any]] = field(default_factory=list)
    ariadna: list[dict[str, Any]] = field(default_factory=list)
    linhas: list[dict[str, Any]] = field(default_factory=list)
    pdf_path: str | None = None
    erros: list[str] = field(default_factory=list)
    executados: list[dict[str, Any]] = field(default_factory=list)
    mensagem: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Env
# ---------------------------------------------------------------------------

def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _ensure_env() -> None:
    _load_dotenv(ROOT / ".env")
    _load_dotenv(Path.home() / ".hermes" / ".env")
    _load_dotenv(Path("/home/hermes") / ".hermes" / ".env")


# ---------------------------------------------------------------------------
# OFX
# ---------------------------------------------------------------------------

_OFX_TAG = re.compile(
    r"<(?P<tag>[A-Z0-9\.]+)>(?P<val>[^\r\n<]*)",
    re.IGNORECASE,
)


def _parse_ofx_date(raw: str) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"[^0-9]", "", raw)[:8]
    if len(digits) < 8:
        return None
    return f"{digits[0:4]}-{digits[4:6]}-{digits[6:8]}"


def _parse_ofx_amount(raw: str) -> float:
    s = (raw or "0").strip().replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return round(float(s), 2)


def _classify_line(nome: str, memo: str = "", trntype: str = "") -> str:
    blob = f"{nome} {memo} {trntype}".upper()
    blob_n = (
        blob.replace("Á", "A")
        .replace("Ã", "A")
        .replace("Â", "A")
        .replace("É", "E")
        .replace("Ê", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ô", "O")
        .replace("Ú", "U")
        .replace("Ç", "C")
    )
    # Rentabilidade ANTES de cartão/pix: RENTAB* e INVEST FACILCRED não são Pix.
    if any(
        k in blob_n
        for k in (
            "RENTAB",  # RENTAB. / RENTABIL / RENTABILIDADE
            "RENTABILIDADE",
            "INVEST FACILCRED",
            "RENDIMENTO",
            "RENDTO",
            "JUROS CAPITAL",
            "REMUNERACAO",
        )
    ):
        return "rentabilidade"
    if any(k in blob_n for k in ("RESGATE", "RESG.", "RESG ")):
        return "resgate"
    if any(
        k in blob_n
        for k in (
            "CIELO",
            "REDECARD",
            "REDE ",
            "STONE",
            "PAGSEGURO",
            "GETNET",
            "SAFRAPAY",
            "CARTAO",
            "CREDITO",
            "DEBITO VISA",
            "DEBITO MASTER",
            "VISA ELECTRON",
            "MASTERCARD",
            "ELO ",
        )
    ):
        return "cartao"
    # Aplicação ANTES de cair em outros: APLIC. / APLIC / APLICACAO / APLIC.INVEST FACIL
    # (APLIC. com ponto — comum no Bradesco — NÃO é "APLIC " com espaço)
    if any(
        k in blob_n
        for k in (
            "APLIC.INVEST FACIL",
            "APLIC.INVEST",
            "APLICACAO",
            "APLICAC",
            "APLIC.",
            "APLIC ",
        )
    ):
        return "aplicacao"
    if any(
        k in blob_n
        for k in (
            "TARIFA",
            "TX ",
            "TAXA ",
            "IOF",
            "TED TAR",
            "DOC TAR",
            "PACOTE DE SERV",
            "MANUTENCAO",
        )
    ):
        return "tarifa"
    if any(
        k in blob_n
        for k in (
            "BOLETO",
            "LIQUIDACAO",
            "LIQ TIT",
            "LIQ.TIT",
            "TITULO COBRANCA",
            "COBRANCA",
            "PAGTO TIT",
        )
    ):
        if "LIQUIDACAO" in blob_n or "LIQ" in blob_n:
            return "liquidacao"
        return "boleto"
    if "PIX" in blob_n:
        return "pix"
    if trntype.upper() in ("CREDIT", "DEP", "DIRECTDEP"):
        return "pix"
    if trntype.upper() in ("DEBIT", "XFER", "PAYMENT"):
        return "outros"
    return "outros"


def ler_ofx(ofx_path: str, data: str) -> list[dict[str, Any]]:
    """Lê OFX e devolve só linhas do dia `data` (YYYY-MM-DD)."""
    path = Path(ofx_path)
    if not path.is_file():
        raise FileNotFoundError(f"OFX não encontrado: {ofx_path}")
    raw = path.read_bytes()
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            text = None
    if text is None:
        text = raw.decode("latin-1", errors="replace")

    # Normaliza tags fechadas <TAG>val</TAG> e abertas <TAG>val
    text = re.sub(r"</?[A-Za-z0-9\.]+>", lambda m: m.group(0).upper(), text)
    blocos = re.split(r"<STMTTRN>", text, flags=re.IGNORECASE)
    linhas: list[dict[str, Any]] = []
    for bloco in blocos[1:]:
        fim = re.split(r"</STMTTRN>", bloco, maxsplit=1, flags=re.IGNORECASE)[0]
        campos: dict[str, str] = {}
        for m in _OFX_TAG.finditer(fim):
            tag = m.group("tag").upper()
            if tag not in campos:
                campos[tag] = m.group("val").strip()
        dia = _parse_ofx_date(campos.get("DTPOSTED") or campos.get("DTUSER") or "")
        if dia != data:
            continue
        valor = abs(_parse_ofx_amount(campos.get("TRNAMT") or "0"))
        nome = (campos.get("NAME") or campos.get("PAYEE") or "").strip()
        memo = (campos.get("MEMO") or "").strip()
        if not nome and memo:
            nome = memo
        trntype = (campos.get("TRNTYPE") or "").strip()
        classe = _classify_line(nome, memo, trntype)
        linhas.append(
            {
                "data": dia,
                "valor": valor,
                "nome": nome,
                "memo": memo,
                "classe": classe,
                "trntype": trntype,
                "fitid": campos.get("FITID") or "",
            }
        )
    return linhas


# ---------------------------------------------------------------------------
# Cielo CSV — líquido e taxa entram na decisão de cartão
# ---------------------------------------------------------------------------

def _cielo_num(raw: str) -> float | None:
    s = (raw or "").strip()
    if (not s) or s == "-" or s.upper() in ("NULL", "N/A"):
        return None
    if s == (chr(92) + "N") or s == (chr(92) + chr(92) + "N"):
        return None
    try:
        return abs(_parse_ofx_amount(s))
    except (ValueError, TypeError):
        return None


def _cielo_key_match(headers: list[str], *candidates: str) -> str | None:
    normed = {h: "".join(c for c in h.lower() if c.isalnum()) for h in headers}
    for cand in candidates:
        c = "".join(x for x in cand.lower() if x.isalnum())
        for h, n in normed.items():
            if c == n or c in n:
                return h
    return None


def ler_cielo_csv(path: str | None) -> list[dict[str, Any]]:
    """Lê CSV Cielo e normaliza bruto / taxa / líquido por linha."""
    if not path:
        return []
    p = Path(path)
    if not p.is_file():
        return []
    raw_rows: list[dict[str, Any]] = []
    text = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = p.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = p.read_text(encoding="latin-1", errors="replace")
    sample = text[:4096]
    delim = ";" if sample.count(";") >= sample.count(",") else ","
    reader = csv.DictReader(text.splitlines(), delimiter=delim)
    for row in reader:
        raw_rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items() if k})
    if not raw_rows:
        return []
    headers = list(raw_rows[0].keys())
    k_bruto = _cielo_key_match(headers, "Valor bruto", "valorbruto", "bruto")
    k_taxa = _cielo_key_match(
        headers, "Valor Taxa/Tarifa", "Valor Taxa", "valortaxatarifa", "taxa", "tarifa"
    )
    k_liq = _cielo_key_match(headers, "Valor líquido", "Valor liquido", "valorliquido", "liquido")
    k_data = _cielo_key_match(headers, "Data de pagamento", "datapagamento", "data")
    k_status = _cielo_key_match(headers, "Status de pagamento", "status")
    out: list[dict[str, Any]] = []
    for row in raw_rows:
        bruto = _cielo_num(row.get(k_bruto or "", "")) if k_bruto else None
        taxa = _cielo_num(row.get(k_taxa or "", "")) if k_taxa else None
        liquido = _cielo_num(row.get(k_liq or "", "")) if k_liq else None
        if liquido is None and bruto is not None and taxa is not None:
            liquido = round(bruto - taxa, 2)
        if liquido is None and bruto is None:
            continue
        out.append(
            {
                "bruto": bruto,
                "taxa": taxa if taxa is not None else (
                    round(bruto - liquido, 2) if bruto is not None and liquido is not None else None
                ),
                "liquido": liquido if liquido is not None else bruto,
                "data_pagamento": row.get(k_data or "", "") if k_data else "",
                "status": row.get(k_status or "", "") if k_status else "",
                "raw": row,
            }
        )
    return out


def enriquecer_cartao_com_cielo(
    extrato: list[dict[str, Any]], cielo: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Anexa líquido/taxa Cielo nas linhas de cartão (match por líquido ±0,02)."""
    if not cielo:
        return extrato
    usados: set[int] = set()
    out: list[dict[str, Any]] = []
    for ln in extrato:
        item = dict(ln)
        if (item.get("classe") or "").lower() != "cartao":
            out.append(item)
            continue
        v = round(float(item.get("valor") or 0), 2)
        match_i = None
        for i, c in enumerate(cielo):
            if i in usados:
                continue
            liq = c.get("liquido")
            if liq is None:
                continue
            if abs(round(float(liq), 2) - v) <= 0.02:
                match_i = i
                break
        if match_i is None:
            out.append(item)
            continue
        usados.add(match_i)
        c = cielo[match_i]
        item["cielo_liquido"] = c.get("liquido")
        item["cielo_taxa"] = c.get("taxa")
        item["cielo_bruto"] = c.get("bruto")
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# Query API (leitura)
# ---------------------------------------------------------------------------

def _query_headers(token: str, tenant: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant": tenant,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _http_json(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: dict | None = None,
    timeout: int = 60,
) -> Any:
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = Request(url, data=data, headers=hdrs, method=method)
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        if not raw:
            return None
        return json.loads(raw)


def query_login(base: str, user: str, password: str, tenant: str) -> str:
    # API Query espera cdLogin / cdSenha (confirmado 200 em teste isolado).
    body = {"cdLogin": user, "cdSenha": password}
    try:
        r = _http_json(
            "POST",
            f"{base.rstrip('/')}/login",
            headers={"X-Tenant": tenant, "Accept": "application/json"},
            body=body,
        )
        if isinstance(r, dict):
            for key in ("token", "access_token", "accessToken", "bearer"):
                if r.get(key):
                    return str(r[key])
                data = r.get("data") or r.get("result") or {}
                if isinstance(data, dict) and data.get(key):
                    return str(data[key])
    except (HTTPError, URLError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"Falha no POST /login Query ({type(exc).__name__}). "
            "Confira QUERY_USER/QUERY_PASS/QUERY_TENANT."
        ) from exc
    raise RuntimeError("Falha no POST /login Query. Confira QUERY_USER/QUERY_PASS/QUERY_TENANT.")


def _normalize_titulos(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = (
            payload.get("data")
            or payload.get("items")
            or payload.get("content")
            or payload.get("result")
            or payload.get("results")
            or []
        )
        if isinstance(items, dict):
            items = items.get("items") or items.get("data") or []
    else:
        return []
    out: list[dict[str, Any]] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        valor = t.get("valor")
        if valor is None:
            valor = t.get("vrTitulo") or t.get("valor_titulo") or t.get("vlr") or 0
        nome = (
            t.get("nome")
            or t.get("cliente")
            or t.get("fornecedor")
            or t.get("nomeCliente")
            or t.get("razaoSocial")
            or t.get("pessoa")
            or ""
        )
        if isinstance(nome, dict):
            nome = nome.get("nome") or nome.get("razaoSocial") or ""
        tid = t.get("id") or t.get("idTitulo") or t.get("codigo") or t.get("nrTitulo")
        out.append(
            {
                "id": tid,
                "valor": round(float(str(valor).replace(",", ".")), 2),
                "nome": str(nome or ""),
                "raw": t,
            }
        )
    return out


def query_get_titulos(
    base: str,
    token: str,
    tenant: str,
    endpoint: str,
    dt_baixa_fim: str,
    caixa: int | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"dt_baixa_fim": dt_baixa_fim}
    if caixa is not None:
        params["caixa"] = caixa
        params["id_caixa"] = caixa
    url = f"{base.rstrip('/')}/{endpoint.lstrip('/')}?{urlencode(params)}"
    try:
        payload = _http_json("GET", url, headers=_query_headers(token, tenant))
        return _normalize_titulos(payload)
    except HTTPError as e:
        # tenta sem caixa se 400/404
        if e.code in (400, 404, 422) and "caixa" in params:
            params.pop("caixa", None)
            params.pop("id_caixa", None)
            url = f"{base.rstrip('/')}/{endpoint.lstrip('/')}?{urlencode(params)}"
            payload = _http_json("GET", url, headers=_query_headers(token, tenant))
            return _normalize_titulos(payload)
        raise


def _query_creds_missing() -> list[str]:
    """Lista o que falta no .env do Hermes. Vazio = ok para GET."""
    _ensure_env()
    missing: list[str] = []
    tenant = os.environ.get("QUERY_TENANT", "").strip()
    token = os.environ.get("QUERY_TOKEN", "").strip()
    user = os.environ.get("QUERY_USER", "").strip()
    password = os.environ.get("QUERY_PASS", "").strip()
    if not tenant:
        missing.append("QUERY_TENANT")
    if token:
        return missing
    if user and password:
        return missing
    # Sem TOKEN e sem par USER+PASS completo
    if not user and not password:
        missing.append("QUERY_TOKEN ou (QUERY_USER + QUERY_PASS)")
    else:
        if not user:
            missing.append("QUERY_USER")
        if not password:
            missing.append("QUERY_PASS")
    return missing


def carregar_query(data: str, caixa: int) -> tuple[list[dict], list[dict], list[str]]:
    """GETs read-only. Retorna (receber, pagar, avisos).

    Exige QUERY_TENANT e (QUERY_TOKEN ou QUERY_USER+QUERY_PASS).
    Não pula GET em silêncio — chame _query_creds_missing() antes.
    """
    _ensure_env()
    avisos: list[str] = []
    missing = _query_creds_missing()
    if missing:
        raise RuntimeError(
            "Credenciais Query faltando no .env do Hermes: "
            + ", ".join(missing)
            + ". Configure QUERY_TENANT e QUERY_TOKEN (ou QUERY_USER + QUERY_PASS) "
            "em ~/.hermes/.env. GETs não foram executados — execução interrompida."
        )
    base = os.environ.get("QUERY_API_BASE", "https://backend.acessoquery.com/api")
    tenant = os.environ.get("QUERY_TENANT", "").strip()
    token = os.environ.get("QUERY_TOKEN", "").strip()
    if not token:
        user = os.environ.get("QUERY_USER", "").strip()
        password = os.environ.get("QUERY_PASS", "").strip()
        try:
            token = query_login(base, user, password, tenant)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Login Query falhou: {exc}") from exc
    dt_fim = (datetime.strptime(data, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    receber: list[dict] = []
    pagar: list[dict] = []
    try:
        receber = query_get_titulos(base, token, tenant, "contas-receber", dt_fim, caixa)
    except Exception as exc:  # noqa: BLE001
        avisos.append(f"GET contas-receber falhou: {exc}")
    try:
        pagar = query_get_titulos(base, token, tenant, "contas-a-pagar", dt_fim, caixa)
    except Exception as exc:  # noqa: BLE001
        avisos.append(f"GET contas-a-pagar falhou: {exc}")
    return receber, pagar, avisos


# ---------------------------------------------------------------------------
# Execução — mgerencia (capturas de tela; só campos observados)
# ---------------------------------------------------------------------------

# Comuns (captura 1200 / 1100)
_ID_PESSOA_BRADESCO = "1117"
_ID_FILIAL = "1"
_ID_CAIXA = "4"
_TIPO_PAGAR_DINHEIRO = "1"  # Financeiro_Cobrancas_Pagar_Tipos_id
_ID_ASSISTENTE_PAGAR = "2"
_ID_ASSISTENTE_RECEITA = "3"
_ID_ASSISTENTE_BAIXA = "2"

# Aplicação — criar.consumo.snf
_APLICACAO_DS_HISTORICO = "aplicacao"
_APLICACAO_ID_PLANO = "30060005"

# Tarifa — mesmo endpoint, plano/histórico da captura
_TARIFA_DS_HISTORICO = "tarifa"
_TARIFA_ID_PLANO = "30060001"

# Receita (rentabilidade/resgate) — criar.novo + receber_transaction
_RECEITA_ID_PLANO = "30060006"
_RECEITA_ID_COBRANCA_TIPO = "115"  # PIX
_RECEITA_ID_PLANO_PGTO = "73"  # A VISTA PIX
_RECEITA_ID_MOEDA = "1"
_RECEITA_CD_MOEDA = "D"


def _data_br(data: str | None) -> str:
    """YYYY-MM-DD → DD/MM/YYYY (formato da tela)."""
    s = (data or "").strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        y, m, d = s.split("-")
        return f"{d}/{m}/{y}"
    return s


def _mgerencia_base() -> str:
    return os.environ.get(
        "QUERY_MGERENCIA_BASE", "https://acessoquery.com/mgerencia"
    ).rstrip("/")


def _mgerencia_host() -> str:
    return os.environ.get("QUERY_MGERENCIA_HOST", "valenlub.com.br").strip()


def mgerencia_session() -> Any:
    """Sessão cookie PHPSESSID após login mgerencia (cdLogin/cdSenha)."""
    _ensure_env()
    tenant = os.environ.get("QUERY_TENANT", "").strip()
    user = os.environ.get("QUERY_USER", "").strip()
    password = os.environ.get("QUERY_PASS", "").strip()
    if not tenant or not user or not password:
        raise RuntimeError(
            "Login mgerencia exige QUERY_TENANT, QUERY_USER e QUERY_PASS."
        )
    base = _mgerencia_base()
    host = _mgerencia_host()
    login_page = f"{base}/login/{host}/{tenant}"
    logon_url = f"{base}/usercontrol/logon/{host}/{tenant}&novo=1"
    jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(jar))
    opener.open(Request(login_page, headers={"User-Agent": "HermesValenLub/1.0"}), timeout=60).read()
    body = urlencode({"cdLogin": user, "cdSenha": password}).encode("utf-8")
    req = Request(
        logon_url,
        data=body,
        headers={
            "User-Agent": "HermesValenLub/1.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": login_page,
        },
        method="POST",
    )
    with opener.open(req, timeout=60) as resp:
        resp.read()
        final = resp.geturl()
    if "login" in final.lower() and "usercontrol/logon" not in final.lower():
        raise RuntimeError(f"Login mgerencia falhou (url={final}).")
    return opener


def _multipart_body(fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"----HermesBoundary{os.urandom(8).hex()}"
    lines: list[bytes] = []
    for name, value in fields.items():
        lines.append(f"--{boundary}".encode())
        lines.append(
            f'Content-Disposition: form-data; name="{name}"'.encode()
        )
        lines.append(b"")
        lines.append(str(value).encode("utf-8"))
    lines.append(f"--{boundary}--".encode())
    lines.append(b"")
    return b"\r\n".join(lines), boundary


def _post_urlencoded(opener: Any, url: str, fields: dict[str, str]) -> str:
    body = urlencode(fields).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={
            "User-Agent": "HermesValenLub/1.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
        },
        method="POST",
    )
    with opener.open(req, timeout=90) as resp:
        return resp.read().decode("utf-8", "replace")


def _post_multipart(opener: Any, url: str, fields: dict[str, str]) -> str:
    raw, boundary = _multipart_body(fields)
    req = Request(
        url,
        data=raw,
        headers={
            "User-Agent": "HermesValenLub/1.0",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "*/*",
        },
        method="POST",
    )
    with opener.open(req, timeout=90) as resp:
        return resp.read().decode("utf-8", "replace")


def query_criar_consumo_snf(
    opener: Any,
    *,
    valor: float,
    data_extrato: str,
    ds_historico: str,
    id_plano: str,
) -> str:
    """POST multipart criar.consumo.snf — despesa + baixa caixa 4 (captura 1200)."""
    data_br = _data_br(data_extrato)
    vr = f"{abs(float(valor)):.2f}"
    fields = {
        "fields[Financeiro_Cobrancas_Pagar][idPessoa]": _ID_PESSOA_BRADESCO,
        "fields[Financeiro_Cobrancas_Pagar][dsHistorico]": ds_historico,
        "fields[Financeiro_Cobrancas_Pagar][vrCobrancaPagar]": vr,
        "fields[Financeiro_Cobrancas_Pagar][dtVencimentoCobrancaPagar]": data_br,
        "fields[Financeiro_Cobrancas_Pagar][dtCompetencia]": data_br,
        "fields[Financeiro_Cobrancas_Pagar][Financeiro_Cobrancas_Pagar_Tipos_id]": _TIPO_PAGAR_DINHEIRO,
        "fields[Financeiro_Cobrancas_Pagar][idFilial]": _ID_FILIAL,
        "fields[Financeiro_Cobrancas_Pagar][idPlanoDeContasSubconta]": id_plano,
        "fields[Financeiro_Cobrancas_Pagar][idCaixaBaixa]": _ID_CAIXA,
        "fields[Financeiro_Cobrancas_Pagar][dtCobrancaPagarBaixa]": data_br,
        "fields[Financeiro_Cobrancas_Pagar][idAssistente]": _ID_ASSISTENTE_PAGAR,
    }
    url = f"{_mgerencia_base()}/scripts/fiscal/compras/actions/criar.consumo.snf"
    return _post_multipart(opener, url, fields)


def query_criar_consumo_aplicacao(
    opener: Any,
    *,
    valor: float,
    data_extrato: str,
) -> str:
    """Compat: aplicação (plano 30060005)."""
    return query_criar_consumo_snf(
        opener,
        valor=valor,
        data_extrato=data_extrato,
        ds_historico=_APLICACAO_DS_HISTORICO,
        id_plano=_APLICACAO_ID_PLANO,
    )


def query_criar_consumo_tarifa(
    opener: Any,
    *,
    valor: float,
    data_extrato: str,
) -> str:
    """Tarifa — mesma tela 1200, plano 30060001 / hist tarifa (captura)."""
    return query_criar_consumo_snf(
        opener,
        valor=valor,
        data_extrato=data_extrato,
        ds_historico=_TARIFA_DS_HISTORICO,
        id_plano=_TARIFA_ID_PLANO,
    )


def query_criar_receita_avulsa(
    opener: Any,
    *,
    valor: float,
    data_extrato: str,
    ds_historico: str,
) -> str:
    """POST urlencoded criar.novo — receita 1100 (caixa baixa vazio). Captura tela."""
    data_br = _data_br(data_extrato)
    vr = f"{abs(float(valor)):.2f}"
    fields = {
        "fields[postBack][isAssistente]": "true",
        "fields[postBack][idAssistente]": _ID_ASSISTENTE_RECEITA,
        "fields[Financeiro_Cobrancas_Receber][idFilial]": _ID_FILIAL,
        "fields[Financeiro_Cobrancas_Receber][idPessoa]": _ID_PESSOA_BRADESCO,
        "fields[Financeiro_Cobrancas_Receber][dsHistorico]": ds_historico,
        "fields[Financeiro_Cobrancas_Receber][vrCobrancaReceber]": vr,
        "fields[Financeiro_Cobrancas_Receber][dtCompetencia]": data_br,
        "fields[Financeiro_Cobrancas_Receber][dtPagamento]": data_br,
        "fields[Financeiro_Cobrancas_Receber][idCaixaBaixa]": "",
        "fields[Financeiro_Cobrancas_Receber][idPlanoDeContasSubconta]": _RECEITA_ID_PLANO,
        "fields[Financeiro_Cobrancas_Receber][idCobrancaTipo]": _RECEITA_ID_COBRANCA_TIPO,
        "fields[Financeiro_Cobrancas_Receber][Financeiro_PlanosDePagamentos_id]": _RECEITA_ID_PLANO_PGTO,
        "fields[Financeiro_Cobrancas_Receber][con]": "financeiro",
        "fields[Financeiro_Cobrancas_Receber][view]": "cobrancas_receber",
        "fields[Financeiro_Cobrancas_Receber][act]": "criar.novo",
        "fields[Financeiro_Cobrancas_Receber][semRedirecionamento]": "1",
        "fields[Financeiro_Cobrancas_Receber][idAssistente]": _ID_ASSISTENTE_RECEITA,
        "fields[Financeiro_Cobrancas_Receber][isAssistente]": "true",
        "fields[Financeiro_Cobrancas_Receber][forceLog]": "1",
        "fields[Financeiro_Cobrancas_Receber][vrDesconto]": "0",
        "fields[Financeiro_Cobrancas_Receber][idMoeda]": _RECEITA_ID_MOEDA,
        "fields[Financeiro_Cobrancas_Receber][vrPcntDesconto]": "0",
    }
    url = f"{_mgerencia_base()}/scripts/financeiro/cobrancas_receber/actions/criar.novo"
    return _post_urlencoded(opener, url, fields)


def _parse_id_cobranca_sucesso(resp: str) -> str | None:
    """Extrai cód Nº NNNN da resposta [Sucesso] criar.novo."""
    m = re.search(r"c[oó]d\s*N[ºo°]?\s*(\d+)", resp or "", re.I)
    if m:
        return m.group(1)
    m = re.search(r"N[ºo°]\s*(\d+)", resp or "", re.I)
    return m.group(1) if m else None


def query_baixar_receber(
    opener: Any,
    *,
    id_cobranca: str,
    valor: float,
    data_extrato: str,
) -> str:
    """POST receber_transaction — Receber Pagamento (juros/multa 0, caixa 4).

    Campos da captura na tela (Concluir). nmCaixa* é dinâmico; idCaixa=4 basta.
    """
    data_br = _data_br(data_extrato)
    vr = f"{abs(float(valor)):.2f}"
    fields = {
        "fields[postBack][isAssistente]": "",
        "fields[postBack][idAssistente]": _ID_ASSISTENTE_BAIXA,
        "fields[Financeiro_Cobrancas_Receber][vrTotal]": vr,
        "fields[Financeiro_Cobrancas_Receber][vrJuros]": "0",
        "fields[Financeiro_Cobrancas_Receber][vrMulta]": "0",
        "fields[Financeiro_Cobrancas_Receber][vrDesconto]": "0",
        "fields[Financeiro_Cobrancas_Receber][vrAcrescimo]": "0",
        "fields[Financeiro_CreditosDeClientes][Financeiro_CreditosDeClientes_valor]": "",
        "fields[Financeiro_Cobrancas_Receber][vrTaxas]": "0.00",
        "fields[Financeiro_Cobrancas_Receber][vrCobrancaReceber]": vr,
        "fields[Financeiro_Cobrancas_Receber][idCaixa]": _ID_CAIXA,
        "fields[Financeiro_Cobrancas_Receber][idMoeda]": _RECEITA_ID_MOEDA,
        "fields[Financeiro_Cobrancas_Receber][cdMoeda]": _RECEITA_CD_MOEDA,
        "fields[Financeiro_Cobrancas_Receber][dtCobrancaReceberRecebimento]": data_br,
        "fields[Financeiro_Cobrancas_Receber][dsObservacoesBaixa]": "",
        "fields[Financeiro_Cobrancas_Receber][idCobrancaReceber]": str(id_cobranca),
    }
    url = (
        f"{_mgerencia_base()}"
        "/scripts/financeiro/cobrancas_receber/actions/receber_transaction"
    )
    return _post_urlencoded(opener, url, fields)


def _data_linha(ln: dict) -> str:
    return str(
        ln.get("data") or ln.get("dt") or ln.get("data_extrato") or ""
    )


def _gravar_despesa_snf(
    opener: Any,
    item: dict,
    ln: dict,
    *,
    ds_historico: str,
    id_plano: str,
) -> dict:
    resp = query_criar_consumo_snf(
        opener,
        valor=float(ln.get("valor") or 0),
        data_extrato=_data_linha(ln),
        ds_historico=ds_historico,
        id_plano=id_plano,
    )
    ok = "[Sucesso]" in resp
    item["status"] = "gravado" if ok else "erro"
    item["gravou"] = ok
    item["endpoint"] = (
        "/mgerencia/scripts/fiscal/compras/actions/criar.consumo.snf"
    )
    item["plano"] = id_plano
    item["historico"] = ds_historico
    item["resposta"] = (resp or "")[:300]
    if not ok:
        item["motivo"] = "Resposta sem [Sucesso]."
    return item


def _gravar_receita_e_baixa(
    opener: Any,
    item: dict,
    ln: dict,
    *,
    ds_historico: str,
) -> tuple[dict, dict | None]:
    """criar.novo → parse id → receber_transaction. Retorna (item, criado?)."""
    valor = float(ln.get("valor") or 0)
    data_ex = _data_linha(ln)
    resp_cria = query_criar_receita_avulsa(
        opener,
        valor=valor,
        data_extrato=data_ex,
        ds_historico=ds_historico,
    )
    id_cob = _parse_id_cobranca_sucesso(resp_cria)
    criado = {
        **item,
        "tipo": "receita_avulsa",
        "historico": ds_historico,
        "id_cobranca": id_cob,
        "resposta_criar": (resp_cria or "")[:300],
    }
    if "[Sucesso]" not in (resp_cria or "") or not id_cob:
        item["status"] = "erro"
        item["gravou"] = False
        item["endpoint"] = (
            "/mgerencia/scripts/financeiro/cobrancas_receber/actions/criar.novo"
        )
        item["resposta"] = (resp_cria or "")[:300]
        item["motivo"] = "criar.novo sem [Sucesso] ou sem cód."
        criado["status"] = "erro"
        return item, criado

    resp_baixa = query_baixar_receber(
        opener,
        id_cobranca=id_cob,
        valor=valor,
        data_extrato=data_ex,
    )
    ok = "[Sucesso]" in (resp_baixa or "")
    item["status"] = "gravado" if ok else "erro"
    item["gravou"] = ok
    item["id_cobranca"] = id_cob
    item["endpoint"] = "criar.novo + receber_transaction"
    item["resposta"] = (resp_baixa or "")[:300]
    if not ok:
        item["motivo"] = "Baixa sem [Sucesso] (título pode ter nascido Aberto)."
    criado["status"] = "criado"
    criado["baixado"] = ok
    return item, criado



_CARTAO_RE = re.compile(
    r"cart[aã]o|cielo|rede|stone|getnet|pagseguro|safrapay|visa|master|amex|elo\b",
    re.I,
)


def _data_periodo_br(data: str | None) -> str:
    """YYYY-MM-DD → DD-MM-YYYY (filtro dtPeriodo da conciliação)."""
    s = (data or "").strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        y, m, d = s.split("-")
        return f"{d}-{m}-{y}"
    if re.match(r"^\d{2}/\d{2}/\d{4}$", s):
        d, m, y = s.split("/")
        return f"{d}-{m}-{y}"
    return s.replace("/", "-")


def _mgerencia_get_json(opener: Any, path_qs: str) -> Any:
    url = f"{_mgerencia_base()}/{path_qs.lstrip('/')}"
    req = Request(
        url,
        headers={
            "User-Agent": "HermesValenLub/1.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        },
        method="GET",
    )
    with opener.open(req, timeout=90) as resp:
        raw = resp.read().decode("utf-8", "replace")
    raw = raw.strip()
    if not raw or raw[0] not in "{[":
        raise RuntimeError(f"Resposta não-JSON em {path_qs[:80]}: {raw[:120]!r}")
    return json.loads(raw)


def query_extrato_pendente(
    opener: Any,
    *,
    id_caixa: str,
    data_extrato: str,
) -> list[dict]:
    """GET extrato.json — linhas a conciliar do dia (captura 1311)."""
    peri = _data_periodo_br(data_extrato)
    path = (
        f"pure/financeiro/conciliacao/extrato.json&idCaixa={id_caixa}"
        f"&modo=pendentes&dtPeriodo={peri}%2C{peri}&cursor=&comSugestoes=0"
    )
    payload = _mgerencia_get_json(opener, path)
    txs = payload.get("transacoes") if isinstance(payload, dict) else None
    return list(txs or [])


def query_movimentacoes_para_alvo(
    opener: Any,
    *,
    id_caixa: str,
    data_extrato: str,
    valor: float,
    tp: str = "Credito",
) -> list[dict]:
    """GET movimentacoes_abertas.json — candidatos ao lote (captura Buscar)."""
    peri = _data_periodo_br(data_extrato)
    # janela larga como a tela (±30d em torno do dia)
    try:
        dt = datetime.strptime(data_extrato[:10], "%Y-%m-%d")
    except ValueError:
        dt = None
    if dt is not None:
        ini = (dt - timedelta(days=30)).strftime("%d-%m-%Y")
        fim = (dt + timedelta(days=30)).strftime("%d-%m-%Y")
        peri = f"{ini}%2C{fim}"
    else:
        peri = f"{peri}%2C{peri}"
    vr = f"{abs(float(valor)):.2f}"
    path = (
        f"pure/financeiro/conciliacao/movimentacoes_abertas.json&idCaixa={id_caixa}"
        f"&dtPeriodo={peri}&tp={tp}&vrAlvo={vr}&termo="
    )
    payload = _mgerencia_get_json(opener, path)
    movs = payload.get("movimentacoes") if isinstance(payload, dict) else None
    return list(movs or [])


def _subset_sum_ids(
    itens: list[tuple[str, float]],
    alvo: float,
    *,
    limite: int = 60,
) -> list[str] | None:
    """Subset-sum em centavos (backtrack podado); devolve ids cuja soma == alvo."""
    T = int(round(abs(float(alvo)) * 100))
    arr: list[tuple[str, int]] = []
    for iid, vr in itens:
        c = int(round(abs(float(vr)) * 100))
        if 0 < c <= T:
            arr.append((str(iid), c))
    arr.sort(key=lambda x: -x[1])
    use = arr[:limite]
    n = len(use)
    # prefixos para poda
    suf = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suf[i] = suf[i + 1] + use[i][1]
    found: list[str] | None = None

    def bt(i: int, resto: int, path: list[int]) -> bool:
        nonlocal found
        if resto == 0:
            found = [use[j][0] for j in path]
            return True
        if i >= n or resto < 0 or suf[i] < resto:
            return False
        # pular itens maiores que o resto
        while i < n and use[i][1] > resto:
            i += 1
        if i >= n:
            return False
        # take
        path.append(i)
        if bt(i + 1, resto - use[i][1], path):
            return True
        path.pop()
        # skip
        return bt(i + 1, resto, path)

    bt(0, T, [])
    return found


def query_conciliar_lote(
    opener: Any,
    *,
    id_extrato: str,
    ids_movimentacao: list[str],
) -> str:
    """POST actions&id=conciliar — ligar extrato ↔ movimentações (captura 1311)."""
    fields = {
        "Financeiro_Caixas_Extratos_id": str(id_extrato),
        "idsMovimentacao": ",".join(str(i) for i in ids_movimentacao),
    }
    url = (
        f"{_mgerencia_base()}"
        "/scripts/financeiro/conciliacao/actions&id=conciliar"
    )
    return _post_urlencoded(opener, url, fields)


def _eh_cartao_mov(m: dict) -> bool:
    blob = " ".join(
        str(m.get(k) or "")
        for k in ("hist", "dsHistorico", "pessoa", "nmPessoa", "origem")
    )
    return bool(_CARTAO_RE.search(blob))


def _gravar_liquidacao(opener: Any, item: dict, ln: dict) -> dict:
    """Lote de boleto: achar linha OFX + movimentações do dia (sem cartão) e conciliar."""
    data_ex = _data_linha(ln)
    valor = abs(float(ln.get("valor") or 0))
    nome = (ln.get("nome") or ln.get("memo") or "").upper()
    txs = query_extrato_pendente(opener, id_caixa=_ID_CAIXA, data_extrato=data_ex)
    # casa por valor ±0,02 e histórico LIQUID* se houver
    cand = []
    for t in txs:
        try:
            vr = abs(float(t.get("vr") or t.get("valor") or 0))
        except (TypeError, ValueError):
            continue
        if abs(vr - valor) > 0.02:
            continue
        hist = str(t.get("hist") or t.get("dsHistorico") or "").upper()
        if "LIQUID" in nome or "LIQUID" in hist or "BOLETO" in nome:
            cand.append(t)
        elif not cand:
            cand.append(t)
    # prefer LIQUID in hist
    liq = [t for t in cand if "LIQUID" in str(t.get("hist") or "").upper()]
    tx = (liq or cand or [None])[0]
    if not tx:
        item["status"] = "erro"
        item["gravou"] = False
        item["motivo"] = (
            f"Extrato pendente não encontrado (caixa {_ID_CAIXA}, "
            f"data {data_ex}, valor {valor:.2f})."
        )
        return item
    id_extrato = str(tx.get("id") or tx.get("Financeiro_Caixas_Extratos_id") or "")
    if not id_extrato:
        item["status"] = "erro"
        item["gravou"] = False
        item["motivo"] = "Linha de extrato sem id."
        return item

    movs = query_movimentacoes_para_alvo(
        opener, id_caixa=_ID_CAIXA, data_extrato=data_ex, valor=valor, tp="Credito"
    )
    # skill: recebimentos do dia; desmarque cartão
    dia_br = _data_br(data_ex)  # DD/MM/YYYY
    filtrados: list[tuple[str, float]] = []
    for m in movs:
        if _eh_cartao_mov(m):
            continue
        mid = m.get("idMovimentacao") or m.get("id")
        if mid is None:
            continue
        try:
            vr = abs(float(m.get("vr") or m.get("valor") or 0))
        except (TypeError, ValueError):
            continue
        if vr <= 0:
            continue
        dt = str(m.get("data") or m.get("dt") or "")
        # prefer same calendar day; if none match later, fall back
        filtrados.append((str(mid), vr, dt))

    mesmo_dia = [
        (i, v) for (i, v, dt) in filtrados if dia_br in dt or dt.replace("-", "/") == dia_br
        or dt[0:10] == data_ex[:10]
    ]
    pool = mesmo_dia or [(i, v) for (i, v, _dt) in filtrados]
    ids = _subset_sum_ids(pool, valor)
    if not ids:
        item["status"] = "erro"
        item["gravou"] = False
        item["motivo"] = (
            f"Lote sem combinação que feche {valor:.2f} "
            f"(movs={len(pool)}, extrato={id_extrato})."
        )
        item["id_extrato"] = id_extrato
        return item

    resp = query_conciliar_lote(
        opener, id_extrato=id_extrato, ids_movimentacao=ids
    )
    ok = False
    try:
        js = json.loads(resp)
        ok = bool(js.get("isOk")) or "sucesso" in str(js.get("message") or "").lower()
        item["resposta"] = json.dumps(js, ensure_ascii=False)[:300]
        item["vinculadas"] = js.get("vinculadas")
    except json.JSONDecodeError:
        ok = "[Sucesso]" in resp or "sucesso" in resp.lower()
        item["resposta"] = (resp or "")[:300]
    item["status"] = "gravado" if ok else "erro"
    item["gravou"] = ok
    item["endpoint"] = (
        "/mgerencia/scripts/financeiro/conciliacao/actions&id=conciliar"
    )
    item["id_extrato"] = id_extrato
    item["ids_movimentacao"] = ids
    if not ok:
        item["motivo"] = "Conciliação sem isOk."
    return item



def _executar_gravar(linhas_gravar: list[dict], modo: str) -> tuple[list[dict], list[dict]]:
    """Em simular: não escreve. Em executar: aplicação/tarifa/receita/liquidação."""
    criados: list[dict] = []
    executados: list[dict] = []
    opener = None
    for ln in linhas_gravar:
        classe = (ln.get("classe") or "").lower()
        item = {
            "classe": classe,
            "valor": ln.get("valor"),
            "nome": ln.get("nome"),
            "id": ln.get("id"),
            "acao": ln.get("acao"),
            "veredito": ln.get("veredito"),
            "data": ln.get("data"),
        }
        if modo == "simular":
            item["status"] = "simulado"
            if classe in ("resgate", "rentabilidade"):
                criados.append({**item, "tipo": "receita_avulsa_seria_criada"})
            if classe == "aplicacao":
                item["tipo"] = "despesa_aplicacao_seria_criada"
            if classe == "tarifa":
                item["tipo"] = "despesa_tarifa_seria_criada"
            if classe == "liquidacao":
                item["tipo"] = "lote_boleto_seria_conciliado"
            executados.append(item)
            continue

        try:
            if classe in ("aplicacao", "tarifa", "resgate", "rentabilidade", "liquidacao"):
                if opener is None:
                    opener = mgerencia_session()

            if classe == "aplicacao":
                item = _gravar_despesa_snf(
                    opener,
                    item,
                    ln,
                    ds_historico=_APLICACAO_DS_HISTORICO,
                    id_plano=_APLICACAO_ID_PLANO,
                )
                executados.append(item)
                continue

            if classe == "tarifa":
                item = _gravar_despesa_snf(
                    opener,
                    item,
                    ln,
                    ds_historico=_TARIFA_DS_HISTORICO,
                    id_plano=_TARIFA_ID_PLANO,
                )
                executados.append(item)
                continue

            if classe in ("resgate", "rentabilidade"):
                hist = "resgate" if classe == "resgate" else "rentabilidade"
                item, criado = _gravar_receita_e_baixa(
                    opener, item, ln, ds_historico=hist
                )
                if criado is not None:
                    criados.append(criado)
                executados.append(item)
                continue

            if classe == "liquidacao":
                item = _gravar_liquidacao(opener, item, ln)
                executados.append(item)
                continue

        except Exception as exc:  # noqa: BLE001
            item["status"] = "erro"
            item["gravou"] = False
            item["motivo"] = str(exc)
            executados.append(item)
            continue

        # demais classes sem captura
        item["status"] = "stub_noop"
        item["gravou"] = False
        item["motivo"] = (
            "AVISO: modo executar — escrita implementada para aplicacao, "
            "tarifa, rentabilidade, resgate e liquidacao. "
            f"Classe '{classe}': use a tela."
        )
        executados.append(item)
    return criados, executados


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _montar_json_pdf(
    data: str,
    linhas: list[dict],
    executados: list[dict],
    ariadna: list[dict],
    modo: str,
) -> dict[str, Any]:
    by_classe: dict[str, list[dict]] = {}
    for e in executados:
        by_classe.setdefault((e.get("classe") or "outros").lower(), []).append(e)
    fechou = []
    for classe, items in sorted(by_classe.items()):
        feito = items[0].get("acao") or "Baixado e ligado."
        if modo == "simular":
            feito = f"[simular] {feito}"
        elif items[0].get("status") == "stub_noop":
            feito = f"[pendente tela] {feito}"
        fechou.append({"classe": classe, "qtd": len(items), "feito": feito})
    falta_linhas = []
    for a in ariadna:
        falta_linhas.append(
            {
                "valor": f"{float(a.get('valor') or 0):.2f}".replace(".", ","),
                "classe": a.get("classe") or "",
                "acao": a.get("acao") or f"Extrato: {a.get('nome') or ''}",
            }
        )
    conciliado = len(executados)
    falta = len(ariadna)
    fechado = falta == 0 and conciliado > 0
    if conciliado == 0 and falta == 0:
        fechado = False
    return {
        "data": data,
        "linhas": len(linhas),
        "fecha": data,
        "fechado": fechado,
        "conciliado": conciliado,
        "falta": falta,
        "ajuste": 0,
        "fechou": fechou
        or ([{"classe": "—", "qtd": 0, "feito": "Nada gravado nesta passagem."}] if not falta_linhas else []),
        "falta_linhas": falta_linhas,
        "gravado": (
            f"Modo {modo}. GRAVAR {conciliado}. ARIADNA {falta}."
            + (" Aplicacao via criar.consumo.snf; demais classes stub." if modo == "executar" else "")
        ),
    }


def gerar_pdf(dados: dict[str, Any], pdf_path: str) -> str:
    gerar_py = REL_DIR / "gerar.py"
    if not gerar_py.is_file():
        raise FileNotFoundError(f"gerar.py ausente: {gerar_py}")
    Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(dados, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name
    import subprocess

    py = sys.executable
    # garante reportlab no mesmo interpretador; se faltar, tenta .venv do cérebro
    venv_py = ROOT / ".venv" / "bin" / "python"
    runners = [py]
    if venv_py.is_file() and str(venv_py) != py:
        runners.insert(0, str(venv_py))
    last_err = ""
    for runner in runners:
        try:
            proc = subprocess.run(
                [runner, str(gerar_py), tmp_path, pdf_path],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0 and Path(pdf_path).is_file():
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                return pdf_path
            last_err = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
        except OSError as exc:
            last_err = str(exc)
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    raise RuntimeError(f"Falha ao gerar PDF: {last_err}")


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def conciliar_dia_valenlub(
    data: str,
    ofx_path: str,
    caixa: int = 4,
    pdf_path: str | None = None,
    cielo_csv_path: str | None = None,
    modo: str = "simular",
) -> ResultadoConciliacao:
    """Concilia o caixa 4 do dia. Skill 1.33.0.

    modo: "simular" (default) ou "executar".
    """
    erros: list[str] = []
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data or ""):
        return ResultadoConciliacao(
            status="erro",
            data=data or "",
            caixa=caixa,
            modo=modo,
            erros=["data deve ser YYYY-MM-DD"],
            mensagem="Bloqueio: data inválida.",
        )
    if modo not in ("simular", "executar"):
        return ResultadoConciliacao(
            status="erro",
            data=data,
            caixa=caixa,
            modo=modo,
            erros=['modo deve ser "simular" ou "executar"'],
            mensagem="Bloqueio: modo inválido.",
        )
    if not ofx_path or not Path(ofx_path).is_file():
        return ResultadoConciliacao(
            status="erro",
            data=data,
            caixa=caixa,
            modo=modo,
            erros=[f"OFX ausente: {ofx_path}"],
            mensagem="Sem arquivo. Pare.",
        )

    try:
        extrato = ler_ofx(ofx_path, data)
    except Exception as exc:  # noqa: BLE001
        return ResultadoConciliacao(
            status="erro",
            data=data,
            caixa=caixa,
            modo=modo,
            erros=[f"OFX: {exc}"],
            mensagem="Bloqueio: falha ao ler OFX.",
        )

    if not extrato:
        return ResultadoConciliacao(
            status="vazio",
            data=data,
            caixa=caixa,
            modo=modo,
            contagens={"linhas": 0, "gravar": 0, "ariadna": 0},
            mensagem=f"Nenhuma linha OFX no dia {data}.",
        )

    # Credenciais Query obrigatórias — não pular GET
    missing = _query_creds_missing()
    if missing:
        msg = (
            "Bloqueio: credenciais Query faltando no .env do Hermes: "
            + ", ".join(missing)
            + ". Configure QUERY_TENANT e QUERY_TOKEN (ou QUERY_USER + QUERY_PASS) "
            "em ~/.hermes/.env. GET não foi pulado — execução parou."
        )
        return ResultadoConciliacao(
            status="erro",
            data=data,
            caixa=caixa,
            modo=modo,
            contagens={"linhas": len(extrato), "gravar": 0, "ariadna": 0},
            linhas=extrato,
            erros=[msg],
            mensagem=msg,
        )

    # CSV Cielo: líquido + taxa alimentam decisão de cartão
    cielo_rows = ler_cielo_csv(cielo_csv_path)
    extrato = enriquecer_cartao_com_cielo(extrato, cielo_rows)

    try:
        receber, pagar, avisos = carregar_query(data, caixa)
    except RuntimeError as exc:
        return ResultadoConciliacao(
            status="erro",
            data=data,
            caixa=caixa,
            modo=modo,
            contagens={"linhas": len(extrato), "gravar": 0, "ariadna": 0},
            linhas=extrato,
            erros=[str(exc)],
            mensagem=str(exc),
        )
    erros.extend(avisos)

    decisoes = decidir(extrato, receber, pagar)
    gravar = [d for d in decisoes if d.get("veredito") == "GRAVAR"]
    ariadna = [d for d in decisoes if d.get("veredito") == "ARIADNA"]

    criados, executados = _executar_gravar(gravar, modo)

    if pdf_path is None:
        out_dir = ROOT / "cache" / "conciliacao"
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(out_dir / f"conciliacao-{data}-caixa{caixa}.pdf")

    pdf_ok: str | None = None
    try:
        dados_pdf = _montar_json_pdf(data, decisoes, executados, ariadna, modo)
        pdf_ok = gerar_pdf(dados_pdf, pdf_path)
    except Exception as exc:  # noqa: BLE001
        erros.append(f"PDF: {exc}")

    status = "ok"
    if erros and not receber and not pagar:
        status = "parcial"
    if ariadna:
        status = "aberto" if status == "ok" else status
    if not ariadna and executados:
        status = "fechado" if status in ("ok", "fechado") else status

    return ResultadoConciliacao(
        status=status,
        data=data,
        caixa=caixa,
        modo=modo,
        contagens={
            "linhas": len(decisoes),
            "gravar": len(gravar),
            "ariadna": len(ariadna),
            "receber_query": len(receber),
            "pagar_query": len(pagar),
        },
        criados=criados,
        ariadna=[
            {
                "valor": a.get("valor"),
                "nome": a.get("nome"),
                "classe": a.get("classe"),
                "acao": a.get("acao"),
            }
            for a in ariadna
        ],
        linhas=decisoes,
        pdf_path=pdf_ok,
        erros=erros,
        executados=executados,
        mensagem=(
            (
                "Passagem feita."
                if not ariadna
                else f"Passagem feita. ARIADNA {len(ariadna)}."
            )
            + (
                " AVISO: modo executar é stub — nada foi gravado no Query "
                "(API de escrita não documentada)."
                if modo == "executar"
                else ""
            )
        ),
    )


# ---------------------------------------------------------------------------
# Registro opcional no Hermes tools/ (registry.register)
# ---------------------------------------------------------------------------

def _hermes_handler(args: dict, **kwargs) -> str:  # noqa: ARG001
    res = conciliar_dia_valenlub(
        data=str(args.get("data") or ""),
        ofx_path=str(args.get("ofx_path") or ""),
        caixa=int(args.get("caixa") or 4),
        pdf_path=args.get("pdf_path"),
        cielo_csv_path=args.get("cielo_csv_path"),
        modo=str(args.get("modo") or "simular"),
    )
    return json.dumps(res.to_dict(), ensure_ascii=False, default=str)


_HERMES_SCHEMA = {
    "name": "conciliar_dia_valenlub",
    "description": (
        "Concilia o caixa 4 ValenLub no dia informado (skill 1.33.0). "
        "Lê OFX, GET Query contas-receber/contas-a-pagar, decide GRAVAR/ARIADNA, "
        "executa ou simula, gera PDF no visual aprovado."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "data": {"type": "string", "description": "Dia YYYY-MM-DD"},
            "ofx_path": {"type": "string", "description": "Caminho do arquivo OFX"},
            "caixa": {"type": "integer", "description": "Caixa (default 4)", "default": 4},
            "pdf_path": {"type": "string", "description": "Saída PDF opcional"},
            "cielo_csv_path": {"type": "string", "description": "CSV Cielo opcional"},
            "modo": {
                "type": "string",
                "enum": ["simular", "executar"],
                "description": "simular (default) ou executar",
                "default": "simular",
            },
        },
        "required": ["data", "ofx_path"],
    },
}

try:
    from tools.registry import registry  # type: ignore

    registry.register(
        name="conciliar_dia_valenlub",
        toolset="valenlub",
        schema=_HERMES_SCHEMA,
        handler=_hermes_handler,
    )
except Exception:
    pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Conciliação caixa 4 ValenLub")
    p.add_argument("--data", required=True)
    p.add_argument("--ofx", required=True, dest="ofx_path")
    p.add_argument("--caixa", type=int, default=4)
    p.add_argument("--pdf", dest="pdf_path", default=None)
    p.add_argument("--cielo", dest="cielo_csv_path", default=None)
    p.add_argument("--modo", choices=("simular", "executar"), default="simular")
    p.add_argument("--json-out", dest="json_out", default=None)
    args = p.parse_args()
    res = conciliar_dia_valenlub(
        data=args.data,
        ofx_path=args.ofx_path,
        caixa=args.caixa,
        pdf_path=args.pdf_path,
        cielo_csv_path=args.cielo_csv_path,
        modo=args.modo,
    )
    payload = res.to_dict()
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if res.status in ("ok", "fechado", "aberto", "parcial", "vazio") else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
