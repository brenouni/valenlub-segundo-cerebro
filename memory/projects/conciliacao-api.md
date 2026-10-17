# API Query — leitura da conciliação

Não decide baixa. A regra é a skill 1.25.

- Base: `https://backend.acessoquery.com/api`
- Toda chamada: `X-Tenant` + Bearer de `POST /login`.
- Antes de clicar: `GET /contas-receber` e `GET /contas-a-pagar`.
- `dt_baixa_fim` = dia seguinte.
- OFX, caixa 4 e Cielo não existem na spec.
- O script decide. A tela só grava.
