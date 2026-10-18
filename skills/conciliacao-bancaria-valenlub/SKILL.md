---
name: conciliacao-bancaria-valenlub
description: "Conciliação do caixa 4. Anexo de OFX, PDF do extrato ou CSV da Cielo, mesmo sem texto, já é o pedido. Rode. Não peça comando."
version: "1.27.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.27. Você não decide. O script decide.

## Gatilho

Chegou OFX, PDF do extrato ou CSV da Cielo, com ou sem texto: é conciliação.
Não peça comando. Não pergunte o dia.
A data é a do arquivo. Outro dia no mesmo arquivo não entra.
Sem arquivo, pare.

## Ordem

1. Dois GETs. Salve o JSON. `dt_baixa_fim` = dia seguinte.
2. Monte o extrato do dia: valor, nome inteiro, classe.
3. Rode `python3 skills/conciliacao-bancaria-valenlub/decidir.py extrato.json receber.json pagar.json saida.json`.
4. Linha `GRAVAR`: clique e faça. Não reclassifique.
5. Linha `ARIADNA`: não grave. Vai para o PDF, com o nome.
6. PDF no fim. Pare em: “Passagem feita.”

## Resgate

Conta 30060006 RESGATE. Caixa 4. Data do extrato. Juros 0. Multa 0.
Lance, baixe e ligue.
Aplicação e rentabilidade: ARIADNA. Não crie.

## Demais

Centavo: título único até 0,02 é GRAVAR.
Cartão pago no bruto: ligue no líquido. Não edite.
Tarifa: 30060001, caixa 4, data do extrato.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não peça o comando de novo.
