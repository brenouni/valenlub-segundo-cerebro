---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4 ValenLub. Fecha o par único autorizado. Não reabre. Não pergunta o que esta skill já decide."
version: "1.2.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
    related_skills: [conciliar-sinal]
---

# Conciliação — ValenLub, caixa 4

Empresa: Valen Lubrificantes. Não misturar com as outras 7.
Esta skill vence `conciliacao-mapa.md` e qualquer frase antiga de “não baixe”.
Não substitui `conciliar-sinal`. Jev só no bloco Jev.

## Leia primeiro

Dia já Conciliado, Falta 0 e Ajuste 0: pare. Diga “dia fechado”. Não releia. Não pergunte.
Linha já ligada neste turno: não reabra.
Não peça OFX, conta do caixa, subconta de tarifa, nem “posso baixar”. Já está decidido.

Dois modos. Sem a frase “só olhar”, vale a rotina.

Rotina: o que a regra fecha, grave uma vez e ligue. PDF na mesma resposta, depois da releitura. Não devolva à Ariadna.
Só olhar: cruza e lista. Não grave.

## Parada errada — não faça

Par único e regra já autorizada. Aí baixa, liga e segue. Não devolve. Não pede de novo.
Foi erro: tarifa da linha, oito tarifas já autorizadas, centavo de título único, lote com soma exata, Pix aberto com um título só.

## Parada correta — pare aqui

Sem extrato. Dois títulos no mesmo valor. Sem título único. Sem NSU no cartão. Ordem “só olhar”.
Pix sem título: proponha DNI. Não grave. Não marque receita.
Não achei título no pagar: não lance a pessoa.

## Caixa

Caixa 4 = Bradesco 0237, ag 408, cc 38063-6. Não é filial.
Filiais: 1 MATRIZ, 2 DEPOSITO.
Sem extrato, pare. Veredito `aguardando_extrato`.
OFX de vários dias: só o dia pedido.
Entrada igual à saída prova lista completa. Não é um lançamento.
O humano importa na 1305. O agente não importa.

## Ordem

1. 1305, humano.
2. Receita: boleto é lote. Pix é título. Cielo 1104, operadora 22, antes da linha de cartão.
3. 1200: tarifa, e aplicação ou resgate. Não os dois no mesmo dia.

## Regras — terminal

Match = valor exato + data de pagamento + uma contraparte.

Pix recebido. Título no contas a receber.
Um título do valor: fecha. Aberto: baixe no caixa 4, data do extrato, juros e multa zerados, e ligue. Já pago: só ligue.
Antes de dizer que não há título, abra o painel da linha.
Dois do mesmo valor: não fecha. Nome ajuda. Não substitui o valor.
Data no histórico do Pix não é a data do pagamento.

Boleto. `LIQUIDACAO DE COBRANCA` é lote. Não procure um título do valor da linha.
Some só as linhas de pagamento. Soma exata: ligue. Não mande o lote à Ariadna só porque a linha não foi aberta.

Cielo. Ignore o bruto até `Data de pagamento;`. `Data de pagamento:` é filtro.
Sem comprovante, não feche. Sem NSU, não feche.
Não entre no portal. Não importe a baixa de cartão. Não lance recebimento de cartão.
Banco junta. Cielo não. Sem título no valor da linha, no centavo, a linha fica aberta.
Ligue só se o título for o mesmo valor.
36,01 do dia 25 foi Pix. 36,08 foi Cielo. Não reuse.

Centavo. Título único já autorizado: ajuste para o valor do banco, baixe no caixa 4 na data do extrato e ligue. Não recuse. Não peça de novo.
Sem título único: `nao_bate`. Não chute.

Tarifa. Botão Tarifa da linha já liga. Bradesco, taxas, caixa 4, data do extrato.
Baixe e ligue. Não lance outra.
Não lance outra de 0,55 se já existe.
Conta 30060001. As oito já autorizadas: baixe e concilie. Não devolva.

Pagamento e transferência. Não é tarifa e não é receita.
Procure título único no pagar. Aberto: baixe no caixa 4, data do extrato, e ligue.
Não achou: não lance.

Pix enviado. Não nasce como despesa do Bradesco.
Procure no pagar pelo nome. Nada encontrado não autoriza lançar a pessoa.

Aplicação. Nasce no pagar, conta 30060005, não na de taxa.
Resgate: 30060006. No mesmo dia, aplicação ou resgate, não os dois.
Sem linha de aplicação, não crie uma.
Rentabilidade (`RENTAB.INVEST`) não é resgate. Conta ainda aberta: `duvida`.
Resgate e rendimento não têm relatório prévio. Não peça antes.

Não some todo o contas a pagar. O filtro traz linha fora do caixa 4.

## Jev — só o resto

Não chame se: sem extrato, regra já fechou, dois títulos iguais, falta NSU, lote já somado, dia fechado, ordem “só olhar”.
Uma chamada por linha que sobrou. Só descrição, valor e data. Sem nome, documento ou extrato.
Confidence abaixo de 0,6: `duvida`, fila da Ariadna, pare.
Jev não escolhe entre dois títulos. Não grava DNI. Não importa 1104.
Chave só para https://api.typesafe.ai. Nunca exibir.

## Não fazer

Não é fechamento mensal.
Não cria registro a partir do extrato.
Não trata cartão contra venda bruta.
Crédito Cielo cerca de 30 dias. Débito no dia seguinte. Venda de hoje não é “sumiu”.
Não inventa a planilha Fluxo de Caixa LUB.
Não usa `/vendas/reconciliacao` nem `/filiais-movimentacoes`.
Não peça senha. Não grave token.

## Saída — uma vez

Dia. Caixa 4. Totais do recorte.
Tabela só do que a regra não fechou: data, valor, natureza, uma ação.
Sem nome. Sem documento. Sem extrato inteiro.
Se fechou: “dia fechado”. Tabela vazia.
Rodapé: o que foi gravado. Linha ligada não vira “nada foi lançado”.
Não diga “pode baixar”.
PDF no fim, depois da releitura, no mesmo turno. Não reemita.
