---
name: conciliacao-bancaria-valenlub
description: "Conciliação do caixa 4. Anexo sem texto já é o pedido. Tela que fecha não é falta. Tente de novo."
version: "1.39.5"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.39.5. Você não decide. O script decide.

Não narrar passo. Não enviar mensagem de progresso. Não diga “Carrego”, “Vou achar”, “O GET veio”, “Rodo a decisão”.
Só a mensagem final de fechamento (veredito + PDF). Zero narração de passagem.
Chegou OFX: chame a tool `conciliar_dia_valenlub` e devolva só o campo `mensagem` + caminho do PDF. Sem preâmbulo.

## Gatilho

Chegou OFX, PDF do extrato ou CSV da Cielo, com ou sem texto: é conciliação.
Não peça comando. Não pergunte o dia.
A data é a do arquivo. Outro dia no mesmo arquivo não entra.
Sem arquivo, pare. Responda sem ser marcado.

## Ordem (happy path)

1. Chegou OFX → chame a tool `conciliar_dia_valenlub` (modo simular ou executar).
2. Devolva só o campo `mensagem` + caminho do PDF. Zero narração. Zero UI.
3. Não reimplemente GETs, cliques nem `decidir.py` na tela — a tool faz tudo.

## Tool 1.39.5 (produção)

A tool `conciliar_dia_valenlub` (1.39.5) é a execução. Não reimplemente na UI o que a tool já faz.

- GET paginado: (1) `dt_baixa` do dia; (2) suplementar `statusCobranca=Aberto,Pago` por vencimento (~45d) e cobrança (~7d). Merge por id. Cache em `cache/conciliacao/`.
- Gate 0/1/N (aplicação 30060005, tarifa 30060001, resgate/rentabilidade 30060006): 0 cria, 1 só liga, ≥2 bloqueia. Mensagem lista **manter** (id mais antigo) e **estornar** (demais) na 1200/1100. Tool NÃO estorna no fluxo do dia (helpers de desconciliar/estornar/reabrir existem, mas exigem flag explícita).
- Depois de criar, parse do id + `conciliar` com `prefer_hist` (APLIC/TARIFA/RESGATE).
- Cartão: casa líquido ±0,02 ou bruto Cielo (CSV). **Sem fallback 5%**. Desdobro só com evidência Cielo/parcela ou acao Desdobre. N títulos → 1 OFX (±0,02) = agregação (multi-id). Sem título único no Query: se já baixado no painel → **só ligar** (mov 1:1 RECEBIMENTO/CARTÃO/CIELO); 0 ou 2+ movs → ARIADNA. Não baixar de novo.
- Pix / DEPOSIT TED: título Pago → liga; título **Aberto N=1** no valor (centavo) → **GRAVAR** baixar 1100 (`receber_transaction` com `idPessoa` do título, juros/multa 0, caixa 4) + ligar 1:1. N≠1 / ambíguo → ARIADNA. Sem título → tenta ligar pelo valor; senão ARIADNA.
- Liquidação crédito: lote **só PAGTO\* do mesmo dia** do extrato (prefixo PAGTO; sem Pix/cartão; **sem outras datas**). Soma/subset só no dia; se não fecha → ARIADNA.
- Débito `PAGTO ELETRON` / cobrança saída → classe `pagar` (AP por valor); não lote PAGTO crédito.
- PDF/mensagem: `conciliado` = só `gravado`; `planejado` = `simulado`; `falta` inclui stub/bloqueio/desdobro/erro/ja_*; fechado só se falta=0, planejado=0 e conciliado≥1.
- Só a mensagem final + PDF. Zero narração de passagem.

## Reabrir dia (explícito — NÃO no fluxo diário)

