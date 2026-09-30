# Conciliação ValenLub — v0

Status: mapa do processo fechado (29/09). Módulo 1 fechado no desenho. Roteiro dos 6 GETs gravado. Gabarito numérico da 1200 ainda aberto. Sem git. Sem chamada. Ver `conciliacao-mapa.md`.
Fora desta frente: cobrança, Tássia, Relator 08h, Bradesco executor, as outras 7 empresas, baixa, estorno, POST, cliente, estudo da API, git e cron.

Definição de trabalho (ordem 24/09): fechar o dia no caixa 4 — Bradesco = Query = planilha Fluxo de Caixa LUB.
Conta do caixa 4 vista no extrato: Bradesco 237 / ag 408 / cc 38063-6. Não é filial. A planilha Fluxo de Caixa LUB ainda não foi vista.

Papel 22/07/2024: citado como base. Não chegou. Hipótese até a Ariadna validar a tela. Não trava o goal. Não reconstruí a rotina.

## AS IS — linguagem humana

O agente só entra no cruzamento. Não baixa.

1. Arquivo. Sem extrato, para. Entra na lista como falta papel (`aguardando_extrato`).
   - FATO: sem extrato não cruza.
   - A VALIDAR: quem manda o arquivo, formato, horário. Telas 1111, 1305, 1104, 1100 e 1200 = hipótese até a Ariadna.

2. Query, só leitura. Pega o recorte. Não escreve. Não chama POST.
   - FATO: o cruzamento é título do recorte × movimento do arquivo.
   - A VALIDAR: qual filtro do recorte vale nesta frente. Não é o Relator. API não estudada aqui.

3. Lista: bate / não bate / falta papel. Dúvida não fecha na lista — vai para a Ariadna.
   - FATO: vereditos do soul (`bate` / `nao_bate` / `aguardando_extrato` / `duvida`). Dois títulos no mesmo valor → bloqueia. “Pode baixar” → bloqueia. Não chutar saldo.
   - A VALIDAR: regra do bate (valor, data, tarifa). Sem número inventado.

4. Ariadna conclui. Humano no irreversível. O agente não baixa, não estorna, não fala com cliente.

Onde entra: só no passo 3, com arquivo e recorte já em mãos. Não busca extrato, não abre o banco, não baixa, não conclui no lugar da Ariadna.

## Fontes

Lidos: SOUL, MAPA, primeira-onda, soul/conciliador-sinal, skills/conciliar-sinal, TOOLS, MEMORY, hot, pendencias, decisoes/2026-09, business/valenlub, business/grupo-valen, people/ariadna, people/clessia-ramos, people/luiz, HEARTBEAT, USER, soul/financeiro, skills/query-recorte.
Não lido: documento 22/07/2024. docs.acessoquery — próximo goal. Os fatos de API abaixo são os que a ordem já cravou. Não reestudei chamada a chamada.

## AS IS — 6 passos (HIPÓTESE de tela)

Não é a rotina do agente. Papel 22/07 não veio. Códigos a confirmar.

Travas que valem nos 6 (FATO): sinaliza. Não baixa. Não estorna. Não entra no Bradesco. Não chama POST. Não fala com cliente. Não mistura as outras 7. Sem extrato → `aguardando_extrato`. Dois títulos no mesmo valor → bloqueia. “Pode baixar” → bloqueia. Dúvida → Ariadna.

1. Banco (Bradesco)
   - FATO: é a perna banco da definição. Executor fora desta leva (TOOLS). Luiz é a porta de leitura, depois. Sem ele, sem banco. Pendência aberta: critério de leitura, 2ª conexão.
   - A VALIDAR: como o extrato chega, quem puxa, horário, OFX ou outro arquivo. Papel não chegou. Tempo da rotina: não inventado.

2. 1111 boletos
   - FATO: nenhum sobre a tela. O código veio da ordem como “tela do papel, a confirmar”.
   - A VALIDAR: se a tela existe, se é boletos, se entra no fechamento do caixa 4, o que se confere nela.

3. 1305 central / OFX
   - FATO (ordem, spec não reaberta): OFX, caixa 4 e 1305 não existem na spec da API.
   - A VALIDAR: se 1305 é a central de OFX e se é o passo entre 1111 e Cielo.

4. Cielo / 1104
   - FATO (ordem 29/09): regra do arquivo está na seção Arquivo Cielo. Operadora 22. Caixa 4. Sem número de linha.

5. 1100 Pix/receber e 1200 pagar
   - FATO (módulo 1, dia 25): 1200 usa 30060001 nas tarifas e 30060005 na aplicação. Resgate = 30060006. Não houve no 25.
   - A VALIDAR: se as telas existem e se 1100 e 1200 fecham no mesmo caixa. `cdCobrancaTipo` de Pix = falta.

