"""
Rotas de pagamento / assinatura.

Estrutura PREPARADA para integrar Mercado Pago ou Stripe no futuro, mas ainda
SEM cobrança real:
- POST /billing/upgrade  : troca o plano da empresa (uso interno/admin por enquanto).
- POST /billing/webhook  : endpoint pronto para receber eventos do gateway depois.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.database import SessionLocal, criar_tabelas
from app.dependencies.auth_dependency import obter_empresa_id_atual
from app.models.company_model import EmpresaModel
from app.services.company_plan_service import (
    PLANOS,
    atualizar_plano_empresa,
    obter_dados_empresa,
)

router = APIRouter(prefix="/billing", tags=["Pagamento"])


class UpgradeEntrada(BaseModel):
    plano: str


@router.get("/planos")
def rota_listar_planos():
    """Catálogo de planos disponíveis (para a tela de upgrade)."""
    return {
        "planos": [
            {
                "id": chave,
                "nome": dados["nome"],
                "descricao": dados["descricao"],
                "limite_pedidos_mes": dados["limite_pedidos_mes"],
            }
            for chave, dados in PLANOS.items()
        ]
    }


@router.post("/upgrade")
def rota_upgrade_plano(
    dados: UpgradeEntrada,
    empresa_id: int = Depends(obter_empresa_id_atual),
):
    """
    Troca o plano da empresa. Por enquanto sem pagamento real — quando o gateway
    estiver integrado, este passo virá depois da confirmação do pagamento.
    """
    empresa = atualizar_plano_empresa(
        empresa_id=empresa_id,
        plano=dados.plano,
        status_empresa="ativo",
    )
    return {
        "mensagem": "Plano atualizado com sucesso.",
        "empresa": empresa,
    }


@router.post("/webhook")
async def rota_webhook_pagamento(payload: dict):
    """
    Endpoint preparado para receber eventos do gateway (Mercado Pago / Stripe).

    Hoje apenas registra e reconhece o evento. Quando a integração for feita, aqui
    a gente vai: validar a assinatura do webhook, identificar a empresa pelo
    assinatura_id e atualizar assinatura_status / data_vencimento / plano.
    """
    criar_tabelas()

    evento = payload.get("type") or payload.get("action") or "desconhecido"
    assinatura_id = (
        payload.get("assinatura_id")
        or payload.get("subscription_id")
        or (payload.get("data") or {}).get("id")
    )

    atualizado = False

    if assinatura_id:
        db = SessionLocal()
        try:
            empresa = (
                db.query(EmpresaModel)
                .filter(EmpresaModel.assinatura_id == str(assinatura_id))
                .first()
            )
            if empresa:
                status_evento = str(payload.get("status") or "").lower()
                if status_evento in ("authorized", "approved", "active", "ativa"):
                    empresa.assinatura_status = "ativa"
                    empresa.status = "ativo"
                    empresa.data_vencimento = datetime.utcnow() + timedelta(days=30)
                    atualizado = True
                elif status_evento in ("cancelled", "canceled", "cancelada"):
                    empresa.assinatura_status = "cancelada"
                    atualizado = True
                db.commit()
        finally:
            db.close()

    return {"recebido": True, "evento": evento, "empresa_atualizada": atualizado}
