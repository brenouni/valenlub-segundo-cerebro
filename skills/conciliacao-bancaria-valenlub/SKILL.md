---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Fonte única. Fecha o par único. Não reabre. Não pergunta o que esta skill decide."
version: "1.3.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
    related_skills: [conciliar-sinal]
---

# Conciliação — ValenLub, caixa 4

Fonte única desta rotina. `conciliacao.md`, `conciliacao-mapa.md` e `conciliar-sinal` não decidem baixa.
Empresa: Valen Lubrificantes. Não misturar com as outras 7.

## Modo

Sem a frase “só olhar”, é rotina: fecha, liga, segue.
Com “só olhar”: lista. Não grava.

## Uma passagem

1. Dia já Conciliado, Falta 0 e Ajuste 0: pare. Diga “dia fechado”.
2. Sem extrato do dia: pare. `aguardando_extrato`.
3. Recorte só o dia pedido. Entrada igual à saída prova lista completa. Não é lançamento.
4. Classifique cada linha pelo memo, antes de buscar título.
5. Aplique a regra da classe. Uma vez.
6. Linha ligada: não reabra. Não chame Jev.
7. Só o resto vai para a tabela. Uma ação por linha.
8. PDF uma vez, no fim, se houve extrato. Não reemita.

Não peça OFX, conta, subconta nem “posso baixar”. Já está decidido.

## Caixa

Caixa 4 = Bradesco 0237, ag 408, cc 38063-6. Não é filial.
Filiais: 1 MATRIZ, 2 DEPOSITO.
Humano importa OFX e PDF na 1305. O agente não importa.

## Classes

`LIQUIDACAO DE COBRANCA`: lote. Não busque um título do valor da linha. Some só as linhas de pagamento. Soma exata: ligue.
`PIX RECEBIDO` ou `PIX QR`: título no receber. Um do valor: aberto baixa no caixa 4, data do extrato, juros e multa zerados, e liga. Já pago: só liga. Dois do mesmo valor: pare. Sem título, depois de abrir o painel: proponha DNI. Não grave.
`CIELO` ou `COMPRA CARTAO`: não lance recebimento. Ligue só com título do mesmo valor e NSU. Sem isso, fica aberta.
`TARIFA`: botão da linha. Bradesco, 30060001, caixa 4, data do extrato. Baixe e ligue. Não lance outra. Se já existe 0,55 da mesma descrição, não duplique.
`APLIC`: 30060005. `RESG`: 30060006. No mesmo dia, um dos dois. Sem linha, não crie.
`RENTAB`: não é resgate. Conta aberta. `duvida`.
`PAGTO` ou `PAGAMENTO`: título único no pagar. Aberto: baixe e ligue. Não achou: não lance.
`PIX ENVIADO`: procure no pagar pelo nome. Nada encontrado: não lance a pessoa.
Outro: `duvida`.

## Match

Valor exato, data de pagamento, uma contraparte.
Nome ajuda. Não substitui o valor.
Data no histórico do Pix não é a data do pagamento.
Antes de dizer que não há título, abra o painel uma vez.

Centavo: só com título único já achado. Ajuste para o valor do banco, baixe e ligue. Sem título único: `nao_bate`.

Cielo: ignore o bruto até `Data de pagamento;`. `Data de pagamento:` é filtro. Sem número de linha.
Banco junta. Cielo não. Valor sozinho ausente: some mesmo dia e mesma bandeira.
Não entre no portal. Não importe a 1104.

Não some todo o contas a pagar. O filtro traz linha fora do caixa 4.
Resgate e rendimento não têm relatório prévio. Não peça.

## Para

Sem extrato. Dois títulos no mesmo valor. Sem título único. Sem NSU no cartão. Ordem “só olhar”.
Não estorna. Não entra no banco. Não grava DNI. Não fala com cliente. Não pede senha. Não grava token.

## Jev

Só na linha que esta skill não fechou.
Não chame em lote somado, tarifa da linha, par único, dia fechado ou “só olhar”.
Uma chamada. Descrição, valor, data. Sem nome, documento ou extrato.
Confidence abaixo de 0,6: `duvida`, pare.
Jev não escolhe entre dois títulos e não grava.

## Saída

Dia. Caixa 4. Totais do recorte.
Tabela só do resto: data, valor, classe, uma ação.
Sem nome. Sem documento. Sem extrato inteiro.
Rodapé: o que foi gravado. Linha ligada não é “nada foi lançado”.
Não diga “pode baixar”.