6. Planilha Fluxo de Caixa LUB
   - FATO: a definição deste goal exige as três pernas iguais.
   - A VALIDAR: nome, aba, dono, horário. business/valenlub.md ainda em branco: praça, volume, sistema extra, fechamento de caixa (quem + horário).

## Tela × API × arquivo

Fonte API: ordem deste goal. Spec não reaberta. Cobertura de tela ≠ existência de endpoint.

- 1111 boletos — GET `/contas-receber` existe. Se cobre a 1111: A VALIDAR. POST `/boletos/cnab/retorno` existe e é escrita: bloqueado. CNAB e baixa continuam fora. Arquivo até a Ariadna cravar a tela.
- 1305 central/OFX — OFX e 1305 não estão na spec (dito). Continua arquivo. Não entrar no banco para buscar.
- 1104 Cielo — regra do arquivo na seção Arquivo Cielo. Não usar número de linha. Endpoint não citado. Continua arquivo. O agente não entra no portal e não importa a 1104.
- 1100 Pix/receber — endpoint não citado. GET `/contas-receber` pode ou não incluir: A VALIDAR. Continua arquivo. `cdCobrancaTipo` Pix = falta.
- 1200 pagar — dia 25: 30060001 tarifa, 30060005 aplicação, 30060006 resgate (não houve). GET `/contas-a-pagar` existe. Se devolve esses códigos: A VALIDAR. Sem chamada. Continua arquivo.
- Caixa 4 — não está na spec (dito). Continua planilha + extrato em arquivo.
- Bradesco — sem endpoint neste goal. Executor fora. Leitura só depois, com o Luiz.

## Conciliador Sinal

Pode
- Veredito: `bate` / `duvida` / `nao_bate` / `aguardando_extrato`.
- Cruzar título do recorte × movimento, quando os dois existirem.
- Dúvida → Ariadna.
- Gravar o sinal no cérebro.

Não pode
- Baixar, estornar, entrar no Bradesco, chamar POST (inclui `/boletos/cnab/retorno`).
- Falar com cliente. Misturar as outras 7 empresas. Chutar saldo.
- Vereditar `bate` sem extrato. Seguir com dois títulos no mesmo valor. Dizer “pode baixar”.
- Cobrança, Tássia, Relator 08h — fora deste goal. Não ligar.
- Skill `conciliar-sinal` não foi alterada. Telas ainda são hipótese.

Cadência no soul: após o Relator, 1× ao dia. Relator não liga neste goal. Cadência operacional = A VALIDAR.

## Falta para o estudo da API

Não estudado aqui. Lista só.

- X-Tenant
- Login da API é o mesmo usuário da tela?
- Existe caixa ou OFX escondido na spec?
- `idFilial` vs caixa 4
- `cdCobrancaTipo` de Pix e de Cielo

Também falta, fora da spec: o papel 22/07/2024, e a Ariadna na tela. Sem isso o AS IS não vira fato.

## Módulo 1 — fechado no desenho

Ordem 29/09. Sem chamada. Sem senha.

- 1200 do dia 25: 30060001 nas tarifas e 30060005 na aplicação.
- Resgate = 30060006. Não houve no dia 25.
- CSV Cielo: regra completa na seção Arquivo Cielo. Âncora no cabeçalho. Sem número de linha.

## Roteiro API — só leitura

Ordem 29/09. Roteiro encerrado neste recorte. GET 4 ficou de fora de propósito. Sem chamada. Sem senha. Sem git.

Base: `https://backend.acessoquery.com/api`
Header: `X-Tenant` + Bearer depois do `POST /login`.
Login e `GET /me` ficam fora desta lista (pré-requisito).

1. `GET /tipos-cobranca`
   - Devolver: lista com `cdCobrancaTipo` e nome. Precisamos do código curto de Pix e de Cielo (até 5 caracteres).
2. `GET /filiais`
   - Devolver: `idFilial` e nome. Fato do teste: caixa 4 não é filial. Conta: Bradesco 237 / ag 408 / cc 38063-6.
3. `GET /contas-receber?dt_baixa_inicio=2026-09-25&dt_baixa_fim=2026-09-25`
   - Devolver: títulos baixados no dia 25. Tem que dar para achar o boleto 71948.77 e os Pix que a Ariadna baixou.
4. `GET /contas-receber?statusCobranca=Aberto&dt_vencimento_inicio=2026-09-01&dt_vencimento_fim=2026-09-30`
   - Devolver: abertos do mês. Serve para o caso “Pix no extrato, título ainda não baixado”.
