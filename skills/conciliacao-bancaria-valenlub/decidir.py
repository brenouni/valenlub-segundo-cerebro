#!/usr/bin/env python3
"""Decide a conciliação. O agente não escolhe.
Uso: decidir.py extrato.json receber.json pagar.json saida.json
extrato: [{"valor": 150.0, "nome": "...", "classe": "pix|tarifa|cartao|boleto|pagamento|resgate|aplicacao"}]
receber/pagar: [{"id": 1, "valor": 149.99, "nome": "...", "status": "aberto|pago"}]
Saída: veredito GRAVAR ou ARIADNA. GRAVAR o agente executa. Não reclassifica.
"""
import json, sys, unicodedata

def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").upper())
    return "".join(c for c in s if not unicodedata.combining(c))

def cabe(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        # pedaço curto não conta
        curto = a if len(a) <= len(b) else b
        return len(curto) >= 8
    pa, pb = a.split(), b.split()
    if not pa or not pb:
        return False
    return pa[0] == pb[0] and any(x in b for x in pa[1:]) and len(pa[0]) >= 4

def main():
    ext = json.load(open(sys.argv[1], encoding="utf-8"))
    rec = json.load(open(sys.argv[2], encoding="utf-8"))
    pag = json.load(open(sys.argv[3], encoding="utf-8"))
    out = []
    for linha in ext:
        v = round(float(linha["valor"]), 2)
        nome = linha.get("nome") or ""
        classe = (linha.get("classe") or "").lower()
        base = rec if classe in ("pix", "cartao", "boleto") else pag
        if classe in ("resgate", "aplicacao", "rentabilidade"):
            out.append({**linha, "veredito": "ARIADNA", "acao": "Sem linha. Não crio."})
            continue
        if classe == "tarifa":
            out.append({**linha, "veredito": "GRAVAR", "acao": "Tarifa 30060001, caixa 4, data do extrato."})
            continue
        cand = [t for t in base if abs(round(float(t["valor"]), 2) - v) <= 0.02]
        if len(cand) == 1:
            t = cand[0]
            out.append({**linha, "veredito": "GRAVAR", "id": t.get("id"),
                        "acao": f"Título {t.get('id')} {t['valor']}. Ajuste se precisar. Baixe e ligue."})
            continue
        if len(cand) > 1:
            casa = [t for t in cand if cabe(nome, t.get("nome") or "")]
            if len(casa) == 1:
                t = casa[0]
                out.append({**linha, "veredito": "GRAVAR", "id": t.get("id"),
                            "acao": f"Nome casa. Título {t.get('id')}. Baixe e ligue."})
                continue
            out.append({**linha, "veredito": "ARIADNA",
                        "acao": "Vários no valor. Nomes: " + ", ".join((t.get("nome") or "?") for t in cand[:4])})
            continue
        # cartão: título no bruto, diferença até 5%
        if classe == "cartao":
            bruto = [t for t in rec if 0 < round(float(t["valor"]), 2) - v <= max(1.0, v * 0.05)]
            if len(bruto) == 1:
                t = bruto[0]
                out.append({**linha, "veredito": "GRAVAR", "id": t.get("id"),
                            "acao": "Pago no bruto. Ligue no líquido. Não edite."})
                continue
        out.append({**linha, "veredito": "ARIADNA", "acao": f"Extrato: {nome}. Sem título no valor."})
    json.dump(out, open(sys.argv[4], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    g = sum(1 for i in out if i["veredito"] == "GRAVAR")
    print(f"GRAVAR {g} / {len(out)}")

if __name__ == "__main__":
    main()
