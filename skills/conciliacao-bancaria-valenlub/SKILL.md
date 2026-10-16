---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Título pago não se edita. Taxa já lançada não se repete."
version: "1.17.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Nenhum outro arquivo decide baixa.
Texto antigo de “ajuste o título pago” não vale. A tela só edita título Aberto.

## Fecha na hora. Não pergunta.

O que a regra fecha, grava na hora. Não devolva à Ariadna.
Não espere o Breno insistir.

## Rascunho

Antes de clicar, apague `/home/hermes/.hermes/cache/scratch/query-browser`.
Não sobrescreva script. Aviso de file-mutation não é falha. Não pare.

## Relatório

Gerador: `skills/relatorio-conciliacao/gerar.py`. Não monte na mão.
Só depois da releitura. Dia aberto: âmbar. Dia fechado: verde.
O PDF mostra o que a tela confirmou. Linha não ligada não entra como fechada.

## Antes de entregar

Releia o que ficou. Se a regra fecha, feche. Só entregue o que a releitura não fechou.

## Cartão

Não lance recebimento. Não entre no portal. Não importe a 1104.
Abra o CSV. Ignore até `Data de pagamento;`.

1. Título no líquido e NSU igual: ligue.
2. Filtro vazio e um título no líquido: abra e procure o NSU. Achou no líquido: ligue.
3. NSU igual, título no bruto, banco + taxa = título, e o título está Aberto: ajuste para o valor do banco, juros 0, multa 0. Lance a taxa em 30010004 se ainda não existir. Ligue. Não devolva.
4. O título está Pago: não edite. A tela recusa. Não lance outra taxa se a de 30010004 desse valor e desse dia já existe. Tente ligar a linha do banco ao título. Se a tela não ligar, marque e entregue: título, status Pago, valor do título, valor do banco, taxa. A Ariadna desdobra.
5. A conta não fecha no centavo: marque e entregue.
6. Sem NSU e sem título do líquido: marque.

Exemplo do 07/10: título 89490 Pago em 12,02. Banco 11,93. Taxa 0,09 já lançada, título 38675. Não edite. Não lance outra taxa. Se não ligar, entregue.

## Demais classes

Lote. Some só os pagamentos. Soma exata: ligue.
Pix recebido. Um do valor, aberto: juros 0, multa 0, baixe, ligue. Já pago: só ligue. Vários: eliminação por nome. Sem título: proponha DNI. Não grave.
Tarifa. Botão Tarifa. 30060001, caixa 4, data do extrato. Baixe e ligue. Já existente: não duplique.
Pagamento e Pix enviado. Título único aberto: baixe e ligue. Nada achado: não lance pessoa.
Aplicação. Sem linha, não crie.
Resgate. Sem relatório prévio. Não peça.

## Não fazer

Não estorna. Não grava DNI. Não importe a Cielo.
Não edite título Pago. Não lance taxa que já existe.
Não diga que o cartão fechou se a linha do banco não ligou.
