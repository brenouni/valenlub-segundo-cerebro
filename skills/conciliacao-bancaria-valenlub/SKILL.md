---
name: conciliacao-bancaria-valenlub
description: "Conciliação D-1 do caixa 4. Lê pela API. Tela só para baixar e ligar. Ponto aos 15 min."
version: "1.19.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Nenhum outro arquivo decide baixa.

## Tempo

Aos 15 minutos, pare de clicar e escreva o ponto. Não passe de meia hora mudo.
A cada 5 linhas, escreva o que ligou, o que falta e onde parou.
Nunca termine sem essa mensagem.

## Ler pela API. Clicar só para gravar.

Título, valor, status e pessoa vêm da API. Não abra o painel para procurar.
Base: `https://backend.acessoquery.com/api`
Header: `X-Tenant` + Bearer do `POST /login`.
`GET /contas-receber` e `GET /contas-a-pagar`. `dt_baixa_fim` = dia seguinte.
Filiais: 1 MATRIZ, 2 DEPOSITO. Caixa 4 não é filial.
OFX, caixa e Cielo não estão na API. Extrato e CSV continuam em arquivo.
Tela só para baixar, ligar e lançar tarifa ou taxa.
Se a central já está no dia, não reabra. Não volte no dia anterior.

## Fecha na hora

O que a regra fecha, grava na hora. Não devolva. Não espere o Breno insistir.

## Rascunho

Antes de clicar, apague `/home/hermes/.hermes/cache/scratch/query-browser`.
Não sobrescreva script. Aviso de file-mutation não é falha.

## Relatório

Gerador: `skills/relatorio-conciliacao/gerar.py`.
No ponto ou no fim. Dia aberto: âmbar. Dia fechado: verde.

## Cartão

Não lance recebimento.
1. Líquido e NSU iguais: ligue.
2. NSU igual, título Aberto no bruto, banco + taxa = título: ajuste para o banco, taxa em 30010004 se não existir, ligue.
3. Título Pago: não edite. Não lance taxa que já existe. Se não ligar, entregue.

## Demais

Lote. Some só os pagamentos. Soma exata: ligue de uma vez.
Pix. Um do valor, aberto: baixe e ligue. Já pago: só ligue. Vários: nome. Sem título: proponha DNI. Não grave.
Tarifa. Botão Tarifa. 30060001. Já existente: não duplique. A cada 5, ponto.
Pagamento e Pix enviado. Título único: baixe e ligue. Nada achado: não lance pessoa.
Aplicação. Sem linha, não crie.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago.
Não abra a tela para procurar título. Não reabra o dia.
Não termine sem o ponto.
