#!/usr/bin/env python3
"""Conciliação do caixa 4 ValenLub — skill 1.38.3.

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
            "DEBITO VISA",
            "DEBITO MASTER",
            "VISA ELECTRON",
            "MASTERCARD",
            "ELO ",
            "AMEX",
            "AMERICAN EXPRESS",
            "CREDITO VISA",
            "CREDITO MASTER",
            "CREDITO ELO",
            "CREDITO AMEX",
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
    # CREDIT/DEP sozinho NÃO é Pix — exige PIX no histórico/memo.
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
        valor_signed = _parse_ofx_amount(campos.get("TRNAMT") or "0")
        valor = abs(valor_signed)
        nome = (campos.get("NAME") or campos.get("PAYEE") or "").strip()
        memo = (campos.get("MEMO") or "").strip()
        if not nome and memo:
            nome = memo
        trntype = (campos.get("TRNTYPE") or "").strip()
        classe = _classify_line(nome, memo, trntype)
        if valor_signed < 0 or trntype.upper() in ("DEBIT", "XFER", "PAYMENT", "POS", "ATM"):
            sentido = "saida"
        elif valor_signed > 0 or trntype.upper() in ("CREDIT", "DEP", "DIRECTDEP"):
            sentido = "entrada"
        else:
            sentido = "entrada"
        linhas.append(
            {
                "data": dia,
                "valor": valor,
                "valor_signed": valor_signed,
                "sentido": sentido,
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


def _extract_items(payload: Any) -> list:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    items = (
        payload.get("data")
        or payload.get("items")
        or payload.get("content")
        or payload.get("result")
        or payload.get("results")
        or payload.get("titulos")
        or payload.get("cobrancas")
        or []
    )
    if isinstance(items, dict):
        items = (
            items.get("items")
            or items.get("data")
            or items.get("content")
            or items.get("results")
            or []
        )
    return items if isinstance(items, list) else []


def _payload_total(payload: Any, n_items: int) -> int | None:
    if not isinstance(payload, dict):
        return None
    for k in ("total", "totalElements", "total_count", "count", "totalRecords"):
        v = payload.get(k)
        if isinstance(v, (int, float)) and int(v) >= n_items:
            return int(v)
    meta = payload.get("meta") or payload.get("pagination") or payload.get("page") or {}
    if isinstance(meta, dict):
        for k in ("total", "totalElements", "total_count", "count"):
            v = meta.get(k)
            if isinstance(v, (int, float)) and int(v) >= n_items:
                return int(v)
    return None


def _payload_next_cursor(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for k in ("next_cursor", "nextCursor", "cursor", "next"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip() and v not in ("null", "None"):
            return v.strip()
    meta = payload.get("meta") or payload.get("pagination") or {}
    if isinstance(meta, dict):
        for k in ("next_cursor", "nextCursor", "cursor", "next"):
            v = meta.get(k)
            if isinstance(v, str) and v.strip() and v not in ("null", "None"):
                return v.strip()
    links = payload.get("links") if isinstance(payload.get("links"), dict) else {}
    nxt = links.get("next")
    if isinstance(nxt, str) and nxt.strip():
        return nxt.strip()
    return None


def _normalize_titulos(payload: Any) -> list[dict[str, Any]]:
    items = _extract_items(payload)
    out: list[dict[str, Any]] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        vals = t.get("valores")
        if not isinstance(vals, dict):
            r = t.get("raw") if isinstance(t.get("raw"), dict) else {}
            vals = r.get("valores") if isinstance(r.get("valores"), dict) else {}
        if not isinstance(vals, dict):
            vals = {}
        valor = (
            t.get("valor")
            or t.get("vrTitulo")
            or t.get("valor_titulo")
            or t.get("vlr")
            or t.get("vrCobrancaReceber")
            or t.get("vrCobrancaPagar")
            or t.get("vrPago")
            or t.get("vrBruto")
            or vals.get("vrCobrancaPagar")
            or vals.get("vrCobrancaReceber")
            or vals.get("vrPago")
            or vals.get("vrBruto")
            or 0
        )
        pessoa = t.get("pessoa")
        if not isinstance(pessoa, dict):
            r = t.get("raw") if isinstance(t.get("raw"), dict) else {}
            pessoa = r.get("pessoa") if isinstance(r.get("pessoa"), dict) else {}
        if not isinstance(pessoa, dict):
            pessoa = {}
        nome = (
            t.get("nome")
            or t.get("nmPessoa")
            or t.get("nmCliente")
            or t.get("cliente")
            or t.get("fornecedor")
            or t.get("nomeCliente")
            or t.get("razaoSocial")
            or pessoa.get("nmPessoa")
            or pessoa.get("nome")
            or pessoa.get("razaoSocial")
            or pessoa.get("nmCliente")
            or t.get("pessoa")
            or ""
        )
        if isinstance(nome, dict):
            nome = (
                nome.get("nmPessoa")
                or nome.get("nome")
                or nome.get("razaoSocial")
                or nome.get("nmCliente")
                or ""
            )
        tid = (
            t.get("id")
            or t.get("idTitulo")
            or t.get("idCobrancaPagar")
            or t.get("idCobrancaReceber")
            or t.get("codigo")
            or t.get("nrTitulo")
        )
        out.append(
            {
                "id": tid,
                "valor": _parse_ofx_amount(str(valor)),
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
    dt_baixa_ini: str | None = None,
    *,
    return_raw: bool = False,
) -> list[dict[str, Any]] | tuple[list[dict[str, Any]], Any]:
    """GET títulos com janela de baixa e paginação defensiva."""
    params: dict[str, Any] = {"dt_baixa_fim": dt_baixa_fim}
    if dt_baixa_ini:
        params["dt_baixa_ini"] = dt_baixa_ini
        params["dtBaixaIni"] = dt_baixa_ini
        params["dt_baixa_inicio"] = dt_baixa_ini
    params["dtBaixaFim"] = dt_baixa_fim
    if caixa is not None:
        params["caixa"] = caixa
        params["id_caixa"] = caixa
        params["idCaixa"] = caixa

    def _fetch(p: dict[str, Any]) -> Any:
        url = f"{base.rstrip('/')}/{endpoint.lstrip('/')}?{urlencode(p)}"
        try:
            return _http_json("GET", url, headers=_query_headers(token, tenant))
        except HTTPError as e:
            if e.code in (400, 404, 422) and any(
                k in p for k in ("caixa", "id_caixa", "idCaixa")
            ):
                p2 = dict(p)
                for k in ("caixa", "id_caixa", "idCaixa"):
                    p2.pop(k, None)
                url = f"{base.rstrip('/')}/{endpoint.lstrip('/')}?{urlencode(p2)}"
                return _http_json("GET", url, headers=_query_headers(token, tenant))
            raise

    all_norm: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    raw_pages: list[Any] = []
    page = 1
    cursor: str | None = None
    offset = 0
    page_size = 100
    max_pages = 50
    last_payload: Any = None

    while page <= max_pages:
        p = dict(params)
        p["page"] = page
        p["pagina"] = page
        p["pageSize"] = page_size
        p["per_page"] = page_size
        p["limit"] = page_size
        p["size"] = page_size
        p["offset"] = offset
        if cursor:
            p["cursor"] = cursor
            p["next_cursor"] = cursor
        payload = _fetch(p)
        last_payload = payload
        raw_pages.append(payload)
        batch = _normalize_titulos(payload)
        if not batch:
            # primeira página sem page params (API que rejeita paginação)
            if page == 1 and not cursor and offset == 0:
                p0 = dict(params)
                try:
                    payload0 = _fetch(p0)
                    last_payload = payload0
                    raw_pages = [payload0]
                    batch = _normalize_titulos(payload0)
                except Exception:
                    batch = []
            if not batch:
                break
        new_count = 0
        for t in batch:
            tid = str(t.get("id") or "")
            key = tid or f"{t.get('valor')}|{t.get('nome')}|{len(all_norm)}"
            if key in seen_ids:
                continue
            seen_ids.add(key)
            all_norm.append(t)
            new_count += 1
        total = _payload_total(payload, len(batch))
        nxt = _payload_next_cursor(payload)
        if nxt and nxt != cursor:
            cursor = nxt
            page += 1
            offset += page_size
            continue
        if total is not None and len(all_norm) < total and new_count > 0:
            page += 1
            offset += page_size
            continue
        if new_count >= page_size:
            # página cheia — tenta mais
            page += 1
            offset += page_size
            continue
        break

    raw_out: Any = last_payload
    if len(raw_pages) > 1:
        raw_out = {"pages": raw_pages, "total_normalizados": len(all_norm)}
    if return_raw:
        return all_norm, raw_out
    return all_norm


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


def _cache_dir() -> Path:
    d = ROOT / "cache" / "conciliacao"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _dump_json(path: Path, obj: Any) -> None:
    try:
        path.write_text(
            json.dumps(obj, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except OSError:
        pass


def carregar_query(
    data: str,
    caixa: int,
    *,
    dump_prefix: str | None = None,
) -> tuple[list[dict], list[dict], list[str]]:
    """GETs read-only. Retorna (receber, pagar, avisos).

    Exige QUERY_TENANT e (QUERY_TOKEN ou QUERY_USER+QUERY_PASS).
    Não pula GET em silêncio — chame _query_creds_missing() antes.
    Pagina até esgotar. dt_baixa_ini = data do dia; dt_baixa_fim = dia seguinte.
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
    dt_ini = data
    dt_fim = (datetime.strptime(data, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    receber: list[dict] = []
    pagar: list[dict] = []
    receber_raw: Any = None
    pagar_raw: Any = None
    try:
        receber, receber_raw = query_get_titulos(
            base, token, tenant, "contas-receber", dt_fim, caixa,
            dt_baixa_ini=dt_ini, return_raw=True,
        )
    except Exception as exc:  # noqa: BLE001
        avisos.append(f"GET contas-receber falhou: {exc}")
    try:
        pagar, pagar_raw = query_get_titulos(
            base, token, tenant, "contas-a-pagar", dt_fim, caixa,
            dt_baixa_ini=dt_ini, return_raw=True,
        )
    except Exception as exc:  # noqa: BLE001
        avisos.append(f"GET contas-a-pagar falhou: {exc}")
    if dump_prefix:
        cdir = _cache_dir()
        _dump_json(cdir / f"{dump_prefix}-receber-raw.json", receber_raw)
        _dump_json(cdir / f"{dump_prefix}-pagar-raw.json", pagar_raw)
        _dump_json(cdir / f"{dump_prefix}-receber.json", receber)
        _dump_json(cdir / f"{dump_prefix}-pagar.json", pagar)
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
    id_caixa: str | int | None = None,
) -> str:
    """POST multipart criar.consumo.snf — despesa + baixa no caixa (captura 1200)."""
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
        "fields[Financeiro_Cobrancas_Pagar][idCaixaBaixa]": str(id_caixa or _ID_CAIXA),
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
    ds_historico: str = "",
    id_caixa: str | int | None = None,
) -> str:
    """POST receber_transaction — Receber Pagamento (juros/multa 0, caixa).

    Captura Concluir: exige dsHistorico/idHistorico ("Informe um histórico").
    nmCaixa* é dinâmico; idCaixa basta.
    """
    data_br = _data_br(data_extrato)
    vr = f"{abs(float(valor)):.2f}"
    hist = (ds_historico or "").strip() or "resgate"
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
        "fields[Financeiro_Cobrancas_Receber][idCaixa]": str(id_caixa or _ID_CAIXA),
        "fields[Financeiro_Cobrancas_Receber][idMoeda]": _RECEITA_ID_MOEDA,
        "fields[Financeiro_Cobrancas_Receber][cdMoeda]": _RECEITA_CD_MOEDA,
        "fields[Financeiro_Cobrancas_Receber][dtCobrancaReceberRecebimento]": data_br,
        "fields[Financeiro_Cobrancas_Receber][dsObservacoesBaixa]": "",
        "fields[Financeiro_Cobrancas_Receber][idCobrancaReceber]": str(id_cobranca),
        "fields[Financeiro_Cobrancas_Receber][idHistorico]": "0",
        "fields[Financeiro_Cobrancas_Receber][dsHistorico]": hist,
        "fields[Financeiro_Cobrancas_Receber][idPessoa]": _ID_PESSOA_BRADESCO,
        "fields[Financeiro_Cobrancas_Receber][idFilial]": _ID_FILIAL,
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


