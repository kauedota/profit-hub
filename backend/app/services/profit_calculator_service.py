def calcular_lucro_real(
    vendas_produtos: float,
    lucro_upseller: float,
    percentual_imposto: float = 10.0
) -> dict:
    imposto = vendas_produtos * (percentual_imposto / 100)
    lucro_real = lucro_upseller - imposto

    if vendas_produtos > 0:
        margem_real = (lucro_real / vendas_produtos) * 100
    else:
        margem_real = 0

    if lucro_real > 0:
        status = "lucro"
    elif lucro_real < 0:
        status = "prejuizo"
    else:
        status = "elas_por_elas"

    return {
        "vendas_produtos": round(vendas_produtos, 2),
        "lucro_upseller": round(lucro_upseller, 2),
        "percentual_imposto": percentual_imposto,
        "imposto_simples": round(imposto, 2),
        "lucro_real": round(lucro_real, 2),
        "margem_real": round(margem_real, 2),
        "status": status
    }