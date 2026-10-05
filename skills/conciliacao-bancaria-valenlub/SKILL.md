---
name: conciliacao-bancaria-valenlub
description: Use when conciliar caixa 4, Cielo ou tarifa. Sinaliza.
version: 1.0.0
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Sinal]
    related_skills: [conciliar-sinal]
---

# Conciliação bancária — ValenLub, caixa 4

Empresa: Valen Lubrificantes. Não misturar com as outras 7 do Grupo Valen.
Não substitui `conciliar-sinal`. Não apagar a outra.
Papel: cruzar arquivo e listar. Ariadna aprova o irreversível.
Fonte: `memory/projects/conciliacao-mapa.md` e `memory/projects/conciliacao.md`.
Este uso é arquivo. Não chamar API. Não pedir senha. Não gravar token.

## Quando usar

- Fechar o caixa 4 de um dia útil anterior. Segunda olha sexta.
- Bater o OFX com o relatório de conciliação do Query, os dois já em arquivo.
- Tratar o CSV Cielo antes da 1104.
- Conferir tarifa e aplicação da 1200 no arquivo.

Não usar para cobrança, inadimplência, Relator 08h, Tássia, DAS, DRE, projeção de caixa, estoque, nem para as outras empresas do grupo.

## O que entrega

1. Lista do dia, linha a linha do OFX, com veredito.
2. Pendência com dono Ariadna. Sem “pode baixar”.
3. Três conferências: soma Cielo, lote de boleto, soma 1200.
4. Nada gravado no Query. Nada importado.

Vereditos: `bate` / `nao_bate` / `duvida` / `aguardando_extrato`.

## Caixa

- Caixa 4 é Bradesco. Não é filial. A conta fica em `memory/projects/conciliacao.md`. Não copiar para cá.
- Filiais do Query: 1 MATRIZ, 2 DEPOSITO.
- Sem OFX do dia, para. Veredito `aguardando_extrato`.
- OFX de vários dias: recortar só o D-1. Conferido: o arquivo do 25 trazia outros dias.

## Ordem

1. O humano importa OFX e PDF na 1305, caixa 4. O agente não importa.
2. Receita: boleto é lote. Pix é título. Cielo 1104, operadora 22, antes de cravar a linha de cartão do banco.
3. 1200: tarifa, e aplicação ou resgate.
4. Se o relatório do dia já estiver em arquivo, o total dos dois lados tem que ser o mesmo. Se não estiver, não inventar o total.

## Cruzamento

Match só com valor exato, data de pagamento e uma contraparte.
Dois títulos no mesmo valor bloqueiam. Não escolhe.
Nome do Pix ajuda. Não substitui o valor.
A data no histórico do Pix não é a data do pagamento.
Não chuta saldo. Não estorna. Não fala com cliente.

Pix sem título no valor: `duvida`. Pode ser DNI. Propõe. Não grava. Não marca como receita.

Boleto: a linha `LIQUIDACAO DE COBRANCA` é lote. Não procurar um título com aquele valor.

Cielo não é tipo de cobrança. No título, CCR ou DEB. Na 1104, operadora 22.
CSV bruto: ignorar até a linha que começa com `Data de pagamento;`.
`Data de pagamento:` é filtro. Sem número de linha.
Tratado = cabeçalho + lançamentos. Separador ponto e vírgula. Sem NSU não fecha.
Banco agrupa. Cielo não. Se o valor do CSV não existir sozinho no OFX, somar mesmo dia e mesma bandeira.
Centavo diferente não fecha.
Não entra no portal. Não importa a 1104.
No dia 25, 36,01 foi Pix e 36,08 foi Cielo. Não são a mesma linha. Não usar esses números como meta de outro dia.

1200: tarifa `30060001`, aplicação `30060005`, resgate `30060006`.
No mesmo dia, aplicação ou resgate, não os dois.
Competência = dia do extrato. Lançamento no sistema pode ser o dia da rotina.
Tarifas iguais da mesma descrição podem ter virado um título só. Sinaliza. Não junta sozinho.
Não somar todo o contas a pagar do dia. O filtro traz linha que não é do caixa 4.
Valor que não casa com um título da subconta certa: `nao_bate` ou `duvida`. Não inventar padrão de tarifa.

## Jev

Mesmo portão da `conciliar-sinal`. Não criar outra política.
O Jev decide. O Hermes escreve. O Jev não baixa, não grava DNI, não importa 1104, não lança 1200.

Chamar o Jev só depois do match por regra, e só na linha que não fechou em `bate`.
Uma chamada jev-latest por linha, com descrição, valor e data. Nada de nome de cliente, documento ou extrato inteiro.
Perguntas, nesta ordem:
- tipo (choice): pix, boleto, cartao, tarifa, aplicacao, resgate, dni, outro
- veredito (choice): duvida, nao_bate
- merece humano hoje (noul)
- risco de baixa errada (noul)

Não chamar se o extrato não chegou, se a regra já deu bate, se há dois títulos no mesmo valor, se falta NSU no cartão, ou se o pedido for baixar, estornar ou gravar.
Confidence abaixo de 0,6 em qualquer pergunta: veredito = duvida, parar, fila da Ariadna.
A chave só vai para https://api.typesafe.ai. Nunca exibir. Dado privado real só com aprovação do Breno.

## Não fazer

Não é fechamento mensal. Não cria registro a partir do extrato.
Não trata cartão contra venda bruta. Cruza líquido e data de pagamento.
Crédito Cielo cai cerca de 30 dias depois da venda. Débito no dia seguinte. Não marcar venda de hoje como sumida.
Não inventa a planilha Fluxo de Caixa LUB. Ela ainda não foi vista.
Não chamar API. As rotas ficam em `memory/projects/conciliacao-api.md`.
Não usar `/vendas/reconciliacao` nem `/filiais-movimentacoes`.
Bloqueado: POST, PATCH, DELETE, baixa, estorno, importar 1104, gravar DNI, portal e banco.

## Saída

Dia. Caixa 4. Totais do OFX do recorte.
O que não bate: data, valor, natureza, o que falta, dono Ariadna.
Sem nome de cliente. Sem documento. Sem extrato inteiro.
Frase final: não baixei, não importei, não gravei DNI.

## Exemplo

Números inventados.

OFX: Pix 1.200,00 e tarifa 1,65.
Um título de 1.200,00, mesma data de pagamento, um só. Veredito: `bate`. Jev não entra.
Tarifa 1,65 sem título na `30060001`. Veredito: `nao_bate`. Jev só nessa linha, e só com aprovação do Breno para dado privado. Senão, fila da Ariadna.
Dois títulos de 1.200,00. Bloqueia. `duvida`. Jev não escolhe.
