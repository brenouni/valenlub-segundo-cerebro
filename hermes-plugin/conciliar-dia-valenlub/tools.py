"""Handlers Hermes — chama a função do cérebro."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _brain_root(ctx=None) -> Path:
    if ctx is not None:
        try:
            configured = ctx.get_config("brain_root", default="")
            if configured:
                return Path(configured)
        except Exception:
            pass
    env = os.environ.get("VALENLUB_BRAIN") or os.environ.get("HERMES_VALENLUB_BRAIN")
    if env:
        return Path(env)
    candidates = [
        Path("/home/hermes/valenlub-segundo-cerebro"),
        Path.home() / "valenlub-segundo-cerebro",
        Path(__file__).resolve().parents[2],  # repo root when plugin lives in hermes-plugin/
    ]
    for c in candidates:
        if (c / "tools" / "conciliar_dia_valenlub.py").is_file():
            return c
    return candidates[0]


def _load_fn():
    root = _brain_root()
    tools_dir = root / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from conciliar_dia_valenlub import conciliar_dia_valenlub  # type: ignore

    return conciliar_dia_valenlub, root


def conciliar_dia_valenlub(args: dict, **kwargs) -> str:
    """Handler Hermes. Sempre retorna JSON string."""
    del kwargs
    try:
        fn, _root = _load_fn()
        res = fn(
            data=str(args.get("data") or ""),
            ofx_path=str(args.get("ofx_path") or ""),
            caixa=int(args.get("caixa") or 4),
            pdf_path=args.get("pdf_path") or None,
            cielo_csv_path=args.get("cielo_csv_path") or None,
            modo=str(args.get("modo") or "simular"),
        )
        payload = res.to_dict() if hasattr(res, "to_dict") else res
        return json.dumps(payload, ensure_ascii=False, default=str)
    except Exception as exc:  # noqa: BLE001
        return json.dumps(
            {"success": False, "error": str(exc), "status": "erro"},
            ensure_ascii=False,
        )
