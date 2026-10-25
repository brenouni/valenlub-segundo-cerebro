"""Schemas Hermes — o que o modelo vê."""

CONCILIAR_DIA_VALENLUB = {
    "name": "conciliar_dia_valenlub",
    "description": (
        "Concilia o caixa 4 da ValenLub no dia informado (skill conciliacao-bancaria-valenlub 1.38.2). "
        "Lê o OFX do dia, faz GET read-only em contas-receber e contas-a-pagar na API Query, "
        "aplica as regras (GRAVAR/ARIADNA), em modo simular não grava, em executar só o que a regra fecha "
        "grava no Query (aplicacao/tarifa/resgate/liquidacao), gera o PDF no visual aprovado e "
        "retorna status, contagens, criados, ariadna, pdf_path e mensagem (veredito final). "
        "Ao usuário: envie SÓ o campo mensagem + PDF. Zero narração de passagem. "
        "Use quando chegar OFX/extrato/CSV Cielo do caixa 4."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "data": {
                "type": "string",
                "description": "Dia no formato YYYY-MM-DD (só linhas desse dia entram).",
            },
            "ofx_path": {
                "type": "string",
                "description": "Caminho absoluto do arquivo OFX.",
            },
            "caixa": {
                "type": "integer",
                "description": "Número do caixa. Default 4.",
                "default": 4,
            },
            "pdf_path": {
                "type": "string",
                "description": "Caminho de saída do PDF (opcional).",
            },
            "cielo_csv_path": {
                "type": "string",
                "description": "CSV da Cielo do dia (opcional).",
            },
            "modo": {
                "type": "string",
                "enum": ["simular", "executar"],
                "description": '\"simular\" (não grava no Query) ou \"executar\". Default simular.',
                "default": "simular",
            },
        },
        "required": ["data", "ofx_path"],
    },
}
