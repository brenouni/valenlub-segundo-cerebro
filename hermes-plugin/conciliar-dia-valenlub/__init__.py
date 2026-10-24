"""Plugin Hermes — conciliar_dia_valenlub (ValenLub caixa 4)."""
from __future__ import annotations

import logging

from . import schemas, tools

logger = logging.getLogger(__name__)


def register(ctx):
    """Registra a tool no Hermes."""
    ctx.register_tool(
        name="conciliar_dia_valenlub",
        toolset="valenlub",
        schema=schemas.CONCILIAR_DIA_VALENLUB,
        handler=tools.conciliar_dia_valenlub,
    )
    logger.info("Tool conciliar_dia_valenlub registrada (ValenLub caixa 4).")
