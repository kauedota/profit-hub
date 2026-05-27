import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.dependencies.auth_dependency import obter_empresa_id_atual
from app.services.company_plan_service import validar_limite_pedidos
from app.services.importers.importer_factory import (
    marketplaces_disponiveis,
    obter_importador,
)
from app.services.importers.profit_engine import calcular_resultado

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.get("/marketplaces")
def listar_marketplaces():
    """Opções para o seletor de marketplace no frontend."""
    return {"marketplaces": marketplaces_disponiveis()}


@router.post("/pedidos")
async def upload_pedidos(
    arquivo: UploadFile = File(...),
    percentual_imposto: float = Form(10),
    marketplace: str = Form("auto"),
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    """
    Importa um relatório DIRETO de marketplace.

    marketplace: "auto" (detecta), "mercado_livre" ou "shopee".
    O limite do plano é validado ANTES do processamento pesado.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp:
            conteudo = await arquivo.read()
            temp.write(conteudo)
            caminho_temp = temp.name

        # 1) identifica o marketplace e lê os pedidos (leitura leve, sem banco)
        importador = obter_importador(caminho_temp, marketplace=marketplace)
        pedidos = importador.extrair_pedidos(caminho_temp)

        # 2) valida o limite do plano ANTES de cruzar com o cadastro (evita trabalho à toa)
        validar_limite_pedidos(
            empresa_id=empresa_id,
            total_pedidos=len(pedidos),
        )

        # 3) calcula o lucro real cruzando com os produtos cadastrados
        resultado = calcular_resultado(
            pedidos,
            empresa_id=empresa_id,
            percentual_imposto=percentual_imposto,
        )
        resultado["resumo"]["marketplace_detectado"] = importador.rotulo
        resultado["origem"] = importador.nome

        return resultado

    except HTTPException:
        raise

    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))

    except Exception as erro:
        raise HTTPException(status_code=400, detail=str(erro))
