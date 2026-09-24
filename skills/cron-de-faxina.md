# Cron de faxina — cole no Telegram do Hermes

Roda **uma vez por mês**. Se pedir outra frequência, o agente ajusta. Não cria segundo cron no mesmo cérebro.

## Cole isto

```
Quero o cron de faxina do cérebro ValenLub, nome "cerebro-faxina".
Antes de criar: se já existir faxina neste cérebro, NÃO cria outro — só confirma o nome e a próxima data.

Frequência: 1× por mês. Se eu pedir pra mudar, ajusta este cron; não inventa um segundo.

Quando rodar, nesta ordem:

1) Arquivo
   - Move para archive/ as decisões em memory/context/decisoes/ e as notas memory/YYYY-MM-DD*.md com mais de 60 dias.
   - Mantém a etiqueta YAML (data, tipo, origem) pra continuar achável.
   - Não apaga. Move.

2) Lint de tamanho
   - Se MEMORY.md > 2200 caracteres, me avisa pra enxugar. Não corta sozinho.
   - Se USER.md > 1375, avisa do mesmo jeito.

3) Scanner de segredo
   - Varre os .md do cérebro atrás de chave, token (ghp_, sk_live_, Bearer), senha=, CPF, cartão.
   - Se achar: me avisa o arquivo e a linha. NÃO apaga sozinho.

4) Resumo
   - Manda neste Telegram: o que moveu, o que estourou tamanho, o que o scanner achou, próxima data da faxina.
   - Silêncio = falha. Se não conseguir rodar, avisa o motivo.

Pasta do cérebro: a raiz deste repo (valenlub-brain). Token GitHub já está no .env — não me peça de novo.
```

## Provar que o cérebro está vivo (chat novo)

1. Qual é o P1 do meu raio-X?
2. Me resume o que a gente decidiu esta semana.
3. Onde a gente parou no projeto primeira-onda-valenlub?

Respostas esperadas hoje (23/09/2026), se o boot leu o cérebro:

1. GitHub privado + token no `.env` do Hermes (depois cron-de-sync).
2. Query primeiro, conciliação só sinal, Relator 08h, um cérebro = Financeiro, Vendas/Operação/geral só no 2º domínio, visual Grok 3/4.
3. Cérebro montado no workspace; Scout/Relator ainda sem corrida; GitHub remoto pendente.
