#!/usr/bin/env python3
"""Conciliação do caixa 4 ValenLub — skill 1.33.0.

Função principal: conciliar_dia_valenlub(...)

Variáveis de ambiente (nunca hardcode):
  QUERY_API_BASE   (default https://backend.acessoquery.com/api)
  QUERY_TOKEN      Bearer já obtido (opcional se USER/PASS)
  QUERY_TENANT     X-Tenant obrigatório
  QUERY_USER / QUERY_PASS  para POST /login quando sem TOKEN
  QUERY_CAIXA      id do caixa (default = arg caixa)

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
from urllib.request import Request, urlopen

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
    if any(k in blob_n for k in ("APLICACAO", "APLIC ", "APLICAC")):
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
    with p.open(encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delim = ";" if sample.count(";") >= sample.count(",") else ","
        reader = csv.DictReader(f, delimiter=delim)
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
    payload = {"usuario": user, "senha": password, "email": user, "password": password}
    # tenta formatos comuns
    for body in (
        {"usuario": user, "senha": password},
        {"email": user, "password": password},
        {"login": user, "senha": password},
        payload,
    ):
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
        except (HTTPError, URLError, json.JSONDecodeError, KeyError, TypeError):
            continue
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
# Execução (stubs seguros — sem inventar API destrutiva)
# ---------------------------------------------------------------------------

def _executar_gravar(linhas_gravar: list[dict], modo: str) -> tuple[list[dict], list[dict]]:
    """Em simular: não escreve. Em executar: stub documentado (no-op)."""
    criados: list[dict] = []
    executados: list[dict] = []
    for ln in linhas_gravar:
        classe = (ln.get("classe") or "").lower()
        item = {
            "classe": classe,
            "valor": ln.get("valor"),
            "nome": ln.get("nome"),
            "id": ln.get("id"),
            "acao": ln.get("acao"),
            "veredito": ln.get("veredito"),
        }
        if modo == "simular":
            item["status"] = "simulado"
            if classe in ("resgate", "rentabilidade"):
                criados.append({**item, "tipo": "receita_avulsa_seria_criada"})
            executados.append(item)
            continue
        # modo executar: escrita Query não documentada → stub explícito (NÃO grava)
        item["status"] = "stub_noop"
        item["gravou"] = False
        item["motivo"] = (
            "AVISO: modo executar é stub. API de escrita Query não documentada. "
            "Nada foi gravado no Query. Use a tela conforme a skill 1.33.0."
        )
        if classe in ("resgate", "rentabilidade"):
            criados.append({**item, "tipo": "receita_avulsa_pendente_tela"})
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
            + (" Escritas Query em stub (sem endpoint documentado)." if modo == "executar" else "")
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
