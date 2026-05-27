"""
Fábrica de importadores.

Trabalha apenas com relatórios DIRETOS dos marketplaces:
1. Escolha manual (Mercado Livre / Shopee), ou
2. Detecção automática (Mercado Livre -> Shopee).
Se a detecção automática falhar, pede para o usuário escolher manualmente.
"""

from app.services.importers.mercado_livre_importer import MercadoLivreImporter
from app.services.importers.shopee_importer import ShopeeImporter

IMPORTADORES = [MercadoLivreImporter, ShopeeImporter]

_POR_NOME = {
    "mercado_livre": MercadoLivreImporter,
    "mercadolivre": MercadoLivreImporter,
    "ml": MercadoLivreImporter,
    "shopee": ShopeeImporter,
}


def marketplaces_disponiveis():
    """Opções do seletor de marketplace no frontend."""
    return [
        {"valor": "auto", "rotulo": "Detectar automaticamente"},
        {"valor": "mercado_livre", "rotulo": "Mercado Livre"},
        {"valor": "shopee", "rotulo": "Shopee"},
    ]


def obter_importador(caminho_arquivo, marketplace=None):
    """
    Devolve a instância do importador adequado.

    marketplace: None/"auto" => detecção automática; ou "mercado_livre"/"shopee".
    Lança ValueError com mensagem clara quando não conseguir identificar.
    """
    chave = (marketplace or "auto").strip().lower()

    if chave and chave != "auto":
        classe = _POR_NOME.get(chave)
        if not classe:
            raise ValueError(
                "Marketplace inválido. Selecione Mercado Livre ou Shopee."
            )
        return classe()

    for classe in IMPORTADORES:
        try:
            if classe.detectar(caminho_arquivo):
                return classe()
        except Exception:
            continue

    raise ValueError(
        "Não consegui identificar automaticamente o marketplace deste relatório. "
        "Selecione manualmente Mercado Livre ou Shopee e tente de novo."
    )


def processar_relatorio(caminho_arquivo, marketplace=None, empresa_id=1, percentual_imposto=10):
    """Escolhe o importador e processa, devolvendo { resumo, pedidos, resumo_por_loja }."""
    importador = obter_importador(caminho_arquivo, marketplace=marketplace)
    return importador.processar(
        caminho_arquivo,
        empresa_id=empresa_id,
        percentual_imposto=percentual_imposto,
    )
