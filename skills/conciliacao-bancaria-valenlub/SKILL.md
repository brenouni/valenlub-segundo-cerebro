---
name: conciliacao-bancaria-valenlub
description: "Conciliação do caixa 4. Anexo sem texto já é o pedido. Lote de boleto é soma, não um título."
version: "1.29.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.29. Você não decide. O script decide.

## Gatilho

Chegou OFX, PDF do extrato ou CSV da Cielo, com ou sem texto: é conciliação.
Não peça comando. Não pergunte o dia.
A data é a do arquivo. Outro dia no mesmo arquivo não entra.
Sem arquivo, pare. Responda sem ser marcado.

## Ordem

1. Dois GETs. Salve o JSON. `dt_baixa_fim` = dia seguinte.
2. Monte o extrato do dia: valor, nome inteiro, classe.
3. Rode `decidir.py`.
4. Linha `GRAVAR`: clique e faça. Não reclassifique.
5. Linha `ARIADNA`: não grave. Vai para o PDF, com o nome.
6. PDF no fim. Pare em: “Passagem feita.”

## Lote de boleto

LIQUIDACAO DE COBRANCA não é um título. Ariadna, 19/10.
Não procure um título no valor da linha.

1. Abra os recebimentos do dia.
2. Selecione todos.
3. Desmarque o que for recebimento de cartão.
4. Some o que ficou. Se bater com a linha do banco, no centavo, ligue.
5. Não mande o lote para a Ariadna só porque a linha não foi aberta.

## Resgate

Nasce na 1100. Mais receita. Cliente Bradesco. Histórico do extrato.
Competência e pagamento = data do extrato. Conta 30060006.
Pix ou dinheiro. À vista. Baixa: juros 0, multa 0, caixa 4. Ligue.
Aplicação e rentabilidade: ARIADNA. Não crie.

## Demais

Centavo: título único até 0,02 é GRAVAR.
Cartão pago no bruto: ligue no líquido. Não edite.
Tarifa: 30060001, caixa 4, data do extrato.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não procure um título no valor do lote.
