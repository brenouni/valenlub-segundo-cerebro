#!/usr/bin/env python3
"""Decide a conciliação. O agente não escolhe. Fonte: skill 1.33.0."""
import json
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


def pares_cartao(ext, rec):
    """Duas linhas de cartão cuja soma é um título."""
    cart = [
        (i, round(float(l["valor"]), 2))
        for i, l in enumerate(ext)
        if (l.get("classe") or "").lower() == "cartao"
    ]
    usado, mapa = set(), {}
    for a in range(len(cart)):
        ia, va = cart[a]
        if ia in usado:
            continue
        for b in range(a + 1, len(cart)):
            ib, vb = cart[b]
            if ib in usado:
                continue
            soma = round(va + vb, 2)
            tit = [t for t in rec if abs(round(float(t["valor"]), 2) - soma) <= 0.02]
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
    """Aplica a skill 1.33.0. Retorna lista de linhas com veredito/acao/id."""
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
                        "Selecione os recebimentos do dia. Desmarque cartão. "
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
            # Skill 1.33.0: lançar + baixar (GRAVAR). Não ARIADNA.
            out.append(
                {
                    **linha,
                    "veredito": "GRAVAR",
                    "acao": (
                        "1100. Lançar receita avulsa. Cliente 1117 Bradesco. "
                        "Histórico rentabilidade. Conta 30060006. PIX. "
                        "Baixar: juros 0 multa 0 caixa 4. Ligue."
                    ),
                }
            )
            continue
        if classe == "aplicacao":
            out.append({**linha, "veredito": "ARIADNA", "acao": "Aplicação. Sem linha. Não crio."})
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
        cand = [t for t in base if abs(round(float(t["valor"]), 2) - v) <= 0.02]
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
            bruto = [
                t
                for t in rec
                if 0 < round(float(t["valor"]), 2) - v <= max(1.0, v * 0.05)
            ]
            if len(bruto) == 1:
                t = bruto[0]
                out.append(
                    {
                        **linha,
                        "veredito": "GRAVAR",
                        "id": t.get("id"),
                        "acao": "Pago no bruto. Ligue no líquido. Não edite.",
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