A tool agora sabe:
- `query_desconciliar(opener, id_extrato, estornar_titulo=0)` → POST `/scripts/financeiro/conciliacao/actions&id=desconciliar` fields `Financeiro_Caixas_Extratos_id` + `estornarTitulo` (default 0 = só solta vínculo; 1 também estorna baixa — PERIGO).
- `query_estornar_pagar` com payload **nested** `fields[Financeiro_Cobrancas_Pagar][idCobrancaPagar|idCaixaBaixa|dsMotivoEstorno]` (flat falhou).
- `query_extrato_periodo` (`modo=periodo`) lista Conciliado+Falta+Ajuste; `modo=pendentes` não devolve Conciliado.
- Parser `isOk` aceita true / 1 / "1".

**Política:** no `simular`/`executar` do dia a tool **NÃO** desliga nem estorna. Reabrir exige flag explícita:

```bash
python3 tools/conciliar_dia_valenlub.py --reabrir-dia --data YYYY-MM-DD --caixa 4
# dry-run (default). Para mutar:
python3 tools/conciliar_dia_valenlub.py --reabrir-dia --executar-reabrir --data YYYY-MM-DD \
  --estornar-ap 39042,39043
```

Ordem segura: desligar (`estornarTitulo=0`) → conferir Conciliado=0 → estornar só AP órfão `isEstornavel`.

## Exceção — tool não fechou


Só se a tool devolver `erro`/`stub_noop`/`bloqueio_*` e Breno pedir tela: uma aba, refazer a linha, conferir Conciliado. Não narrar o meio. Não invente UI no happy path.

## Cartão desdobrado (humano)

A Cielo junta. O banco separa — ou o inverso (N Cielo → 1 banco).
Duas linhas do banco somam um título: a tool marca `bloqueio_desdobro` (não liga pedaço no título inteiro).
**Desdobrar na tela** (dois valores, soma no centavo) e só então religar.
Linha com título no mesmo valor (±0,02): a tool liga.
Pago no bruto Cielo, diferença = taxa: ligue no líquido. Não edite.
Parcela Elo/bandeira cujo título é a venda inteira (ex. 3239 vs líquido 776,47): desdobro na tela; não usar “quase 5%”.

## Agregação cartão (N→1)

Três (ou N) DEB/CCR Cielo somam um crédito OFX: a tool tenta multi-id. Se títulos Abertos, baixe antes (1100/tela) e rode de novo.


## Cartão já pago no painel (só ligar)

Igual liquidação `PAGTO*`: se o recebimento **já está baixado** no painel (movimentação `RECEBIMENTO DE CARTÃO…` / Cielo / Master / Amex), a tool **não baixa de novo**.
Sem título líquido/bruto/agregação no Query ≠ “sem título” se existir **movimentação 1:1** no valor do OFX.
- 1 mov no líquido → `conciliar` (ligar extrato↔mov).
- 0 ou 2+ movs → ARIADNA (não chute).
Não inventar título 1100 de cartão.

## Lote de boleto (crédito)

Não procure um título no valor da linha.
Selecione **somente** os recebimentos do **mesmo dia do extrato** cujo histórico **inicia com `PAGTO`** (retorno de boletos). “Todos os PAGTO” = todos com esse prefixo **no dia** — nunca outras datas.
**Nunca** incluir no lote: Pix, CR avulso, `RECEBIMENTO DE CARTÃO`, Cielo/Master/Amex.
Desmarque cartão e qualquer mov que não comece com `PAGTO`.
Soma bate no centavo: ligue.
Painel sem PAGTO de boleto, ou soma diferente: Ariadna. Não force. Não ligue parcial.
(Aprendizado 28/10 — dia 19: liquidação 30794 tinha CRs/Pix indevidos; Pix 3484,74 sumiu das movs abertas.)

## Débito PAGTO ELETRON / cobrança (AP)

Não é liquidação de boleto crédito. Ache o AP no valor (±0,02) e ligue. 0 AP → Ariadna 1200.

## Pix Aberto / DEPOSIT cliente (1.39.5)

Preferência: Pix **N=1** no valor (centavo) → **baixar + ligar** na tool; cartão Pago 1:1 `RECEBIMENTO DE CARTÃO` → só ligar no líquido (não baixar de novo).

