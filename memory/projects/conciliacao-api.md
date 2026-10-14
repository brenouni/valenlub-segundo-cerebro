# API Query — estudo, não é regra

Não decide baixa. Fonte única da rotina: `skills/conciliacao-bancaria-valenlub/SKILL.md` versão 1.7.

Fonte: spec pública Query Backend API 1.0.0 (OpenAPI 3.0.3), relida em 29/09.
Docs: `https://backend.acessoquery.com/docs`
Spec: `https://backend.acessoquery.com/openapi.json`
Base: `https://backend.acessoquery.com/api`

Daqui: não chamei endpoint. Não fiz login. Sem senha. Sem token.

## Como entra

- Toda chamada: header `X-Tenant`. É a `dsKey` do tenant.
- Depois do login: `Authorization` Bearer.
- `POST /login` pede `X-Tenant` e não pede Bearer. Corpo: `cdLogin`, `cdSenha`. Resposta: `token`, `expires_at`.
- `GET /me` devolve o usuário do token.
- OAuth2 ainda não vale na REST.
- `X-Tenant` da Lub é o token da URL do mgerencia. Não é o domínio. O valor não está neste arquivo.
- `GET /me`: `idUsuario` 82, `idFilial` 1.

## Leitura que existe

`GET /contas-receber`
- `statusCobranca`: `Aberto`, `Pago`, `Desdobrado`, `Devolvido`.
- `dt_baixa_fim` no mesmo dia = 0. A data vem `T03:00:00Z`. Usar o dia seguinte.
- Página padrão 50. Dia cheio pede `per_page=500` e `with_total=1`.
- Path real: `idCobrancaReceber`. Não existe `{id}`.

`GET /contas-a-pagar`
- Não tem `cdCobrancaTipo`. Tem `idPlanoDeContasSubconta` = `nrSubconta`.
- Path real: `idCobrancaPagar`.
- O filtro do dia traz linha fora do caixa 4. Não somar tudo.

`GET /tipos-cobranca`
- Códigos da Lub: `PIX`, `BOL`, `CCR`, `DEB`, `DIN`, `CHE`, `DEP/T`, `CRED`, `BON`, `CRE`, `CAN`.
- Cielo não é tipo. Operadora 22 na 1104. No título, CCR ou DEB.

`GET /filiais`
- 1 MATRIZ, 2 DEPOSITO. Caixa 4 não é filial.

`GET /plano-de-contas/subcontas`
- 30060001 TAXAS. 30060005 APLICACAO. 30060006 RESGATE.
- `?codigo=` não filtra.

## Não existe na spec

OFX, PDF de extrato, caixa 4, tela 1305, portal Cielo, extrato Bradesco.
`GET /vendas/reconciliacao` não é banco.
`GET /filiais-movimentacoes` não é extrato.
