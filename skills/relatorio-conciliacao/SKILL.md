---
name: relatorio-conciliacao
description: "PDF da conciliação ValenLub no modelo aprovado. Use no fim da passagem do caixa 4. Não decide baixa."
version: "1.0.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Relatorio]
---

# Relatório da conciliação

Não decide baixa. A regra vive em `conciliacao-bancaria-valenlub`.
Esta skill só desenha o PDF no modelo aprovado.

## Quando emitir

Dia aberto: emita este PDF só se o Breno pedir o relatório. Selo âmbar. Sem `/new`.
Dia fechado: emita sempre. Selo verde. Depois `/new`.
Dia fechado = Conciliado, Falta 0, Ajuste 0, tabela do resto vazia.
Não emita no meio da passagem.

## Como emitir

1. Monte o JSON do dia. Um arquivo só.
2. Rode `python3 skills/relatorio-conciliacao/gerar.py <json> <pdf>`.
3. Entregue o PDF. Não descreva o visual. Não monte tabela no chat.

## JSON

```json
{
  "data": "06/10/2026",
  "linhas": 44,
  "conciliado": 39,
  "falta": 5,
  "ajuste": 0,
  "fecha": "199.299,40",
  "fechado": false,
  "fechou": [
    {"classe": "Boleto (lote)", "qtd": 1, "feito": "Ligado na central"}
  ],
  "falta_linhas": [
    {"valor": "84,32", "classe": "Cartão débito", "acao": "Central, dia 06/10. Ligar se o título tiver o mesmo valor e o NSU 734479. Não lançar recebimento."}
  ],
  "gravado": "Lote ligado. Quatro tarifas baixadas."
}
```

## Regras do texto

Uma ação por linha. Sem “não busquei”. Sem “painel não carregou”.
Nome só quando dois valores iguais precisam de eliminação. Sem documento. Sem extrato.
O que já fechou vai em classe e quantidade. Não liste as 39 linhas.
