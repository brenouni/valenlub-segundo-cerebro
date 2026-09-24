# Conciliação — o que falta

Fonte: conciliacao.md e conciliacao-api.md. Sem chamada. Sem senha.

## 1. Já temos (fato)

- Só Valen Lubrificantes. O agente só cruza. Não baixa, não estorna, não entra no Bradesco, não chama POST, não fala com cliente.
- Sem extrato, não cruza. Vereditos: bate, não bate, falta papel, dúvida. Dúvida vai para a Ariadna. Dois títulos no mesmo valor bloqueiam. “Pode baixar” bloqueia.
- Entrada da API: `X-Tenant` + Bearer de `POST /login`. Token de `/oauth/token` não vale na REST atual.
- Leitura: `GET /contas-receber`, `GET /contas-a-pagar`, `GET /tipos-cobranca`. Filtros de status, data, tipo e filial estão nomeados na spec.
- A spec não tem OFX, tela 1305, Cielo, extrato Bradesco, nem o código caixa 4.
- `POST /boletos/cnab/retorno` existe e está bloqueado. Equivale a baixar.
- `/vendas/reconciliacao` e `/filiais-movimentacoes` não são conciliação bancária.

## 2. Falta para o Conciliador funcionar

Pergunta ao Italo. Sem senha.

- `X-Tenant` da Lub (`dsKey`). Não está na spec.
- O `cdLogin` da API é o usuário da tela?
- Existe caixa ou OFX fora desta spec? Nela, não.
- `idFilial` é o caixa 4? A spec não diz. Não tratar como o mesmo.
- `cdCobrancaTipo` de Pix e de Cielo na Lub. Campo até 5 caracteres. Exemplos da spec: `DIN`, `BOL`. Código da Lub não está.

## 3. Falta para a Ariadna validar

Tela
- 1111, 1305, 1104, 1100 e 1200 existem e entram no caixa 4?
- Caixa 4 e a planilha Fluxo de Caixa LUB ainda não foram vistos. Aba e dono, em aberto.
- 1100 e 1200 fecham juntos? A tarifa 30060001 entra?
- Regra do bate: valor, data, tarifa. Sem número inventado.

Arquivo
- Papel de 22/07 não chegou.
- Quem manda o extrato e em que formato. OFX não está na spec.

Horário
- Quem fecha e a que horas. Ainda em branco.

## WhatsApp — Italo

Italo, da API da Valen Lubrificantes. Sem senha, sem token.

1. Qual o X-Tenant (dsKey) da Lub?
2. O login da API é o mesmo usuário da tela?
3. Existe caixa ou OFX fora da spec pública? Nela, não achei.
4. idFilial é o caixa 4? Se não for, qual idFilial usar?
5. Qual o cdCobrancaTipo de Pix e de Cielo? Até 5 caracteres.
