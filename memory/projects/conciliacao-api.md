# API Query — leitura da conciliação

Não decide baixa. A regra é a skill 1.24.

- Base: `https://backend.acessoquery.com/api`
- Toda chamada: `X-Tenant` + Bearer de `POST /login`.
- `X-Tenant` da Lub é o token da URL do mgerencia.
- Antes de clicar: `GET /contas-receber` e `GET /contas-a-pagar`.
- `dt_baixa_fim` = dia seguinte. No mesmo dia volta zero.
- Guarde valor, status, pessoa e id.
- `GET /me`: idUsuario 82, idFilial 1.
- Filiais: 1 MATRIZ, 2 DEPOSITO. Caixa 4 não é filial.
- Tipos: PIX, BOL, CCR, DEB.
- 30060001 tarifas. 30010004 taxa de cartão. 30060005 aplicação. 30060006 resgate.
- OFX, caixa 4 e Cielo não existem na spec. Extrato e CSV vêm em arquivo.
- Se a API respondeu, zero clique para procurar. Tela só para baixar, ligar e lançar.
