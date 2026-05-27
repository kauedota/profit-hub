"""
Utilitários de SKU e KIT usados pelo motor de cálculo.

Antes ficavam em excel_import_service (importador UpSeller). Foram extraídos para
cá para que o sistema não dependa mais de nenhum código da UpSeller.
"""

import re

from app.services.sku_service import identificar_sku


def normalizar_sku(sku):
    return str(sku or "").strip().upper()


def interpretar_sku(sku_original):
    """
    Descobre o SKU base e o multiplicador de KIT a partir do SKU do pedido.
    Ex.: "SACO5060-KIT2" -> ("SACO5060", 2).
    """
    sku_original = normalizar_sku(sku_original)
    sku_base = sku_original
    quantidade_kit = 1

    try:
        resultado = identificar_sku(sku_original)

        if isinstance(resultado, dict):
            sku_base = normalizar_sku(
                resultado.get("sku_base")
                or resultado.get("base")
                or resultado.get("sku")
                or sku_original
            )
            quantidade_kit = int(
                resultado.get("quantidade_kit") or resultado.get("quantidade") or 1
            )
            return sku_base, quantidade_kit

        if isinstance(resultado, (list, tuple)) and len(resultado) >= 2:
            return normalizar_sku(resultado[0]), int(resultado[1] or 1)

    except Exception:
        pass

    padrao_kit = re.search(r"(.+)-KIT(\d+)$", sku_original)
    if padrao_kit:
        sku_base = normalizar_sku(padrao_kit.group(1))
        quantidade_kit = int(padrao_kit.group(2))

    return sku_base, quantidade_kit


def obter_componentes_kit(produto, sku_base, quantidade_kit):
    if not produto:
        return []

    componentes = produto.get("componentes") or []
    if componentes:
        return componentes

    if quantidade_kit > 1:
        return [{"sku": sku_base, "quantidade": quantidade_kit}]

    return []


def calcular_custo_total_produto(produto, quantidade_kit):
    if not produto:
        return 0

    custo = float(produto.get("custo") or 0)
    tipo = produto.get("tipo") or "unitario"

    if tipo == "kit_personalizado":
        return custo

    if quantidade_kit > 1:
        return custo * quantidade_kit

    return custo
