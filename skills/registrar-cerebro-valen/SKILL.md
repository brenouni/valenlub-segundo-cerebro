---
name: registrar-cerebro-valen
description: Use ao registrar fatos e decisões no cérebro Valen.
version: 1.0.0
author: GoFluxo
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [valen, segundo-cerebro, git, governanca]
---

# Registrar no Cérebro Valen

Use somente quando Breno, Cléssia ou outro responsável autorizado pedir para guardar, registrar, aprender ou transformar uma rotina confirmada em conhecimento durável.

## Regras

- O repositório é `/home/hermes/valenlub-segundo-cerebro`.
- Leia `MAPA.md` antes de escolher o destino.
- Fato confirmado, hipótese e lacuna nunca podem ser misturados.
- Não grave senha, token, CPF, cartão, dado bancário, extrato bruto ou segredo.
- Não registre informação de outra empresa no cérebro ValenLub.
- Nunca use `git add .`, `git add -A`, `--force`, rebase automático com árvore suja ou resolução automática de conflito.
- Não faça escrita externa, baixa, estorno, pagamento ou contato com cliente.

## Workflow

1. Identifique exatamente o fato, decisão, pendência, pessoa, projeto ou rotina solicitado.
2. Confirme a fonte e rotule o conteúdo como `Registrado`, `Hipótese`, `Lacuna` ou `Decisão humana`.
3. Consulte `MAPA.md` e escolha um único destino principal.
4. Se o destino estiver ambíguo, pergunte antes de escrever.
5. Verifique se o repositório está limpo. Se houver mudanças de outra tarefa, pare e reporte os caminhos.
6. Edite somente os arquivos necessários e mantenha índices relacionados consistentes.
7. Faça varredura dos arquivos alterados por padrões de segredo e dados pessoais.
8. Revise o diff e valide que nenhuma empresa, pessoa ou sistema foi misturado.
9. Adicione ao Git apenas os caminhos escritos nesta execução, explicitamente.
10. Crie um commit curto com prefixo `cerebro:`. Não faça push manual; o `cerebro-sync` fará a sincronização.
11. Informe arquivos, commit e qualquer lacuna restante.

## Destinos

- decisão → `memory/context/decisoes/YYYY-MM.md`
- pendência → `memory/context/pendencias.md`
- empresa/processo durável → `memory/context/business/`
- pessoa/papel → `memory/context/people/`
- prazo da semana → `memory/hot.md`
- projeto → `memory/projects/` e `_index.md`
- rotina repetível → `skills/<nome>/SKILL.md` e `skills/_mapa.md`
- nota operacional do servidor → `memory/YYYY-MM-DD.md`

## Bloqueios

Pare sem escrever quando:

- a informação vier sem fonte ou responsável e estiver sendo apresentada como fato;
- houver credencial ou dado pessoal no conteúdo;
- o repo já estiver sujo por outra execução;
- houver conflito Git;
- a mudança implicar outra empresa do Grupo Valen;
- o pedido envolver ação financeira irreversível.

## Saída

```text
Registrado: <resumo>
Classificação: <fato|hipótese|lacuna|decisão humana>
Arquivos: <paths>
Commit: <hash curto ou bloqueado>
Pendência: <se houver>
```
