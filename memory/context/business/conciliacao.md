# ValenLub — Conciliação bancária (caixa 4)

Distribuidora GT OIL. Frente 1 desta leva: fechar o banco no fim do dia.

## O que é
Conferir se o dinheiro que o banco mostra é o mesmo que o Query e a planilha LUB mostram. Se bater, o dia fecha. Não é cobrança. Não é protesto.

## AS IS (doc 2024 — Ariadna corrige o que mudou)
1. Banco: baixa extrato de ontem (OFX + PDF) + arquivo de boletos pagos.
2. 1111 — Boletos pagos: o banco avisa que o cliente pagou; a tela registra no título.
3. 1305 — Mesa da conciliação: extrato encontra o caixa 4. Tela principal.
4. 1104 — Cartão Cielo: sobe a planilha e baixa no caixa.
5. 1100 — O que vamos receber (Pix e outras entradas). Centavos divergentes se ajustam aqui.
6. 1200 — O que já pagamos (conta, tarifa, estorno). Nada se apaga: errou, estorna.
7. Planilha Fluxo de Caixa LUB: saldo do dia precisa fechar.

## Caixa
Caixa 4 (a confirmar se ainda é). Cartão: Cielo (a confirmar se é só). Planilha LUB: a confirmar se ainda é obrigatória todo dia.

## Quem
- Ariadna: dona da rotina hoje. Mostra a tela (20–30 min).
- Cléssia: prioridade e desbloqueio.
- Equipe: quem aperta concluir no Query. O ajudante só lê e aponta.

## Regras duras
- Ajudante lê OFX / PDF / CSV Cielo / export Query. Não mexe.
- Cruza: bateu / não bateu / falta arquivo.
- Entrega rascunho curto para Ariadna: “estes N itens precisam dos seus olhos.”
- Nunca entra no Bradesco. Nunca aperta 1111 / concluir. Nunca apaga. Nunca fala com cliente. Nunca inventa número.
- Skill canônica: `skills/conciliacao-bancaria-valenlub/SKILL.md` versão 1.38.4. Ela vence este arquivo.

## Fora desta frente
Cobrança, Relator 08h, Tássia, as outras 7 empresas do grupo.
