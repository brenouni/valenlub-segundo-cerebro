---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Fecha na hora. PDF sempre no fim. Cartão com NSU e taxa: desdobrar."
version: "1.11.0"
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
Texto antigo de “não baixe” não vale. Texto antigo de “PDF só se pedir” não vale.

## Fecha na hora. Não pergunta.

A regra já foi decidida. Não peça confirmação. Não pare no meio. Não devolva à Ariadna o que a regra fecha.
O que a regra fecha: baixe, ligue e vá à próxima linha. Na mesma passagem.
Ariadna só recebe a linha que a regra não fecha, depois da última linha. Uma ação. A tela. O dia.

## Relatório

Não monte o PDF na mão. Carregue `relatorio-conciliacao` e rode o `gerar.py`.
Sempre no fim da passagem. Não espere pedido.
Dia aberto: selo âmbar. Sem `/new`.
Dia fechado: selo verde. Escreva “Dia fechado. Mande /new.”
Dia fechado = Conciliado, Falta 0, Ajuste 0, tabela do resto vazia.
Não emita no meio.

O resto da regra permanece o da 1.10. Esta versão só muda quando o PDF sai.