def _prefer_hist_despesa(id_plano: str, ds_historico: str) -> tuple[str, ...]:
    if id_plano == _APLICACAO_ID_PLANO or "aplic" in (ds_historico or "").lower():
        return ("APLIC", "APLICACAO", "APLIC.")
    if id_plano == _TARIFA_ID_PLANO or "tarif" in (ds_historico or "").lower():
        return ("TARIFA", "TX ", "TAXA")
    return tuple(
        p for p in ((ds_historico or "").upper().split()[:2]) if len(p) >= 3
    )


def _gravar_despesa_snf(
    opener: Any,
    item: dict,
    ln: dict,
    *,
    ds_historico: str,
    id_plano: str,
    id_caixa: str | int | None = None,
    prefer_hist: tuple[str, ...] = (),
) -> dict:
    resp = query_criar_consumo_snf(
        opener,
        valor=float(ln.get("valor") or 0),
        data_extrato=_data_linha(ln),
        ds_historico=ds_historico,
        id_plano=id_plano,
        id_caixa=id_caixa,
    )
    ok = "[Sucesso]" in (resp or "")
    id_tit = _parse_id_cobranca_sucesso(resp or "")
    item["status"] = "gravado" if ok else "erro"
    item["gravou"] = ok
    item["endpoint"] = (
        "/mgerencia/scripts/fiscal/compras/actions/criar.consumo.snf"
    )
    item["plano"] = id_plano
    item["historico"] = ds_historico
    item["resposta"] = (resp or "")[:300]
    if id_tit:
        item["id_titulo"] = id_tit
        item["id_cobranca"] = id_tit
    if not ok:
        item["motivo"] = "Resposta sem [Sucesso]."
        return item
    ph = prefer_hist or _prefer_hist_despesa(id_plano, ds_historico)
    # Fecha a linha OFX na 1311 após criar+baixar (com id + hist preferido)
    item = _ligar_extrato_apos_criar(
        opener,
        item,
        ln,
        id_caixa=id_caixa,
        tp="Debito",
        id_titulo=id_tit,
        prefer_hist=ph,
    )
    return item


def _gravar_receita_e_baixa(
    opener: Any,
    item: dict,
    ln: dict,
    *,
    ds_historico: str,
    id_caixa: str | int | None = None,
) -> tuple[dict, dict | None]:
    """criar.novo → parse id → receber_transaction → conciliar OFX. Retorna (item, criado?)."""
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
        ds_historico=ds_historico,
        id_caixa=id_caixa,
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
        criado["baixado"] = False
        return item, criado
    criado["status"] = "criado"
    criado["baixado"] = True
    hist_l = (ds_historico or "").lower()
    if "rentab" in hist_l or "rend" in hist_l:
        ph = ("RENTAB", "RENTABILIDADE", "RENDIMENTO", "RENDTO")
    else:
        ph = ("RESGATE", "RESG")
    item = _ligar_extrato_apos_criar(
        opener,
        item,
        ln,
        id_caixa=id_caixa,
        tp="Credito",
        id_titulo=id_cob,
        prefer_hist=ph,
    )
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



def query_estornar_pagar(
    opener: Any,
    *,
    id_cobranca_pagar: str | int,
    id_caixa_baixa: str | int | None = None,
    ds_motivo_estorno: str = "Duplicado conciliação — estorno automático",
) -> str:
    """POST estornar contas a pagar (captura 1200).

    Endpoint: /mgerencia/scripts/financeiro/cobrancas_pagar/actions/estornar
    Fields: idCobrancaPagar, idCaixaBaixa, dsMotivoEstorno.
    """
    fields = {
        "idCobrancaPagar": str(id_cobranca_pagar),
        "idCaixaBaixa": str(id_caixa_baixa if id_caixa_baixa is not None else _ID_CAIXA),
        "dsMotivoEstorno": ds_motivo_estorno,
    }
    url = (
        f"{_mgerencia_base()}"
        "/scripts/financeiro/cobrancas_pagar/actions/estornar"
    )
    return _post_urlencoded(opener, url, fields)


def _eh_cartao_mov(m: dict) -> bool:
    blob = " ".join(
        str(m.get(k) or "")
        for k in ("hist", "dsHistorico", "pessoa", "nmPessoa", "origem")
    )
    return bool(_CARTAO_RE.search(blob))



def _caixa_str(id_caixa: str | int | None = None) -> str:
    return str(id_caixa if id_caixa is not None else _ID_CAIXA)


def _achar_extrato_por_valor(
    opener: Any,
    *,
    id_caixa: str,
    data_extrato: str,
    valor: float,
    prefer_hist: tuple[str, ...] = (),
) -> dict | None:
    txs = query_extrato_pendente(opener, id_caixa=id_caixa, data_extrato=data_extrato)
    cand: list[dict] = []
    for t in txs:
        try:
            vr = abs(float(t.get("vr") or t.get("valor") or 0))
        except (TypeError, ValueError):
            continue
        if abs(vr - abs(float(valor))) > 0.02:
            continue
        cand.append(t)
    if not cand:
        return None
    if prefer_hist:
        pref = [
            t
            for t in cand
            if any(
                k in str(t.get("hist") or t.get("dsHistorico") or "").upper()
                for k in prefer_hist
            )
        ]
        if pref:
            return pref[0]
    return cand[0]


