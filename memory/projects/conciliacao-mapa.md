# Mapa — Conciliação ValenLub

Empresa: Valen Lubrificantes. Não misturar com as outras 7.
Regra viva: `skills/conciliacao-bancaria-valenlub/SKILL.md` versão 1.2.
Este arquivo é índice. Não repete a regra. Se divergir, a skill vence.
`conciliar-sinal` não decide baixa. Aponta para a 1.2.

Atualizado em 14/10. Sem senha. Sem token.

## Papel

Breno conduz.
Ariadna recebe só o que a regra não fecha.
Atlas, na rotina: fecha o par único, liga e segue. Não pergunta o que a skill já decide.
Modo “só olhar”: só se o Breno disser. Aí não grava.

## Caixa

Caixa 4 = Bradesco 0237, ag 408, cc 38063-6. Não é filial.
Filiais: 1 MATRIZ, 2 DEPOSITO.
D-1. Segunda olha sexta. Sem extrato, para.

## Contas

Tarifa 30060001. Aplicação 30060005. Resgate 30060006.
No mesmo dia, aplicação ou resgate, não os dois.
Rentabilidade (`RENTAB.INVEST`) não é resgate. Conta ainda aberta.
Cielo não é tipo. No título, CCR ou DEB. Na 1104, operadora 22.

## O que a rotina fecha — não devolver

Pix com um título do valor. Aberto: baixa no caixa 4, data do extrato, juros e multa zerados, e liga. Já pago: só liga.
Lote de boleto com soma exata das linhas de pagamento: liga.
Tarifa da linha, conta 30060001: baixa e liga. Não lança outra.
Centavo de título único: ajusta para o valor do banco, baixa e liga.
Pagamento com título único no pagar: baixa e liga.

## O que para — não executar

Sem extrato. Dois títulos no mesmo valor. Sem título único. Sem NSU no cartão.
Pix sem título: propõe DNI. Não grava.
Sem título no pagar: não lança a pessoa.
Cielo sem comprovante ou sem título no valor da linha: fica aberta. Não lança recebimento.
Dia já Conciliado, Falta 0 e Ajuste 0: pare. Não reabra.

## Continua bloqueado

Estorno. Importar 1104. Portal Cielo. Banco. Gravar DNI. Importar OFX na 1305.

## Fatos medidos — não reabrir

25/09: 22 linhas, 103.968,78 dos dois lados, Conciliado. Cielo 387,47. Visa 21,84+14,24 = 36,08.
36,01 daquele dia foi Pix. 36,08 foi Cielo.
Lote 25/09: 60 títulos, 71.948,77.
01/10 no arquivo: 52 linhas. Cartão 16,84, NSU 734466. Lote 69.221,30. Dois Pix de 1.000 e dois de 400 não fecham sozinhos. Resgate 404.529,09. Rentabilidade 8,28. Tarifas 3.072,94.
28/09: DNI 755,47, 1.637,94 e 714,90. Agente não grava DNI. Quatro tarifas 0,55 = 2,20.

## Lacuna aberta

Conta da rentabilidade. Planilha Fluxo de Caixa LUB, ainda não vista.
Telas 1111 e 1100, hipótese.
