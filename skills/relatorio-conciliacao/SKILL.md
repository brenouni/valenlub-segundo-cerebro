---
name: relatorio-conciliacao
description: "PDF da conciliação ValenLub no modelo aprovado. Sai sempre no fim da passagem. Não decide baixa."
version: "1.1.0"
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

Sempre no fim da passagem. Não espere pedido.
Dia aberto: selo âmbar. Sem `/new`.
Dia fechado: selo verde. Depois escreva “Dia fechado. Mande /new.”
Dia fechado = Conciliado, Falta 0, Ajuste 0, tabela do resto vazia.
Não emita no meio da passagem.

## Como emitir

1. Monte o JSON do dia. Um arquivo só.
2. Rode `python3 skills/relatorio-conciliacao/gerar.py <json> <pdf>`.
3. Entregue o PDF. Não descreva o visual. Não monte tabela no chat.

## Regras do texto

Uma ação por linha. Sem “não busquei”. Sem “painel não carregou”.
Nome só quando dois valores iguais precisam de eliminação. Sem documento. Sem extrato.
O que já fechou vai em classe e quantidade. Não liste linha a linha.
