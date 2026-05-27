from fastapi import APIRouter, Depends

from app.dependencies.auth_dependency import obter_empresa_id_atual, obter_usuario_atual
from app.models.user_model import UsuarioModel
from app.services.company_plan_service import obter_dados_empresa

router = APIRouter(prefix="/minha-conta", tags=["Minha Conta"])


@router.get("")
def rota_minha_conta(
    usuario: UsuarioModel = Depends(obter_usuario_atual),
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    empresa = obter_dados_empresa(empresa_id)

    return {
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "perfil": usuario.perfil,
            "ativo": usuario.ativo,
        },
        "empresa": empresa,
    }
