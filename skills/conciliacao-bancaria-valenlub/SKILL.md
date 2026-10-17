---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4. Classifica pela API e grava na tela. Não reabrir não é não clicar."
version: "1.20.0"
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

A API classifica. A tela grava.
Se a ação é baixar ou ligar, clique e faça. Não escreva “só ligar” no PDF e pare.
“Não reabra o dia” quer dizer: não saia do dia e não volte no anterior. Não quer dizer não clicar.
Linha cuja regra é baixar ou ligar não vai para a Ariadna. Vai para a tela.
Se você entregou “só ligar” ou “baixar e ligar” como falta, a passagem falhou.

## Tempo

Aos 15 minutos, pare e escreva o ponto: o que ligou, o que falta, onde parou. Depois siga, ou pare nessa mensagem. Nunca mudo.

## Ler e gravar

Título, valor, status e pessoa: API. `GET /contas-receber` e `GET /contas-a-pagar`. `dt_baixa_fim` = dia seguinte.
Tela: baixar, ligar, tarifa, taxa. Só isso.
Se a central já está no dia, fique nela. Clique na linha. Não reabra.

## Fecha na hora

O que a regra fecha, grava na hora. Não liste. Não espere o Breno.

## Cartão

1. Líquido e NSU iguais: ligue.
2. NSU igual, título Aberto no bruto, banco + taxa = título: ajuste, taxa em 30010004 se não existir, ligue.
3. Título Pago: não edite. Não lance taxa que já existe. Se não ligar, aí entregue.

## Demais

Lote. Soma exata: ligue.
Pix já pago no valor, um só: ligue. Nome diferente não impede se o valor é único.
Pix aberto no valor, um só: juros 0, multa 0, baixe e ligue. Nome diferente não impede se o valor é único.
Vários do mesmo valor: eliminação por nome.
Sem título: proponha DNI. Não grave.
Tarifa. Botão Tarifa. 30060001. Já existente: não duplique.
Pagamento e Pix enviado. Título único: baixe e ligue.
Aplicação. Sem linha, não crie.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago.
Não entregue como falta o que a regra manda baixar ou ligar.
