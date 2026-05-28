"""
Rotas de integração com a API do Mercado Livre.

GET  /ml/connect      → retorna a URL de autorização OAuth para o frontend redirecionar
GET  /ml/callback     → recebe o código do ML, troca por token, redireciona pro frontend
GET  /ml/status       → retorna se a conta ML está conectada e o último sync
POST /ml/sync         → sincroniza pedidos do período escolhido
DELETE /ml/desconectar → remove os tokens salvos
"""

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.database import SessionLocal, criar_tabelas
from app.dependencies.auth_dependency import obter_empresa_id_atual
from app.models.company_model import EmpresaModel
from app.services.company_plan_service import validar_limite_pedidos
from app.services.importers.profit_engine import calcular_resultado
from app.services.ml_api_service import (
    buscar_pedidos_api,
    desconectar_ml,
    gerar_url_oauth,
    normalizar_pedidos_api,
    trocar_codigo_por_token,
)

router = APIRouter(prefix="/ml", tags=["Mercado Livre"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://profit-hub-mauve.vercel.app")


class SyncEntrada(BaseModel):
    data_inicio: str  # "YYYY-MM-DD"
    data_fim: str  # "YYYY-MM-DD"
    percentual_imposto: float = 10.0


@router.get("/connect")
def rota_connect(empresa_id: int = Depends(obter_empresa_id_atual)):
    """Devolve a URL de autorização OAuth do Mercado Livre."""
    url = gerar_url_oauth(empresa_id)
    return {"url": url}


@router.get("/callback")
def rota_callback(code: str = "", state: str = "", error: str = ""):
    """
    Recebe o código de autorização do Mercado Livre após o usuário autorizar.
    state = empresa_id (passado na URL de autorização).
    Após salvar os tokens, redireciona de volta pro frontend.
    """
    if error or not code:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/minha-conta?ml=erro&motivo={error or 'cancelado'}"
        )

    try:
        empresa_id = int(state)
        trocar_codigo_por_token(code=code, empresa_id=empresa_id)
        return RedirectResponse(url=f"{FRONTEND_URL}/minha-conta?ml=conectado")
    except Exception as e:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/minha-conta?ml=erro&motivo={str(e)[:60]}"
        )


@router.get("/status")
def rota_status(empresa_id: int = Depends(obter_empresa_id_atual)):
    """Retorna o status da conexão com o Mercado Livre."""
    criar_tabelas()
    db = SessionLocal()
    try:
        emp = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
        if not emp:
            return {"conectado": False}

        conectado = bool(emp.ml_access_token and emp.ml_seller_id)
        token_ok = (
            (
                emp.ml_token_expiry is not None
                and datetime.utcnow() < emp.ml_token_expiry
            )
            if conectado
            else False
        )

        return {
            "conectado": conectado,
            "seller_id": emp.ml_seller_id or "",
            "token_valido": token_ok,
            "token_expira_em": (
                emp.ml_token_expiry.isoformat() if emp.ml_token_expiry else None
            ),
            "ultimo_sync": (
                emp.ml_ultimo_sync.isoformat() if emp.ml_ultimo_sync else None
            ),
        }
    finally:
        db.close()


@router.post("/sync")
def rota_sync(
    dados: SyncEntrada,
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    """
    Sincroniza pedidos do Mercado Livre para o período informado.
    Retorna o mesmo formato {resumo, pedidos, resumo_por_loja} que o upload de relatório.
    """
    orders = buscar_pedidos_api(
        empresa_id=empresa_id,
        data_inicio=dados.data_inicio,
        data_fim=dados.data_fim,
    )

    pedidos = normalizar_pedidos_api(orders)

    # Valida o limite do plano antes de processar
    validar_limite_pedidos(empresa_id=empresa_id, total_pedidos=len(pedidos))

    resultado = calcular_resultado(
        pedidos,
        empresa_id=empresa_id,
        percentual_imposto=dados.percentual_imposto,
    )
    resultado["resumo"]["marketplace_detectado"] = "Mercado Livre (API)"
    resultado["origem"] = "mercado_livre_api"
    resultado["total_orders_api"] = len(orders)

    return resultado


@router.delete("/desconectar")
def rota_desconectar(empresa_id: int = Depends(obter_empresa_id_atual)):
    """Remove os tokens do Mercado Livre salvos na empresa."""
    desconectar_ml(empresa_id=empresa_id)
    return {"mensagem": "Conta do Mercado Livre desconectada."}
