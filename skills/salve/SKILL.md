---
name: salve
description: >
  Guarda o que você acabou de fazer no lugar certo do cérebro e sobe pro GitHub.
  Lê o conteúdo, decide o destino pelo MAPA, pergunta quando está em dúvida,
  escreve, e dá commit + push. Use quando quiser salvar algo no computador
  (Claude Code, Gemini CLI, Codex) — no Telegram o Hermes salva sozinho.
  Triggers: "/salve", "salva", "salva isso", "guarda isso".
disable-model-invocation: true
---

<!-- disable-model-invocation: faz "push" (ação externa, sobe pro GitHub) — só
     roda quando o dono pede, nunca auto-disparada pelo modelo. Efetiva no Claude
     Code; inofensiva nos outros runtimes. -->
> **Gemini CLI:** a memória nativa do Gemini (auto-memory / `save_memory`) é SEPARADA
> do cérebro — ela grava local e NÃO vai pro GitHub. Pra salvar de verdade no cérebro,
> roteie sempre por esta skill (`/salve` / "salva isso"), não pela memória nativa.

# /salve — guarda no lugar certo (versão simples: 1 cérebro, sem cross-brain)

> No Telegram o Hermes salva sozinho (memory-flush nativo). Esta skill é o mesmo
> motor pra quando você trabalha o cérebro NO COMPUTADOR.

## Passo 1 — Identificar

Olhar o que foi feito/decidido nesta conversa e que vale guardar. Se for trivial
(pergunta solta, teste), não salvar — não polua o cérebro.

## Passo 2 — Classificar pelo destino (consultar o MAPA como gabarito)

São 6 destinos. O `MAPA.md` do cérebro é a fonte — se ele e esta tabela
divergirem, o MAPA vence.

| O que você salvou | Vai pra | Gatilho |
|---|---|---|
| Decisão / "decidi que…" | `memory/context/decisoes/{AAAA-MM}.md` (append) | escolha, definição, "vamos com X" |
| Pendência / "ficou de…" | `memory/context/pendencias.md` (append) | tarefa em aberto, follow-up |
| Negócio / contexto da empresa | `memory/context/business/{nome}.md` | o que é/como roda o negócio |
| Projeto / status | `memory/projects/{nome}.md` (+ `_index.md`) | iniciativa nomeada, andamento |
| Pessoa / "fulano é…" | `memory/context/people/{nome}.md` | contato relevante (cresce sozinho) |
| Rascunho / "escrevi um post" | `content/drafts/{slug}.md` | conteúdo que o agente criou |
| Vira rotina | `skills/{categoria}/{nome}/SKILL.md` | processo repetível |
| **Em dúvida** | **PERGUNTA** | não casa limpo com nada acima |

Regra de ouro: **classifica sozinho quando é óbvio; pergunta o destino quando
está em dúvida.** Se a categoria certa ainda não existe (ex.: "vagas" → criar
`memory/context/rh/`), **oferecer criar a pasta e registrar no MAPA** — mas com
parcimônia: só quando claramente não cabe em nenhum bucket.

## Passo 3 — Escrever

Append nas listas (decisoes, pendencias); arquivo novo em projeto/draft/pessoa.
**Antes de escrever, garanta a pasta** com `mkdir -p "$(dirname <arquivo>)"` — pasta
vazia não vem do git, então no clone fresco o destino pode não existir ainda.

**Nota do dia (convenção anti-colisão):** ao registrar 1 linha da nota do dia, use
`memory/{AAAA-MM-DD}-local.md` no computador — **o sufixo `-local` é obrigatório.** O
nome sem sufixo (`memory/{AAAA-MM-DD}.md`) é **reservado pro servidor** — o computador
nunca escreve nele; use sempre o `-local`. Nomes diferentes = os dois lados podem
escrever no MESMO dia e o git nunca conflita (são arquivos distintos).

## Passo 4 — Commit + push (o cérebro no Git já é o seu backup)

```bash
CEREBRO="$(git rev-parse --show-toplevel)"
cd "$CEREBRO"
# git add SÓ os caminhos que o /salve escreveu neste passo — NUNCA "git add ." nem "-A".
git add "memory/context/decisoes/$(date +%Y-%m).md" "memory/context/pendencias.md"   # ajuste à lista real do que escreveu
git commit -m "salve: <resumo do que foi guardado>"
git pull --rebase
git push
```

**Por que paths explícitos e nunca `git add .`/`-A`:** um `.env`, uma senha
colada num `.txt`, um print com token — qualquer arquivo solto na pasta — entraria
junto e ficaria **permanente** no histórico do GitHub. Você adiciona só o que
escreveu. (É a regra de segurança nº1 do cérebro.)

**Se o push pedir senha / der `Authentication failed`:** PARE e avise — "Seu git
do computador não está conectado ao GitHub. É uma vez só: `gh auth login`. Te ajudo."
Não travar mudo.

**Se o `pull --rebase` der conflito:** PARE. Avise em linguagem simples — "O cérebro
mudou em outro lugar e bateu com o que você salvou aqui. Eu **não vou resolver
sozinho** pra não apagar nada. Seu trabalho está salvo no computador. Me chama que
a gente reconcilia." Manter o local, nunca `--force`, nunca re-clonar por conta própria.

---

**O que esta skill NÃO faz** (cortado de propósito): nada de cross-brain (empresa),
nada de privacy scanner pesado, nada de worktree, dedup ou archive sweep. Isso é
máquina de quem tem 3 cérebros e um time — você tem 1 cérebro, 1 dono. Quando
chegar lá, é a Trilha de empresa.
