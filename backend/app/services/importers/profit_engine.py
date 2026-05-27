"""
Motor de cálculo de lucro real (compartilhado por todos os importadores diretos).

Recebe uma lista de PedidoNormalizado e devolve EXATAMENTE o mesmo contrato que
o frontend já consome hoje: { resumo, pedidos, resumo_por_loja }.

Modelo de cálculo (relatórios diretos):
    receita_liquida = valor_liquido informado pelo marketplace
                      (ou venda - taxas - frete, quando o líquido não vier)
    lucro_antes_imposto = receita_liquida - custo_cadastrado
    imposto             = valor_venda * (percentual / 100)
    lucro_real          = lucro_antes_imposto - imposto

O custo SEMPRE vem do cadastro do Profit Hub. Produto não cadastrado => custo 0,
marcado como não cadastrado, sem inventar valor.
"""


def _carregar_dependencias():
    """
    Importa as funções reais do app de forma preguiçosa, para o módulo poder
    ser testado isoladamente (sem subir o FastAPI/SQLite).
    """
    from app.services.product_storage_service import (
        buscar_produto_por_sku,
        buscar_produto_por_codigo_externo,
    )
    from app.services.importers.kit_utils import (
        interpretar_sku,
        calcular_custo_total_produto,
        obter_componentes_kit,
    )

    return (
        buscar_produto_por_sku,
        buscar_produto_por_codigo_externo,
        interpretar_sku,
        calcular_custo_total_produto,
        obter_componentes_kit,
    )


