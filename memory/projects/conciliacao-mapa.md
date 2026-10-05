# Mapa — Conciliação bancária D-1

Empresa: Valen Lubrificantes
Domínio: Financeiro
Responsável: Registrado — Ariadna aprova o irreversível. Breno conduz o projeto. Atlas só sinaliza.
Fonte de verdade: Registrado — OFX do caixa 4 × título do Query. PDF do banco e CSV Cielo são pernas. Planilha Fluxo de Caixa LUB: lacuna.

Fechado no mapa em 29/09. Sem git. Sem chamada nesta gravação. Sem senha. Sem token.

## Processo real

D-1. Segunda olha a sexta. Sem extrato, para (`aguardando_extrato`).

1. Bancário, rotina 1305. Registrado na ata de 28/09. Importa OFX e PDF do Bradesco. Caixa 4 não é filial.
2. Cartão, rotina 1104. Registrado. CSV Cielo, operadora 22, caixa 4. Âncora no cabeçalho `Data de pagamento;`. Sem número de linha. Sem NSU não baixa. Centavo diferente não fecha sozinho.
3. DNI. Registrado. Crédito não identificado fica rastreável até achar o cliente. O agente pode propor. Não grava.
4. Despesa, rotina 1200. Registrado. Tarifa 30060001. Aplicação 30060005. Resgate 30060006. No mesmo dia, aplicação ou resgate, não os dois.

Veredito: `bate` / `duvida` / `nao_bate` / `aguardando_extrato`.
Match automático só com valor exato, data de pagamento e uma única contraparte. Dois títulos no mesmo valor bloqueiam. Dúvida vai para a Ariadna.

## Permissões

- Leitura: OFX, PDF, CSV tratado a partir da âncora, GET do Query.
- Sugestão: veredito, proposta de lançamento 1200, proposta de DNI.
- Escrita bloqueada: baixa, estorno, importar 1104, gravar 1200, gerar DNI, POST, portal Cielo, banco.

Telas 1305, 1104 e 1200 não estão na spec. Gravar por elas seria inventar caminho.

## O que o dia 25 já mede

Registrado. Não é a fala da reunião.

- OFX do 25: 22 lançamentos. 103.968,78 dos dois lados.
- Relatório Query do 25: Conciliado, diferença 0,00.
- Cielo: 5 lançamentos, líquido 387,47. Visa 21,84+14,24 = 36,08 no OFX.
- Pagar medido: 22,62 / 10,44 / 5,94 / 1,65 na 30060001. 103.928,13 na 30060005. Lançado no sistema dia 28, competência 25.
- 30060006: 0.
- Pix 8.880 cruza com a pessoa do título 88379.

## Lacunas

