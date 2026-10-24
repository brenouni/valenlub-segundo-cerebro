---
name: relatorio-conciliacao
description: "PDF da conciliação ValenLub. Linha em falta traz o nome do extrato. Não decide baixa."
version: "1.2.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Relatorio]
---

# Relatório da conciliação

Não decide baixa. A regra vive em `conciliacao-bancaria-valenlub`, versão 1.33.0.

## Quando emitir

Sempre no fim da passagem. Dia aberto: âmbar. Dia fechado: verde.

## Como emitir

1. Monte o JSON. Um arquivo só.
2. Rode `python3 skills/relatorio-conciliacao/gerar.py <json> <pdf>`.
3. Entregue o PDF. Não descreva o visual.

## Texto da linha em falta

Sempre o nome do extrato, inteiro. Se o OFX cortou, pegue o nome no PDF do extrato.
Se houve eliminação, traga também o nome do título que não casou.
Sem documento. Sem extrato inteiro.
Uma ação por linha.

Exemplo: `516,65. Extrato: RICARDO ANDRE DE OLIV. Títulos: F G GONCALVES LTDA. Nome diferente. Não liguei.`
