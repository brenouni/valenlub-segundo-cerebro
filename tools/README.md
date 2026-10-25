# Tools — ValenLub

## `conciliar_dia_valenlub`

Conciliação do caixa 4 (skill `conciliacao-bancaria-valenlub` 1.38.2).

```bash
# na raiz do cérebro
python3 tools/conciliar_dia_valenlub.py \
  --data 2026-10-21 \
  --ofx /caminho/extrato.ofx \
  --modo simular
```

Env: `QUERY_TENANT`, `QUERY_TOKEN` (ou `QUERY_USER`/`QUERY_PASS`), opcional `QUERY_API_BASE`.

## Registrar no Hermes

Cópia ou symlink do plugin:

```bash
mkdir -p ~/.hermes/plugins
ln -sfn /home/hermes/valenlub-segundo-cerebro/hermes-plugin/conciliar-dia-valenlub \
  ~/.hermes/plugins/conciliar-dia-valenlub
hermes plugins enable conciliar-dia-valenlub
# reinicie o Hermes / gateway
```

Configure `plugins.entries.conciliar-dia-valenlub.settings.brain_root` se o cérebro não estiver em `/home/hermes/valenlub-segundo-cerebro`.

Alternativa: dropar `tools/conciliar_dia_valenlub.py` no `tools/` do Hermes (há `registry.register` opcional com try/except).
