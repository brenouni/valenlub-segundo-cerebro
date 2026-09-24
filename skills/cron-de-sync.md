# O cérebro salva sozinho — cole isto no Telegram

> **Como usar:** abra a conversa do seu agente (Hermes) no Telegram e **cole o
> texto do quadro abaixo**. Se você fez a Trilha 1, seu agente já tem o cron
> `backup-diario` — este texto **transforma** ele (o backup evolui: de 1×/dia pra
> a cada 30 minutos, com sincronização de verdade). Se não tem, ele cria do zero.
> Nos dois casos: UM cron, que sobe o seu cérebro pro GitHub e te avisa se algo
> der errado. Você fecha o computador, ele continua guardando.

## Antes de colar — 2 segundos de atenção

- **NÃO cole nenhuma senha ou token aqui.** O seu token do GitHub já está guardado
  no lugar seguro do agente (o `.env` dele) — ver `SECRETS.md`. Se você colar o
  token no chat, ele fica no histórico do Telegram. Nunca faça isso. (Única exceção:
  a entrega inicial do token no passo 0 — chat privado, e você apaga a mensagem
  depois que o agente confirmar. Fora isso: nunca.)
- **Um cron por cérebro.** Este texto cria o cron DESTE cérebro; se você montar
  outro cérebro (ex.: o da sua área, na Trilha 4), repete o gesto trocando o nome
  e a pasta. Mas nunca dois crons pro MESMO cérebro — eles brigam e enchem seu
  Telegram de aviso. O texto abaixo já pede pro agente conferir antes de criar.

## Cole este texto no Telegram

```
Quero o cron de sincronização do meu cérebro, chamado "cerebro-sync" (montando
outro cérebro? troque o nome — ex.: "area-sync" — e aponte a pasta daquele
cérebro). Antes de qualquer coisa, confere o que já existe:

- Se existe o meu cron "backup-diario" (da Trilha 1) apontando pra esta pasta:
  NÃO cria um novo — TRANSFORMA ele: edita pra rodar a cada 30 minutos, adiciona
  o git pull --rebase antes do push, e renomeia pra "cerebro-sync". Me confirma
  a transformação. (O backup não morre — ele evolui.)
- Se já existe um cron de sync pra esta pasta/cérebro: NÃO cria outro, só me
  confirma qual é.
- Se não existe nenhum: cria do zero.

O cron "cerebro-sync" deve, a cada 30 minutos:
1. ir até a pasta do meu cérebro
2. dar git pull --rebase e depois git push
3. usar o token do GitHub que já está no seu .env (NÃO me peça o token de novo)
4. se o push falhar (token expirado, conflito de git, ou sem internet), me mandar
   uma mensagem AQUI no Telegram explicando o que houve e como resolver — não
   fique em silêncio, porque silêncio me faz achar que está salvando quando não está.
5. conferir se o meu MEMORY.md passou de 2200 caracteres ou o meu USER.md passou de
   1375 — se passou, me avisa aqui. Acima disso você corta o que sobra quando acorda
   e eu perco contexto sem perceber.

Quando criar, me diz o nome do cron e a próxima hora que ele roda.
```

## Como saber que funcionou

Depois que o agente confirmar, peça a ele:

> *"roda esse cron agora pra eu ver"* — ele dispara na hora e te mostra o resultado.

E mais tarde, pra confirmar que está rodando sozinho:

> *"quando foi o último sync que você fez?"* — ele responde com a hora. Se a hora
> avança sozinha sem você pedir, está persistindo. É a prova de que o "me lembra
> de salvar" morreu.

## Se um dia parar

O sinal de que algo quebrou é o **aviso de falha** chegar no Telegram (token
expirado é o mais comum — eles vencem em 90 dias). Quando chegar, é só gerar um
token novo (ver `SECRETS.md`) e avisar o agente. Enquanto o cérebro estiver no seu
computador, nada se perde — o sync só volta a subir pro GitHub.
