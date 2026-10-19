---
name: conciliacao-bancaria-valenlub
description: "Conciliação do caixa 4. Anexo sem texto já é o pedido. Cartão somado desdobra. Lote é soma."
version: "1.30.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.30. Você não decide. O script decide.

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

## Cartão desdobrado

Ariadna, 19/10. A Cielo junta. O banco separa.
Duas linhas do banco somam um título: é desdobrar. Não é falta.

1. Ache o título no valor da soma.
2. Clique em desdobrar.
3. Informe os dois valores do banco. A soma tem que bater no centavo.
4. Ligue cada linha no seu pedaço.

Linha de cartão com título no mesmo valor: só ligue.
Pago no bruto, diferença = taxa: ligue no líquido. Não edite.

## Lote de boleto

Não procure um título no valor da linha.
Selecione os recebimentos do dia. Desmarque cartão. Soma bate, ligue.

## Resgate

Nasce na 1100. Cliente Bradesco. Conta 30060006.
Competência e pagamento = data do extrato.
Baixa: juros 0, multa 0, caixa 4. Ligue.
Aplicação e rentabilidade: ARIADNA. Não crie.

## Demais

Centavo: título único até 0,02 é GRAVAR.
Tarifa: 30060001, caixa 4, data do extrato.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não procure um título no valor do lote.
Não deixe duas linhas de cartão em falta se a soma é um título.
