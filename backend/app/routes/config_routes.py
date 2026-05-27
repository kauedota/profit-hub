from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies.auth_dependency import obter_empresa_id_atual
from app.services.company_config_service import (
    atualizar_configuracoes,
    obter_configuracoes,
)

router = APIRouter(prefix="/configuracoes", tags=["Configurações"])


class ConfiguracaoEntrada(BaseModel):
    nomeEmpresa: str = ""
    impostoPadrao: float = 10
    margemMinima: float = 20


@router.get("")
def rota_obter_configuracoes(
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    return obter_configuracoes(empresa_id=empresa_id)


@router.put("")
def rota_atualizar_configuracoes(
    configuracoes: ConfiguracaoEntrada,
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    return atualizar_configuracoes(
        configuracoes.model_dump(),
        empresa_id=empresa_id,
    )
