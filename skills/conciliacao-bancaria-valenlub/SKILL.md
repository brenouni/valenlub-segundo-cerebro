---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Sempre entrega o ponto. Nunca termina mudo."
version: "1.18.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Nenhum outro arquivo decide baixa.

## Sempre entrega

Nunca termine mudo. Se o tempo estourar, pare de clicar e escreva o ponto antes de qualquer outra coisa.
A cada 5 linhas fechadas, ou se uma leva estourar, escreva:
- o que já ligou
- o que ainda falta
- em que linha parou
Depois siga. Se não der para seguir, pare nessa mensagem. Não suma.
PDF no fim, ou no ponto se a passagem não acabar.

## Fecha na hora

O que a regra fecha, grava na hora. Não devolva. Não espere o Breno insistir.

## Rascunho

Antes de clicar, apague `/home/hermes/.hermes/cache/scratch/query-browser`.
Não sobrescreva script. Aviso de file-mutation não é falha. Não pare.

## Relatório

Gerador: `skills/relatorio-conciliacao/gerar.py`.
Dia aberto: âmbar. Dia fechado: verde.
Linha não ligada não entra como fechada.

## Cartão

Não lance recebimento.
1. Líquido e NSU iguais: ligue.
2. NSU igual, título Aberto no bruto, banco + taxa = título: ajuste para o banco, lance a taxa em 30010004 se não existir, ligue.
3. Título Pago: não edite. Não lance taxa que já existe. Se não ligar, entregue.

## Demais

Lote. Some só os pagamentos. Soma exata: ligue.
Pix. Um do valor, aberto: baixe e ligue. Já pago: só ligue. Vários: nome. Sem título: proponha DNI. Não grave.
Tarifa. Botão Tarifa. 30060001. Já existente: não duplique. Uma por vez. A cada 5, escreva o ponto.
Pagamento e Pix enviado. Título único: baixe e ligue. Nada achado: não lance pessoa.
Aplicação. Sem linha, não crie.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago.
Não termine sem dizer onde parou.
