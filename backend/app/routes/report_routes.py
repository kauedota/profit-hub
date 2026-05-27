from fastapi import APIRouter, Depends

from app.dependencies.auth_dependency import obter_empresa_id_atual
from app.services.profit_calculator_service import calcular_lucro_real

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/calcular-lucro-real")
def rota_calcular_lucro_real(
    vendas_produtos: float,
    lucro_marketplace: float,
    percentual_imposto: float = 10.0,
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    return calcular_lucro_real(
        vendas_produtos=vendas_produtos,
        lucro_upseller=lucro_marketplace,
        percentual_imposto=percentual_imposto,
    )
