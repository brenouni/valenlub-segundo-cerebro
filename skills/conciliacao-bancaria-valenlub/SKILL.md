---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Fecha na hora o que a regra fecha. Não pergunta. Não devolve à Ariadna."
version: "1.9.1"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Nenhum outro arquivo decide baixa. `leitura-query` não decide. `relatorio-conciliacao` não decide.
Empresa: Valen Lubrificantes. Não misturar com as outras 7.
Texto antigo de “não baixe” não vale.

## Fecha na hora. Não pergunta.

A regra já foi decidida. Não peça confirmação. Não pare no meio. Não devolva à Ariadna o que a regra fecha.
O que a regra fecha: baixe, ligue e vá à próxima linha. Na mesma passagem.
Ariadna só recebe a linha que a regra não fecha, depois da última linha. Uma ação. A tela. O dia.
Não diga “posso baixar”, “consigo o que a regra fecha” nem “Peça pra Ariadna” no meio.

## Relatório

Não monte o PDF na mão. Carregue `relatorio-conciliacao` e rode o `gerar.py`.
Dia aberto: PDF só se o Breno pedir. Selo âmbar. Sem `/new`.
Dia fechado: PDF sempre. Selo verde. Depois `/new`.
Dia fechado = Conciliado, Falta 0, Ajuste 0, tabela do resto vazia.
Não emita no meio da passagem.

O resto da regra permanece o da 1.9. Esta versão só troca o visual do PDF.
