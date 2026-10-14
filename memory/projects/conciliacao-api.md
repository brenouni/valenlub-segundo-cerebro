# API Query — estudo, não é regra

Não decide baixa. Fonte única: skill 1.8.

- Toda chamada: `X-Tenant` + Bearer depois do login.
- `X-Tenant` da Lub é o token da URL do mgerencia. Valor não está aqui.
- `GET /me`: idUsuario 82, idFilial 1.
- Filiais: 1 MATRIZ, 2 DEPOSITO. Caixa 4 não é filial.
- `dt_baixa_fim` no mesmo dia = 0. Usar o dia seguinte.
- Tipos: PIX, BOL, CCR, DEB. Cielo não é tipo. Operadora 22.
- 30060001 tarifas. 30060005 aplicação. 30060006 resgate.
- OFX, caixa 4 e Cielo não existem na spec.
- `GET /vendas/reconciliacao` não é banco.
