---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Fonte única. Executa o par único. Não reabre. Não pergunta o que esta skill decide."
version: "1.4.0"
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
Texto antigo de “não baixe” não vale. Par único autorizado: baixa, liga, segue. Não devolva.

## Modo

Sem “só olhar”: rotina. Fecha e liga.
Com “só olhar”: lista. Não grava.

## Uma passagem

1. Dia Conciliado, Falta 0 e Ajuste 0: pare. “Dia fechado.”
2. Sem extrato do dia: pare. `aguardando_extrato`.
3. Recorte só o dia. Entrada = saída prova lista completa. Não é lançamento.
4. Classe pelo memo. Depois busca título.
5. Regra da classe, uma vez.
6. Linha ligada: não reabra. Sem Jev.
7. Resto na tabela. Uma ação.
8. PDF uma vez, no fim. Não reemita.

Não peça OFX, conta, subconta nem “posso baixar”.

## Caixa

Caixa 4 = Bradesco 0237, ag 408, cc 38063-6. Não é filial.
Filiais: 1 MATRIZ, 2 DEPOSITO.
Humano importa OFX e PDF na 1305. O agente não importa.
Baixa sempre no caixa 4, data do extrato.

## Classes

Lote. Memo `LIQUIDACAO DE COBRANCA`. Não busque um título do valor da linha. Some só as linhas de pagamento. Soma exata: ligue. Não mande à Ariadna só porque a linha não foi aberta.

Pix recebido. Memo `PIX RECEBIDO` ou `PIX QR`. Título no receber.
Um do valor, aberto: juros 0, multa 0, baixe, ligue.
Um do valor, já pago: só ligue.
Dois do mesmo valor: pare. Nome ajuda. Não substitui o valor.
Sem título, depois de abrir o painel uma vez: proponha DNI. Não grave. Não marque receita.
Data no histórico não é a data do pagamento.

Cartão. Memo `CIELO` ou `COMPRA CARTAO`. Não lance recebimento. Não entre no portal. Não importe a 1104.
Ligue só com título do mesmo valor e NSU. Sem isso, fica em falta.
CSV bruto: ignore até `Data de pagamento;`. `Data de pagamento:` é filtro.
Banco junta. Cielo não. Valor sozinho ausente: some mesmo dia e mesma bandeira.

Tarifa. Memo `TARIFA`. Botão Tarifa da linha. Bradesco, 30060001, caixa 4, data do extrato.
Baixe e ligue. Não lance outra. Não devolva.
0,55 da mesma descrição já existente: não duplique.

Centavo. Só com título único já achado. Ajuste para o valor do banco, juros 0, multa 0, baixe e ligue. Não peça de novo.
Sem título único: `nao_bate`.

Pagamento. Memo `PAGTO` ou `PAGAMENTO`. Não é tarifa e não é receita.
Título único no pagar, aberto: baixe e ligue. Não achou: não lance.
Não some todo o contas a pagar. O filtro traz linha fora do caixa 4.

Pix enviado. Memo `PIX ENVIADO`. Não nasce como despesa do banco.
Procure no pagar pelo nome. Nada encontrado: não lance a pessoa.

Aplicação. Memo `APLIC`. Conta 30060005, não a de taxa. Sem linha, não crie.
Resgate. Memo `RESG`. Conta 30060006. Sem relatório prévio. Não peça.
No mesmo dia, aplicação ou resgate, não os dois.

Rentabilidade. Memo `RENTAB`. Não é resgate. Conta aberta. `duvida`.

Outro: `duvida`.

## Para

Sem extrato. Dois títulos no mesmo valor. Sem título único. Sem NSU no cartão. “Só olhar”.
Não estorna. Não entra no banco. Não grava DNI. Não fala com cliente. Não pede senha. Não grava token.

## Jev

Só na linha que esta skill não fechou.
Não chame em lote somado, tarifa, par único, dia fechado ou “só olhar”.
Uma chamada. Descrição, valor, data. Sem nome, documento ou extrato.
Confidence abaixo de 0,6: `duvida`, pare.

## Saída

Dia. Caixa 4. Totais do recorte.
Tabela só do resto: data, valor, classe, uma ação.
Sem nome. Sem documento. Sem extrato inteiro.
Rodapé: o que foi gravado. Linha ligada não é “nada foi lançado”.
Não diga “pode baixar”.
