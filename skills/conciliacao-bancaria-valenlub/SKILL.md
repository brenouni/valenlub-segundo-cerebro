---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Fecha na hora. Releitura antes de entregar. PDF no fim."
version: "1.12.0"
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
Texto antigo de “não baixe” não vale. Texto antigo de “entregue na primeira falha” não vale.

## Fecha na hora. Não pergunta.

A regra já foi decidida. Não peça confirmação. Não pare no meio. Não devolva à Ariadna o que a regra fecha.
O que a regra fecha: baixe, ligue e vá à próxima linha. Na mesma passagem.
Não espere o Breno dizer “resolve o que falta”. Isso já é a passagem.

## Antes de entregar

A passagem não acaba na primeira tentativa.
Depois da última linha, não entregue. Não gere o PDF ainda.
Releia só o que ficou em falta.
Painel que não carregou: abra de novo. Uma vez. Depois busque o título pelo valor.
Se a regra fecha nessa releitura, feche. Não peça.
Só entregue o que a releitura também não fechou.
Não diga “lançar DNI” se você não abriu o painel e não buscou o título pelo valor.

## Relatório

Não monte o PDF na mão. Carregue `relatorio-conciliacao` e rode o `gerar.py`.
Só depois da releitura. Não espere pedido.
Dia aberto: selo âmbar. Sem `/new`.
Dia fechado: selo verde. Escreva “Dia fechado. Mande /new.”
Dia fechado = Conciliado, Falta 0, Ajuste 0, tabela do resto vazia.

## Uma passagem

1. Sem extrato do dia: fim. Sem PDF.
2. Recorte só o dia. Entrada = saída prova lista completa. Não é lançamento.
3. Para cada linha: classe pelo memo, depois título, depois a regra. Uma vez.
4. Fechou: ligue e vá à próxima. Não reabra. Sem mensagem no meio.
5. Não fechou: marque a linha e vá à próxima. Não pare o dia.
6. Última linha: releitura do que ficou. Feche o que a regra fecha.
7. Só então o PDF. Âmbar se sobrou. Verde se fechou.

Não peça OFX, conta, subconta nem “posso baixar”.
Não rode `/new` no meio do dia.

## Caixa

Caixa 4 = Bradesco 0237, ag 408, cc 38063-6. Não é filial.
Humano importa OFX e PDF na 1305. O agente não importa.
Baixa sempre no caixa 4, data do extrato. Juros 0. Multa 0.

## Valor igual — eliminação

Dois ou mais do mesmo valor não travam o dia.
Olhe os dois lados. Ligue o par cujo nome é igual ou próximo.
O que sobrar sem nome que distinga: marque `duvida` e siga.
Não chute só pelo valor.

## Classes

Lote. Memo `LIQUIDACAO DE COBRANCA`. Não busque um título do valor da linha. Some só as linhas de pagamento. Soma exata: ligue e siga.

Pix recebido. Memo `PIX RECEBIDO` ou `PIX QR`. Título no receber.
Um do valor, aberto: juros 0, multa 0, baixe, ligue, siga. Não devolva.
Um do valor, já pago: só ligue e siga.
Vários do mesmo valor: eliminação por nome. O par que casa, liga. O que não casa, marque e siga.
Sem título, depois do painel e da busca pelo valor: proponha DNI. Não grave. Marque e siga.
Data no histórico não é a data do pagamento.

Cartão. Memo `CIELO` ou `COMPRA CARTAO`. Não lance recebimento. Não entre no portal. Não importe a 1104.
Abra o CSV. Ignore até `Data de pagamento;`.
1. Título do mesmo valor líquido e do mesmo NSU: ligue e siga.
2. NSU igual e o título está no bruto, ou no total da venda, e a diferença é a taxa da linha do CSV: marque `desdobrar`. Não ligue. A Ariadna desdobra. Depois ligue.
3. Sem NSU e sem título do líquido: marque em falta e siga.
Banco junta. Cielo não. Valor sozinho ausente: some mesmo dia e mesma bandeira.

Tarifa. Memo `TARIFA`. Botão Tarifa da linha. Bradesco, 30060001, caixa 4, data do extrato.
Baixe, ligue e siga. Não lance outra.
0,55 da mesma descrição já existente: não duplique. Painel que não carregou: abra de novo antes de marcar.

Centavo. Só com título único já achado. Ajuste para o valor do banco, juros 0, multa 0, baixe, ligue e siga.

Pagamento. Memo `PAGTO` ou `PAGAMENTO`.
Título único no pagar, aberto: baixe, ligue e siga. Não devolva.
Vários do mesmo valor: eliminação por nome. O que não casa: marque. Não lance.

Pix enviado. Memo `PIX ENVIADO`.
Procure no pagar pelo nome. Igual ou próximo, aberto: baixe, ligue e siga.
Nada encontrado: marque. Não lance a pessoa.

Aplicação. Memo `APLIC`. Conta 30060005. Sem linha, não crie. Marque e siga.
Resgate. Memo `RESG`. Conta 30060006. Sem relatório prévio. Não peça.
Rentabilidade. Memo `RENTAB`. Marque `duvida` e siga.

Outro: marque `duvida` e siga.

## Não fazer

Não estorna. Não entra no banco. Não grava DNI. Não fala com cliente. Não pede senha.
Não pare para perguntar. Não espere o Breno insistir.
Não desdobre sozinho. Não importe o arquivo da Cielo.

## Saída

Dia aberto: PDF no fim, depois da releitura. Selo âmbar. Uma ação por linha. Sem `/new`.
Linha `desdobrar`: título, valor do título, valor do banco, taxa.
Dia fechado: PDF. Selo verde. Escreva “Dia fechado. Mande /new.”