Se o GET achar título **Aberto** único no valor (±0,02) e extrato Pix/DEP 1:1:
1. `receber_transaction` (Receber Pagamento) com **idPessoa do título** (não Bradesco), juros 0, multa 0, caixa 4, data do extrato.
2. Ligar extrato ↔ mov do título.
Isso é **GRAVAR** (`baixa_antes=true`) — não mandar Ariadna.

Se N≠1 no valor (vários ids) ou ambíguo: **ARIADNA** (tool não escolhe).
Se **Pago**: só ligue. Pix já baixado sem id no GET: tente ligar pelo valor na central.

(Aprendizado 28/10 — dias 19 e 23: Pix Abertos 1:1 conhecidos iam ARIADNA «baixar 1100»; agora a tool baixa+liga.)

## Mov presa em liquidação (Pix/CR «não aparece»)

Se título **Pago** mas a tool diz «movimento/extrato não aparece» / Sem movimentação: **não** marque Falta/ARIADNA ainda.

1. Cheque se o CR do título está em outra linha **Conciliado** do dia (quase sempre uma **liquidação** com origens indevidas — Pix/cartão misturados no lote PAGTO).
2. Se sim → `desconciliar` essa liquidação com `estornarTitulo=0` (só solta vínculo; não estorna baixa).
3. Ligue o Pix/CR **1:1** no extrato certo (Falta).
4. Religue a liquidação **só com PAGTO*** cuja soma feche o valor do extrato.

A tool no fluxo do dia **não** desliga sozinha (precisa flag `--reabrir-dia` ou ação humana). Em `ja_pago_painel` / Sem movimentação ela aponta liquidação Conciliado suspeita no motivo.
(Aprendizado 28/10 — dia 19: CR 89292/título 90764 preso na liquidação 30794; extrato Pix 30799 Falta.)

## Tarifa duplicada (humano)

Gate ≥2: manter o id mais antigo; **estornar** os mais novos na 1200. No fluxo do dia: só orienta ids. Estorno/desligar só com --reabrir-dia explícito.

## Resgate — lançar e baixar

- Rotina 1100, botão Receita, “Lançar receita avulsa”.
- Cliente 1117 BANCO BRADESCO S.A., histórico resgate, valor da linha, competência e pagamento na data do extrato, conta 30060006 RESGATE, forma PIX, plano A VISTA - A VISTA PIX, caixa para baixa vazio.
- Concluir. Título nasce Aberto.
- Abrir Receber Pagamento. Zerar vrJuros e vrMulta. Caixa Destino = caixa 4. Data de Recebimento = data do extrato. Valor recebido = valor do título. Concluir.
- Ligar na central do caixa 4.
- Não criar se já existir título único na 30060006 no mesmo valor e dia. Uma aba só.

## Rentabilidade — lançar e baixar

- Rotina 1100, botão Receita, “Lançar receita avulsa”.
- Cliente 1117 BANCO BRADESCO S.A., histórico rentabilidade, valor da linha, competência e pagamento na data do extrato, conta 30060006 RESGATE, forma PIX, plano A VISTA - A VISTA PIX, caixa para baixa vazio.
- Concluir. Título nasce Aberto.
- Abrir Receber Pagamento. Zerar vrJuros e vrMulta. Caixa Destino = caixa 4. Data de Recebimento = data do extrato. Valor recebido = valor do título. Concluir.
- Ligar na central do caixa 4.
- Não criar se já existir título único na 30060006 no mesmo valor e dia. Uma aba só.

## Aplicação — lançar e baixar (contas a pagar)

- Rotina 1200 (contas a pagar), Mais despesa.
- Fornecedor: Bradesco. Descrição: aplicação. Valor: o do extrato.
- Data de vencimento e competência: data do extrato.
- Plano de contas: aplicação (30060005). Rateio: não preenche.
- Marca pagamento. Caixa: 4. Data de pagamento: data do extrato.
- Ligar na central do caixa 4.
- Gate na tool (executar): 0 título 30060005 no valor/dia → cria; 1 → só liga (não cria); 2+ → não escolhe, não cria, marca estorno do duplicado na 1200.
- Não criar se já existir título único na 30060005 no mesmo valor e dia. Uma aba só.
- Nunca ARIADNA. Nunca classifique como `outros` nem Pix.