def _parse_conciliar_ok(resp: str, item: dict) -> bool:
    ok = False
    try:
        js = json.loads(resp)
        ok = bool(js.get("isOk")) or "sucesso" in str(js.get("message") or "").lower()
        item["resposta"] = json.dumps(js, ensure_ascii=False)[:300]
        item["vinculadas"] = js.get("vinculadas")
    except json.JSONDecodeError:
        ok = "[Sucesso]" in resp or "sucesso" in (resp or "").lower()
        item["resposta"] = (resp or "")[:300]
    return ok


def _achar_mov_ids(
    opener: Any,
    *,
    id_caixa: str,
    data_extrato: str,
    valor: float,
    tp: str,
    id_titulo: str | None = None,
    excluir_cartao: bool = False,
    prefer_mesmo_dia: bool = True,
) -> list[str] | None:
    movs = query_movimentacoes_para_alvo(
        opener, id_caixa=id_caixa, data_extrato=data_extrato, valor=valor, tp=tp
    )
    dia_br = _data_br(data_extrato)
    pool: list[tuple[str, float, str]] = []
    for m in movs:
        if excluir_cartao and _eh_cartao_mov(m):
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
        blob = " ".join(str(m.get(k) or "") for k in m)
        if id_titulo and str(id_titulo) in blob and abs(vr - abs(float(valor))) <= 0.02:
            return [str(mid)]
        dt = str(m.get("data") or m.get("dt") or "")
        pool.append((str(mid), vr, dt))
    if id_titulo:
        exact = [(i, v, d) for (i, v, d) in pool if abs(v - abs(float(valor))) <= 0.02]
        if prefer_mesmo_dia:
            mesmo = [
                (i, v)
                for (i, v, dt) in exact
                if dia_br in dt or dt.replace("-", "/") == dia_br or dt[:10] == data_extrato[:10]
            ]
            if len(mesmo) == 1:
                return [mesmo[0][0]]
        if len(exact) == 1:
            return [exact[0][0]]
    mesmo_dia = [
        (i, v)
        for (i, v, dt) in pool
        if dia_br in dt or dt.replace("-", "/") == dia_br or dt[:10] == data_extrato[:10]
    ]
    use = mesmo_dia if (prefer_mesmo_dia and mesmo_dia) else [(i, v) for (i, v, _) in pool]
    return _subset_sum_ids(use, valor)


def _ligar_extrato_apos_criar(
    opener: Any,
    item: dict,
    ln: dict,
    *,
    id_caixa: str | int | None = None,
    tp: str = "Debito",
    id_titulo: str | None = None,
    prefer_hist: tuple[str, ...] = (),
) -> dict:
    """Após criar+baixar: POST conciliar para fechar a linha OFX."""
    cx = _caixa_str(id_caixa)
    data_ex = _data_linha(ln)
    valor = abs(float(ln.get("valor") or 0))
    tx = _achar_extrato_por_valor(
        opener, id_caixa=cx, data_extrato=data_ex, valor=valor, prefer_hist=prefer_hist
    )
    if not tx:
        item["ligacao"] = "pendente_extrato"
        item["status"] = "ja_existe_ligar"
        item["gravou"] = False
        item["motivo"] = (
            (item.get("motivo") or "")
            + f" Título criado; extrato pendente não achado (caixa {cx}, {valor:.2f})."
        ).strip()
        return item
    id_extrato = str(tx.get("id") or tx.get("Financeiro_Caixas_Extratos_id") or "")
    if not id_extrato:
        item["ligacao"] = "pendente_extrato"
        item["status"] = "ja_existe_ligar"
        item["gravou"] = False
        return item
    ids = _achar_mov_ids(
        opener,
        id_caixa=cx,
        data_extrato=data_ex,
        valor=valor,
        tp=tp,
        id_titulo=id_titulo or str(item.get("id_cobranca") or item.get("id_titulo") or "") or None,
    )
    if not ids:
        item["ligacao"] = "pendente_mov"
        item["id_extrato"] = id_extrato
        item["status"] = "ja_existe_ligar"
        item["gravou"] = False
        item["motivo"] = (
            (item.get("motivo") or "")
            + f" Extrato {id_extrato} achado; sem movimentação para conciliar."
        ).strip()
        return item
    resp = query_conciliar_lote(opener, id_extrato=id_extrato, ids_movimentacao=ids)
    ok = _parse_conciliar_ok(resp, item)
    item["id_extrato"] = id_extrato
    item["ids_movimentacao"] = ids
    item["ligacao"] = "ok" if ok else "falhou"
    if ok:
        item["status"] = "gravado"
        item["gravou"] = True
    else:
        item["status"] = "ja_existe_ligar"
        item["gravou"] = False
        item["motivo"] = (
            (item.get("motivo") or "") + " Conciliação OFX sem isOk."
        ).strip()
    return item


def _ligar_titulo_na_linha(
    opener: Any,
    item: dict,
    ln: dict,
    *,
    id_caixa: str | int | None = None,
    id_titulo: str | None = None,
    tp: str = "Credito",
    prefer_hist: tuple[str, ...] = (),
    excluir_cartao: bool = False,
) -> dict:
    """POST conciliar extrato↔movimentação para cartão/pix/boleto com título."""
    cx = _caixa_str(id_caixa)
    data_ex = _data_linha(ln)
    valor = abs(float(ln.get("valor") or 0))
    tx = _achar_extrato_por_valor(
        opener, id_caixa=cx, data_extrato=data_ex, valor=valor, prefer_hist=prefer_hist
    )
    if not tx:
        # Sem pendência no valor = linha já ligada na passagem anterior.
        item["status"] = "ja_conciliado"
        item["gravou"] = True
        item["motivo"] = (
            f"Extrato {valor:.2f} já não está pendente no caixa {cx} "
            f"({data_ex}) — tratado como já conciliado."
        )
        return item
    id_extrato = str(tx.get("id") or tx.get("Financeiro_Caixas_Extratos_id") or "")
    if not id_extrato:
        item["status"] = "erro"
        item["gravou"] = False
        item["motivo"] = "Linha de extrato sem id."
        return item
    ids = _achar_mov_ids(
        opener,
        id_caixa=cx,
        data_extrato=data_ex,
        valor=valor,
        tp=tp,
        id_titulo=id_titulo,
        excluir_cartao=excluir_cartao,
    )
    if not ids:
        item["status"] = "erro"
        item["gravou"] = False
        item["id_extrato"] = id_extrato
        item["id_titulo"] = id_titulo
        item["motivo"] = (
            f"Sem movimentação para título {id_titulo} / valor {valor:.2f} "
            f"(extrato {id_extrato})."
        )
        return item
    resp = query_conciliar_lote(opener, id_extrato=id_extrato, ids_movimentacao=ids)
    ok = _parse_conciliar_ok(resp, item)
    item["status"] = "gravado" if ok else "erro"
    item["gravou"] = ok
    item["endpoint"] = (
        "/mgerencia/scripts/financeiro/conciliacao/actions&id=conciliar"
    )
    item["id_extrato"] = id_extrato
    item["ids_movimentacao"] = ids
    item["id_titulo"] = id_titulo
    if not ok:
        item["motivo"] = "Conciliação sem isOk."
    return item


def _hist_mov(m: dict) -> str:
    """Histórico/descrição da movimentação aberta (tela de conciliação)."""
    for k in (
        "hist",
        "dsHistorico",
        "historico",
        "descricao",
        "ds",
        "nome",
        "memo",
        "dsMovimentacao",
    ):
        v = m.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _eh_pagto_mov(m: dict) -> bool:
    """Ariadna 2026-10-27: liquidação = só recebimentos que INICIAM com PAGTO."""
    return _hist_mov(m).upper().startswith("PAGTO")


