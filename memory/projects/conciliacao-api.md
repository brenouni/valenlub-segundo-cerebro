# API Query — recorte da conciliação

Fonte: spec pública Query Backend API 1.0.0 (OpenAPI 3.0.3), relida em 29/09.
Docs: `https://backend.acessoquery.com/docs`
Spec: `https://backend.acessoquery.com/openapi.json`
Base: `https://backend.acessoquery.com/api`

Daqui: não chamei endpoint. Não fiz login. Sem senha. Sem token. Sem git.
O teste foi fora deste chat. Não repetir a chamada.

Telas 1111, 1305, 1104, 1100 e 1200 não estão na spec. Continuam hipótese da Ariadna.

## Estudo da spec — 29/09

Relido na docs e no openapi. Sem chamada.

- Toda requisição pede `X-Tenant`. Fora o login, pede `Authorization`.
- `POST /logout` existe e invalida o token. Bloqueado. Simulação não faz logout.
- `GET /contas-receber`: só `isAtivo = Sim`. Ordem `idCobrancaReceber DESC`.
- Página: padrão 50, máximo 500. O dia 25 teve 138 pagos. Página padrão não fecha o dia. `with_total=1` traz `total` e `last_page`.
- `Desdobrado` é lápide. Os filhos nascem `Aberto`. Somar os dois conta duas vezes.
- `dtAtualizacao` anterior a 2026-07-17 foi preenchida com a data da cobrança. `data_ultima_alteracao` pode reentregar. Não é o filtro da baixa do dia.
- Baixa do contas a pagar traz `idCaixaBaixa` e `tpBaixa` (exemplo `Caixa`). Não é o caixa 4.
- 401 = token ausente, inválido, expirado, ou `X-Tenant` inválido.

## Como entra

FATO da spec
- Toda chamada: header `X-Tenant`. É a `dsKey` do tenant. Obrigatório.
- Depois do login: `Authorization` Bearer.
- `POST /login` pede `X-Tenant` e não pede Bearer. Corpo: `cdLogin`, `cdSenha`. Resposta: `token`, `expires_at`.
- `GET /me` devolve o usuário do token.
- OAuth2 / IdP existe no papel e ainda não vale na REST. Token de `POST /oauth/token` não é aceito nos `/api/*` atuais.

FATO de teste
- `X-Tenant` da Lub é o token da URL do mgerencia. Não é o domínio `valenlub.com.br`. O valor não está neste arquivo.
- O login da tela `amanda` autenticou na REST. Senha não está neste arquivo.
- `GET /me`: `idUsuario` 82, `idFilial` 1.

Não falta o `X-Tenant`. Falta só o valor, e ele não entra neste arquivo.

## O que o Conciliador pode ler

Leitura. Não baixa. Não escreve. Não inventar rota.

`GET /contas-receber`
- `statusCobranca` (CSV): `Aberto`, `Pago`, `Desdobrado`, `Devolvido`. Sem filtro vem tudo, inclusive `Desdobrado`. Não somar `vrCobrancaReceber` do resultado cru.
- Datas: `dt_vencimento_*`, `dt_baixa_*`, `dt_cobranca_*`, `dt_competencia_*`.
- `idPessoa`, `idFilial`, `idCobrancaTipo`, `cdCobrancaTipo` (até 5 caracteres), `data_ultima_alteracao`.
- `include`: `venda`, `pessoa`, `planoDeContas`.
- FATO de teste: `dt_baixa_fim` no mesmo dia = 0. A data vem `T03:00:00Z`. Usar o dia seguinte.

`GET /contas-receber/{idCobrancaReceber}`
- O path `{id}` não existe. O parâmetro da spec é `idCobrancaReceber`.

`GET /contas-a-pagar`
- `statusCobranca`: `Aberto`, `Pago`, `Aguardando`, `Desdobrado`, `Devolvido`, `Recusado`.
- Datas: `dt_vencimento_*`, `dt_baixa_*`, `dt_competencia_*`.
- Não tem `idCobrancaTipo` nem `cdCobrancaTipo`. Não inventar.
- Tem `idPlanoDeContasSubconta`. No teste, esse id é o `nrSubconta`.

`GET /contas-a-pagar/{idCobrancaPagar}`
- O path `{id}` não existe. O parâmetro da spec é `idCobrancaPagar`.

`GET /tipos-cobranca`
- Spec: `tpPagamento` = `A Vista`, `Cartao`, `A Prazo`.
- FATO de teste, códigos da Lub: `PIX`, `BOL`, `CCR`, `DEB`, `DIN`, `CHE`, `DEP/T`, `CRED`, `BON`, `CRE`, `CAN`.
- Cielo não é tipo. Cielo = operadora 22 na 1104. No título: `CCR` ou `DEB`.

`GET /filiais`
- FATO de teste: 1 MATRIZ, 2 DEPOSITO. Caixa 4 não é filial. A pergunta “idFilial é o caixa 4?” está fechada: não.

