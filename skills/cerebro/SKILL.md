---
name: cerebro
description: >
  Liga o segundo cérebro no computador. Faz git pull, lê os arquivos-raiz na
  ordem de boot, navega o MAPA e devolve um raio-X ("o que eu já sei de você").
  Use no começo da sessão, quando abrir o agente num computador (Claude Code,
  Gemini CLI, Codex) — onde não existe o boot automático que o Hermes tem no
  Telegram. Triggers: "/cerebro", "liga o cérebro", "carrega meu contexto".
---

# /cerebro — liga o cérebro (versão simples: 1 cérebro, 1 dono)

> Esta skill replica, no computador, o que o Hermes já faz sozinho no Telegram:
> acordar lendo o seu cérebro. No Telegram você NÃO precisa dela. No PC, precisa.

## Passo 0 — Diagnóstico de conexão (sempre roda primeiro)

Antes de carregar nada, conferir se o cérebro está acessível. Rodar e MOSTRAR o
resultado (P14 — nunca fingir que rodou):

```bash
CEREBRO="$(git rev-parse --show-toplevel 2>/dev/null)"   # raiz do repo do cérebro
if [ -z "$CEREBRO" ]; then echo "SEM_REPO"; else
  echo "WORKSPACE=$CEREBRO"
  git -C "$CEREBRO" remote -v | head -1
  ls "$CEREBRO/MAPA.md" "$CEREBRO"/{SOUL,USER,AGENTS}.md 2>/dev/null
  ls -d "$CEREBRO/memory/context" "$CEREBRO/memory/projects" 2>/dev/null
fi
```

Interpretar e dar o veredito EM LINGUAGEM DE LEIGO (nunca jargão de git):
- **`SEM_REPO`** → "Não achei um cérebro neste computador. Ele vive no GitHub (e na
  VPS do seu agente). Pra trabalhar nele aqui, traga-o: `gh repo clone
  <seu-usuario>/<repo-do-cerebro>` e entre na pasta (não sabe o nome? rode
  `gh repo list`). Se você ainda não ligou o cérebro ao GitHub, é o passo 0 da
  Trilha 3 (`CRIAR-O-CEREBRO-NO-GITHUB.md`)."
- **Sem remote** → "Seu cérebro está no computador mas ainda não está ligado ao
  GitHub. Sem isso ele não sincroniza entre o PC e o agente. Quer que eu ligue?"
- **Faltam pastas (`context/`, `projects/`)** → listar quais faltam e oferecer
  criar a estrutura mínima (não despejar tudo — só as gavetas que faltam).
- **Tudo presente** → seguir pro Passo 1.

## Passo 1 — Sincronizar (puxar antes de ler)

O cérebro pode ter mudado noutra interface (o Hermes salvou algo, ou você mexeu
em outro PC). Puxar primeiro:

```bash
git -C "$CEREBRO" pull --rebase 2>&1
```

Se vier `Authentication failed` / `could not read Username` / pedido de senha:
**PARE e avise em linguagem simples** — "Seu git do computador não está conectado
ao GitHub. Isso é uma vez só: rode `gh auth login` (ou configure um token). Te
ajudo se quiser." NUNCA travar mudo dentro da skill.
Conflito de rebase → ver a mesma regra do `/salve` (para, avisa, mantém local).

## Passo 2 — Boot: ler os arquivos-raiz que EXISTIREM

Ler, na ordem que o `AGENTS.md` documentar (não cravar a lista de cor):
`SOUL.md` (como ele pensa) → `USER.md` (quem é você) → `MAPA.md` (onde está tudo)
→ `AGENTS.md` (regras). Se existirem `TOOLS.md` / `PROPAGATION.md` / `HEARTBEAT.md`,
ler também. É UM repo só; a única coisa que muda entre Claude e Hermes é o
`CLAUDE.md` — não fazer 2 versões.

## Passo 3 — Navegar o MAPA (carregar o crítico, não tudo)

Usar o `MAPA.md` como gabarito. Abrir:
`memory/context/pendencias.md` (o que está em aberto), `memory/context/business/`
(o negócio), `memory/projects/` (status), `memory/context/decisoes/` do mês atual,
e a **nota do dia mais recente** (`memory/{data}*.md` — pega tanto a `{data}.md`,
reservada ao servidor, quanto a `-local` do PC) pro "onde paramos".
Não ler o cérebro inteiro — só o que dá o quadro de hoje.

## Passo 4 — Pré-flight do tamanho (lint, evita truncar no Hermes)

O Hermes corta silenciosamente arquivos grandes no boot (`MEMORY.md` acima de
~2200 caracteres, `USER.md` acima de ~1375). Esta skill roda no PC e não controla
o boot do Hermes — então **avisa antes**, como um lint:

```bash
for f in MEMORY.md USER.md; do
  [ -f "$CEREBRO/$f" ] && echo "$f: $(wc -c < "$CEREBRO/$f") chars"
done
```

Se `MEMORY.md` > 2200 ou `USER.md` > 1375: avisar — "Seu $f está grande
($N caracteres). No Telegram o agente vai cortar o que passar do limite e você
nem percebe. Vale enxugar pro essencial." (Avisa, não corta sozinho.)

## Passo 5 — Raio-X: devolver o que já sabe

Fechar SEMPRE com o raio-X em linguagem natural — é o que faz você SENTIR o
cérebro ligado (não um log técnico):

```
=== CÉREBRO LIGADO — DD/MM ===
Eu já sei: você é [nome], [negócio em 1 linha do USER/business].
Projetos ativos (N): [lista de 1 linha de memory/projects/].
Última decisão: [a mais recente de context/decisoes/].
Em aberto: [1-2 itens de pendencias.md].
Ainda falta preencher: [pastas/arquivos vazios, se houver].

O que vamos fazer hoje?
```

---

**O que esta skill NÃO faz** (de propósito — simplicidade é a pedagogia):
sem Notion, sem Gmail, sem "dependem de você", sem diff de sessão, sem índice
semântico. Com ~5 arquivos, ler direto basta. Isso vira upsell quando o cérebro
crescer — não agora.
