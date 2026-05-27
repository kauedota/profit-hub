"""
Importador do relatório DIRETO de Vendas do Mercado Livre.

Arquivo: "Vendas BR" (Vendas -> Exportar para Excel).
O cabeçalho real fica na linha 6 (as 5 primeiras são banner/título).

Colunas relevantes:
- N.º de venda                         -> pedido_plataforma
- Data da venda                        -> data
- Estado / Descrição do status         -> status
- Unidades                             -> quantidade
- Receita por produtos (BRL)           -> valor_venda
- Tarifa de venda e impostos (BRL)     -> comissão ML (negativa => custo)
- Tarifas de envio (BRL)               -> frete vendedor (negativa => custo)
- Total (BRL)                          -> líquido já com taxas e frete descontados
- SKU / Canal de venda / Loja oficial / Título do anúncio
"""

from app.services.importers.base_importer import BaseImporter
from app.services.importers.column_utils import (
    ler_excel_detectando_cabecalho,
    listar_abas,
    localizar_coluna,
    valor_numero,
    valor_texto,
)
from app.services.importers.normalized_order import PedidoNormalizado

MARCADORES_CABECALHO = ["N.º de venda", "Tarifa de venda e impostos", "Receita por produtos"]


class MercadoLivreImporter(BaseImporter):
    nome = "mercado_livre"
    rotulo = "Mercado Livre"

    @classmethod
    def detectar(cls, caminho_arquivo):
        abas = [str(a).lower() for a in listar_abas(caminho_arquivo)]
        if any("vendas" in a for a in abas):
            try:
                df = ler_excel_detectando_cabecalho(
                    caminho_arquivo, marcadores_cabecalho=MARCADORES_CABECALHO
                )
                return localizar_coluna(df, ["N.º de venda", "Numero de venda"]) is not None
            except Exception:
                return False
        return False

    def extrair_pedidos(self, caminho_arquivo):
        df = ler_excel_detectando_cabecalho(
            caminho_arquivo, marcadores_cabecalho=MARCADORES_CABECALHO
        )

        col = {
            "pedido": localizar_coluna(df, ["N.º de venda", "Numero de venda", "Nº de venda"]),
            "data": localizar_coluna(df, ["Data da venda"]),
            "status": localizar_coluna(df, ["Estado", "Descrição do status"]),
            "unidades": localizar_coluna(df, ["Unidades"]),
            "venda": localizar_coluna(
                df, ["Receita por produtos (BRL)", "Receita por produtos"]
            ),
            "tarifa": localizar_coluna(
                df, ["Tarifa de venda e impostos (BRL)", "Tarifa de venda e impostos"]
            ),
            "frete": localizar_coluna(
                df, ["Tarifas de envio (BRL)", "Tarifas de envio"]
            ),
            "total": localizar_coluna(df, ["Total (BRL)", "Total"]),
            "sku": localizar_coluna(df, ["SKU", "Código SKU"]),
            "canal": localizar_coluna(df, ["Canal de venda", "Plataforma"]),
            "loja": localizar_coluna(df, ["Loja oficial", "Loja"]),
            "titulo": localizar_coluna(df, ["Título do anúncio", "Titulo do anuncio"]),
            "preco_unit": localizar_coluna(
                df, ["Preço unitário de venda do anúncio (BRL)"]
            ),
            "receita_envio": localizar_coluna(df, ["Receita por envio (BRL)"]),
            "cancel": localizar_coluna(df, ["Cancelamentos e reembolsos (BRL)"]),
        }

        if not col["sku"]:
            raise ValueError(
                "Não encontrei a coluna SKU no relatório do Mercado Livre. "
                "Confirme que é o relatório de Vendas exportado para Excel."
            )

        pedidos = []
        for _, linha in df.iterrows():
            sku = valor_texto(linha.get(col["sku"]))
            if not sku:
                continue

            venda = valor_numero(linha.get(col["venda"])) if col["venda"] else 0
            tarifa = abs(valor_numero(linha.get(col["tarifa"]))) if col["tarifa"] else 0
            total = valor_numero(linha.get(col["total"])) if col["total"] else 0
            receita_envio = (
                valor_numero(linha.get(col["receita_envio"])) if col["receita_envio"] else 0
            )
            # frete bruto cobrado (negativo) + o que o comprador pagou (positivo)
            # => custo REAL de frete do vendedor (ex.: -42,54 + 33,99 = -8,55)
            tarifas_envio = valor_numero(linha.get(col["frete"])) if col["frete"] else 0
            frete_liquido = tarifas_envio + receita_envio
            frete = abs(min(frete_liquido, 0))

            status_txt = valor_texto(linha.get(col["status"]))
            cancelado = any(
                k in status_txt.lower()
                for k in ["cancel", "devolv", "não concret", "nao concret"]
            )

            pedido = PedidoNormalizado(
                marketplace="Mercado Livre",
                loja=valor_texto(linha.get(col["loja"])) or "Sem loja",
                pedido_plataforma=valor_texto(linha.get(col["pedido"])),
                numero_pedido=valor_texto(linha.get(col["pedido"])),
                data=valor_texto(linha.get(col["data"])),
                sku=sku,
                titulo=valor_texto(linha.get(col["titulo"])),
                quantidade=valor_numero(linha.get(col["unidades"])) or 1,
                valor_venda=venda,
                taxas_marketplace=tarifa,
                frete_vendedor=frete,
                frete_pago_comprador=receita_envio,
                frete_subsidio_marketplace=0,
                valor_liquido=total,
                status_marketplace=status_txt,
                cancelado=cancelado,
                detalhe={
                    "tarifa_venda_e_impostos": valor_numero(linha.get(col["tarifa"]))
                    if col["tarifa"]
                    else 0,
                    "tarifas_de_envio": valor_numero(linha.get(col["frete"]))
                    if col["frete"]
                    else 0,
                    "receita_por_envio": receita_envio,
                    "cancelamentos_reembolsos": valor_numero(linha.get(col["cancel"]))
                    if col["cancel"]
                    else 0,
                    "total_brl": total,
                    "canal_venda": valor_texto(linha.get(col["canal"])),
                },
            )
            pedidos.append(pedido)

        return pedidos
