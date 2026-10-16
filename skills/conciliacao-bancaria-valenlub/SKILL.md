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

Fonte única. Nenhum outro arquivo decide baixa.
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
2. Recorte só o dia. Entrada = saída prova lista completa.
3. Para cada linha: classe, título, regra. Uma vez.
4. Fechou: ligue e vá à próxima. Sem mensagem no meio.
5. Não fechou: marque e vá à próxima. Não pare o dia.
6. Última linha: releitura do que ficou. Feche o que a regra fecha.
7. Só então o PDF. Âmbar se sobrou. Verde se fechou.

## Classes

Lote. Memo `LIQUIDACAO DE COBRANCA`. Some só os pagamentos. Soma exata: ligue e siga.

Pix recebido. Um do valor, aberto: juros 0, multa 0, baixe, ligue, siga. Não devolva.
Um do valor, já pago: só ligue.
Vários do mesmo valor: eliminação por nome.
Sem título, depois do painel e da busca pelo valor: proponha DNI. Não grave.

Cartão. Não lance recebimento. Não entre no portal.
1. Líquido e NSU iguais: ligue.
2. NSU igual, título no bruto ou no total, diferença = taxa do CSV: `desdobrar`. Não ligue. A Ariadna desdobra.
3. Sem NSU e sem título do líquido: marque.

Tarifa. Botão Tarifa. Bradesco, 30060001, caixa 4, data do extrato. Baixe e ligue. Não lance outra.
0,55 já existente: não duplique. Painel que não carregou: abra de novo antes de marcar.

Pagamento e Pix enviado. Título único aberto: baixe e ligue. Valor repetido: eliminação por nome. Nada achado: não lance pessoa.

Aplicação. Sem linha, não crie. Marque.
Resgate. Sem relatório prévio. Não peça.

## Não fazer

Não estorna. Não entra no banco. Não grava DNI. Não desdobra sozinho. Não importe a Cielo.
Não pare para perguntar. Não espere o Breno insistir.