`GET /plano-de-contas/subcontas`
- Spec: filtro por `nrSubconta` ou `idPlanoDeContasSubconta`. Não existe parâmetro `codigo`.
- FATO de teste: 143 itens. `idPlanoDeContasSubconta` = `nrSubconta`. `?codigo=` não filtra.
- `30060001` TAXAS BANCÁRIAS. `30060005` APLICACAO. `30060006` RESGATE.

Também existem, leitura, ainda sem teste:
- `GET /plano-de-contas/subcontas/{idPlanoDeContasSubconta}`
- `GET /plano-de-contas/arvore`
- `GET /plano-de-contas/grupos`
- `GET /plano-de-contas/contas`
- `GET /planos-pagamento`
- `GET /filiais/{idFilial}`
- `GET /tipos-cobranca/{idCobrancaTipo}`

## O que não existe na spec

- OFX: zero.
- PDF de extrato do banco: zero.
- Caixa 4: zero. Não é filial e não é campo da spec.
- Tela 1305: zero.
- Portal Cielo: zero.
- Extrato Bradesco: zero. A palavra extrato só aparece em cupom de promoção (`/promocoes-movimentacoes`).

Não confundir
- PDF de boleto: `GET /contas-receber/{idCobrancaReceber}/boleto`. Bancos `001`, `237`, `422`. Não é extrato. Fora da leitura desta frente.

## Bloqueado

FATO da spec — escrita, existe
- `POST /boletos/cnab/retorno`
- `POST /boletos/{idBoleto}/enviar`
- `DELETE /boletos/{idBoleto}`
- `PATCH /boletos/{idBoleto}/prorrogar`
- Qualquer outro POST, PATCH ou DELETE.

FATO da regra
- Qualquer POST, PATCH ou DELETE está bloqueado. Equivale a baixar. Não chamar.
- A spec não diz “bloqueado”. O bloqueio é deste cérebro.
- Proibido alterar o acesso da tela. Daqui não entra.

## Armadilha

- `GET /vendas/reconciliacao`: hash de vendas. Não é banco.
- `GET /filiais-movimentacoes`: mercadoria na filial. Não é extrato. PUT e POST existem — bloqueados.
- `GET /contas-receber/{idCobrancaReceber}/boleto`: PDF de boleto. Não é extrato.
- `?codigo=` em subconta: não existe na spec e no teste não filtra.

## FATO de teste — dia 25

Feito fora. Sem senha. Sem chamada daqui.

- Baixa: 138 pagos. 12 `PIX` + 126 `BOL`. Filial 1.
- 10 valores Pix do OFX existem na API. 10 mil do Vony não (DNI).
- 71.948,77 não é um título `BOL`. É lote.
- `CCR` e `DEB` não vieram nesse GET. Cielo continua na 1104.
- `GET /contas-a-pagar` no 25: histórico igual ao OFX. `30060001` e `30060005`.

## GETs que ainda ajudam

Só lista. Não executar.

- `GET /contas-receber` com `dt_baixa_fim` no dia seguinte. O mesmo dia dá 0.
- `GET /contas-receber/{idCobrancaReceber}` quando precisar de um título.
- `GET /contas-a-pagar?idPlanoDeContasSubconta=30060001` e `30060005`. Feito nesta simulação. Ver fato abaixo.
- `GET /plano-de-contas/subcontas/{idPlanoDeContasSubconta}` pelo id. Feito nesta simulação. Não usar `?codigo=`.
- Abertos do mês (`statusCobranca=Aberto`) ficaram de fora de propósito. Não executar.

## Roteiro dos 6

Encerrado neste recorte. Não repetir.

1. `GET /tipos-cobranca` — feito fora.
2. `GET /filiais` — feito fora.
3. `GET /contas-receber` do dia 25 — feito fora. `dt_baixa_fim` = dia seguinte.
4. Abertos do mês — de fora de propósito.
5. `GET /contas-a-pagar` no 25 — feito fora.
6. `GET /plano-de-contas/subcontas` — feito fora. 143 itens.

## FATO de simulação — só leitura — 29/09

Feito daqui. Só GET depois do login. Sem logout. Sem senha. Sem token no arquivo.

- `GET /me`: `idUsuario` 82. `idFilial` não veio na raiz.
- `GET /filiais`: 1 MATRIZ, 2 DEPOSITO.
- `GET /plano-de-contas/subcontas/30060001` = TAXAS BANCÁRIAS.
- `GET /plano-de-contas/subcontas/30060005` = APLICACAO.
- `GET /plano-de-contas/subcontas/30060006` = RESGATE.
- `GET /contas-a-pagar` do 25, filtro por subconta, `per_page=500`, `with_total=1`:
  - 30060001: 4 títulos.
  - 30060005: 1 título, histórico APLIC.AUTOM.INVESTFACI.
  - 30060006: 0. Sem resgate no 25.

## FATO de teste — A e B — fora

Feito fora. Sem senha. Sem chamada daqui.

