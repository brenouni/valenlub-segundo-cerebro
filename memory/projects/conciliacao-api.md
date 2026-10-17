# API Query — leitura da conciliação

Não decide baixa. A regra é a skill 1.19.

- Base: `https://backend.acessoquery.com/api`
- Toda chamada: `X-Tenant` + Bearer de `POST /login`.
- `X-Tenant` da Lub é o token da URL do mgerencia.
- `GET /me`: idUsuario 82, idFilial 1.
- Filiais: 1 MATRIZ, 2 DEPOSITO. Caixa 4 não é filial.
- Leitura: `GET /contas-receber`, `GET /contas-a-pagar`, `GET /tipos-cobranca`.
- `dt_baixa_fim` no mesmo dia = 0. Usar o dia seguinte.
- Tipos: PIX, BOL, CCR, DEB.
- 30060001 tarifas. 30010004 taxa de cartão. 30060005 aplicação. 30060006 resgate.
- OFX, caixa 4 e Cielo não existem na spec. Extrato e CSV vêm em arquivo.
- Tela só para baixar, ligar e lançar.
