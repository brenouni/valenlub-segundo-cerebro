#!/usr/bin/env python3
"""PDF da conciliação no modelo aprovado. Uso: gerar.py dados.json saida.pdf"""
import json, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import white, HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

NAVY = HexColor("#0B1F3A")
BLUE = HexColor("#1F6FEB")
GREEN = HexColor("#0F7B4C")
GREEN_SOFT = HexColor("#E6F6EE")
AMBER = HexColor("#B45309")
AMBER_SOFT = HexColor("#FEF4E6")
INK = HexColor("#1A1A1A")
MUTED = HexColor("#5C6670")
LINE = HexColor("#E4E7EC")
ROW = HexColor("#F7F8FA")
PAGE_W, PAGE_H = A4

def draw(c, doc, fechado):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 22*mm, PAGE_W, 22*mm, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.rect(0, PAGE_H - 24*mm, PAGE_W, 2*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(18*mm, PAGE_H - 10*mm, "GoFluxo")
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - 18*mm, PAGE_H - 10*mm, "Valen Lubrificantes  ·  Caixa 4")
    c.setFont("Helvetica", 8)
    c.drawString(18*mm, PAGE_H - 16*mm, "Conciliação bancária")
    c.restoreState()
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, 12*mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica", 7.5)
    rodape = "Dia fechado." if fechado else "Dia aberto. Sem PDF final."
    c.drawString(18*mm, 5*mm, rodape)
    c.drawRightString(PAGE_W - 18*mm, 5*mm, f"Página {doc.page}")
    c.restoreState()

def main():
    src, out = sys.argv[1], sys.argv[2]
    d = json.load(open(src, encoding="utf-8"))
    fechado = bool(d.get("fechado"))
    S = getSampleStyleSheet()
    S.add(ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=18, textColor=NAVY, leading=22))
    S.add(ParagraphStyle("Lead", fontName="Helvetica", fontSize=10, textColor=INK, leading=14))
    S.add(ParagraphStyle("Sec", fontName="Helvetica-Bold", fontSize=11, textColor=NAVY, leading=14, spaceBefore=10, spaceAfter=4))
    S.add(ParagraphStyle("Body", fontName="Helvetica", fontSize=9, textColor=INK, leading=12))
    S.add(ParagraphStyle("Small", fontName="Helvetica", fontSize=8, textColor=MUTED, leading=10))
    S.add(ParagraphStyle("Th", fontName="Helvetica-Bold", fontSize=8, textColor=white, leading=10))
    S.add(ParagraphStyle("Td", fontName="Helvetica", fontSize=8.5, textColor=INK, leading=11))
    S.add(ParagraphStyle("TdR", fontName="Helvetica", fontSize=8.5, textColor=INK, leading=11, alignment=2))
    S.add(ParagraphStyle("Badge", fontName="Helvetica-Bold", fontSize=8, textColor=GREEN if fechado else AMBER, leading=10, alignment=1))

    def P(t, s="Td"): return Paragraph(str(t), S[s])
    story = [Spacer(1, 8*mm), P(f"Conciliação do dia {d['data']}", "H1"),
             P(f"Caixa 4 · Bradesco · {d['linhas']} lançamentos · Entrada e saída fecham em {d['fecha']}", "Lead")]

    badge = Table([[P("DIA FECHADO" if fechado else "DIA ABERTO", "Badge")]], colWidths=[34*mm])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GREEN_SOFT if fechado else AMBER_SOFT),
        ("BOX", (0,0), (-1,-1), 0.6, GREEN if fechado else AMBER),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    def metric(label, value, tone):
        return Table([[Paragraph(f'<font color="{tone}"><b>{value}</b></font>', S["Body"])],
                      [P(label, "Small")]], colWidths=[38*mm])
    metrics = Table([[badge, metric("Conciliado", d["conciliado"], "#0F7B4C"),
                      metric("Em falta", d["falta"], "#B45309"),
                      metric("Ajuste", d["ajuste"], "#1A1A1A")]],
                    colWidths=[36*mm, 40*mm, 40*mm, 40*mm])
    metrics.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    story += [metrics, Spacer(1, 4*mm)]
    if fechado:
        story.append(P("Resumo. Dia fechado. Nada ficou para a Ariadna.", "Lead"))
    else:
        story.append(P(f"Resumo. {d['conciliado']} linhas já estão ligadas. Sobram {d['falta']}.", "Lead"))

    story.append(P("O que já fechou", "Sec"))
    rows = [[P("Classe","Th"), P("Qtd","Th"), P("O que foi feito","Th")]]
    for i in d.get("fechou", []):
        rows.append([P(i["classe"]), Paragraph(str(i["qtd"]), S["TdR"]), P(i["feito"])])
    t = Table(rows, colWidths=[40*mm, 18*mm, 116*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, ROW]),
        ("BOX", (0,0), (-1,-1), 0.3, LINE),
        ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(t)

    if not fechado and d.get("falta_linhas"):
        story.append(P("O que ainda falta", "Sec"))
        story.append(P("Uma ação por linha.", "Body"))
        rows = [[P("Valor","Th"), P("Classe","Th"), P("Ação","Th")]]
        for i in d["falta_linhas"]:
            rows.append([Paragraph(str(i["valor"]), S["TdR"]), P(i["classe"]), P(i["acao"])])
        t2 = Table(rows, colWidths=[28*mm, 32*mm, 114*mm], repeatRows=1)
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), AMBER),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [AMBER_SOFT, white]),
            ("BOX", (0,0), (-1,-1), 0.3, HexColor("#F0D9B5")),
            ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        story.append(t2)

    if d.get("gravado"):
        story.append(P("O que foi gravado", "Sec"))
        story.append(P(d["gravado"], "Body"))

    def page(c, doc):
        draw(c, doc, fechado)
    SimpleDocTemplate(out, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm,
                      topMargin=28*mm, bottomMargin=16*mm,
                      title=f"Conciliação {d['data']}", author="GoFluxo"
                      ).build(story, onFirstPage=page, onLaterPages=page)
    print(out)

if __name__ == "__main__":
    main()
