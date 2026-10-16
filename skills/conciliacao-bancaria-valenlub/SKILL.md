---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Cartão: banco + taxa = título, fecha. Não devolve."
version: "1.16.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Nenhum outro arquivo decide baixa.
Texto antigo de “desdobrar e devolver” não vale. Texto antigo de “não desdobre sozinho” não vale quando a conta fecha.

## Fecha na hora. Não pergunta.

O que a regra fecha, grava na hora. Não devolva à Ariadna.
Não espere o Breno insistir.

## Rascunho

Antes de clicar, apague `/home/hermes/.hermes/cache/scratch/query-browser`.
Não sobrescreva script. Se existir, use outro nome.
Aviso de file-mutation não é falha. Não pare.

## Relatório

Gerador: `skills/relatorio-conciliacao/gerar.py`. Não monte na mão.
Só depois da releitura. Dia aberto: âmbar. Dia fechado: verde.

## Antes de entregar

Releia o que ficou. Painel que não carregou: abra de novo. Busque pelo valor.
Se a regra fecha, feche. Só entregue o que a releitura não fechou.

## Cartão

Não lance recebimento. Não entre no portal. Não importe a 1104.
Abra o CSV. Ignore até `Data de pagamento;`.

1. Título no líquido e NSU igual: ligue.
2. Filtro vazio e um título no líquido: abra e procure o NSU. Achou no líquido: ligue.
3. NSU igual e título no bruto, ou no total da venda. Banco + taxa do CSV = valor do título, no centavo: feche.
   Ajuste o título para o valor do banco. Juros 0. Multa 0.
   Lance a taxa em 30010004, caixa 4, data do extrato.
   Ligue a linha do banco. Não devolva.
4. A conta não fecha no centavo: marque `desdobrar` e entregue. Aí a Ariadna faz.
5. Sem NSU e sem título do líquido: marque.

Exemplo do 07/10: banco 11,93 + taxa 0,09 = título 89490 de 12,02. NSU 706662. Fecha. Não devolve.

## Demais classes

Lote. Some só os pagamentos. Soma exata: ligue.
Pix recebido. Um do valor, aberto: juros 0, multa 0, baixe, ligue. Já pago: só ligue. Vários: eliminação por nome. Sem título: proponha DNI. Não grave.
Tarifa. Botão Tarifa. 30060001, caixa 4, data do extrato. Baixe e ligue.
Pagamento e Pix enviado. Título único aberto: baixe e ligue. Nada achado: não lance pessoa.
Aplicação. Sem linha, não crie.
Resgate. Sem relatório prévio. Não peça.

## Não fazer

Não estorna. Não grava DNI. Não importe a Cielo.
Não devolva cartão quando banco + taxa = título.
