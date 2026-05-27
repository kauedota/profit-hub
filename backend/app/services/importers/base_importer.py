"""
Contrato comum dos importadores.

Cada importador concreto implementa:
- detectar(caminho_arquivo) -> bool        : reconhece se o arquivo é desse marketplace
- extrair_pedidos(caminho_arquivo) -> [PedidoNormalizado]

E herda processar(), que roda o motor de cálculo compartilhado e devolve o
contrato { resumo, pedidos, resumo_por_loja } esperado pelo frontend.
"""

from app.services.importers.profit_engine import calcular_resultado


class BaseImporter:
    nome = "base"
    rotulo = "Base"

    @classmethod
    def detectar(cls, caminho_arquivo):
        raise NotImplementedError

    def extrair_pedidos(self, caminho_arquivo):
        raise NotImplementedError

    def processar(self, caminho_arquivo, empresa_id=1, percentual_imposto=10):
        pedidos = self.extrair_pedidos(caminho_arquivo)
        resultado = calcular_resultado(
            pedidos,
            empresa_id=empresa_id,
            percentual_imposto=percentual_imposto,
        )
        resultado["resumo"]["marketplace_detectado"] = self.rotulo
        resultado["origem"] = self.nome
        return resultado
