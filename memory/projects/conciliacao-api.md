# API Query — recorte da conciliação

Fonte: `https://backend.acessoquery.com/openapi.json` (OpenAPI 3.0.3). Docs no mesmo host. Não chamei endpoint. Não fiz login.

Base da REST: `https://backend.acessoquery.com/api`.
Telas 1111, 1305, 1104, 1100 e 1200 continuam hipótese da Ariadna. A spec não confirma esses códigos.

## 1. Como entra

FATO
- `X-Tenant` em toda chamada. É a `dsKey` do tenant. Obrigatório.
- Bearer legado sai de `POST /login` (no servidor, `/api/login`). Corpo: `cdLogin`, `cdSenha`. Resposta: `token`, `expires_at`. O login pede `X-Tenant` e não pede Bearer.
- O esquema Bearer da spec: esse token protege os `/api/*` atuais. Token do IdP via `POST /oauth/token` ainda não é aceito nesses endpoints.
- Authorization Code: a spec diz em desenvolvimento. Token ainda não aceito na REST.

A VALIDAR
- Client Credentials está descrito (server-to-server, ainda pede `X-Tenant`). A frase “não aceito” está no Bearer, para token de `/oauth/token`. Nesta frente não uso OAuth.
- Valor do `X-Tenant` da Lub: não está na spec.

## 2. O que o Conciliador pode ler

Só estes três. Leitura. Não baixa. Não escreve.

`GET /contas-receber`
- status: `statusCobranca` (CSV). Valores observados: `Aberto`, `Pago`, `Desdobrado`, `Devolvido`. Sem filtro vem tudo, inclusive `Desdobrado`. Não somar `vrCobrancaReceber` do resultado cru.
- data: `dt_vencimento_inicio`, `dt_vencimento_fim`, `dt_cobranca_inicio`, `dt_cobranca_fim`, `dt_baixa_inicio`, `dt_baixa_fim`, `dt_competencia_inicio`, `dt_competencia_fim`.
- tipo: `idCobrancaTipo` (CSV), `cdCobrancaTipo` (até 5 caracteres).
- filial: `idFilial` (CSV).

`GET /contas-a-pagar`
- status: `statusCobranca`. Valores conhecidos: `Aberto`, `Pago`, `Aguardando`, `Desdobrado`, `Devolvido`, `Recusado`.
- data: `dt_vencimento_inicio`, `dt_vencimento_fim`, `dt_competencia_inicio`, `dt_competencia_fim`, `dt_baixa_inicio`, `dt_baixa_fim`.
- filial: `idFilial` (CSV).
- tipo de cobrança: este GET não tem `idCobrancaTipo` nem `cdCobrancaTipo`. Não inventar.

`GET /tipos-cobranca`
- `cdCobrancaTipo` (CSV), `idCobrancaTipo` (CSV).
- `tpPagamento`: `A Vista`, `Cartao`, `A Prazo`.
- `q` busca `nmCobrancaTipo` ou `cdCobrancaTipo`.
- Sem filial. Sem `statusCobranca`.
- Campo `hasPIXBB` existe (`Sim` / `Não`). Não é o código Pix da Lub.

## 3. O que não existe na spec

FATO — ausente
- OFX: zero.
- Tela 1305: zero.
- Cielo: zero.
- Extrato bancário e extrato Bradesco: zero. A palavra extrato só aparece em cupom de promoção (`/promocoes-movimentacoes`).
- Caixa 4: o código não aparece. Os três GET não têm filtro de caixa.

Não confundir com o que existe e não é conciliação bancária
- Bradesco (`237`) só no PDF do boleto: `GET /contas-receber/{idCobrancaReceber}/boleto`. Não é extrato. Fora da lista de leitura desta frente.
- `tpBaixa` com exemplo `Caixa` em conta a receber. `idCaixaBaixa` na baixa do contas a pagar. `idCaixaDeposito` em cobrança de venda. Nenhum desses é a tela caixa 4.

## 4. Bloqueado

FATO da spec: `POST /boletos/cnab/retorno` existe. Sobe arquivo `.RET`. Aplica ocorrência, inclusive `06` liquidação e `09` / `10` baixa.
FATO da regra: bloqueado. Equivale a baixar. Qualquer escrita bloqueada. Não chamar.
A spec não diz “bloqueado”. O bloqueio é deste cérebro.

## 5. Armadilha

- `GET /vendas/reconciliacao`: reconciliação de vendas contra drift (hash por dia). Não é banco. Não é caixa.
- `/filiais-movimentacoes`: entrada e saída de filial, separação de venda. Não é extrato. POST e PUT existem — escrita, bloqueados.

## 6. Perguntar ao Italo

Sem senha. Sem colar credencial.

- `X-Tenant` da Lub (`dsKey`). Não está na spec.
- `cdLogin` da API é o usuário da tela?
- Caixa 4 ou OFX escondido fora desta spec? Nesta spec, não.
- `idFilial` é caixa 4? A spec não diz. Não tratar como o mesmo.
- `cdCobrancaTipo` de Pix e de Cielo na Lub. O campo existe (até 5 caracteres). Exemplos da spec: `DIN`, `BOL`. Código da Lub não está. Cielo não aparece. Pix na spec é `hasPIXBB` e QR em venda (bancos `bb` / `sicoob`), não o código da tela 1100.
