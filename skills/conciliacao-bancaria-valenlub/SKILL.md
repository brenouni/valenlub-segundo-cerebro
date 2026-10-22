---
name: conciliacao-bancaria-valenlub
description: "Conciliação do caixa 4. Anexo sem texto já é o pedido. Tela que fecha não é falta. Tente de novo."
version: "1.31.0"
author: Breno Alencar, Hermes Agent
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [ValenLub, Conciliacao, Rotina]
---

# Conciliação — ValenLub, caixa 4

Fonte única. Versão 1.31. Você não decide. O script decide.

Não narrar passo. Não enviar mensagem de progresso. Só o veredito final.

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
7. PDF no fim. Pare em: “Passagem feita.”

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

## Resgate

Nasce na 1100. Cliente Bradesco. Conta 30060006.
Competência e pagamento = data do extrato.
Baixa: juros 0, multa 0, caixa 4. Ligue.
Aplicação e rentabilidade: ARIADNA. Não crie.

## Demais

Centavo: título único até 0,02 é GRAVAR.
Tarifa: 30060001, caixa 4, data do extrato.

## Não fazer

Não estorna. Não grava DNI. Não edite título Pago. Não escolha entre vários.
Não procure um título no valor do lote.
Não entregue o dia com GRAVAR em aberto.