- A) Pagar 25: `valores.vrPago` bate o OFX. 22,62 / 10,44 / 5,94 / 1,65 na 30060001. 103928,13 na 30060005. Lançado no sistema dia 28. Competência 25.
- B) `GET /contas-receber/88379?include=pessoa`: Pix 8880 = NICOLAU DERIVADOS / POSTO PALOMA. Nome do OFX cruza.

Teste Atlas pagar 25: sem credencial no cofre. Sem chamada.

## FATO de teste — leitura no sistema — 29/09

Somente GET depois do login. Sem logout. Sem senha. Sem token no arquivo.

- Pagar do 25, filtro de baixa, `per_page=500`: 14 títulos, não 5.
- Caixa 4 bate o OFX: 30060001 = 22,62 / 10,44 / 5,94 / 1,65. 30060005 = 103.928,13. 30060006 = 0.
- Os outros 9 não estão no OFX. Não são despesa do caixa 4. O filtro do dia traz também desconto, juros dispensado, multa dispensada e ajuste de estoque. O Conciliador não pode somar todo o pagar do dia.
- Receber do 25: 138 pagos. 12 PIX + 126 BOL.
- Pix de valor único bate o OFX, inclusive 36,01. Nome não reaberto neste GET.
- Dois títulos de 1.000,00. A regra bloqueia.
- 10.000,00 está no OFX e não está nos 138 pagos.
- 19,99 está nos pagos e não está no OFX do 25.
- 71.948,77 não é um título. A soma dos 126 BOL é 147.067,05. O lote não foi isolado.
- Cielo não veio neste GET. Esperado. O cruzamento dela continua no CSV.

## FATO de teste — dia 24 — só leitura — 29/09

Um dia. Sem logout. Sem senha. Sem token.

- O OFX deste pacote não tem 22 nem 23. Tem o 24: 6 créditos, 219.611,82. Sem débito.
- Os 6 créditos batem `GET /contas-receber` do 24, subconta 30060006, tipo PIX. Três resgates e três rentabilidades.
- No mesmo dia o pagar tem 6 tarifas 30060001 e 4 resgates 30060006 com outros valores. Esses 10 não estão neste OFX.
- 30060005 não apareceu no 24. No extrato houve resgate, não aplicação.
- Receber do 24: 118 pagos. 24 PIX, 92 BOL, 1 DEB, 1 DIN.

## FATO de teste — dia 28 — só leitura — 29/09

Arquivo + GET. Sem logout. Sem senha. Sem token. Sem nome de cliente no arquivo.

- OFX do 28: 28 lançamentos. 85.414,04 dos dois lados. Relatório Query: 28 linhas, Conciliado, diferença 0,00.
- Caixa 4: aplicação 85.372,93 na 30060005. Sem resgate.
- Tarifas 10,44 / 20,88 / 5,94 / 1,65 batem título a título na 30060001.
- O banco tem 4 tarifas de 0,55, mesmo histórico. O Query tem 1 título de 2,20. 0,55 × 4 = 2,20. Observado neste dia. Ainda não é regra fechada.
- Cielo: 4 lançamentos, líquido 940,34, todos com NSU. O bruto e o tratado têm as mesmas 4 linhas. Âncora no cabeçalho, neste bruto na linha 22.
- O banco juntou os dois créditos Mastercard, 377,74 + 78,67 = 456,41. Visa 355,20 ficou separado. Débito 128,73 ficou separado. CSV soma o mesmo 940,34.
- 12 Pix de valor único batem o receber do 28.
- 755,47, 1.637,94 e 714,90 estão conciliados no relatório e não aparecem no GET de Pix entre 26 e 30, nem na competência 28. Dúvida. Não chamei de DNI.
- 713,64 está pago no 28, competência 15/05, e não está no OFX do 28.
- 75.118,28 não é um boleto. A soma dos 232 BOL é 285.632,64. Lote não isolado.
- Um Pix do extrato traz 26/09 no histórico e foi conciliado no 28. A data do histórico não é a data do pagamento.

## FATO — resposta do Breno — 29/09

Sem chamada. Sem senha.

- Os Pix 755,47, 1.637,94 e 714,90 do dia 28 foram conciliados como DNI. Motivo: identificar e baixar depois, e não deixar a conciliação aberta. O agente não grava DNI.
- Tarifas iguais da mesma descrição podem ser um lançamento só, para desdobrar depois. No dia 28, quatro de 0,55 viraram 2,20. Descrição: tarifa de transferência Pix.

## FATO — lote do boleto — tela — 30/09

Print da pré-conciliação, caixa 4, dia 28. Sem chamada. Sem senha. Sem nome de cliente.

- A linha do banco abre a lista `CONCILIADAS`.
- Cabeçalho visto: `30045 - LIQUIDACAO DE COBRANCA VALOR DISPONIVEL VALOR: 75.118,28 (9.038.063) - (N100C3)`.
- Boleto nessa lista: histórico começa com `PAGTO`.
- A soma das conciliadas é 75.118,28. Diferença 0.
- `30045`, `9.038.063` e `N100C3` são deste movimento. Não viram regra até repetir noutro dia.
- O GET `/contas-receber` não devolve esse pacote.
