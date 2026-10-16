---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Fecha na hora. NSU no bruto: desdobrar. Não sobrescreve rascunho."
version: "1.15.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Nenhum outro arquivo decide baixa. `leitura-query` não decide. `relatorio-conciliacao` não decide.
Empresa: Valen Lubrificantes. Não misturar com as outras 7.
Texto antigo de “não baixe” não vale. Texto antigo de “NSU no bruto = falta” não vale.

## Fecha na hora. Não pergunta.

A regra já foi decidida. Não peça confirmação. Não pare no meio. Não devolva à Ariadna o que a regra fecha.
O que a regra fecha: baixe, ligue e vá à próxima linha. Na mesma passagem.
Não espere o Breno dizer “resolve o que falta”. Isso já é a passagem.

## Rascunho

Antes de clicar na tela, apague `/home/hermes/.hermes/cache/scratch/query-browser`.
Não sobrescreva script que já existe. Se existir, use outro nome.
O aviso de file-mutation não é falha da conciliação. Não pare por causa dele.

## Relatório

O gerador está no cérebro: `skills/relatorio-conciliacao/gerar.py`.
Não procure em outra pasta. Não monte o PDF na mão.
Só depois da releitura. Não espere pedido.
Dia aberto: selo âmbar. Sem `/new`.
Dia fechado: selo verde. Escreva “Dia fechado. Mande /new.”

## Antes de entregar

A passagem não acaba na primeira tentativa.
Depois da última linha, não entregue. Não gere o PDF ainda.
Releia só o que ficou em falta.
Painel que não carregou: abra de novo. Uma vez. Depois busque o título pelo valor.
Se a regra fecha nessa releitura, feche. Não peça.
Só entregue o que a releitura também não fechou.

## Uma passagem

1. Apague o rascunho.
2. Sem extrato do dia: fim. Sem PDF.
3. Recorte só o dia. Entrada = saída prova lista completa.
4. Para cada linha: classe, título, regra.
5. Fechou: ligue e vá à próxima.
6. Não fechou: marque e vá à próxima. Não pare o dia.
7. Última linha: releitura. Feche o que a regra fecha.
8. Só então o PDF. Âmbar se sobrou. Verde se fechou.

## Classes

Lote. Some só os pagamentos. Soma exata: ligue.

Pix recebido. Um do valor, aberto: juros 0, multa 0, baixe, ligue. Já pago: só ligue.
Vários do mesmo valor: eliminação por nome.
Sem título, depois do painel e da busca: proponha DNI. Não grave.

Cartão. Não lance recebimento.
1. Líquido e NSU iguais: ligue.
2. Filtro vazio e um título no líquido: abra e procure o NSU. Achou no líquido: ligue.
3. NSU achado no título do bruto, ou do total, e a diferença é a taxa: `desdobrar`. Não é falta. Não ligue. Entregue título, valor do título, valor do banco e taxa.
4. Sem NSU e sem título do líquido: marque.
Exemplo do 07/10: 11,93. NSU 706662 no título 89490, bruto 12,02. Taxa 0,09. É desdobrar.

Tarifa. Botão Tarifa. Bradesco, 30060001, caixa 4, data do extrato. Baixe e ligue. Não lance outra.

Pagamento e Pix enviado. Título único aberto: baixe e ligue. Valor repetido: eliminação por nome. Nada achado: não lance pessoa.

Aplicação. Sem linha, não crie.
Resgate. Sem relatório prévio. Não peça.

## Não fazer

Não estorna. Não grava DNI. Não desdobra sozinho. Não importe a Cielo.
Não marque falta quando o NSU está no bruto e a diferença é a taxa.
Não pare por causa do aviso de file-mutation.
