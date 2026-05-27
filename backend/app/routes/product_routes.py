import tempfile
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.dependencies.auth_dependency import obter_empresa_id_atual
from app.services.product_storage_service import (
    atualizar_produto,
    buscar_produto_por_sku,
    cadastrar_produto,
    excluir_produto,
    gerar_modelo_importacao_produtos,
    importar_mapa_shopee,
    importar_produtos_excel,
    listar_produtos,
)

router = APIRouter(prefix="/produtos", tags=["Produtos"])


class ComponenteEntrada(BaseModel):
    sku: str
    quantidade: float = 1


class ProdutoEntrada(BaseModel):
    sku: str
    nome: str
    custo: float = 0
    imposto: float = 0
    tipo: str = "unitario"
    frete_gratis: float = 0
    observacao: str = ""
    componentes: Optional[List[ComponenteEntrada]] = []
    codigosExternos: str = ""


@router.get("")
def rota_listar_produtos(
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    return listar_produtos(empresa_id=empresa_id)


@router.post("")
def rota_cadastrar_produto(
    produto: ProdutoEntrada,
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    try:
        return cadastrar_produto(
            produto.model_dump(),
            empresa_id=empresa_id,
        )

    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@router.put("/{produto_id}")
def rota_atualizar_produto(
    produto_id: int,
    produto: ProdutoEntrada,
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    try:
        return atualizar_produto(
            produto_id,
            produto.model_dump(),
            empresa_id=empresa_id,
        )

    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@router.delete("/{produto_id}")
def rota_excluir_produto(
    produto_id: int,
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    try:
        return excluir_produto(
            produto_id,
            empresa_id=empresa_id,
        )

    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@router.get("/buscar/{sku}")
def rota_buscar_produto(
    sku: str,
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    produto = buscar_produto_por_sku(sku, empresa_id=empresa_id)

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    return produto


@router.get("/modelo-importacao")
def rota_baixar_modelo_importacao():
    arquivo = gerar_modelo_importacao_produtos()

    return StreamingResponse(
        arquivo,
        media_type=(
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                "attachment; filename=modelo_importacao_produtos_profit_hub.xlsx"
            )
        },
    )


@router.post("/importar-excel")
async def rota_importar_produtos_excel(
    arquivo: UploadFile = File(...),
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp:
            conteudo = await arquivo.read()
            temp.write(conteudo)
            caminho_temp = temp.name

        return importar_produtos_excel(
            caminho_temp,
            empresa_id=empresa_id,
        )

    except Exception as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@router.post("/importar-mapa-shopee")
async def rota_importar_mapa_shopee(
    arquivo: UploadFile = File(...),
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    """Importa a planilha da Shopee (mass_update_basic_info) que liga ID do Produto ao SKU."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp:
            conteudo = await arquivo.read()
            temp.write(conteudo)
            caminho_temp = temp.name

        return importar_mapa_shopee(
            caminho_temp,
            empresa_id=empresa_id,
        )

    except Exception as erro:
        raise HTTPException(status_code=400, detail=str(erro))