- Gabarito da 1200 no dia 25. Fechado neste teste de arquivo. OFX tem 22,62 / 10,44 / 5,94 / 1,65 e 103.928,13. Não tem 25,00 nem 139,20. A fala da ata não entra.
- Credencial no cofre. Sem ela, leitura diária do Query não roda daqui.
- NSU, só leitura, 01/10. Não está na conciliação nem no contas a pagar. Fica no contas a receber, no cartão da venda, campo nrDoc, coluna NSU. Na 1100 o filtro é DOC / CV / NSU. Quatro vendas de 26/09: crédito Visa 734453, 413,20, vencimento 26/10, Aberto; débito Mastercard 734450, líquido 128,73, Conciliado; débito Visa 734445, líquido 14,24, Conciliado; crédito Elo 734458, 102,64, vencimento 26/10, Aberto. Débito vence no dia seguinte e o crédito em cerca de 30 dias. O 128,73 é a linha do banco. A baixa casa o NSU do arquivo da Cielo com esse campo. Não baixei.
- Cartão na 1104, 30/09. É Baixa de Cartão. Tipo Cielo, operadora 22 = CIELO S.A, caixa por código, data e arquivo RET. Enviar e revisar e Confirmar baixa não foram clicados.
- Lote do boleto. Medido no navegador, só leitura, em três dias. A linha `LIQUIDACAO DE COBRANCA VALOR DISPONIVEL` abre só `PAGTO`, data de pagamento do dia, soma exata. Dia 22: 143 títulos, 86048 a 86190, 172.567,40. Dia 25: 60, 86529 a 86588, 71.948,77. Dia 28: 66, 86937 a 87002, 75.118,28. Não cliquei em conciliar.
- Outros dias, caixa 4, só leitura, 30/09. 22, 23 e 24 estão conciliados, zero em Falta. 26 não tem lançamento. Naquela leitura o 29 estava aberto: 4 conciliados e 46 em Falta.
- Dia 29 no papel, 01/10. OFX, extrato e PDF da conciliação batem: 50 lançamentos, 236.541,04 dos dois lados, diferença 0, todos Conciliado. A leitura da tela de 30/09 ficou velha. Cartão: dois líquidos, 340,34 e 315,28, soma 655,62. NSU 706565 Visa 4/4 venda 29/05 e NSU 43504 Master 2/2 venda 30/07. Não é venda do dia. Boleto 210.514,36. Aplicação 92.001,53. Não reabri a tela. Não baixei. Teste real ainda não: o dia já fechou, e o DNI não foi lido na tela.
- Despesas do 29, relatório da 1200, 01/10. 30 títulos, todos Pago, caixa 4. Competência da baixa 29/09, baixa no sistema 01/10. Soma 236.541,04, igual a cada débito do extrato, centavo a centavo. As quatro tarifas estão na 30060001. A aplicação de 92.001,53 está na 30060005. Não abre a tela da 1200.
- Dia 30 no papel, 01/10. O PDF da conciliação já está fechado: 29 linhas, 120.857,21 dos dois lados, diferença 0, todos Conciliado. Cartão 17,24, NSU 706652. Despesa: 7 títulos iguais aos 7 débitos. Uma tarifa Pix de 1,65 com data 01/10 no título.
- Teste do dia 01/10, só arquivo, 02/10. Caixa 4, 52 lançamentos. Cartão bate: débito Visa, líquido 16,84, NSU 734466, venda 30/09. Boleto 69.221,30 não medido na tela. Dois Pix de 1.000,00 e dois de 400,00 não fecham sozinhos. Resgate 404.529,09, proposta 30060006. Cinco rentabilidades somam 8,28. Nove tarifas somam 3.072,94, proposta 30060001. Quatro de 0,55 somam 2,20. Sem relatório da 1200, folha e pagamentos ficam em dúvida. Tela não aberta. Não baixei. Olhar em 04/10, só leitura: caixa 4, dia 01/10, zero em Falta, Conciliado e Ajuste. De 30/09 a 05/10, Falta zero. Conciliado só 30/09, 29 linhas. O OFX do 01/10 não está na pré-conciliação. Não importei.
- Pix conciliado como DNI. Fechado por Breno em 29/09. Os 755,47, 1.637,94 e 714,90 do dia 28 foram DNI para a conciliação não ficar aberta. A baixa correta fica para depois. O agente não grava DNI.
- Tarifa Pix repetida. Fechado por Breno em 29/09. Várias tarifas da mesma descrição podem virar um lançamento só, para desdobrar depois. No dia 28, 4 × 0,55 = 2,20.
- Planilha Fluxo de Caixa LUB. Terceira perna da definição. Não vista.
- Telas 1111 e 1100. Hipótese. A ata não cravou.
- API da Cielo. Não bloqueia. Enquanto não existir, entra CSV.
- Direção 30/09: o lote da tela vai pelo navegador, no modelo da Ester, adaptado. A Ester não clicou item a item. Usou sessão autenticada e a operação interna da tela. Ela mesma disse que, sem essa operação, o Atlas precisa de automação visual. Primeiro teste: só abrir a tela, sem preencher e sem confirmar. Gravação, importação e baixa continuam bloqueadas.
- 36,01: 1 título PIX pago no filtro do 25 e 1 linha no OFX. Bate por valor. Nome não reaberto.

## Menor próximo passo

Cravar o gabarito do 25 contra o OFX, linha a linha da 1200. Depois, um segundo dia no mesmo pacote: OFX, PDF, CSV Cielo, relatório Query. Se a mesma regra fechar os dois, aí a ferramenta. Antes disso, não há código.
