# API Query — leitura da conciliação

Não decide baixa. A regra é a skill 1.33.0.

- Base: `https://backend.acessoquery.com/api`
- Toda chamada: `X-Tenant` + Bearer de `POST /login`.
- Antes de clicar: `GET /contas-receber` e `GET /contas-a-pagar`.
- `dt_baixa_fim` = dia seguinte.
- Tela que fecha tenta de novo. O script decide. A tela só grava.