5. `GET /contas-a-pagar?dt_baixa_inicio=2026-09-25&dt_baixa_fim=2026-09-25`
   - Devolver: o que existir. No dia 25 as tarifas nasceram na 1200; pode vir vazio. Isso é fato, não erro.
6. `GET /plano-de-contas/subcontas`
   - Devolver: achar 30060001 TAXAS BANCÁRIAS e 30060005 APLICACAO. Se a API usar id interno, anotar o id dessas duas.

Armadilha: não usar `GET /vendas/reconciliacao` nem `GET /filiais-movimentacoes`. Não são conciliação bancária.

## Arquivo Cielo — tratamento

FATO. Ordem 29/09. Sem senha. Âncora no cabeçalho. Sem número de linha.

Origem
- Portal Cielo → Vendas e Recebíveis → Meus Recebíveis → detalhado.
- Filtro = data de pagamento do D-1 útil.
- Exportar CSV. Fica no portal 90 dias.
- O agente não entra no portal.

Dois arquivos
1. Bruto = o que sai do portal.
2. Tratado = o que a 1104 importa.

O que o bruto tem em cima (descartar)
- Ouvidoria, telefones, horário de atendimento, usuário, estabelecimento, CNPJ, tipo de visualização, título “Recebíveis Detalhado”, filtros, totalizador (Quantidade de lançamentos / Valor bruto / Taxa/tarifa / Valor líquido).
- Esse bloco muda de tamanho. Não use número de linha.

Âncora
- No bruto, a linha `Data de pagamento:` (dois pontos) é filtro. Descartar.
- O cabeçalho é a linha que começa com `Data de pagamento;` (ponto e vírgula).
- Tudo antes desse cabeçalho se ignora. Tudo depois é lançamento.
- Não use número de linha. No bruto do 25/09 o totalizador veio antes do cabeçalho.

Tratado
- Cabeçalho + lançamentos.
- Separador: ponto e vírgula.
- Não inventar coluna.

Conferência
- A soma dos “Valor líquido” do tratado tem que bater com o totalizador do bruto e com a soma das linhas Cielo do OFX do mesmo dia.
- No 25/09: 5 lançamentos, líquido 387,47.

Cruzamento com o OFX (fato 25/09)
- Cielo não agrupa. Banco agrupa.
- 147,67 Elo crédito = 1 linha OFX.
- 188,37 Elo débito = 1 linha OFX.
- 15,35 Master débito = 1 linha OFX.
- 21,84 + 14,24 Visa débito = 1 linha OFX 36,08.
- Se o valor do CSV não existir sozinho no OFX, somar mesmo dia + mesma bandeira.

1104
- Importa só o tratado.
- Operadora Cielo, código 22.
- Caixa 4 (Bradesco 237 / ag 408 / cc 38063-6).
- Data = D-1 útil.
- Sem NSU não baixa.
- Valor tem que ser exato. Centavo diferente = vermelho. A tela não explica o erro.
- O agente não importa a 1104. Não baixa.

O agente
- Pode ler o bruto, achar a âncora, montar o tratado e apontar o par CSV↔OFX.
- Não entra no portal Cielo. Não importa a 1104. Não baixa.

## Conferência 25/09

Visto nos arquivos. Sem senha. Sem CSV inteiro. Sem commit.

- Caixa 4: extrato PDF agência 408, conta 38063-6. OFX banco 0237, conta 38063. Não é filial.
- Dia 25 no OFX: 22 lançamentos. Crédito 103.968,78. Débito 103.968,78. O arquivo traz outros dias; o recorte do 25 é que tem 22.
- Relatório Query do 25: as linhas estão Conciliado, diferença 0,00. Totais 103.968,78 e -103.968,78.
- Cielo: 5 lançamentos, líquido 387,47. Visa 21,84+14,24=36,08 no OFX. Elo crédito 147,67. Elo débito 188,37. Master débito 15,35.
- Plano visto no CSV: 30060001 TAXAS BANCÁRIAS, 30060005 APLICACAO, 30060006 RESGATE.

## Ledger

- goal conciliacao aberto em 2026-09-24
- goal conciliacao retomado, sem git
- módulo 1 fechado no desenho em 2026-09-29. Sem chamada.
- roteiro dos 6 GETs gravado em 2026-09-29. Sem chamada.
- roteiro encerrado neste recorte em 2026-09-29. GET 4 de fora de propósito. Sem chamada.
- regra do arquivo Cielo gravada em 2026-09-29. Âncora no cabeçalho. Sem commit.
- conferência do 25 gravada em 2026-09-29. Sem commit.
- mapa do processo fechado em 2026-09-29. Gabarito numérico da 1200 aberto. Sem commit.
