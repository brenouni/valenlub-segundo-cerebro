---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1. O script decide. O agente só grava o que o script marcou GRAVAR."
version: "1.25.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.25. Você não decide. O script decide.

## Ordem

1. Dois GETs. Salve o JSON. `dt_baixa_fim` = dia seguinte.
2. Monte o extrato do dia: valor, nome inteiro, classe.
3. Rode `python3 skills/conciliacao-bancaria-valenlub/decidir.py extrato.json receber.json pagar.json saida.json`.
4. Linha `GRAVAR`: clique e faça. Não reclassifique. Não escreva a ação no PDF e pare.
5. Linha `ARIADNA`: não grave. Vai para o PDF, com o nome.
6. Se você entregou uma linha GRAVAR como falta, a passagem falhou.

Centavo: título único até 0,02 de diferença é GRAVAR. Ajuste para o banco, juros 0, baixe e ligue.
Cartão pago no bruto: GRAVAR manda ligar no líquido. Não edite.
Tarifa: GRAVAR. 30060001, caixa 4, data do extrato.
Resgate, aplicação, rentabilidade: ARIADNA. Não crie.

## Tempo

A cada 5 linhas gravadas, ponto. Aos 15 minutos, ponto. Nunca mudo.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não procure na tela o que o script já classificou.