def _gravar_liquidacao(
    opener: Any, item: dict, ln: dict, *, id_caixa: str | int | None = None
) -> dict:
    """Lote de boleto: extrato + movimentações PAGTO* do dia; POST conciliar."""
    cx = _caixa_str(id_caixa)
    data_ex = _data_linha(ln)
    valor = abs(float(ln.get("valor") or 0))
    nome = (ln.get("nome") or ln.get("memo") or "").upper()
    sentido = str(ln.get("sentido") or "").lower()
    trn = str(ln.get("trntype") or "").upper()
    is_saida = sentido == "saida" or trn in (
        "DEBIT", "DEBITO", "D", "PAYMENT", "XFER", "POS", "ATM"
    )
    tp_mov = "Debito" if is_saida else "Credito"
    txs = query_extrato_pendente(opener, id_caixa=cx, data_extrato=data_ex)
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
        item["status"] = "ja_conciliado"
        item["gravou"] = True
        item["motivo"] = (
            f"Extrato {valor:.2f} já não está pendente no caixa {cx} "
            f"({data_ex}) — tratado como já conciliado."
        )
        return item
    id_extrato = str(tx.get("id") or tx.get("Financeiro_Caixas_Extratos_id") or "")
    if not id_extrato:
        item["status"] = "erro"
        item["gravou"] = False
        item["motivo"] = "Linha de extrato sem id."
        return item

    movs = query_movimentacoes_para_alvo(
        opener, id_caixa=cx, data_extrato=data_ex, valor=valor, tp=tp_mov
    )
    # entrada (liquidação): só PAGTO*; saída (pagto eletrôn): sem filtro PAGTO
    dia_br = _data_br(data_ex)  # DD/MM/YYYY
    filtrados: list[tuple[str, float, str]] = []
    n_pagto = 0
    for m in movs:
        if _eh_cartao_mov(m):
            continue
        if not is_saida:
            if not _eh_pagto_mov(m):
                continue
            n_pagto += 1
        else:
            n_pagto += 1  # conta candidatos débito
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
        filtrados.append((str(mid), vr, dt))

    if n_pagto == 0:
        item["status"] = "erro"
        item["gravou"] = False
        item["id_extrato"] = id_extrato
        item["motivo"] = (
            (
                f"Painel sem PAGTO de boleto (movs={len(movs)}, extrato={id_extrato}). "
                "Ariadna: não force lote sem prefixo PAGTO."
            )
            if not is_saida
            else (
                f"Sem movimentação a débito para {valor:.2f} "
                f"(movs={len(movs)}, extrato={id_extrato})."
            )
        )
        return item

    # Ariadna: TODOS os PAGTO (não só mesmo dia). Mesmo-dia entra primeiro no subset.
    mesmo_dia = [
        (i, v) for (i, v, dt) in filtrados
        if dia_br in dt or dt.replace("-", "/") == dia_br or dt[0:10] == data_ex[:10]
    ]
    outros = [
        (i, v) for (i, v, dt) in filtrados
        if not (dia_br in dt or dt.replace("-", "/") == dia_br or dt[0:10] == data_ex[:10])
    ]
    pool = mesmo_dia + outros  # prioriza dia na ordem do backtrack
    soma_pool = round(sum(v for _, v in pool), 2)
    ids = None
    if abs(soma_pool - valor) <= 0.02 and pool:
        ids = [i for i, _ in pool]
    if not ids and mesmo_dia:
        ids = _subset_sum_ids(mesmo_dia, valor, limite=120)
    if not ids:
        ids = _subset_sum_ids(pool, valor, limite=120)
    if not ids:
        item["status"] = "erro"
        item["gravou"] = False
        item["motivo"] = (
            f"Lote PAGTO sem combinação que feche {valor:.2f} "
            f"(pagto={len(pool)}, dia={len(mesmo_dia)}, soma={soma_pool:.2f}, "
            f"extrato={id_extrato})."
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
    item["filtro"] = "debito" if is_saida else "PAGTO*"
    if not ok:
        item["motivo"] = "Conciliação sem isOk."
    return item



def _plano_do_titulo(t: dict) -> str:
    """Extrai id do plano de contas do título (raw defensivo)."""
    raw = t.get("raw") if isinstance(t.get("raw"), dict) else {}
    for src in (raw, t):
        if not isinstance(src, dict):
            continue
        for k in (
            "idPlanoDeContasSubconta",
            "id_plano",
            "idPlano",
            "conta",
            "plano",
            "cdPlano",
            "codigoPlano",
            "idPlanoContas",
            "Financeiro_PlanoDeContas_Subcontas_id",
        ):
            v = src.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
        nested = src.get("planoDeContas") or src.get("subconta") or src.get("plano_de_contas")
        if isinstance(nested, dict):
            for k in ("id", "codigo", "cd", "idPlanoDeContasSubconta"):
                if nested.get(k) is not None and str(nested.get(k)).strip():
                    return str(nested.get(k)).strip()
    blob = " ".join(str(v) for v in (raw or {}).values() if v is not None)
    for pid in (_APLICACAO_ID_PLANO, _TARIFA_ID_PLANO, _RECEITA_ID_PLANO):
        if pid in blob:
            return pid
    return ""


def _data_do_titulo(t: dict) -> str:
    """Data do título (baixa/vencimento/pagamento), incl. datas.* aninhado."""
    raw = t.get("raw") if isinstance(t.get("raw"), dict) else {}
    datas_list: list[dict] = []
    for src in (raw, t):
        if isinstance(src, dict) and isinstance(src.get("datas"), dict):
            datas_list.append(src["datas"])
    for src in (*datas_list, raw, t):
        if not isinstance(src, dict):
            continue
        for k in (
            "dtBaixa",
            "dt_baixa",
            "dtCobrancaPagarBaixa",
            "dtCobrancaReceberRecebimento",
            "dtVencimentoCobrancaPagar",
            "dtVencimentoCobrancaReceber",
            "dtVencimento",
            "dt_vencimento",
            "dtPagamento",
            "dt_pagamento",
            "dtCompetencia",
            "data",
            "dt",
        ):
            v = src.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
    return ""


def _mesmo_dia_titulo(dia_linha: str, dia_tit: str) -> bool:
    """True só se datas batem. Título sem data → False (não casa)."""
    if not (dia_tit or "").strip():
        return False
    dl = (dia_linha or "").strip()
    dt = dia_tit.strip()
    if not dl:
        return False
    # normaliza pedaços YYYY-MM-DD / DD/MM/YYYY / DD-MM-YYYY
    def parts(s: str) -> set[str]:
        s2 = s.replace("T", " ").split()[0]
        out = {s2, s2.replace("/", "-")}
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s2)
        if m:
            y, mo, d = m.groups()
            out.update({f"{d}/{mo}/{y}", f"{d}-{mo}-{y}", f"{y}-{mo}-{d}"})
        m = re.match(r"^(\d{2})[/\-](\d{2})[/\-](\d{4})", s2)
        if m:
            d, mo, y = m.groups()
            out.update({f"{y}-{mo}-{d}", f"{d}/{mo}/{y}", f"{d}-{mo}-{y}"})
        return out

    return bool(parts(dl) & parts(dt))


def _historico_do_titulo(t: dict) -> str:
    raw = t.get("raw") if isinstance(t.get("raw"), dict) else {}
    parts: list[str] = []
    for src in (raw, t):
        if not isinstance(src, dict):
            continue
        for k in (
            "dsHistorico",
            "historico",
            "hist",
            "descricao",
            "ds_historico",
            "nmHistorico",
        ):
            v = src.get(k)
            if v is not None and str(v).strip():
                parts.append(str(v))
    return " ".join(parts).upper()


def _candidatos_plano(
    titulos: list[dict] | None,
    valor: float,
    dia: str,
    id_plano: str,
    hist_keywords: tuple[str, ...] = (),
) -> list[dict]:
    """Gate 0/1/N: valor±0,02 + mesmo dia (data obrigatória) + (plano OU hist OU fallback)."""
    out: list[dict] = []
    alvo = abs(float(valor))
    kws = tuple(k.upper() for k in hist_keywords if k)
    for t in titulos or []:
        try:
            tv = abs(float(t.get("valor") or 0))
        except (TypeError, ValueError):
            continue
        if abs(tv - alvo) > 0.02:
            continue
        dia_tit = _data_do_titulo(t)
        if not _mesmo_dia_titulo(dia, dia_tit):
            continue
        plano = _plano_do_titulo(t)
        if plano == id_plano:
            out.append(t)
            continue
        hist = _historico_do_titulo(t)
        if not plano and kws and any(k in hist for k in kws):
            out.append(t)
            continue
        # fallback: plano+histórico vazios → valor±0,02 + mesmo dia (data já presente)
        if not plano and not (hist or "").strip():
            out.append(t)
    return out


def _candidatos_aplicacao(pagar: list[dict] | None, valor: float, dia: str) -> list[dict]:
    """Títulos 30060005 no mesmo valor (±0,02); fallback por histórico aplicação."""
    return _candidatos_plano(
        pagar, valor, dia, _APLICACAO_ID_PLANO, ("APLICACAO", "APLIC.", "APLIC ")
    )


