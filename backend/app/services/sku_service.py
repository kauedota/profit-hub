import re


def identificar_sku(sku: str) -> dict:
    """
    Identifica se o SKU é unitário ou kit automático.

    Exemplos:
    LE885C -> produto_unitario
    LE885C-KIT2 -> kit_automatico com quantidade 2
    LE885C-KIT3 -> kit_automatico com quantidade 3
    """

    if not sku:
        return {
            "sku_original": sku,
            "tipo": "sku_invalido",
            "sku_base": None,
            "quantidade": 0
        }

    sku_limpo = sku.strip().upper()

    padrao_kit = r"^(.+)-KIT(\d+)$"
    resultado = re.match(padrao_kit, sku_limpo)

    if resultado:
        sku_base = resultado.group(1)
        quantidade = int(resultado.group(2))

        return {
            "sku_original": sku_limpo,
            "tipo": "kit_automatico",
            "sku_base": sku_base,
            "quantidade": quantidade
        }

    return {
        "sku_original": sku_limpo,
        "tipo": "produto_unitario",
        "sku_base": sku_limpo,
        "quantidade": 1
    }