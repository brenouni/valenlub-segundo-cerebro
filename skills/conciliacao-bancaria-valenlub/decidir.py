#!/usr/bin/env python3
"""Decide a conciliação. O agente não escolhe. Fonte: skill 1.38.3."""
import json
import re
import sys
import unicodedata


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").upper())
    return "".join(c for c in s if not unicodedata.combining(c))


def cabe(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        curto = a if len(a) <= len(b) else b
        return len(curto) >= 8
    pa, pb = a.split(), b.split()
    if not pa or not pb:
        return False
    return pa[0] == pb[0] and any(x in b for x in pa[1:]) and len(pa[0]) >= 4


def data_tit(t):
    """Data do título quando disponível (raw.datas / campos)."""
    raw = t.get("raw") if isinstance(t.get("raw"), dict) else {}
    datas = raw.get("datas") if isinstance(raw.get("datas"), dict) else {}
    for src in (datas, raw, t):
        if not isinstance(src, dict):
            continue
        for k in (
            "dtBaixa",
            "dt_baixa",
            "dtCobrancaReceberRecebimento",
            "dtCobrancaPagarBaixa",
            "dtVencimentoCobrancaReceber",
            "dtVencimentoCobrancaPagar",
            "dtVencimento",
            "dt_pagamento",
            "dtPagamento",
            "data",
            "dt",
        ):
            v = src.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
    return ""


def _parts_dia(s):
    s2 = (s or "").replace("T", " ").split()[0]
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


def mesmo_dia_quando_ha(linha_data, tit_data):
    """Data do título obrigatória (skill 1.38.3). Sem data → não casa."""
    if not (tit_data or "").strip():
        return False
    if not (linha_data or "").strip():
        return False
    return bool(_parts_dia(linha_data) & _parts_dia(tit_data))


def pares_cartao(ext, rec):
    """Duas linhas de cartão cuja soma é um título."""
    cart = [
        (i, round(float(l["valor"]), 2), l.get("data") or "")
        for i, l in enumerate(ext)
        if (l.get("classe") or "").lower() == "cartao"
    ]
    usado, mapa = set(), {}
    for a in range(len(cart)):
        ia, va, da = cart[a]
        if ia in usado:
            continue
        for b in range(a + 1, len(cart)):
            ib, vb, db = cart[b]
            if ib in usado:
                continue
            soma = round(va + vb, 2)
            dia = da or db
            tit = [
                t
                for t in rec
                if abs(round(float(t["valor"]), 2) - soma) <= 0.02
                and mesmo_dia_quando_ha(dia, data_tit(t))
            ]
            if len(tit) == 1:
                t = tit[0]
                acao = (
                    f"Desdobre o título {t.get('id')} de {t['valor']} "
                    f"em {va:.2f} e {vb:.2f}. Ligue cada linha."
                )
                mapa[ia] = {"id": t.get("id"), "acao": acao}
                mapa[ib] = {"id": t.get("id"), "acao": acao}
                usado.update((ia, ib))
                break
    return mapa


def decidir(ext, rec, pag):
    """Aplica a skill 1.38.3. Retorna lista de linhas com veredito/acao/id."""
    desdobra = pares_cartao(ext, rec)
    out = []
    for i, linha in enumerate(ext):
        v = round(float(linha["valor"]), 2)
        nome = linha.get("nome") or ""
        classe = (linha.get("classe") or "").lower()
        if i in desdobra:
            out.append({**linha, "veredito": "GRAVAR", **desdobra[i]})
            continue
        if classe in ("boleto", "liquidacao"):
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "acao": (
                        "Lote. Não procure um título neste valor. "
                        "Selecione TODOS os recebimentos que iniciam com PAGTO "
                        "(retorno de boletos). Desmarque cartão. "
                        "Se a soma bater no centavo, ligue."
                    ),
                }
            )
            continue
        if classe == "resgate":
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "acao": (
                        "1100. Lançar receita avulsa. Cliente 1117 Bradesco. "
                        "Histórico resgate. Conta 30060006. PIX. "
                        "Baixar: juros 0 multa 0 caixa 4. Ligue."
                    ),
                }
            )
            continue
        if classe == "rentabilidade":
            # Skill 1.38.3: criar e baixar (GRAVAR). Nunca Pix/ARIADNA.
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "acao": (
                        "1100. Criar e baixar receita avulsa. Cliente 1117 Bradesco. "
                        "Histórico rentabilidade. Conta 30060006. "
                        "Baixar: juros 0 multa 0 caixa 4. Ligue."
                    ),
                }
            )
            continue
        if classe == "aplicacao":
            # Skill 1.38.3: 1200 Mais despesa, 30060005, GRAVAR. Nunca ARIADNA.
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "acao": (
                        "1200. Mais despesa. Fornecedor Bradesco. Descrição aplicação. "
                        "Vencimento e competência = data do extrato. Conta 30060005. "
                        "Rateio vazio. Marca pagamento. Caixa 4. Pagamento = data do extrato. Ligue."
                    ),
                }
            )
            continue
        if classe == "tarifa":
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "acao": "Tarifa 30060001, caixa 4, data do extrato.",
                }
            )
            continue
        base = rec if classe in ("pix", "cartao") else pag
        dia_ln = linha.get("data") or ""
        cand = [
            t
            for t in base
            if abs(round(float(t["valor"]), 2) - v) <= 0.02
            and (
                classe not in ("pix", "cartao")
                or mesmo_dia_quando_ha(dia_ln, data_tit(t))
            )
        ]
        if len(cand) == 1:
            t = cand[0]
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "id": t.get("id"),
                    "acao": f"Título {t.get('id')} {t['valor']}. Ajuste se precisar. Baixe e ligue.",
                }
            )
            continue
        if len(cand) > 1:
            casa = [t for t in cand if cabe(nome, t.get("nome") or "")]
            if len(casa) == 1:
                t = casa[0]
                out.append(
                    {
                        **linha,
                        "veredito": "GRAVAR",
                        "id": t.get("id"),
                        "acao": f"Nome casa. Título {t.get('id')}. Baixe e ligue.",
                    }
                )
                continue
            out.append(
                {
                    **linha,
                    "veredito": "ARIADNA",
                    "acao": "Vários no valor. Nomes: "
                    + ", ".join((t.get("nome") or "?") for t in cand[:4]),
                }
            )
            continue
        if classe == "cartao":
            # Cielo: se veio líquido/taxa/bruto, usa bruto p/ achar título e liga no líquido
            cielo_bruto = linha.get("cielo_bruto")
            cielo_taxa = linha.get("cielo_taxa")
            cielo_liq = linha.get("cielo_liquido")
            if cielo_bruto is not None:
                alvo = round(float(cielo_bruto), 2)
                tit_bruto = [
                    t
                    for t in rec
                    if abs(round(float(t["valor"]), 2) - alvo) <= 0.02
                    and mesmo_dia_quando_ha(linha.get("data") or "", data_tit(t))
                ]
                if len(tit_bruto) == 1:
                    t = tit_bruto[0]
                    taxa_txt = (
                        f" Taxa Cielo {float(cielo_taxa):.2f}."
                        if cielo_taxa is not None
                        else ""
                    )
                    liq_txt = (
                        f" Líquido {float(cielo_liq):.2f}."
                        if cielo_liq is not None
                        else f" Líquido {v:.2f}."
                    )
                    out.append(
                        {
                            **linha,
                            "veredito": "GRAVAR",
                            "id": t.get("id"),
                            "acao": (
                                f"Cielo: título {t.get('id')} no bruto {alvo:.2f}."
                                f"{taxa_txt}{liq_txt} Ligue no líquido. Não edite."
                            ),
                        }
                    )
                    continue
            bruto = [
                t
                for t in rec
                if 0 < round(float(t["valor"]), 2) - v <= max(1.0, v * 0.05)
                and mesmo_dia_quando_ha(linha.get("data") or "", data_tit(t))
            ]
            if len(bruto) == 1:
                t = bruto[0]
                taxa_extra = ""
                if cielo_taxa is not None:
                    taxa_extra = f" Taxa Cielo {float(cielo_taxa):.2f}."
                out.append(
                    {
                        **linha,
                        "veredito": "GRAVAR",
                        "id": t.get("id"),
                        "acao": f"Pago no bruto. Ligue no líquido. Não edite.{taxa_extra}",
                    }
                )
                continue
        # Ariadna 2026-10-27: Pix já baixado fica disponível no valor — ligue.
        if classe == "pix":
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "acao": (
                        "Pix já baixado. Ligue pelo valor na central do caixa. "
                        "Não é falta de título se a baixa já foi feita."
                    ),
                }
            )
            continue
        out.append(
            {
                **linha,
                "veredito": "ARIADNA",
                "acao": f"Extrato: {nome}. Sem título no valor.",
            }
        )
    return out


def main():
    ext = json.load(open(sys.argv[1], encoding="utf-8"))
    rec = json.load(open(sys.argv[2], encoding="utf-8"))
    pag = json.load(open(sys.argv[3], encoding="utf-8"))
    out = decidir(ext, rec, pag)
    json.dump(out, open(sys.argv[4], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    g = sum(1 for i in out if i["veredito"] == "GRAVAR")
    print(f"GRAVAR {g} / {len(out)}")


if __name__ == "__main__":
    main()
