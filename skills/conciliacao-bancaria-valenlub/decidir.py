#!/usr/bin/env python3
"""Decide a conciliação. O agente não escolhe. Fonte: skill 1.39.2."""
import json
import re
import sys
import unicodedata
from itertools import combinations


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
            "dtCobrancaReceberBaixa",
            "dtCobrancaReceberRecebimento",
            "dtCobrancaPagarBaixa",
            "dtVencimentoCobrancaReceber",
            "dtVencimentoCobrancaPagar",
            "dtVencimento",
            "dtCobrancaReceber",
            "dt_pagamento",
            "dtPagamento",
            "dtCompetencia",
            "data",
            "dt",
        ):
            v = src.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
    return ""


def status_tit(t):
    raw = t.get("raw") if isinstance(t.get("raw"), dict) else {}
    for src in (raw, t):
        if not isinstance(src, dict):
            continue
        for k in ("statusCobranca", "status", "situacao", "status_cobranca"):
            v = src.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
    return str(t.get("status") or "").strip()


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
    """Data do título obrigatória (skill 1.39.2). Sem data → não casa."""
    if not (tit_data or "").strip():
        return False
    if not (linha_data or "").strip():
        return False
    return bool(_parts_dia(linha_data) & _parts_dia(tit_data))


def _vr(t):
    try:
        return round(float(t.get("valor") or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def pares_cartao(ext, rec):
    """Duas linhas de cartão cuja soma é um título (desdobro banco)."""
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
                if abs(_vr(t) - soma) <= 0.02
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


def _agregar_titulos(rec, alvo, max_n=5):
    """N títulos cuja soma fecha o valor OFX (±0,02)."""
    pool = [t for t in rec if 0 < _vr(t) <= alvo + 0.02]
    pool = sorted(pool, key=_vr)
    # limita explosão
    if len(pool) > 40:
        pool = pool[:40]
    for n in range(2, min(max_n, len(pool)) + 1):
        for combo in combinations(pool, n):
            if abs(round(sum(_vr(t) for t in combo), 2) - alvo) <= 0.02:
                return list(combo)
    return []


def _match_valor(base, v, dia_ln, exigir_dia=True):
    out = []
    for t in base:
        if abs(_vr(t) - v) > 0.02:
            continue
        if exigir_dia and not mesmo_dia_quando_ha(dia_ln, data_tit(t)):
            continue
        out.append(t)
    return out


def _pick_nome(cand, nome):
    if len(cand) == 1:
        return cand[0], None
    if len(cand) > 1:
        casa = [t for t in cand if cabe(nome, t.get("nome") or "")]
        if len(casa) == 1:
            return casa[0], None
        return None, cand
    return None, None


def decidir(ext, rec, pag):
    """Aplica a skill 1.39.2. Retorna lista de linhas com veredito/acao/id."""
    desdobra = pares_cartao(ext, rec)
    out = []
    for i, linha in enumerate(ext):
        v = round(float(linha["valor"]), 2)
        nome = linha.get("nome") or ""
        classe = (linha.get("classe") or "").lower()
        sentido = str(linha.get("sentido") or "").lower()
        trn = str(linha.get("trntype") or "").upper()
        is_saida = sentido == "saida" or trn in (
            "DEBIT", "DEBITO", "D", "PAYMENT", "POS", "ATM"
        )
        dia_ln = linha.get("data") or ""

        if i in desdobra:
            out.append({**linha, "veredito": "GRAVAR", **desdobra[i]})
            continue

        # Débito PAGTO ELETRON / cobrança saída → AP (não lote PAGTO crédito)
        if classe in ("boleto", "liquidacao", "pagar") and is_saida:
            cand = _match_valor(pag, v, dia_ln, exigir_dia=False)
            # prioriza mesmo dia se houver
            mesmo = [t for t in cand if mesmo_dia_quando_ha(dia_ln, data_tit(t))]
            use = mesmo if mesmo else cand
            t, varios = _pick_nome(use, nome)
            if t is not None:
                st = status_tit(t).lower()
                if st.startswith("abert"):
                    out.append(
                        {
                            **linha,
                            "veredito": "ARIADNA",
                            "id": t.get("id"),
                            "classe": "pagar",
                            "acao": (
                                f"AP {t.get('id')} Aberto no valor {v:.2f}. "
                                "Baixar na 1200 e religar. Tool não inventa baixa AP."
                            ),
                        }
                    )
                else:
                    out.append(
                        {
                            **linha,
                            "veredito": "GRAVAR",
                            "id": t.get("id"),
                            "classe": "pagar",
                            "acao": (
                                f"AP {t.get('id')} {t['valor']} ({status_tit(t) or 'Pago'}). "
                                "Débito PAGTO ELETRON — ligue no contas a pagar. "
                                "Não use lote PAGTO de boleto crédito."
                            ),
                        }
                    )
                continue
            if varios:
                out.append(
                    {
                        **linha,
                        "veredito": "ARIADNA",
                        "classe": "pagar",
                        "acao": (
                            "Vários AP no valor do débito. Ids: "
                            + ", ".join(str(t.get("id")) for t in varios[:6])
                        ),
                    }
                )
                continue
            out.append(
                {
                    **linha,
                    "veredito": "ARIADNA",
                    "classe": "pagar",
                    "acao": (
                        f"Débito {v:.2f} PAGTO ELETRON/cobrança. "
                        "Sem AP no valor — Ariadna (1200)."
                    ),
                }
            )
            continue

        if classe in ("boleto", "liquidacao"):
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "acao": (
                        "Lote. Não procure um título neste valor. "
                        "Selecione SOMENTE recebimentos que INICIAM com PAGTO "
                        "(retorno de boletos). Nunca Pix/CR/RECEBIMENTO DE CARTÃO. "
                        "Desmarque cartão. Se a soma bater no centavo, ligue."
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

        # Pix / depósito TED-cliente: achar título por valor (Pago ou Aberto)
        if classe in ("pix", "deposito"):
            # 1) mesmo dia
            cand = _match_valor(rec, v, dia_ln, exigir_dia=True)
            if not cand:
                # 2) sem exigir dia (Aberto com baixa null / emissão outra)
                cand = _match_valor(rec, v, dia_ln, exigir_dia=False)
            t, varios = _pick_nome(cand, nome)
            if t is not None:
                st = status_tit(t).lower()
                if st.startswith("abert"):
                    out.append(
                        {
                            **linha,
                            "veredito": "ARIADNA",
                            "id": t.get("id"),
                            "acao": (
                                f"Título {t.get('id')} Aberto no valor {v:.2f}. "
                                "Baixar na 1100 (Receber Pagamento) e religar. "
                                "Não inventar baixa automática de cliente."
                            ),
                        }
                    )
                else:
                    out.append(
                        {
                            **linha,
                            "veredito": "GRAVAR",
                            "id": t.get("id"),
                            "acao": (
                                f"Título {t.get('id')} {t['valor']} "
                                f"({status_tit(t) or 'Pago'}). Ligue pelo valor. "
                                "Se mov não aparecer: CR pode estar preso em "
                                "liquidação Conciliado — desconciliar "
                                "estornarTitulo=0, ligar Pix 1:1, religar só PAGTO*."
                            ),
                        }
                    )
                continue
            if varios:
                out.append(
                    {
                        **linha,
                        "veredito": "ARIADNA",
                        "acao": "Vários no valor. Ids: "
                        + ", ".join(
                            f"{t.get('id')}({status_tit(t) or '?'})" for t in varios[:6]
                        ),
                    }
                )
                continue
            # Pix sem título: ainda tenta ligar pelo valor na central (já baixado)
            if classe == "pix":
                out.append(
                    {
                        **linha,
                        "veredito": "GRAVAR",
                        "acao": (
                            "Pix sem id no GET. Tente ligar pelo valor na central. "
                            "Se não houver mov/título, Ariadna (não inventar)."
                        ),
                    }
                )
                continue
            out.append(
                {
                    **linha,
                    "veredito": "ARIADNA",
                    "acao": f"Extrato: {nome}. Sem título no valor {v:.2f}.",
                }
            )
            continue

        if classe == "cartao":
            # 1) match líquido ±0,02
            cand = _match_valor(rec, v, dia_ln, exigir_dia=True)
            if not cand:
                cand = _match_valor(rec, v, dia_ln, exigir_dia=False)
            t, varios = _pick_nome(cand, nome)
            if t is not None and abs(_vr(t) - v) <= 0.02:
                out.append(
                    {
                        **linha,
                        "veredito": "GRAVAR",
                        "id": t.get("id"),
                        "acao": f"Título {t.get('id')} {t['valor']}. Ligue.",
                    }
                )
                continue
            # 2) Cielo bruto → título no bruto (sem fallback 5%)
            cielo_bruto = linha.get("cielo_bruto")
            cielo_taxa = linha.get("cielo_taxa")
            cielo_liq = linha.get("cielo_liquido")
            if cielo_bruto is not None:
                alvo = round(float(cielo_bruto), 2)
                tit_bruto = [t for t in rec if abs(_vr(t) - alvo) <= 0.02]
                # prefer mesmo dia se houver
                mesmo = [
                    t for t in tit_bruto if mesmo_dia_quando_ha(dia_ln, data_tit(t))
                ]
                use = mesmo if len(mesmo) == 1 else tit_bruto
                if len(use) == 1:
                    t = use[0]
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
                    # se título >> líquido (parcela de venda maior) → desdobro tela
                    if _vr(t) - v > 0.02 and abs(_vr(t) - alvo) > 0.02:
                        out.append(
                            {
                                **linha,
                                "veredito": "GRAVAR",
                                "id": t.get("id"),
                                "acao": (
                                    f"Desdobre o título {t.get('id')} de {t['valor']} "
                                    f"para o líquido {v:.2f} (Cielo). Desdobrar na tela."
                                ),
                            }
                        )
                    else:
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
                if len(use) > 1:
                    # Vários no bruto: não ARIADNA ainda — tenta agregação / painel 1:1
                    pass
            # 3) agregação: N títulos (ex. 3 DEB) somam 1 OFX
            combo = _agregar_titulos(rec, v, max_n=5)
            # se veio cielo_agregados, prioriza esses líquidos
            agreg = linha.get("cielo_agregados") or []
            if agreg:
                ids_ag = []
                ok_ag = True
                for c in agreg:
                    br = c.get("bruto")
                    li = c.get("liquido")
                    hits = []
                    # prefer líquido (OFX), depois bruto (título CCR/DEB)
                    for alvo_c in (
                        round(float(li), 2) if li is not None else None,
                        round(float(br), 2) if br is not None else None,
                    ):
                        if alvo_c is None:
                            continue
                        hits = [t for t in rec if abs(_vr(t) - alvo_c) <= 0.02]
                        if len(hits) == 1:
                            break
                        hits = []
                    if len(hits) != 1:
                        # aceita 1 título no bruto mesmo se líquido não existir no pool
                        if br is not None:
                            hits = [
                                t
                                for t in rec
                                if abs(_vr(t) - round(float(br), 2)) <= 0.02
                            ]
                        if len(hits) != 1:
                            ok_ag = False
                            break
                    ids_ag.append(hits[0])
                if ok_ag and ids_ag:
                    # evidência Cielo: líquidos somam OFX — não exige soma dos brutos
                    combo = ids_ag
            if combo:
                ids = [str(t.get("id")) for t in combo]
                soma = round(sum(_vr(t) for t in combo), 2)
                liq_ag = linha.get("cielo_liquido")
                out.append(
                    {
                        **linha,
                        "veredito": "GRAVAR",
                        "id": ids[0],
                        "ids": ids,
                        "acao": (
                            f"Agregação Cielo/banco: {len(ids)} títulos "
                            f"({', '.join(ids)}; soma títulos {soma:.2f}) "
                            f"→ OFX {v:.2f}"
                            + (f" (líq Cielo {float(liq_ag):.2f})" if liq_ag else "")
                            + ". Ligue o lote (multi-id). Se algum Aberto, baixe antes."
                        ),
                    }
                )
                continue
            # Sem título líquido/bruto/agregação: cartão já baixado no painel → só ligar
            hint = ""
            if cielo_bruto is not None:
                hint = f" Cielo bruto {float(cielo_bruto):.2f}."
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "acao": (
                        "Cartão já pago no painel — ligar no líquido. "
                        "Sem título único no Query; use movimentação "
                        "RECEBIMENTO/CARTÃO/CIELO 1:1."
                        + hint
                    ),
                }
            )
            continue

        # demais / outros
        base = pag
        cand = _match_valor(base, v, dia_ln, exigir_dia=False)
        t, varios = _pick_nome(cand, nome)
        if t is not None:
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "id": t.get("id"),
                    "acao": f"Título {t.get('id')} {t['valor']}. Ajuste se precisar. Baixe e ligue.",
                }
            )
            continue
        if varios:
            out.append(
                {
                    **linha,
                    "veredito": "ARIADNA",
                    "acao": "Vários no valor. Nomes: "
                    + ", ".join((t.get("nome") or "?") for t in varios[:4]),
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