def _candidatos_tarifa(pagar: list[dict] | None, valor: float, dia: str) -> list[dict]:
    return _candidatos_plano(
        pagar, valor, dia, _TARIFA_ID_PLANO, ("TARIFA", "TX ", "TAXA")
    )


def _candidatos_receita(receber: list[dict] | None, valor: float, dia: str, classe: str) -> list[dict]:
    if classe == "resgate":
        kws = ("RESGATE", "RESG.", "RESG ")
    else:
        kws = ("RENTAB", "RENTABILIDADE", "RENDIMENTO", "RENDTO")
    return _candidatos_plano(receber, valor, dia, _RECEITA_ID_PLANO, kws)


def _id_mov_do_titulo(t: dict) -> str | None:
    raw = t.get("raw") if isinstance(t.get("raw"), dict) else {}
    for src in (raw, t):
        if not isinstance(src, dict):
            continue
        for k in (
            "idMovimentacao",
            "id_movimentacao",
            "Financeiro_Caixas_Movimentacoes_id",
            "idMovimento",
            "idBaixa",
            "id_baixa",
            "idMovimentacaoCaixa",
        ):
            v = src.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
    return None


def _ligar_aplicacao(
    opener: Any, item: dict, ln: dict, titulo: dict, *, id_caixa: str | int | None = None
) -> dict:
    """Liga extrato ↔ movimentação do título 30060005 único (não cria)."""
    cx = _caixa_str(id_caixa)
    data_ex = _data_linha(ln)
    valor = abs(float(ln.get("valor") or 0))
    txs = query_extrato_pendente(opener, id_caixa=cx, data_extrato=data_ex)
    cand: list[dict] = []
    for t in txs:
        try:
            vr = abs(float(t.get("vr") or t.get("valor") or 0))
        except (TypeError, ValueError):
            continue
        if abs(vr - valor) > 0.02:
            continue
        cand.append(t)
    aplic = [
        t
        for t in cand
        if "APLIC" in str(t.get("hist") or t.get("dsHistorico") or "").upper()
    ]
    tx = (aplic or cand or [None])[0]
    if not tx:
        item["status"] = "ja_existe_ligar"
        item["gravou"] = False
        item["id_titulo"] = titulo.get("id")
        item["motivo"] = (
            f"Título único {titulo.get('id')} 30060005 existe; "
            f"extrato pendente não encontrado (caixa {cx}, "
            f"data {data_ex}, valor {valor:.2f}) — ligar via conciliar."
        )
        return item
    id_extrato = str(tx.get("id") or tx.get("Financeiro_Caixas_Extratos_id") or "")
    if not id_extrato:
        item["status"] = "ja_existe_ligar"
        item["gravou"] = False
        item["id_titulo"] = titulo.get("id")
        item["motivo"] = "Linha de extrato sem id — ligar título único via conciliar."
        return item

    mid = _id_mov_do_titulo(titulo)
    if not mid:
        movs = query_movimentacoes_para_alvo(
            opener, id_caixa=cx, data_extrato=data_ex, valor=valor, tp="Debito"
        )
        tid = str(titulo.get("id") or "")
        pool: list[tuple[str, float]] = []
        for m in movs:
            mmid = m.get("idMovimentacao") or m.get("id")
            if mmid is None:
                continue
            try:
                vr = abs(float(m.get("vr") or m.get("valor") or 0))
            except (TypeError, ValueError):
                continue
            if abs(vr - valor) > 0.02:
                continue
            blob = " ".join(str(m.get(k) or "") for k in m)
            if tid and tid in blob:
                mid = str(mmid)
                break
            pool.append((str(mmid), vr))
        if not mid and len(pool) == 1:
            mid = pool[0][0]
        if not mid and pool:
            ids = _subset_sum_ids(pool, valor)
            if ids and len(ids) == 1:
                mid = ids[0]

    if not mid:
        item["status"] = "ja_existe_ligar"
        item["gravou"] = False
        item["id_titulo"] = titulo.get("id")
        item["id_extrato"] = id_extrato
        item["motivo"] = (
            f"Título único {titulo.get('id')} 30060005 — extrato {id_extrato} achado; "
            "sem idMovimentacao no raw. Ligue via conciliar na central."
        )
        return item

    resp = query_conciliar_lote(
        opener, id_extrato=id_extrato, ids_movimentacao=[mid]
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
    item["ids_movimentacao"] = [mid]
    item["id_titulo"] = titulo.get("id")
    item["tipo"] = "aplicacao_ligada"
    if not ok:
        item["motivo"] = "Conciliação aplicação sem isOk."
    return item



def _titulo_id(t: dict) -> str:
    tid = t.get("id")
    return str(tid).strip() if tid is not None else ""


def _pick_stable(cands: list[dict]) -> dict:
    """Escolha estável: menor id numérico, senão menor string."""
    def key(t: dict):
        tid = _titulo_id(t)
        try:
            return (0, int(tid))
        except (TypeError, ValueError):
            return (1, tid)
    return sorted(cands, key=key)[0]


def _count_ofx_mesmo_valor(linhas_gravar: list[dict], classe: str, valor: float) -> int:
    alvo = abs(float(valor))
    n = 0
    for x in linhas_gravar:
        if (x.get("classe") or "").lower() != classe:
            continue
        try:
            vx = abs(float(x.get("valor") or 0))
        except (TypeError, ValueError):
            continue
        if abs(vx - alvo) <= 0.02:
            n += 1
    return n


def _cands_livres(cands: list[dict], used: set[str]) -> list[dict]:
    out = []
    for t in cands:
        tid = _titulo_id(t)
        if not tid or tid in used:
            continue
        out.append(t)
    return out


def _decidir_gate_pool(
    *,
    cands_all: list[dict],
    used: set[str],
    n_ofx: int,
    plano_label: str,
    tela_estorno: str,
) -> tuple[str, dict | None, str]:
    """Gate 0/1/N com pool 1:1.

    Retorna (acao, titulo|None, motivo):
      - "ligar": pick 1 livre
      - "criar": pool esgotado (0 livres)
      - "bloqueio": 1 OFX + >=2 livres (ambíguo) OU nota de extras (M>N) só no último?
        bloqueio só quando 1 OFX e >=2 cands livres.
    """
    livres = _cands_livres(cands_all, used)
    m_total = len(cands_all)
    m_livres = len(livres)

    if m_livres == 0:
        return "criar", None, ""

    # 1 OFX + >=2 títulos livres → ambíguo, não escolher
    if n_ofx <= 1 and m_livres >= 2:
        ids = [_titulo_id(t) for t in livres]
        return (
            "bloqueio",
            None,
            f"Vários {plano_label} no valor/dia ({', '.join(ids)}) — "
            f"1 linha OFX e {m_livres} títulos; estornar duplicado na {tela_estorno}.",
        )

    # N OFX + M títulos: consumir 1:1
    pick = _pick_stable(livres)
    motivo_extra = ""
    if m_total > n_ofx:
        # sobram extras no pool — nota informativa (não bloqueia a ligação)
        sobra = m_total - n_ofx
        motivo_extra = (
            f"Pool 1:1: {n_ofx} OFX × {m_total} títulos; "
            f"{sobra} sobra(m) p/ estornar na {tela_estorno}."
        )
    return "ligar", pick, motivo_extra


def _executar_gravar(
    linhas_gravar: list[dict],
    modo: str,
    pagar: list[dict] | None = None,
    receber: list[dict] | None = None,
    id_caixa: str | int | None = None,
) -> tuple[list[dict], list[dict]]:
    """Em simular: não escreve. Em executar: gates 0/1/N pool 1:1 + conciliar cartão/pix/boleto."""
    criados: list[dict] = []
    executados: list[dict] = []
    opener = None
    cx = _caixa_str(id_caixa)
    used_title_ids: set[str] = set()

    def _need_session() -> Any:
        nonlocal opener
        if opener is None:
            opener = mgerencia_session()
        return opener

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
            "sentido": ln.get("sentido"),
            "trntype": ln.get("trntype"),
        }
        if modo == "simular":
            item["status"] = "simulado"
            v = abs(float(ln.get("valor") or 0))
            dia = _data_linha(ln)
            if classe == "aplicacao":
                cands = _candidatos_aplicacao(pagar, v, dia)
                n_ofx = _count_ofx_mesmo_valor(linhas_gravar, "aplicacao", v)
                acao, pick, motivo = _decidir_gate_pool(
                    cands_all=cands, used=used_title_ids, n_ofx=n_ofx,
                    plano_label="30060005", tela_estorno="1200",
                )
                if acao == "ligar" and pick is not None:
                    item["tipo"] = "aplicacao_seria_ligada"
                    item["id_titulo"] = pick.get("id")
                    if motivo:
                        item["motivo"] = motivo
                    used_title_ids.add(_titulo_id(pick))
                elif acao == "bloqueio":
                    item["tipo"] = "aplicacao_bloqueio_duplicado"
                    item["status"] = "bloqueio_duplicado"
                    item["motivo"] = motivo
                    item["ids_titulos"] = [_titulo_id(t) for t in _cands_livres(cands, used_title_ids)]
                else:
                    item["tipo"] = "despesa_aplicacao_seria_criada"
            elif classe == "tarifa":
                cands = _candidatos_tarifa(pagar, v, dia)
                n_ofx = _count_ofx_mesmo_valor(linhas_gravar, "tarifa", v)
                acao, pick, motivo = _decidir_gate_pool(
                    cands_all=cands, used=used_title_ids, n_ofx=n_ofx,
                    plano_label="30060001", tela_estorno="1200",
                )
                if acao == "ligar" and pick is not None:
                    item["tipo"] = "tarifa_seria_ligada"
                    item["id_titulo"] = pick.get("id")
                    if motivo:
                        item["motivo"] = motivo
                    used_title_ids.add(_titulo_id(pick))
                elif acao == "bloqueio":
                    item["tipo"] = "tarifa_bloqueio_duplicado"
                    item["status"] = "bloqueio_duplicado"
                    item["motivo"] = motivo
                    item["ids_titulos"] = [_titulo_id(t) for t in _cands_livres(cands, used_title_ids)]
                else:
                    item["tipo"] = "despesa_tarifa_seria_criada"
            elif classe in ("resgate", "rentabilidade"):
                cands = _candidatos_receita(receber, v, dia, classe)
                n_ofx = _count_ofx_mesmo_valor(linhas_gravar, classe, v)
                acao, pick, motivo = _decidir_gate_pool(
                    cands_all=cands, used=used_title_ids, n_ofx=n_ofx,
                    plano_label="30060006", tela_estorno="1100",
                )
                if acao == "ligar" and pick is not None:
                    item["tipo"] = f"{classe}_seria_ligada"
                    item["id_titulo"] = pick.get("id")
                    if motivo:
                        item["motivo"] = motivo
                    used_title_ids.add(_titulo_id(pick))
                elif acao == "bloqueio":
                    item["tipo"] = f"{classe}_bloqueio_duplicado"
                    item["status"] = "bloqueio_duplicado"
                    item["motivo"] = motivo
                    item["ids_titulos"] = [_titulo_id(t) for t in _cands_livres(cands, used_title_ids)]
                else:
                    item["tipo"] = "receita_avulsa_seria_criada"
                    criados.append({**item, "tipo": "receita_avulsa_seria_criada"})
            elif classe in ("liquidacao", "boleto"):
                item["tipo"] = "lote_boleto_seria_conciliado"
            elif classe in ("cartao", "pix"):
                if classe == "cartao" and ln.get("id"):
                    acao = str(ln.get("acao") or "")
                    v = abs(float(ln.get("valor") or 0))
                    tid = ln.get("id")
                    tit_valor = None
                    for tt in (receber or []):
                        if str(tt.get("id") or "") == str(tid):
                            try:
                                tit_valor = abs(float(tt.get("valor") or 0))
                            except (TypeError, ValueError):
                                tit_valor = None
                            break
                    n_mesmo = sum(
                        1
                        for x in linhas_gravar
                        if (x.get("classe") or "").lower() == "cartao"
                        and str(x.get("id") or "") == str(tid)
                    )
                    if (
                        "desdobre" in acao.lower()
                        or n_mesmo >= 2
                        or (tit_valor is not None and abs(v - tit_valor) > 0.02)
                    ):
                        item["tipo"] = "cartao_bloqueio_desdobro"
                        item["status"] = "bloqueio_desdobro"
                        item["motivo"] = (
                            "Cartão desdobrado — não ligar pedaço; desdobrar na tela."
                        )
                    else:
                        item["tipo"] = "cartao_seria_ligado"
                elif ln.get("id"):
                    item["tipo"] = f"{classe}_seria_ligado"
                else:
                    item["tipo"] = f"{classe}_sem_titulo"
            executados.append(item)
            continue

        try:
            if classe in (
                "aplicacao", "tarifa", "resgate", "rentabilidade",
                "liquidacao", "boleto", "cartao", "pix",
            ):
                _need_session()

            if classe == "aplicacao":
                v = abs(float(ln.get("valor") or 0))
                cands = _candidatos_aplicacao(pagar, v, _data_linha(ln))
                n_ofx = _count_ofx_mesmo_valor(linhas_gravar, "aplicacao", v)
                acao, pick, motivo = _decidir_gate_pool(
                    cands_all=cands, used=used_title_ids, n_ofx=n_ofx,
                    plano_label="30060005", tela_estorno="1200",
                )
                if acao == "ligar" and pick is not None:
                    item = _ligar_aplicacao(
                        opener, item, ln, pick, id_caixa=cx
                    )
                    used_title_ids.add(_titulo_id(pick))
                    if motivo:
                        item["motivo_pool"] = motivo
                elif acao == "bloqueio":
                    item["status"] = "bloqueio_duplicado"
                    item["gravou"] = False
                    item["motivo"] = motivo
                    item["ids_titulos"] = [
                        _titulo_id(t) for t in _cands_livres(cands, used_title_ids)
                    ]
                else:
                    item = _gravar_despesa_snf(
                        opener, item, ln,
                        ds_historico=_APLICACAO_DS_HISTORICO,
                        id_plano=_APLICACAO_ID_PLANO,
                        id_caixa=cx,
                    )
                executados.append(item)
                continue

            if classe == "tarifa":
                v = abs(float(ln.get("valor") or 0))
                cands = _candidatos_tarifa(pagar, v, _data_linha(ln))
                n_ofx = _count_ofx_mesmo_valor(linhas_gravar, "tarifa", v)
                acao, pick, motivo = _decidir_gate_pool(
                    cands_all=cands, used=used_title_ids, n_ofx=n_ofx,
                    plano_label="30060001", tela_estorno="1200",
                )
                if acao == "ligar" and pick is not None:
                    item = _ligar_titulo_na_linha(
                        opener, item, ln,
                        id_caixa=cx,
                        id_titulo=str(pick.get("id") or ""),
                        tp="Debito",
                        prefer_hist=("TARIFA", "TX ", "TAXA"),
                    )
                    item["tipo"] = "tarifa_ligada"
                    used_title_ids.add(_titulo_id(pick))
                    if motivo:
                        item["motivo_pool"] = motivo
                elif acao == "bloqueio":
                    item["status"] = "bloqueio_duplicado"
                    item["gravou"] = False
                    item["motivo"] = motivo
                    item["ids_titulos"] = [
                        _titulo_id(t) for t in _cands_livres(cands, used_title_ids)
                    ]
                else:
                    item = _gravar_despesa_snf(
                        opener, item, ln,
                        ds_historico=_TARIFA_DS_HISTORICO,
                        id_plano=_TARIFA_ID_PLANO,
                        id_caixa=cx,
                    )
                executados.append(item)
                continue

            if classe in ("resgate", "rentabilidade"):
                v = abs(float(ln.get("valor") or 0))
                hist = "resgate" if classe == "resgate" else "rentabilidade"
                cands = _candidatos_receita(receber, v, _data_linha(ln), classe)
                n_ofx = _count_ofx_mesmo_valor(linhas_gravar, classe, v)
                acao, pick, motivo = _decidir_gate_pool(
                    cands_all=cands, used=used_title_ids, n_ofx=n_ofx,
                    plano_label="30060006", tela_estorno="1100",
                )
                if acao == "ligar" and pick is not None:
                    item = _ligar_titulo_na_linha(
                        opener, item, ln,
                        id_caixa=cx,
                        id_titulo=str(pick.get("id") or ""),
                        tp="Credito",
                        prefer_hist=(hist.upper(),),
                    )
                    item["tipo"] = f"{classe}_ligada"
                    used_title_ids.add(_titulo_id(pick))
                    if motivo:
                        item["motivo_pool"] = motivo
                elif acao == "bloqueio":
                    item["status"] = "bloqueio_duplicado"
                    item["gravou"] = False
                    item["motivo"] = motivo
                    item["ids_titulos"] = [
                        _titulo_id(t) for t in _cands_livres(cands, used_title_ids)
                    ]
                else:
                    item, criado = _gravar_receita_e_baixa(
                        opener, item, ln, ds_historico=hist, id_caixa=cx
                    )
                    if criado is not None:
                        criados.append(criado)
                executados.append(item)
                continue

            if classe in ("liquidacao", "boleto"):
                item = _gravar_liquidacao(opener, item, ln, id_caixa=cx)
                executados.append(item)
                continue

            if classe == "cartao":
                tid = ln.get("id")
                v = abs(float(ln.get("valor") or 0))
                acao = str(ln.get("acao") or "")
                if not tid:
                    item["status"] = "stub_noop"
                    item["gravou"] = False
                    item["motivo"] = "Cartão GRAVAR sem id de título — use a tela."
                    executados.append(item)
                    continue
                # Desdobro: não ligar pedaço no título inteiro
                tit_valor = None
                for tt in (receber or []):
                    if str(tt.get("id") or "") == str(tid):
                        try:
                            tit_valor = abs(float(tt.get("valor") or 0))
                        except (TypeError, ValueError):
                            tit_valor = None
                        break
                # ocorrências deste tid entre cartões GRAVAR
                n_mesmo_id = sum(
                    1
                    for x in linhas_gravar
                    if (x.get("classe") or "").lower() == "cartao"
                    and str(x.get("id") or "") == str(tid)
                )
                is_desdobro = (
                    "desdobre" in acao.lower()
                    or n_mesmo_id >= 2
                    or (tit_valor is not None and abs(v - tit_valor) > 0.02)
                )
                if is_desdobro:
                    item["status"] = "bloqueio_desdobro"
                    item["gravou"] = False
                    item["id_titulo"] = tid
                    item["motivo"] = (
                        f"Cartão desdobrado: linha {v:.2f} ≠ título {tid}"
                        + (f" ({tit_valor:.2f})" if tit_valor is not None else "")
                        + " — não ligar pedaço no título inteiro; desdobrar na tela."
                    )
                    executados.append(item)
                    continue
                item = _ligar_titulo_na_linha(
                    opener, item, ln,
                    id_caixa=cx,
                    id_titulo=str(tid),
                    tp="Credito",
                    prefer_hist=("CIELO", "CARTAO", "VISA", "MASTER", "ELO", "AMEX", "REDE"),
                )
                item["tipo"] = "cartao_ligado"
                executados.append(item)
                continue

            if classe == "pix":
                tid = ln.get("id")
                v = abs(float(ln.get("valor") or 0))
                dia = _data_linha(ln)
                if tid:
                    # tenta ligar; se extrato/mov ausente → ja_pago_painel
                    before = dict(item)
                    item = _ligar_titulo_na_linha(
                        opener, item, ln,
                        id_caixa=cx,
                        id_titulo=str(tid),
                        tp="Credito",
                        prefer_hist=("PIX",),
                    )
                    if item.get("status") == "erro" and (
                        "Extrato pendente" in (item.get("motivo") or "")
                        or "Sem movimentação" in (item.get("motivo") or "")
                    ):
                        item["status"] = "ja_pago_painel"
                        item["gravou"] = False
                        item["id_titulo"] = tid
                        item["motivo"] = (
                            f"Pix {v:.2f}: título {tid} já pago no caixa {cx}; "
                            "movimento/extrato não aparece. Não liguei e não criei outro."
                        )
                    executados.append(item)
                    continue
                # sem id: Ariadna — Pix já baixado liga pelo valor na central
                cand = [
                    t for t in (receber or [])
                    if abs(float(t.get("valor") or 0) - v) <= 0.02
                    and _mesmo_dia_titulo(dia, _data_do_titulo(t))
                ]
                tid_guess = str(cand[0].get("id")) if len(cand) == 1 else None
                item = _ligar_titulo_na_linha(
                    opener, item, ln,
                    id_caixa=cx,
                    id_titulo=tid_guess,
                    tp="Credito",
                    prefer_hist=("PIX",),
                    excluir_cartao=True,
                )
                if item.get("status") == "gravado":
                    item["tipo"] = "pix_ligado_valor"
                    executados.append(item)
                    continue
                if len(cand) == 1 and item.get("status") == "erro" and (
                    "Extrato pendente" in (item.get("motivo") or "")
                    or "Sem movimentação" in (item.get("motivo") or "")
                ):
                    item["status"] = "ja_pago_painel"
                    item["gravou"] = False
                    item["id_titulo"] = cand[0].get("id")
                    item["motivo"] = (
                        f"Pix {v:.2f}: título {cand[0].get('id')} já no painel; "
                        "sem movimento para ligar. Não criei outro."
                    )
                elif item.get("status") != "gravado":
                    item["status"] = item.get("status") or "erro"
                    item["gravou"] = False
                    item["motivo"] = item.get("motivo") or (
                        f"Pix {v:.2f}: sem movimentação no valor para ligar."
                    )
                executados.append(item)
                continue

        except Exception as exc:  # noqa: BLE001
            item["status"] = "erro"
            item["gravou"] = False
            item["motivo"] = str(exc)
            executados.append(item)
            continue

        item["status"] = "stub_noop"
        item["gravou"] = False
        item["motivo"] = (
            "AVISO: modo executar — escrita implementada para aplicacao, "
            "tarifa, rentabilidade, resgate, liquidacao/boleto, cartao e pix. "
            f"Classe '{classe}': use a tela."
        )
        executados.append(item)
    return criados, executados



