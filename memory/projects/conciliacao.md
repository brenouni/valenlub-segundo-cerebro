# Conciliação ValenLub — v0

Status: goal retomado, sem git. Só Valen Lubrificantes. Um passo.
Fora desta frente: cobrança, Tássia, Relator 08h, Bradesco executor, as outras 7 empresas, baixa, estorno, POST, cliente, estudo da API, git e cron.

Definição de trabalho (ordem 24/09): fechar o dia no caixa 4 — Bradesco = Query = planilha Fluxo de Caixa LUB.
Caixa 4 e o nome da planilha ainda não foram vistos na tela. Ariadna valida.

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
   - FATO: nenhum sobre a tela.
   - A VALIDAR: código, se é Cielo, se entra no caixa 4. `cdCobrancaTipo` de Cielo = falta do estudo da API.

5. 1100 Pix/receber e 1200 pagar / tarifa 30060001
   - FATO: nenhum sobre as telas. A ordem junta os dois neste passo. Não confirmo se a rotina real junta.
   - A VALIDAR: 1100, 1200, tarifa 30060001, Pix, e se os dois fecham no mesmo caixa. `cdCobrancaTipo` de Pix = falta do estudo da API.

6. Planilha Fluxo de Caixa LUB
   - FATO: a definição deste goal exige as três pernas iguais.
   - A VALIDAR: nome, aba, dono, horário. business/valenlub.md ainda em branco: praça, volume, sistema extra, fechamento de caixa (quem + horário).

## Tela × API × arquivo

Fonte API: ordem deste goal. Spec não reaberta. Cobertura de tela ≠ existência de endpoint.

- 1111 boletos — GET `/contas-receber` existe. Se cobre a 1111: A VALIDAR. POST `/boletos/cnab/retorno` existe e é escrita: bloqueado. CNAB e baixa continuam fora. Arquivo até a Ariadna cravar a tela.
- 1305 central/OFX — OFX e 1305 não estão na spec (dito). Continua arquivo. Não entrar no banco para buscar.
- 1104 Cielo — endpoint não citado neste goal. Não inventar. Continua arquivo. `cdCobrancaTipo` Cielo = falta.
- 1100 Pix/receber — endpoint não citado. GET `/contas-receber` pode ou não incluir: A VALIDAR. Continua arquivo. `cdCobrancaTipo` Pix = falta.
- 1200 pagar / tarifa 30060001 — GET `/contas-a-pagar` existe. Se cobre a 1200 ou a tarifa: A VALIDAR. Continua arquivo.
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

## Ledger

- goal conciliacao aberto em 2026-09-24
- goal conciliacao retomado, sem git
