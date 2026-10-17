---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4. GET antes do clique. Sobrenome tem que caber. Nome na falta."
version: "1.23.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única.

## GET antes de clicar

Antes de abrir a tela, dois GETs. Só leitura.
`GET /contas-receber` e `GET /contas-a-pagar`.
Base: `https://backend.acessoquery.com/api`. Header: `X-Tenant` + Bearer.
`dt_baixa_fim` = dia seguinte. No mesmo dia volta zero.
Guarde valor, status, pessoa e id. Monte a lista.
Se a API respondeu, zero clique para procurar. A tela só baixa, liga, tarifa e taxa.
Se a API falhar, aí a tela. Uma vez. Não repita a busca.

## Não reabrir não é não gravar

Se a ação é baixar ou ligar, clique e faça.
“Não reabra” = não saia do dia.

## Tempo

A cada 5 linhas, ponto. Aos 15 minutos, ponto. Nunca mudo.

## Nome

Nome inteiro. OFX cortou: leia o PDF do extrato.
Liga se o nome for igual, ou o primeiro nome e o sobrenome couberem, ou a sigla do banco couber no título.
Primeiro nome sozinho não liga. Mariana Silva não é Mariana Costa.
Pedaço não liga. OLIV não é OLIVEIRA.
Nome diferente: não ligue. Não grave DNI. Não lance pessoa.
Linha em falta: o campo ação traz o nome do extrato e, se buscou, o nome do título.

## Ajuste de 0,55

Abra a linha. Um 0,55 no painel: ligue. Painel vazio: Tarifa, 30060001, caixa 4, data do extrato.
Não pare em “já tem movimento” sem abrir.

## Cartão

Líquido e NSU iguais: ligue.
Pago no bruto: tente ligar no líquido. Não edite. Tela aceitou: fechou.
Aberto no bruto, banco + taxa = título: ajuste, taxa em 30010004 se não existir, ligue.

## Demais

Lote. Soma exata: ligue.
Pix valor único, aberto: juros 0, multa 0, baixe e ligue. Já pago: só ligue.
Sem título no dia: busque o valor sem filtro de dia. Um só e nome casa: ligue. Vários: não escolha. Nenhum: proponha DNI. Não grave.
Aplicação. Sem linha, não crie.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não ligue por pedaço de nome.
Não procure na tela se a API respondeu.