def calcular_resultado(
    pedidos_normalizados,
    empresa_id=1,
    percentual_imposto=10,
    dependencias=None,
):
    if dependencias is None:
        dependencias = _carregar_dependencias()

    (
        buscar_produto_por_sku,
        buscar_produto_por_codigo_externo,
        interpretar_sku,
        calcular_custo_total_produto,
        obter_componentes_kit,
    ) = dependencias

    perc = float(percentual_imposto or 0)

    pedidos_processados = []
    resumo_por_loja = {}

    acumulado = {
        "total_pedidos": 0,
        "total_vendas_produtos": 0.0,
        "total_taxas_marketplace": 0.0,
        "total_lucro_upseller": 0.0,  # = receita líquida da plataforma
        "total_custo_cadastrado": 0.0,
        "total_lucro_corrigido_antes_imposto": 0.0,
        "total_imposto_simples": 0.0,
        "total_lucro_real": 0.0,
        "total_frete": 0.0,
        "total_frete_vendedor": 0.0,
        "total_frete_pago_comprador": 0.0,
        "total_frete_subsidio_marketplace": 0.0,
        "total_frete_relatorio_original": 0.0,
        "total_reembolso_comprador": 0.0,
        "com_produto": 0,
        "sem_produto": 0,
        "cancelados": 0,
    }

    for indice, pedido in enumerate(pedidos_normalizados):
        sku_original = str(pedido.sku or "").strip().upper()
        if not sku_original:
            continue

        acumulado["total_pedidos"] += 1

        sku_base, quantidade_kit = interpretar_sku(sku_original)

        # quantidade efetiva: a do relatório, ampliada pelo multiplicador de KIT
        quantidade_relatorio = float(pedido.quantidade or 1)
        quantidade_efetiva = quantidade_relatorio * max(quantidade_kit, 1)

        produto = buscar_produto_por_sku(sku_original, empresa_id=empresa_id)
        tipo_busca = "sku_original"
        if not produto:
            produto = buscar_produto_por_sku(sku_base, empresa_id=empresa_id)
            tipo_busca = "sku_base"
        if not produto and pedido.id_produto_plataforma:
            produto = buscar_produto_por_codigo_externo(
                pedido.id_produto_plataforma, empresa_id=empresa_id
            )
            if produto:
                tipo_busca = "codigo_externo"
        if not produto:
            # último recurso: tratar o próprio SKU do relatório como código externo
            produto = buscar_produto_por_codigo_externo(
                sku_original, empresa_id=empresa_id
            )
            if produto:
                tipo_busca = "codigo_externo"

        encontrado = produto is not None

        if encontrado:
            acumulado["com_produto"] += 1
            nome_produto = produto.get("nome") or sku_original
            sku_custo_usado = produto.get("sku") or sku_original
            custo_unitario = float(produto.get("custo") or 0)
            # custo_total considerando kit (multiplicador) e quantidade do relatório
            custo_total = calcular_custo_total_produto(produto, quantidade_kit)
            if quantidade_relatorio > 1:
                custo_total = custo_total * quantidade_relatorio
            componentes_kit = obter_componentes_kit(produto, sku_base, quantidade_kit)
            erro_produto = ""
        else:
            acumulado["sem_produto"] += 1
            nome_produto = pedido.titulo or ""
            sku_custo_usado = ""
            custo_unitario = 0.0
            custo_total = 0.0
            componentes_kit = []
            erro_produto = f"Produto não cadastrado para o SKU {sku_original}"

        valor_venda = float(pedido.valor_venda or 0)
        taxas = float(pedido.taxas_marketplace or 0)
        frete_vendedor_custo = float(pedido.frete_vendedor or 0)  # magnitude positiva

        # receita líquida: usa o líquido do marketplace quando informado
        if pedido.valor_liquido:
            receita_liquida = float(pedido.valor_liquido)
            regra_calculo = (
                f"{pedido.marketplace}: líquido informado pelo marketplace "
                "menos custo cadastrado menos imposto."
            )
        else:
            receita_liquida = valor_venda - taxas - frete_vendedor_custo
            regra_calculo = (
                f"{pedido.marketplace}: venda menos taxas menos frete vendedor "
                "menos custo cadastrado menos imposto."
            )

        if encontrado:
            lucro_antes_imposto = receita_liquida - custo_total
        else:
            # sem custo cadastrado não dá para corrigir; mantém líquido como base
            lucro_antes_imposto = receita_liquida
            regra_calculo += " Custo ausente: produto não cadastrado."

        imposto = valor_venda * (perc / 100)
        lucro_real = lucro_antes_imposto - imposto
        margem_real = (lucro_real / valor_venda * 100) if valor_venda > 0 else 0

        if lucro_real > 0:
            status = "lucro"
        elif lucro_real < 0:
            status = "prejuizo"
        else:
            status = "elas_por_elas"

        # frete_vendedor exibido como NEGATIVO (custo) para nunca parecer ganho
        frete_vendedor_exibicao = -abs(frete_vendedor_custo)

        registro = {
            "linha_excel": indice + 2,
            "pedido": pedido.numero_pedido or pedido.pedido_plataforma,
            "pedido_upseller": pedido.numero_pedido,
            "numero_pedido": pedido.numero_pedido or pedido.pedido_plataforma,
            "pedido_plataforma": pedido.pedido_plataforma,
            "numero_pedido_plataforma": pedido.pedido_plataforma,
            "pedido_marketplace": pedido.pedido_plataforma,
            "data": pedido.data,
            "plataforma": pedido.marketplace,
            "loja": pedido.loja or "Sem loja",
            "sku": sku_original,
            "sku_original": sku_original,
            "sku_exibicao": (produto.get("sku") if encontrado else sku_original),
            "id_produto_plataforma": pedido.id_produto_plataforma,
            "sku_base": sku_base,
            "quantidade_kit": quantidade_kit,
            "quantidade_anuncio": round(quantidade_relatorio, 2),
            "quantidade_efetiva": round(quantidade_efetiva, 2),
            "produto_encontrado": encontrado,
            "tipo_busca_produto": tipo_busca,
            "sku_custo_usado": sku_custo_usado,
            "nome_produto": nome_produto,
            "titulo_anuncio": pedido.titulo,
            "custo_unitario_cadastrado": round(custo_unitario, 2),
            "custo_total_cadastrado": round(custo_total, 2),
            "componentes_kit": componentes_kit,
            "erro_produto": erro_produto,
            "vendas_produtos": round(valor_venda, 2),
            "venda_produtos": round(valor_venda, 2),
            "venda": round(valor_venda, 2),
            "taxas_marketplace": round(taxas, 2),
            "valor_liquido_plataforma": round(receita_liquida, 2),
            # compatibilidade com o frontend atual (card "lucro marketplace")
            "lucro_upseller": round(receita_liquida, 2),
            "custo_produto_upseller": 0.0,
            "taxa_frete": round(frete_vendedor_exibicao, 2),
            "frete": round(frete_vendedor_exibicao, 2),
            "frete_vendedor": round(frete_vendedor_exibicao, 2),
            "frete_pago_comprador": round(float(pedido.frete_pago_comprador or 0), 2),
            "frete_subsidio_marketplace": round(
                float(pedido.frete_subsidio_marketplace or 0), 2
            ),
            "frete_relatorio_original": round(frete_vendedor_exibicao, 2),
            "reembolso_comprador": round(
                float(pedido.detalhe.get("reembolso", 0) or 0), 2
            ),
            "pedido_multi_sku": bool(pedido.pedido_multi_sku),
            "pedido_cancelado": bool(pedido.cancelado),
            "status_marketplace": pedido.status_marketplace,
            "regra_frete": regra_calculo,
            "regra_calculo": regra_calculo,
            "lucro_corrigido_antes_imposto": round(lucro_antes_imposto, 2),
            "imposto_simples": round(imposto, 2),
            "lucro_real": round(lucro_real, 2),
            "margem_real": round(margem_real, 2),
            "status": status,
            "detalhe": pedido.detalhe,
        }

        pedidos_processados.append(registro)

        if pedido.cancelado:
            acumulado["cancelados"] += 1

        acumulado["total_vendas_produtos"] += valor_venda
        acumulado["total_taxas_marketplace"] += taxas
        acumulado["total_lucro_upseller"] += receita_liquida
        acumulado["total_custo_cadastrado"] += custo_total
        acumulado["total_lucro_corrigido_antes_imposto"] += lucro_antes_imposto
        acumulado["total_imposto_simples"] += imposto
        acumulado["total_lucro_real"] += lucro_real
        acumulado["total_frete"] += frete_vendedor_exibicao
        acumulado["total_frete_vendedor"] += frete_vendedor_exibicao
        acumulado["total_frete_pago_comprador"] += float(
            pedido.frete_pago_comprador or 0
        )
        acumulado["total_frete_subsidio_marketplace"] += float(
            pedido.frete_subsidio_marketplace or 0
        )
        acumulado["total_frete_relatorio_original"] += frete_vendedor_exibicao
        acumulado["total_reembolso_comprador"] += float(
            pedido.detalhe.get("reembolso", 0) or 0
        )

        chave = f"{pedido.marketplace}||{pedido.loja or 'Sem loja'}"
        loja = resumo_por_loja.setdefault(
            chave,
            {
                "plataforma": pedido.marketplace,
                "loja": pedido.loja or "Sem loja",
                "total_pedidos": 0,
                "total_vendas_produtos": 0.0,
                "vendas": 0.0,
                "total_lucro_upseller": 0.0,
                "total_taxas_marketplace": 0.0,
                "total_imposto_simples": 0.0,
                "total_imposto": 0.0,
                "total_lucro_real": 0.0,
                "lucro_real": 0.0,
                "total_frete": 0.0,
                "total_frete_vendedor": 0.0,
                "total_frete_pago_comprador": 0.0,
                "total_frete_subsidio_marketplace": 0.0,
                "total_frete_relatorio_original": 0.0,
                "total_reembolso_comprador": 0.0,
                "total_atencao": 0,
            },
        )
        loja["total_pedidos"] += 1
        loja["total_vendas_produtos"] += valor_venda
        loja["vendas"] += valor_venda
        loja["total_lucro_upseller"] += receita_liquida
        loja["total_taxas_marketplace"] += taxas
        loja["total_imposto_simples"] += imposto
        loja["total_imposto"] += imposto
        loja["total_lucro_real"] += lucro_real
        loja["lucro_real"] += lucro_real
        loja["total_frete"] += frete_vendedor_exibicao
        loja["total_frete_vendedor"] += frete_vendedor_exibicao
        loja["total_frete_pago_comprador"] += float(pedido.frete_pago_comprador or 0)
        loja["total_frete_subsidio_marketplace"] += float(
            pedido.frete_subsidio_marketplace or 0
        )
        loja["total_frete_relatorio_original"] += frete_vendedor_exibicao
        loja["total_reembolso_comprador"] += float(
            pedido.detalhe.get("reembolso", 0) or 0
        )

    margem_total = (
        acumulado["total_lucro_real"] / acumulado["total_vendas_produtos"] * 100
        if acumulado["total_vendas_produtos"] > 0
        else 0
    )

    lista_lojas = []
    for loja in resumo_por_loja.values():
        margem_loja = (
            loja["total_lucro_real"] / loja["total_vendas_produtos"] * 100
            if loja["total_vendas_produtos"] > 0
            else 0
        )
        for k in list(loja.keys()):
            if isinstance(loja[k], float):
                loja[k] = round(loja[k], 2)
        loja["margem_real"] = round(margem_loja, 2)
        lista_lojas.append(loja)

    resumo = {
        "empresa_id": empresa_id,
        "total_pedidos": acumulado["total_pedidos"],
        "total_vendas_produtos": round(acumulado["total_vendas_produtos"], 2),
        "total_taxas_marketplace": round(acumulado["total_taxas_marketplace"], 2),
        "total_lucro_upseller": round(acumulado["total_lucro_upseller"], 2),
        "total_custo_produto_upseller": 0.0,
        "total_custo_cadastrado": round(acumulado["total_custo_cadastrado"], 2),
        "total_lucro_corrigido_antes_imposto": round(
            acumulado["total_lucro_corrigido_antes_imposto"], 2
        ),
        "total_imposto_simples": round(acumulado["total_imposto_simples"], 2),
        "total_lucro_real": round(acumulado["total_lucro_real"], 2),
        "total_frete": round(acumulado["total_frete"], 2),
        "total_frete_vendedor": round(acumulado["total_frete_vendedor"], 2),
        "total_frete_pago_comprador": round(acumulado["total_frete_pago_comprador"], 2),
        "total_frete_subsidio_marketplace": round(
            acumulado["total_frete_subsidio_marketplace"], 2
        ),
        "total_frete_relatorio_original": round(
            acumulado["total_frete_relatorio_original"], 2
        ),
        "total_reembolso_comprador": round(acumulado["total_reembolso_comprador"], 2),
        "margem_real": round(margem_total, 2),
        "margem_real_total": round(margem_total, 2),
        "pedidos_com_produto_cadastrado": acumulado["com_produto"],
        "pedidos_sem_produto_cadastrado": acumulado["sem_produto"],
        "total_produtos_nao_cadastrados": acumulado["sem_produto"],
        "total_cancelados": acumulado["cancelados"],
    }

    return {
        "resumo": resumo,
        "pedidos": pedidos_processados,
        "resumo_por_loja": lista_lojas,
    }
