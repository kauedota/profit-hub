"""
Importador do relatório DIRETO de Renda (Income) da Shopee.

Arquivo: "Income_..." -> aba "Renda". Cabeçalho na linha 3.

Pegadinha estrutural: cada pedido vem em DUAS linhas:
- Ver = "Order" : traz as finanças (taxas, frete, líquido) e o comprador,
                  porém SKU vem como "-".
- Ver = "Sku"   : traz o SKU e o nome do produto.
Casamos as duas pelo "ID do pedido". As taxas/frete só entram UMA vez por pedido
(na primeira linha de SKU), para não duplicar em pedidos com vários itens.

Colunas relevantes:
- ID do pedido                         -> pedido_plataforma
- SKU / Nome do produto
- Preço do produto                     -> valor_venda
- Quantia total lançada (R$)           -> líquido recebido
- Taxa de comissão líquida             -> custo (negativa)
- Taxa de serviço líquida              -> custo (negativa)
- Taxa de transação                    -> custo (negativa)
- Frete cobrado pelo parceiro logístico + Desconto de frete pela Shopee -> frete líquido
- Taxa de frete paga pelo comprador / Valor do Reembolso / Cupom
"""

import pandas as pd

from app.services.importers.base_importer import BaseImporter
from app.services.importers.column_utils import (
    listar_abas,
    localizar_coluna,
    valor_numero,
    valor_texto,
)
from app.services.importers.normalized_order import PedidoNormalizado

ABA_RENDA = ["Renda", "Income", "Income Details", "Order Income"]


def _ler_aba_renda(caminho_arquivo):
    """Lê a aba de renda detectando a linha de cabeçalho (que tem 'ID do pedido')."""
    abas = listar_abas(caminho_arquivo)
    aba_alvo = None
    for nome in abas:
        if str(nome).strip().lower() in [a.lower() for a in ABA_RENDA]:
            aba_alvo = nome
            break
    if aba_alvo is None:
        aba_alvo = abas[-1] if abas else 0

    bruto = pd.read_excel(
        caminho_arquivo, sheet_name=aba_alvo, header=None, dtype=object
    )

    linha_cab = None
    for i in range(min(8, len(bruto))):
        valores = [valor_texto(v).lower() for v in bruto.iloc[i].tolist()]
        if any("id do pedido" in v for v in valores):
            linha_cab = i
            break
    if linha_cab is None:
        linha_cab = 0

    cabecalho = [
        str(c).strip() if c is not None else "" for c in bruto.iloc[linha_cab].tolist()
    ]
    dados = bruto.iloc[linha_cab + 1 :].copy()
    dados.columns = cabecalho
    dados = dados.loc[:, [c for c in dados.columns if str(c).strip() != ""]]
    dados.reset_index(drop=True, inplace=True)
    return dados