def _contagens_honestas(
    executados: list[dict], ariadna: list[dict]
) -> tuple[int, int, bool, int]:
    """conciliado=gravado; planejado=simulado; falta=ariadna+stubs/bloqueios/erros/ja_*.
    simulado conta como planejado — NUNCA fecha o dia."""
    conciliado = sum(
        1 for e in executados if e.get("status") in ("gravado", "ja_conciliado")
    )
    planejado = sum(1 for e in executados if e.get("status") == "simulado")
    falta_status = {
        "ariadna",
        "stub_noop",
        "bloqueio_duplicado",
        "bloqueio_desdobro",
        "erro",
        "ja_existe_ligar",
        "ja_pago_painel",
    }
    falta = len(ariadna) + sum(
        1 for e in executados if e.get("status") in falta_status
    )
    fechado = falta == 0 and conciliado >= 1 and planejado == 0
    return conciliado, falta, fechado, planejado


def _totais_entrada_saida(decisoes: list[dict]) -> tuple[float, float]:
    ent = sai = 0.0
    for d in decisoes:
        try:
            v = abs(float(d.get("valor") or 0))
        except (TypeError, ValueError):
            continue
        sentido = str(d.get("sentido") or "").lower()
        sinal = str(d.get("trntype") or d.get("tipo") or "").upper()
        if sentido == "saida" or sinal in ("DEBIT", "DEBITO", "D", "SAIDA", "XFER", "PAYMENT", "POS", "ATM"):
            sai += v
        elif sentido == "entrada" or sinal in ("CREDIT", "CREDITO", "C", "ENTRADA", "DEP", "DIRECTDEP"):
            ent += v
        else:
            cl = (d.get("classe") or "").lower()
            if cl in ("aplicacao", "tarifa"):
                sai += v
            elif cl in ("resgate", "rentabilidade", "liquidacao", "boleto", "cartao"):
                ent += v
            elif cl == "pix":
                # pix: default entrada se não houver sentido
                vs = d.get("valor_signed")
                if vs is not None and float(vs) < 0:
                    sai += v
                else:
                    ent += v
            else:
                vs = d.get("valor_signed")
                if vs is not None and float(vs) < 0:
                    sai += v
                else:
                    ent += v
    return round(ent, 2), round(sai, 2)


