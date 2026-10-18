---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1. O script decide. Resgate lança na 30060006."
version: "1.26.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.26. Você não decide. O script decide.

## Ordem

1. Dois GETs. Salve o JSON. `dt_baixa_fim` = dia seguinte.
2. Monte o extrato do dia: valor, nome inteiro, classe.
3. Rode `python3 skills/conciliacao-bancaria-valenlub/decidir.py extrato.json receber.json pagar.json saida.json`.
4. Linha `GRAVAR`: clique e faça. Não reclassifique.
5. Linha `ARIADNA`: não grave. Vai para o PDF, com o nome.
6. Se você entregou uma linha GRAVAR como falta, a passagem falhou.

## Resgate

Autorizado pela Ariadna em 18/10.
Conta 30060006 RESGATE. Caixa 4. Data do extrato.
Juros 0. Multa 0. O valor baixado é o do extrato.
Lance, baixe e ligue. Não peça passo a passo.

Aplicação e rentabilidade: ARIADNA. Não crie.

## Demais

Centavo: título único até 0,02 é GRAVAR. Ajuste, juros 0, baixe e ligue.
Cartão pago no bruto: ligue no líquido. Não edite.
Tarifa: 30060001, caixa 4, data do extrato.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não crie aplicação nem rentabilidade.
