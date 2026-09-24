---
name: mapear-operacao-valen
description: Use ao mapear processos reais antes de automatizar.
version: 1.0.0
author: GoFluxo
license: Proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [valen, processos, conhecimento, automacao]
---

# Mapear Operação Valen

Use antes de criar painel, rotina, integração, skill ou automação para uma área do Grupo Valen.

## Regra central

Não construir a automação antes de mapear a operação real. Um documento elegante sem fonte, responsável e próximo passo não é um mapa operacional.

## Escopo atual

- Empresa ativa: Valen Lubrificantes.
- Domínio ativo: Financeiro.
- Outras empresas e domínios permanecem separados até autorização explícita.
- Query permanece em leitura e ações financeiras irreversíveis permanecem humanas.

## Workflow

1. Declare empresa, domínio, processo e objetivo.
2. Leia `MAPA.md` e as fontes apontadas por ele; não leia o repositório inteiro sem necessidade.
3. Identifique a fonte de verdade transacional e o responsável humano.
4. Extraia entradas, passos, saídas, horários, exceções, aprovações e evidências.
5. Rotule cada campo:
   - **Registrado:** aparece diretamente em fonte verificada.
   - **Hipótese:** inferência útil ainda não confirmada.
   - **Lacuna:** informação ausente que bloqueia o desenho.
   - **Decisão humana:** escolha aprovada por responsável identificado.
6. Liste sistemas envolvidos e classifique o acesso como leitura, sugestão ou escrita.
7. Identifique pontos irreversíveis e mantenha aprovação humana obrigatória.
8. Proponha somente o menor piloto capaz de provar o processo.
9. Registre o mapa no projeto correspondente usando `registrar-cerebro-valen` após aprovação.
10. Só então proponha skill, integração, cron, webhook ou automação.

## Campos obrigatórios

1. Objetivo
2. Estado atual
3. Responsável
4. Fonte de verdade
5. Entradas
6. Passos reais
7. Saídas
8. Exceções
9. Aprovação humana
10. Evidência e trilha de auditoria
11. Próxima ação
12. Prazo
13. Risco ou bloqueio
14. Último movimento

## Limites

- Não inferir responsável pelo contexto da conversa.
- Não tratar pasta ou documento vazio como processo existente.
- Não importar extratos brutos, credenciais ou dados pessoais ao Git.
- Não misturar ValenLub com outras empresas do grupo.
- Não automatizar escrita no Query, banco, cobrança ou pagamento nesta fase.
- Não criar estrutura ampla quando um único piloto financeiro ainda não foi validado.

## Saída

```markdown
# Mapa — <processo>

Empresa: <empresa>
Domínio: <domínio>
Responsável: <registrado|lacuna> — <nome ou ausência>
Fonte de verdade: <registrado|hipótese|lacuna> — <fonte>

## Processo real
...

## Permissões
- Leitura: ...
- Sugestão: ...
- Escrita bloqueada: ...

## Lacunas
...

## Menor próximo passo
...
```
