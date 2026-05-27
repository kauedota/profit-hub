"""
Schema interno único de pedido.

Todo importador (Mercado Livre, Shopee, UpSeller) traduz o relatório original
para uma lista de PedidoNormalizado. A partir daí o cálculo de lucro é igual
para todos, num único lugar (profit_engine).

Convenção de sinais:
- valor_venda: positivo (receita bruta dos produtos do item)
- taxas_marketplace: positivo, representando CUSTO (comissão + serviço + transação)
- frete_vendedor: positivo, representando CUSTO de frete pago pelo vendedor
- valor_liquido: o líquido que o próprio marketplace informa ter repassado
  (já com taxas e frete descontados). Quando disponível, é a base mais confiável.
"""

from dataclasses import dataclass, field


@dataclass
class PedidoNormalizado:
    marketplace: str = "-"  # "Mercado Livre" | "Shopee" | "UpSeller"
    loja: str = "Sem loja"
    numero_pedido: str = ""  # nº interno/UpSeller quando houver
    pedido_plataforma: str = ""  # nº do pedido na plataforma
    data: str = ""
    sku: str = ""
    id_produto_plataforma: str = ""
    titulo: str = ""
    quantidade: float = 1.0

    valor_venda: float = 0.0
    taxas_marketplace: float = 0.0
    frete_vendedor: float = 0.0
    frete_pago_comprador: float = 0.0
    frete_subsidio_marketplace: float = 0.0
    valor_liquido: float = (
        0.0  # 0 => não informado, engine cai para venda - taxas - frete
    )

    status_marketplace: str = ""
    pedido_multi_sku: bool = False
    cancelado: bool = False

    # detalhamento bruto por marketplace (vai inteiro para a exportação Excel)
    detalhe: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "marketplace": self.marketplace,
            "loja": self.loja,
            "numero_pedido": self.numero_pedido,
            "pedido_plataforma": self.pedido_plataforma,
            "data": self.data,
            "sku": self.sku,
            "id_produto_plataforma": self.id_produto_plataforma,
            "titulo": self.titulo,
            "quantidade": self.quantidade,
            "valor_venda": self.valor_venda,
            "taxas_marketplace": self.taxas_marketplace,
            "frete_vendedor": self.frete_vendedor,
            "frete_pago_comprador": self.frete_pago_comprador,
            "frete_subsidio_marketplace": self.frete_subsidio_marketplace,
            "valor_liquido": self.valor_liquido,
            "status_marketplace": self.status_marketplace,
            "pedido_multi_sku": self.pedido_multi_sku,
            "cancelado": self.cancelado,
            "detalhe": self.detalhe,
        }
