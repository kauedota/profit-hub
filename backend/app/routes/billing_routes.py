"""
Rotas de pagamento via Mercado Pago.

Fluxo completo:
  POST /billing/assinar   → cria assinatura no MP, devolve link de checkout
  POST /billing/webhook   → recebe eventos do MP e atualiza o plano da empresa
  POST /billing/cancelar  → cancela assinatura ativa
  GET  /billing/planos    → lista planos disponíveis (para o frontend)
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.dependencies.auth_dependency import obter_empresa_id_atual, obter_usuario_atual
from app.models.user_model import UsuarioModel
from app.services.company_plan_service import PLANOS, PLANO_PADRAO, obter_dados_empresa
from app.services.mp_service import (
    cancelar_assinatura,
    criar_assinatura,
    processar_webhook_mp,
)

router = APIRouter(prefix="/billing", tags=["Pagamento"])

PLANOS_ATIVOS = ["free", "profissional", "avancado"]


class AssinarEntrada(BaseModel):
    plano: str


@router.get("/planos")
def rota_listar_planos():
    """Catálogo de planos para exibir na tela de Minha Conta."""
    return {
        "planos": [
            {
                "id": chave,
                "nome": PLANOS[chave]["nome"],
                "descricao": PLANOS[chave]["descricao"],
                "limite_pedidos_mes": PLANOS[chave]["limite_pedidos_mes"],
                "preco": PLANOS[chave].get("preco", 0),
            }
            for chave in PLANOS_ATIVOS
        ]
    }


@router.post("/assinar")
def rota_assinar(
    dados: AssinarEntrada,
    usuario: UsuarioModel = Depends(obter_usuario_atual),
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    """
    Cria uma assinatura recorrente no Mercado Pago.
    Devolve o link de checkout (init_point) para o frontend redirecionar o usuário.
    """
    empresa = obter_dados_empresa(empresa_id)
    return criar_assinatura(
        empresa_id=empresa_id,
        plano=dados.plano,
        email_usuario=usuario.email,
        nome_empresa=empresa.get("nome", ""),
    )


@router.post("/cancelar")
def rota_cancelar(
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    """Cancela a assinatura ativa da empresa."""
    return cancelar_assinatura(empresa_id=empresa_id)


@router.post("/webhook")
async def rota_webhook_mp(request: Request):
    """
    Recebe eventos do Mercado Pago (preapproval authorized/cancelled/paused).
    O MP chama este endpoint automaticamente quando o status da assinatura muda.
    URL pra configurar no painel do MP: https://<seu-backend>/billing/webhook
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    resultado = processar_webhook_mp(payload)
    # Sempre retorna 200 pro MP (ele reenvia se der erro)
    return {"ok": True, **resultado}
