---
name: conciliacao-bancaria-valenlub
description: "Conciliação do caixa 4. Anexo de OFX, PDF ou CSV, mesmo sem texto, já é o pedido. Resgate nasce na 1100."
version: "1.28.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.28. Você não decide. O script decide.

## Gatilho

Chegou OFX, PDF do extrato ou CSV da Cielo, com ou sem texto: é conciliação.
Não peça comando. Não pergunte o dia.
A data é a do arquivo. Outro dia no mesmo arquivo não entra.
Sem arquivo, pare.

## Ordem

1. Dois GETs. Salve o JSON. `dt_baixa_fim` = dia seguinte.
2. Monte o extrato do dia: valor, nome inteiro, classe.
3. Rode `decidir.py`.
4. Linha `GRAVAR`: clique e faça. Não reclassifique.
5. Linha `ARIADNA`: não grave. Vai para o PDF, com o nome.
6. PDF no fim. Pare em: “Passagem feita.”

## Resgate

Nasce na 1100, contas a receber. Não no pagar. Ariadna, 19/10.

1. 1100. Mais receita.
2. Cliente: Bradesco.
3. Histórico: copie a descrição do extrato. Ex.: RESGATE INVEST FACIL.
4. Valor: o do extrato.
5. Competência: data do extrato. Pagamento: data do extrato.
6. Caixa, neste lançamento: não preencha.
7. Plano de contas: digite resgate. Selecione 30060006.
8. Forma: Pix ou dinheiro. Plano: à vista. Operador: não preencha.
9. Conclua.
10. Ignore a data. Cliente: Bradesco. Ache o valor.
11. Antes de baixar: apague juros e multa.
12. Caixa: caixa 4. Conclua o pagamento.
13. Ligue na central.

Aplicação e rentabilidade: ARIADNA. Não crie.

## Demais

Centavo: título único até 0,02 é GRAVAR.
Cartão pago no bruto: ligue no líquido. Não edite.
Tarifa: 30060001, caixa 4, data do extrato.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não peça o comando de novo.
