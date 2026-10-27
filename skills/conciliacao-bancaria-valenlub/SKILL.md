---
name: conciliacao-bancaria-valenlub
description: "Conciliação do caixa 4. Anexo sem texto já é o pedido. Tela que fecha não é falta. Tente de novo."
version: "1.38.3"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.38.3. Você não decide. O script decide.

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

## Tool 1.38.3 (produção)

A tool `conciliar_dia_valenlub` (1.38.3) é a execução. Não reimplemente na UI o que a tool já faz.

- GET paginado com `dt_baixa_ini` = dia e `dt_baixa_fim` = dia seguinte. Cache em `cache/conciliacao/`.
- Gate 0/1/N (aplicação 30060005, tarifa 30060001, resgate/rentabilidade 30060006): 0 cria, 1 só liga, ≥2 bloqueia (estorno). Data do título obrigatória para casar; fallback valor+dia se plano+hist vazios.
- Depois de criar, parse do id + `conciliar` com `prefer_hist` (APLIC/TARIFA/RESGATE).
- Cartão / Pix / boleto com id: POST `conciliar` (não stub). Desdobro (valor linha ≠ título ou acao Desdobre) → `bloqueio_desdobro`, não liga pedaço. Pix já pago sem movimento → `ja_pago_painel`.
- PDF/mensagem: `conciliado` = só `gravado`; `planejado` = `simulado` (não fecha); `falta` inclui stub/bloqueio/desdobro/erro/ja_*; fechado só se falta=0, planejado=0 e conciliado≥1.
- Só a mensagem final + PDF. Zero narração de passagem.

## Exceção — tool não fechou

Só se a tool devolver `erro`/`stub_noop`/`bloqueio_*` e Breno pedir tela: uma aba, refazer a linha, conferir Conciliado. Não narrar o meio. Não invente UI no happy path.

## Cartão desdobrado

A Cielo junta. O banco separa.
Duas linhas do banco somam um título: a tool marca `bloqueio_desdobro` (não liga pedaço no título inteiro).
Desdobrar na tela (dois valores, soma no centavo) e só então religar.
Linha com título no mesmo valor (±0,02): a tool liga.
Pago no bruto, diferença = taxa: ligue no líquido. Não edite.

## Lote de boleto

Não procure um título no valor da linha.
Selecione TODOS os recebimentos que **iniciam com `PAGTO`** (retorno de boletos). Desmarque cartão.
Soma bate no centavo: ligue.
Painel sem PAGTO de boleto, ou soma dos boletos Pago no dia diferente da linha do banco: vai para a Ariadna. Não force. Não ligue parcial. Não volte.

Pix do extrato já baixado: ligue pelo valor na central. Não marque como falta de título se a baixa já foi feita.

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
- Tarifa / boleto / liquidação → classes próprias
- Pix só se `PIX` no histórico/memo (CREDIT/DEP sozinho ≠ pix)

## Demais

Centavo: título único até 0,02 é GRAVAR.
Tarifa: 30060001, caixa 4, data do extrato.
Aplicação (`APLIC.INVEST FACIL` / `APLICACAO` / `APLIC.`): GRAVAR 1200 (ver seção). Nunca classifique como `outros` nem Pix.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não procure um título no valor do lote.
Não entregue o dia com GRAVAR em aberto.
