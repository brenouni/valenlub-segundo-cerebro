---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4. Nome do extrato na falta. Eliminação só com nome igual."
version: "1.22.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única.

## Não reabrir não é não gravar

Se a ação é baixar ou ligar, clique e faça.
“Não reabra” = não saia do dia.

## Uma leitura. Depois só grava.

No começo, um GET do dia em receber e em pagar. `dt_baixa_fim` = dia seguinte.
Tela só para baixar, ligar, tarifa e taxa.

## Tempo

A cada 5 linhas, ponto. Aos 15 minutos, ponto. Nunca mudo.

## Nome

Pegue o nome inteiro. Se o OFX cortou, leia o PDF do extrato.
Ligue por nome só se for igual, o primeiro nome for o mesmo, ou a sigla do banco couber no título.
Pedaco não liga. OLIV não é OLIVEIRA.
Nome diferente: não ligue. Não grave DNI. Não lance pessoa.
No PDF, linha em falta traz o nome do extrato e, se houve busca, o nome do título.

## Ajuste de 0,55

Abra a linha. Painel com um 0,55: ligue. Painel vazio: Tarifa, 30060001, caixa 4, data do extrato.
Não pare em “já tem movimento” sem abrir.

## Cartão

Líquido e NSU iguais: ligue.
Pago no bruto: tente ligar no líquido. Não edite. Tela aceitou: fechou.
Aberto no bruto, banco + taxa = título: ajuste, taxa em 30010004 se não existir, ligue.

## Demais

Lote. Soma exata: ligue.
Pix valor único, aberto: juros 0, multa 0, baixe e ligue. Já pago: só ligue.
Sem título no dia: busque o valor sem filtro de dia. Um só e nome casa: ligue. Vários e nome não casa: não escolha. Nenhum: proponha DNI. Não grave.
Aplicação. Sem linha, não crie.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não ligue por pedaço de nome.