def _mensagem_fechamento(
    data: str,
    caixa: int,
    modo: str,
    decisoes: list[dict],
    executados: list[dict],
    ariadna: list[dict],
    pdf_path: str | None,
) -> str:
    """Único texto a enviar ao usuário — veredito final, sem narração."""
    try:
        dt = datetime.strptime(data[:10], "%Y-%m-%d")
        dia_br = dt.strftime("%d/%m")
    except ValueError:
        dia_br = data
    conciliado, falta, fechado, planejado = _contagens_honestas(executados, ariadna)
    ent, sai = _totais_entrada_saida(decisoes)

    def _br(n: float) -> str:
        return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if abs(ent - sai) <= 0.02 and (ent or sai):
        fecha_txt = f" Entrada e saída fecham em {_br(ent)}."
    elif ent or sai:
        fecha_txt = f" Entrada {_br(ent)}; saída {_br(sai)}."
    else:
        fecha_txt = ""

    estado = "fechado" if fechado else "aberto"
    head = (
        f"Dia {dia_br}, caixa {caixa}.{fecha_txt} "
        f"Na central: {conciliado} ligadas, {falta} em falta, ajuste 0 ({estado})."
    )
    if modo == "executar" and executados:
        head += f" Executar: {conciliado}/{len(executados)} gravado."
    elif modo == "simular":
        head += (
            f" Simular. Planejado {planejado}. GRAVAR {len(executados)}. "
            f"ARIADNA {len(ariadna)}."
        )

    blocos: list[str] = []
    by_cl: dict[str, list[dict]] = {}
    for e in executados:
        by_cl.setdefault((e.get("classe") or "outros").lower(), []).append(e)
    for a in ariadna:
        by_cl.setdefault((a.get("classe") or "outros").lower(), []).append(
            {**a, "status": "ariadna"}
        )

    def _vf(x: Any) -> str:
        try:
            return f"{float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return str(x or "")

    if "cartao" in by_cl:
        itens = by_cl["cartao"]
        partes = []
        for e in itens:
            st = e.get("status")
            if st == "gravado":
                partes.append(f"{_vf(e.get('valor'))} ligado")
            elif st == "ariadna":
                partes.append(f"{_vf(e.get('valor'))} em falta")
            elif st == "bloqueio_desdobro":
                partes.append(f"{_vf(e.get('valor'))} desdobro (bloqueio)")
            else:
                partes.append(f"{_vf(e.get('valor'))} ({st})")
        blocos.append("Cartão. " + "; ".join(partes) + ".")
    if "pix" in by_cl:
        for e in by_cl["pix"]:
            st = e.get("status")
            if st == "ariadna":
                blocos.append(
                    f"Pix {_vf(e.get('valor'))}. {e.get('acao') or 'Em falta.'}"
                )
            elif st == "ja_pago_painel":
                blocos.append(
                    f"Pix {_vf(e.get('valor'))}. Travou no painel. "
                    f"{e.get('motivo') or 'Já pago; não liguei e não criei outro.'}"
                )
            elif st == "gravado":
                blocos.append(f"Pix {_vf(e.get('valor'))}. Ligado.")
            else:
                blocos.append(
                    f"Pix {_vf(e.get('valor'))}. "
                    + (e.get("motivo") or st or "")
                )
    if "aplicacao" in by_cl:
        for e in by_cl["aplicacao"]:
            v = _vf(e.get("valor"))
            st = e.get("status")
            if st == "bloqueio_duplicado":
                blocos.append(
                    f"Aplicação {v}. Travou na escolha. São dois ou mais títulos "
                    "do mesmo valor. Não escolhi e não criei o terceiro. "
                    "O duplicado se estorna na 1200."
                )
            elif st == "ja_existe_ligar":
                blocos.append(
                    f"Aplicação {v}. Título único já existe; "
                    f"{e.get('motivo') or 'ligar via conciliar.'}"
                )
            elif st == "gravado":
                tip = e.get("tipo") or ""
                if tip == "aplicacao_ligada":
                    blocos.append(f"Aplicação {v}. Ligada no título existente.")
                else:
                    blocos.append(f"Aplicação {v}. Criada, baixada e ligada.")
            elif st == "simulado":
                tip = e.get("tipo") or ""
                if tip == "aplicacao_bloqueio_duplicado":
                    blocos.append(
                        f"Aplicação {v}. [simular] bloqueio duplicado — estornar na 1200."
                    )
                elif tip == "aplicacao_seria_ligada":
                    blocos.append(f"Aplicação {v}. [simular] ligaria o título único.")
                else:
                    blocos.append(f"Aplicação {v}. [simular] criaria despesa.")
            else:
                blocos.append(f"Aplicação {v}. {e.get('motivo') or st or ''}")

    for cl in sorted(by_cl):
        if cl in ("cartao", "pix", "aplicacao"):
            continue
        for e in by_cl[cl]:
            st = e.get("status")
            if st == "ariadna":
                blocos.append(
                    f"{cl.capitalize()} {_vf(e.get('valor'))}. "
                    f"{e.get('acao') or 'Em falta.'}"
                )
            elif st == "bloqueio_duplicado":
                blocos.append(
                    f"{cl.capitalize()} {_vf(e.get('valor'))}. "
                    f"{e.get('motivo') or 'Duplicado — não criei.'}"
                )
            elif st == "gravado":
                blocos.append(f"{cl.capitalize()} {_vf(e.get('valor'))}. Gravado.")
            elif st and st not in ("simulado",):
                blocos.append(
                    f"{cl.capitalize()} {_vf(e.get('valor'))}. "
                    f"{e.get('motivo') or st}"
                )

    body = "\n\n".join(blocos)
    pdf_line = f"\nPDF: {pdf_path}" if pdf_path else ""
    if body:
        return f"{head}\n\n{body}{pdf_line}".strip()
    return f"{head}{pdf_line}".strip()





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
        gravados = [x for x in items if x.get("status") in ("gravado", "ja_conciliado")]
        if not gravados:
            continue
        feito = gravados[0].get("acao") or "Baixado e ligado."
        if modo == "simular":
            feito = f"[simular] {feito}"
        fechou.append({"classe": classe, "qtd": len(gravados), "feito": feito})
    falta_linhas = []
    for a in ariadna:
        falta_linhas.append(
            {
                "valor": f"{float(a.get('valor') or 0):.2f}".replace(".", ","),
                "classe": a.get("classe") or "",
                "acao": a.get("acao") or f"Extrato: {a.get('nome') or ''}",
            }
        )
    for e in executados:
        st = e.get("status")
        if st in (
            "stub_noop",
            "bloqueio_duplicado",
            "bloqueio_desdobro",
            "erro",
            "ja_existe_ligar",
            "ja_pago_painel",
        ):
            falta_linhas.append(
                {
                    "valor": f"{float(e.get('valor') or 0):.2f}".replace(".", ","),
                    "classe": e.get("classe") or "",
                    "acao": e.get("motivo") or st,
                }
            )
    conciliado, falta, fechado, planejado = _contagens_honestas(executados, ariadna)
    return {
        "data": data,
        "linhas": len(linhas),
        "fecha": data,
        "fechado": fechado,
        "conciliado": conciliado,
        "planejado": planejado,
        "falta": falta,
        "ajuste": 0,
        "fechou": fechou
        or ([{"classe": "—", "qtd": 0, "feito": "Nada gravado nesta passagem."}] if not falta_linhas else []),
        "falta_linhas": falta_linhas,
        "gravado": (
            f"Modo {modo}. Conciliado {conciliado}. Planejado {planejado}. Falta {falta}."
            + (
                " Escrita: aplicacao/tarifa (gate 0/1/N + criar.consumo.snf + conciliar), "
                "resgate/rentabilidade (gate + criar.novo+baixa + conciliar), "
                "liquidacao/boleto/cartao/pix (conciliar); desdobro → bloqueio_desdobro."
                if modo == "executar"
                else " Simulado não fecha o dia."
            )
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
    """Concilia o caixa 4 do dia. Skill 1.38.3.

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

    dump_prefix = f"{data}-caixa{caixa}"
    try:
        receber, pagar, avisos = carregar_query(
            data, caixa, dump_prefix=dump_prefix
        )
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

    _dump_json(_cache_dir() / f"{dump_prefix}-extrato.json", extrato)

    decisoes = decidir(extrato, receber, pagar)
    gravar = [d for d in decisoes if d.get("veredito") == "GRAVAR"]
    ariadna = [d for d in decisoes if d.get("veredito") == "ARIADNA"]

    _dump_json(_cache_dir() / f"{dump_prefix}-decisao.json", decisoes)

    criados, executados = _executar_gravar(
        gravar, modo, pagar=pagar, receber=receber, id_caixa=caixa
    )

    if pdf_path is None:
        out_dir = _cache_dir()
        pdf_path = str(out_dir / f"conciliacao-{data}-caixa{caixa}.pdf")

    pdf_ok: str | None = None
    try:
        dados_pdf = _montar_json_pdf(data, decisoes, executados, ariadna, modo)
        pdf_ok = gerar_pdf(dados_pdf, pdf_path)
    except Exception as exc:  # noqa: BLE001
        erros.append(f"PDF: {exc}")

    conciliado, falta, fechado, planejado = _contagens_honestas(executados, ariadna)
    status = "fechado" if fechado else ("aberto" if (falta or ariadna or planejado) else "ok")
    if erros and not receber and not pagar:
        status = "parcial"

    return ResultadoConciliacao(
        status=status,
        data=data,
        caixa=caixa,
        modo=modo,
        contagens={
            "linhas": len(decisoes),
            "gravar": len(gravar),
            "ariadna": len(ariadna),
            "conciliado": conciliado,
            "planejado": planejado,
            "falta": falta,
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
        mensagem=_mensagem_fechamento(
            data, caixa, modo, decisoes, executados, ariadna, pdf_ok
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
        "Concilia o caixa 4 ValenLub no dia informado (skill 1.38.3). "
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