class ShopeeImporter(BaseImporter):
    nome = "shopee"
    rotulo = "Shopee"

    @classmethod
    def detectar(cls, caminho_arquivo):
        abas = [str(a).strip().lower() for a in listar_abas(caminho_arquivo)]
        if any(a in abas for a in ["renda", "income", "service fee details"]):
            return True
        try:
            df = _ler_aba_renda(caminho_arquivo)
            return (
                localizar_coluna(df, ["ID do pedido"]) is not None
                and localizar_coluna(
                    df, ["Quantia total lançada (R$)", "Quantia total lançada"]
                )
                is not None
            )
        except Exception:
            return False

    def extrair_pedidos(self, caminho_arquivo):
        df = _ler_aba_renda(caminho_arquivo)

        c = {
            "ver": localizar_coluna(df, ["Ver"]),
            "pedido": localizar_coluna(df, ["ID do pedido", "Order ID"]),
            "sku": localizar_coluna(df, ["SKU"]),
            "sku_ref": localizar_coluna(
                df,
                [
                    "Número de referência do SKU",
                    "Nº de referência do SKU",
                    "Numero de referencia do SKU",
                    "SKU de referência",
                    "Referência do SKU",
                    "SKU da variação",
                    "SKU da Variação",
                ],
            ),
            "nome": localizar_coluna(df, ["Nome do produto"]),
            "data": localizar_coluna(
                df, ["Data de criação do pedido", "Data de conclusão do pagamento"]
            ),
            "preco": localizar_coluna(df, ["Preço do produto"]),
            "liquido": localizar_coluna(
                df, ["Quantia total lançada (R$)", "Quantia total lançada"]
            ),
            "comissao": localizar_coluna(df, ["Taxa de comissão líquida"]),
            "servico": localizar_coluna(df, ["Taxa de serviço líquida"]),
            "transacao": localizar_coluna(df, ["Taxa de transação"]),
            "frete_parceiro": localizar_coluna(
                df, ["Frete cobrado pelo parceiro logístico"]
            ),
            "desconto_frete": localizar_coluna(df, ["Desconto de frete pela Shopee"]),
            "frete_comprador": localizar_coluna(
                df, ["Taxa de frete paga pelo comprador"]
            ),
            "envio_reverso": localizar_coluna(df, ["Taxa de envio reverso"]),
            "reembolso": localizar_coluna(df, ["Valor do Reembolso"]),
            "cupom": localizar_coluna(df, ["Cupom"]),
            "status": localizar_coluna(df, ["Tipo de pedido"]),
            "transportadora": localizar_coluna(
                df, ["Nome da Transportadora", "Transportadora"]
            ),
        }

        if not c["pedido"]:
            raise ValueError(
                "Não encontrei 'ID do pedido' na aba Renda da Shopee. "
                "Confirme que é o relatório de Renda/Income exportado."
            )

        # Agrupa as linhas por ID do pedido, separando a linha Order das linhas Sku
        grupos = {}
        ordem = []
        for _, linha in df.iterrows():
            pid = valor_texto(linha.get(c["pedido"]))
            if not pid:
                continue
            if pid not in grupos:
                grupos[pid] = {"order": None, "skus": []}
                ordem.append(pid)

            tipo = valor_texto(linha.get(c["ver"])).lower() if c["ver"] else ""
            if tipo == "order":
                grupos[pid]["order"] = linha
            elif tipo == "sku":
                grupos[pid]["skus"].append(linha)
            else:
                # se não houver coluna "Ver", a própria linha serve de tudo
                if valor_texto(linha.get(c["sku"])):
                    grupos[pid]["skus"].append(linha)
                else:
                    grupos[pid]["order"] = linha

        pedidos = []
        for pid in ordem:
            grupo = grupos[pid]
            linha_order = grupo["order"]
            linhas_sku = grupo["skus"] or (
                [linha_order] if linha_order is not None else []
            )

            # fonte das finanças: linha Order quando existir, senão a primeira de SKU
            fin = linha_order if linha_order is not None else linhas_sku[0]

            comissao = abs(valor_numero(fin.get(c["comissao"]))) if c["comissao"] else 0
            servico = abs(valor_numero(fin.get(c["servico"]))) if c["servico"] else 0
            transacao = (
                abs(valor_numero(fin.get(c["transacao"]))) if c["transacao"] else 0
            )
            taxas = comissao + servico + transacao

            frete_parceiro = (
                valor_numero(fin.get(c["frete_parceiro"])) if c["frete_parceiro"] else 0
            )
            desconto_frete = (
                valor_numero(fin.get(c["desconto_frete"])) if c["desconto_frete"] else 0
            )
            frete_comprador = (
                valor_numero(fin.get(c["frete_comprador"]))
                if c["frete_comprador"]
                else 0
            )
            envio_reverso = (
                valor_numero(fin.get(c["envio_reverso"])) if c["envio_reverso"] else 0
            )
            # frete líquido do vendedor = frete do parceiro (negativo)
            #   + desconto da Shopee (positivo) + o que o comprador pagou (positivo)
            #   + frete reverso de devolução (negativo, quando houver).
            # Na prática, na maioria dos pedidos isso zera (o vendedor não paga frete).
            frete_liquido = (
                frete_parceiro + desconto_frete + frete_comprador + envio_reverso
            )
            frete_vendedor = abs(min(frete_liquido, 0))

            reembolso = valor_numero(fin.get(c["reembolso"])) if c["reembolso"] else 0
            liquido = valor_numero(fin.get(c["liquido"])) if c["liquido"] else 0

            multi = len(linhas_sku) > 1

            status_txt = valor_texto(fin.get(c["status"])) if c["status"] else ""
            cancelado = abs(reembolso) > 0.01 or any(
                k in status_txt.lower()
                for k in ["cancel", "devol", "reembol", "não pago", "nao pago"]
            )

            for idx, ls in enumerate(linhas_sku):
                primeiro = idx == 0
                id_produto = valor_texto(
                    ls.get(c["sku"])
                )  # nesse relatório é o ID do produto
                sku_ref = valor_texto(ls.get(c["sku_ref"])) if c["sku_ref"] else ""
                sku_final = sku_ref or id_produto  # usa o SKU de texto se existir
                pedidos.append(
                    PedidoNormalizado(
                        marketplace="Shopee",
                        loja="Shopee",
                        pedido_plataforma=pid,
                        numero_pedido=pid,
                        data=valor_texto(fin.get(c["data"])) if c["data"] else "",
                        sku=sku_final,
                        id_produto_plataforma=id_produto,
                        titulo=valor_texto(ls.get(c["nome"])),
                        quantidade=1,
                        valor_venda=(
                            valor_numero(ls.get(c["preco"])) if c["preco"] else 0
                        ),
                        # taxas/frete/líquido só na primeira linha do pedido (evita duplicar)
                        taxas_marketplace=taxas if primeiro else 0,
                        frete_vendedor=frete_vendedor if primeiro else 0,
                        frete_pago_comprador=frete_comprador if primeiro else 0,
                        frete_subsidio_marketplace=desconto_frete if primeiro else 0,
                        valor_liquido=liquido if primeiro else 0,
                        status_marketplace=status_txt,
                        pedido_multi_sku=multi,
                        cancelado=cancelado,
                        detalhe={
                            "comissao": comissao if primeiro else 0,
                            "taxa_servico": servico if primeiro else 0,
                            "taxa_transacao": transacao if primeiro else 0,
                            "frete_parceiro": frete_parceiro if primeiro else 0,
                            "desconto_frete_shopee": desconto_frete if primeiro else 0,
                            "frete_pago_comprador": frete_comprador if primeiro else 0,
                            "reembolso": reembolso if primeiro else 0,
                            "cupom": (
                                valor_numero(fin.get(c["cupom"]))
                                if c["cupom"] and primeiro
                                else 0
                            ),
                            "quantia_total_lancada": liquido if primeiro else 0,
                            "transportadora": (
                                valor_texto(fin.get(c["transportadora"]))
                                if c["transportadora"]
                                else ""
                            ),
                        },
                    )
                )

        return pedidos
