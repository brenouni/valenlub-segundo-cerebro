---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4. Ajuste vazio vira tarifa. Cartão pago liga no líquido. API uma vez."
version: "1.21.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Lições do dia 08/10.

## Não reabrir não é não gravar

Se a ação é baixar ou ligar, clique e faça. Não escreva a ação no PDF e pare.
“Não reabra” = não saia do dia. Não é não clicar.

## Uma leitura. Depois só grava.

No começo, um `GET /contas-receber` e um `GET /contas-a-pagar` do dia. `dt_baixa_fim` = dia seguinte.
Monta a lista. Não abra painel para achar título.
Tela só para baixar, ligar, tarifa e taxa.

## Tempo

A cada 5 linhas, ponto. Aos 15 minutos, ponto e pare de clicar se ainda não acabou. Nunca mudo.

## Ajuste de 0,55

Ajuste não é linha fechada.
Abra a linha. Leia o painel.
Um 0,55 único no painel: ligue. Não lance outra.
Painel vazio: botão Tarifa. Bradesco, 30060001, caixa 4, data do extrato. Baixe e ligue.
Não pare em “já tem movimento” sem abrir a linha.
Exemplo do 08/10: 15 de 0,55. Painel vazio nas 15. Tarifa lançada e ligada. Dia foi de 33 para 48.

## Cartão

1. Líquido e NSU iguais: ligue.
2. Título pago no bruto, NSU igual: tente ligar no recebimento do líquido. Não edite o título pago. Se a tela aceitar, fechou.
3. Título Aberto no bruto, banco + taxa = título: ajuste, taxa em 30010004 se não existir, ligue.
4. Tela recusou: entregue. Não lance taxa que já existe.
Exemplo do 08/10: 81,87. Liguei no líquido. Tela aceitou. Não editei.

## Demais

Lote. Soma exata: ligue.
Pix já pago, valor único: ligue. Nome diferente não impede.
Pix aberto, valor único: juros 0, multa 0, baixe e ligue.
Sem título no dia: busque o valor na API, sem filtro de dia. Um só: baixe e ligue. Vários: não escolha. Nenhum: proponha DNI. Não grave.
Pagamento e Pix enviado. Título único: baixe e ligue. Outra pessoa: não lance.
Aplicação. Sem linha, não crie.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não duplique tarifa ligada.
Não entregue como falta o que a regra manda baixar ou ligar.
