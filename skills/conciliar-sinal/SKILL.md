---
name: conciliar-sinal
description: "Veredito do cruzamento. Não decide baixa. A rotina vive em conciliacao-bancaria-valenlub 1.2."
---

Não use esta skill para baixar, ligar ou gravar.
A regra viva é `skills/conciliacao-bancaria-valenlub/SKILL.md` versão 1.2.
Se esta skill divergir, a 1.2 vence.

1. Sem extrato: `aguardando_extrato`. Pare.
2. Par único autorizado: não sinalize de novo. A 1.2 executa.
3. Dois títulos no mesmo valor, sem título, sem NSU: `duvida`. Fila da Ariadna.

## Jev

Só na linha que a 1.2 não fechou.
Não chame se a regra já fechou, se há dois títulos iguais, se falta NSU, ou se o dia já está Conciliado.
Uma chamada. Só descrição, valor e data. Sem nome, documento ou extrato.
Confidence abaixo de 0,6: `duvida`, pare.
Jev não baixa, não grava DNI, não importa 1104.
Chave só para https://api.typesafe.ai. Nunca exibir.
