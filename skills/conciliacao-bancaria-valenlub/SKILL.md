---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Fonte única. Fecha linha a linha. O dia só para sem extrato ou já fechado."
version: "1.6.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
    related_skills: [conciliar-sinal]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Nenhum outro arquivo decide baixa.
Empresa: Valen Lubrificantes. Não misturar com as outras 7.
Texto antigo de “não baixe” não vale. Par autorizado: baixa, liga, segue a próxima linha.

## O que “para” significa

Para é da linha. Não é do dia.
Esgotou o que o robô pode fazer naquele item: marque e vá para a próxima.
Só duas coisas param o dia: sem extrato, ou dia já Conciliado com Falta 0 e Ajuste 0.
O resto segue até a última linha. Depois, o relatório.

## Modo

Sem “só olhar”: rotina. Fecha e liga.
Com “só olhar”: lista. Não grava.

## Uma passagem

1. Dia Conciliado, Falta 0 e Ajuste 0: fim. “Dia fechado.”
2. Sem extrato do dia: fim. `aguardando_extrato`.
3. Recorte só o dia. Entrada = saída prova lista completa. Não é lançamento.
4. Para cada linha: classe pelo memo, depois título, depois a regra. Uma vez.
5. Fechou: ligue e vá à próxima. Não reabra. Sem Jev.
6. Não fechou: marque a linha e vá à próxima. Não pare o dia.
7. Última linha: tabela do resto. Uma ação por linha.
8. PDF uma vez, no fim. Não reemita.

Não peça OFX, conta, subconta nem “posso baixar”.

## Caixa

Caixa 4 = Bradesco 0237, ag 408, cc 38063-6. Não é filial.
Filiais: 1 MATRIZ, 2 DEPOSITO.
Humano importa OFX e PDF na 1305. O agente não importa.
Baixa sempre no caixa 4, data do extrato.

## Valor igual — eliminação

Dois ou mais do mesmo valor não travam o dia.
Olhe os dois lados. Ligue o par cujo nome é igual ou próximo.
Nome próximo: mesma pessoa, mesmo primeiro nome, ou a sigla do banco cabe no nome do título.
Cada linha do extrato liga um título. Não reuse.
O que sobrar sem nome que distinga: marque a linha `duvida` e siga.
Não chute só pelo valor.

## Classes

Lote. Memo `LIQUIDACAO DE COBRANCA`. Não busque um título do valor da linha. Some só as linhas de pagamento. Soma exata: ligue e siga. Não mande à Ariadna só porque a linha não foi aberta.

Pix recebido. Memo `PIX RECEBIDO` ou `PIX QR`. Título no receber.
Um do valor, aberto: juros 0, multa 0, baixe, ligue, siga.
Um do valor, já pago: só ligue e siga.
Vários do mesmo valor: eliminação por nome. O par que casa, liga. O que não casa, marque e siga.
Sem título, depois de abrir o painel uma vez: proponha DNI. Não grave. Marque e siga.
Data no histórico não é a data do pagamento.

Cartão. Memo `CIELO` ou `COMPRA CARTAO`. Não lance recebimento. Não entre no portal. Não importe a 1104.
Ligue só com título do mesmo valor e NSU. Sem isso, marque em falta e siga.
CSV bruto: ignore até `Data de pagamento;`. `Data de pagamento:` é filtro.
Banco junta. Cielo não. Valor sozinho ausente: some mesmo dia e mesma bandeira.

Tarifa. Memo `TARIFA`. Botão Tarifa da linha. Bradesco, 30060001, caixa 4, data do extrato.
Baixe, ligue e siga. Não lance outra. Não devolva.
0,55 da mesma descrição já existente: não duplique. Marque e siga.

Centavo. Só com título único já achado, ou com par já separado por nome. Ajuste para o valor do banco, juros 0, multa 0, baixe, ligue e siga.
Sem título que distinga: marque `nao_bate` e siga.

Pagamento. Memo `PAGTO` ou `PAGAMENTO`. Não é tarifa e não é receita.
Título único no pagar, aberto: baixe, ligue e siga.
Vários do mesmo valor: eliminação por nome. O que não casa: marque e siga. Não lance.
Não some todo o contas a pagar. O filtro traz linha fora do caixa 4.

Pix enviado. Memo `PIX ENVIADO`. Não nasce como despesa do banco.
Procure no pagar pelo nome. Igual ou próximo: ligue e siga. Nada encontrado: marque e siga. Não lance a pessoa.

Aplicação. Memo `APLIC`. Conta 30060005, não a de taxa. Sem linha, não crie. Marque e siga.
Resgate. Memo `RESG`. Conta 30060006. Sem relatório prévio. Não peça.
No mesmo dia, aplicação ou resgate, não os dois.

Rentabilidade. Memo `RENTAB`. Não é resgate. Conta aberta. Marque `duvida` e siga.

Outro: marque `duvida` e siga.

## Não fazer, em nenhuma linha

Não estorna. Não entra no banco. Não grava DNI. Não fala com cliente. Não pede senha. Não grava token.

## Jev

Só na linha que esta skill não fechou, e só depois de esgotar a regra.
Não chame em lote somado, tarifa, par já ligado, dia fechado ou “só olhar”.
Uma chamada. Descrição, valor, data. Sem nome, documento ou extrato.
Confidence abaixo de 0,6: marque `duvida` e siga.

## Saída — só no fim

Dia. Caixa 4. Totais do recorte.
Tabela só do que a linha não fechou: data, valor, classe, uma ação.
Sem nome. Sem documento. Sem extrato inteiro.
Rodapé: o que foi gravado. Linha ligada não é “nada foi lançado”.
Não diga “pode baixar”.
