---
name: conciliar-sinal
description: Cruza título × movimento. Só sinaliza.
---
1. Pegar recorte.
2. Sem extrato → aguardando_extrato.
3. Veredito bate/duvida/nao_bate. Dúvida → Ariadna.

## Jev
O Jev decide. O Hermes escreve. O Jev não baixa, não grava DNI, não importa 1104, não lança 1200.

Chamar o Jev só depois do match por regra, e só na linha que não fechou em bate.
Uma chamada jev-latest por linha, com descrição, valor e data. Nada de nome de cliente, documento ou extrato inteiro.
Perguntas, nesta ordem:
- tipo (choice): pix, boleto, cartao, tarifa, aplicacao, resgate, dni, outro
- veredito (choice): duvida, nao_bate
- merece humano hoje (noul)
- risco de baixa errada (noul)

Não chamar se o extrato não chegou, se a regra já deu bate, se há dois títulos no mesmo valor, se falta NSU no cartão, ou se o pedido for baixar, estornar ou gravar.
Confidence abaixo de 0,6 em qualquer pergunta: veredito = duvida, parar, fila da Ariadna.
A chave só vai para https://api.typesafe.ai. Nunca exibir. Dado privado real só com aprovação do Breno.
