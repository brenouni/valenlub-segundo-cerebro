---
name: conciliacao-bancaria-valenlub
description: "Conciliação do caixa 4. Anexo sem texto já é o pedido. Tela que fecha não é falta. Tente de novo."
version: "1.38.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.38.0. Você não decide. O script decide.

Não narrar passo. Não enviar mensagem de progresso. Não diga “Carrego”, “Vou achar”, “O GET veio”, “Rodo a decisão”.
Só a mensagem final de fechamento (veredito + PDF). Zero narração de passagem.
Chegou OFX: chame a tool `conciliar_dia_valenlub` e devolva só o campo `mensagem` + caminho do PDF. Sem preâmbulo.

## Gatilho

Chegou OFX, PDF do extrato ou CSV da Cielo, com ou sem texto: é conciliação.
Não peça comando. Não pergunte o dia.
A data é a do arquivo. Outro dia no mesmo arquivo não entra.
Sem arquivo, pare. Responda sem ser marcado.

## Ordem

1. Uma aba. Feche as outras do Query antes de começar.
2. Dois GETs. Salve o JSON. `dt_baixa_fim` = dia seguinte.
3. Monte o extrato do dia: valor, nome inteiro, classe.
4. Rode `decidir.py`.
5. Linha `GRAVAR`: clique e faça. Não reclassifique.
6. Linha `ARIADNA`: não grave. Vai para o PDF, com o nome.
7. PDF no fim. Responda só com o `mensagem` da tool (veredito de fechamento) + PDF. Nada no meio.

## Tool 1.38.0 (produção)

A tool `conciliar_dia_valenlub` é a execução. Não reimplemente na UI o que a tool já faz.

- GET paginado com `dt_baixa_ini` = dia e `dt_baixa_fim` = dia seguinte. Cache em `cache/conciliacao/`.
- Gate 0/1/N (aplicação 30060005, tarifa 30060001, resgate/rentabilidade 30060006): 0 cria, 1 só liga, ≥2 bloqueia (estorno). Fallback por histórico se plano vazio.
- Depois de criar, a tool chama `conciliar` para fechar a linha OFX.
- Cartão / Pix / boleto com id: POST `conciliar` (não stub). Pix já pago sem movimento → `ja_pago_painel`, não cria.
- PDF/mensagem: `conciliado` = só `gravado`; `falta` inclui stub/bloqueio/erro/ja_*; fechado só se falta=0 e conciliado≥1.
- Só a mensagem final + PDF. Zero narração de passagem.

## Tela que falha

Não é falta. Não é da Ariadna. Breno, 21/10.

Formulário fechou antes do Concluir. Navegador fechou. Aba não abriu. Várias abas. Painel vazio. Busca não carregou.

1. Feche as abas extras. Deixe uma.
2. Abra de novo a mesma tela.
3. Preencha de novo. Conclua.
4. Confira na tela: a linha ficou Conciliado.
5. Só então passe para a próxima.

Não escreva “Passagem feita” com linha GRAVAR em aberto.
Não coloque no PDF como falta o que o formulário não gravou.
Três tentativas. Na quarta, diga o campo que travou e pare só nessa linha.

## Cartão desdobrado

A Cielo junta. O banco separa.
Duas linhas do banco somam um título: desdobre. Não é falta.
Informe os dois valores. A soma tem que bater no centavo. Ligue cada pedaço.
Linha com título no mesmo valor: só ligue.
Pago no bruto, diferença = taxa: ligue no líquido. Não edite.

## Lote de boleto

Não procure um título no valor da linha.
Selecione os recebimentos do dia. Desmarque cartão.
Soma bate no centavo: ligue.
Painel sem PAGTO de boleto, ou soma dos boletos Pago no dia diferente da linha do banco: vai para a Ariadna. Não force. Não ligue parcial. Não volte.

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
- Tarifa / boleto / liquidação / PIX → classes próprias

## Demais

Centavo: título único até 0,02 é GRAVAR.
Tarifa: 30060001, caixa 4, data do extrato.
Aplicação (`APLIC.INVEST FACIL` / `APLICACAO` / `APLIC.`): GRAVAR 1200 (ver seção). Nunca classifique como `outros` nem Pix.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não procure um título no valor do lote.
Não entregue o dia com GRAVAR em aberto.