## Classificação do extrato

Histórico (nome/memo) decide a classe. Ordem importa.

- `RENTAB` / `RENTABILIDADE` / `INVEST FACILCRED` / `RENDIMENTO` → **rentabilidade** (GRAVAR 1100)
- `RESGATE` / `RESG.` → **resgate** (GRAVAR 1100)
- `CIELO` / cartão → **cartao**
- `APLIC.INVEST FACIL` / `APLICACAO` / `APLIC.` / `APLIC ` → **aplicacao** (GRAVAR 1200)
- Tarifa / boleto crédito / liquidação → classes próprias
- `PAGTO ELETRON` / cobrança a débito → **pagar** (AP)
- `DEPOSIT TRANSFER` / TED recebida → **deposito** (casa título cliente; não `outros`)
- Pix só se `PIX` no histórico/memo (CREDIT/DEP sozinho ≠ pix)

## Demais

Centavo: título único até 0,02 é GRAVAR.
Tarifa: 30060001, caixa 4, data do extrato.
Aplicação (`APLIC.INVEST FACIL` / `APLICACAO` / `APLIC.`): GRAVAR 1200 (ver seção). Nunca classifique como `outros` nem Pix.


## Deploy (obrigatório após pull)

Após `git pull` da skill/tool no VPS, **sempre** reiniciar o gateway — o Python mantém o módulo em memória. SKILL.md no disco ≠ tool carregada.

```bash
systemctl --user restart hermes-gateway.service
# prova: PID novo + versão em memória = disco (smoke 1.39.5)
```

Falha clássica (28/10): disco em 1.39.1, gateway sem restart desde 24/10 → `receber_query` ~50 em vez de ~5040; 9 linhas «sem título».

## PDF / cabeçalho = central live (1.39.5)

O PDF **não pode mentir**. Cabeçalho Conciliado/Falta/Ajuste = GET `query_extrato_periodo` (central Omie), **não** a contagem da passagem.

- Re-executar em dia já Conciliado: cartão/aplicação/pix/liquidação sem pendência → `ja_conciliado` (confirma status Conciliado na central). **Nunca** ARIADNA/`ja_existe_ligar` só porque `extrato_pendente` sumiu.
- Seção «em falta» do PDF: só o que a central ainda tem Falta. Se Falta=0, lista vazia.
- Relatório só-leitura (zero POST): `python3 tools/conciliar_dia_valenlub.py --relatorio-central --data YYYY-MM-DD --caixa 4 --pdf /caminho.pdf`
(Aprendizado 28/10 — dia 19 já 27/0/0; re-executar gerou PDF 22/5 mentiroso.)

## Não fazer

Não estorna no fluxo do dia (só com --reabrir-dia --executar-reabrir). Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não procure um título no valor do lote de boleto crédito.
Não use fallback “≈5%” em cartão.
Não invente baixa 1100 de Pix/DEP quando N≠1/ambíguo (só ARIADNA). N=1 Aberto → baixar+ligar com idPessoa do título.
Não invente baixa 1100 de cartão já pago no painel (só ligar 1:1).
Não inclua Pix/CR/`RECEBIMENTO DE CARTÃO` no lote de liquidação (só `PAGTO*`).
Não marque Falta/ARIADNA por «mov não aparece» sem checar se o CR está preso em liquidação Conciliado.
Não marque Falta/ARIADNA/`ja_existe_ligar` em re-executar só porque extrato_pendente sumiu — confira Conciliado na central.
Não imprima no PDF cabeçalho de passagem quando a central diz outra coisa (cabeçalho = live).
Não entregue o dia com GRAVAR em aberto.
Não faça `git pull` da tool sem reiniciar `hermes-gateway.service`.
