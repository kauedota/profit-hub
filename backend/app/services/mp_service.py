"""
Integração com a API de Assinaturas do Mercado Pago.

Fluxo:
1. Cliente clica "Assinar" na tela Minha Conta.
2. Backend cria uma "preapproval" (assinatura) via API do MP.
3. MP devolve um init_point (URL de checkout).
4. Cliente é redirecionado pro checkout do MP → paga.
5. MP chama o webhook com o status atualizado.
6. Backend recebe o webhook e atualiza o plano da empresa.
"""

import os
from datetime import datetime, timedelta

import requests
from fastapi import HTTPException, status

from app.database import SessionLocal, criar_tabelas
from app.models.company_model import EmpresaModel
from app.services.company_plan_service import PLANOS, PLANO_PADRAO

MP_BASE = "https://api.mercadopago.com"


def _token():
    token = os.getenv("MP_ACCESS_TOKEN", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pagamento não configurado. Tente novamente em instantes.",
        )
    return token


def _headers():
    return {
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
    }


def criar_assinatura(
    empresa_id: int, plano: str, email_usuario: str, nome_empresa: str
):
    """
    Cria uma assinatura recorrente no Mercado Pago e devolve o link de checkout.
    O cliente paga mensalmente via cartão, Pix ou boleto.
    """
    if plano not in PLANOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plano inválido.",
        )

    dados_plano = PLANOS[plano]
    preco = dados_plano.get("preco", 0)

    if preco == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plano Free não requer assinatura.",
        )

    base_url = os.getenv("FRONTEND_URL", "https://profit-hub-mauve.vercel.app")

    corpo = {
        "reason": f"Profit Hub — {dados_plano['nome']}",
        "external_reference": str(empresa_id),
        "payer_email": email_usuario,
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": preco,
            "currency_id": "BRL",
        },
        "back_url": f"{base_url}/minha-conta?assinatura=processando",
        "status": "pending",
    }

    resposta = requests.post(
        f"{MP_BASE}/preapproval",
        json=corpo,
        headers=_headers(),
        timeout=15,
    )

    if not resposta.ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Mercado Pago retornou erro: {resposta.text[:200]}",
        )

    dados = resposta.json()
    init_point = dados.get("init_point")
    preapproval_id = dados.get("id")

    if not init_point:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Mercado Pago não retornou o link de pagamento.",
        )

    # Salva o ID da assinatura na empresa para rastrear pelo webhook
    criar_tabelas()
    db = SessionLocal()
    try:
        empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
        if empresa:
            empresa.assinatura_id = preapproval_id
            empresa.gateway_pagamento = "mercado_pago"
            empresa.assinatura_status = "pendente"
            db.commit()
    finally:
        db.close()

    return {"init_point": init_point, "assinatura_id": preapproval_id}


def _plano_por_valor(valor: float) -> str:
    """Descobre qual plano corresponde ao valor cobrado."""
    for chave, dados in PLANOS.items():
        if chave in ("teste", "inicial"):
            continue
        if abs(dados.get("preco", -1) - valor) < 0.01:
            return chave
    return PLANO_PADRAO


def processar_webhook_mp(payload: dict):
    """
    Processa eventos enviados pelo Mercado Pago via webhook.
    Atualiza o plano e o status da assinatura da empresa.
    """
    tipo = payload.get("type") or payload.get("topic")
    dados_id = (payload.get("data") or {}).get("id") or payload.get("id")

    if tipo not in ("preapproval", "subscription_preapproval") or not dados_id:
        return {"ignorado": True, "tipo": tipo}

    # Busca os detalhes da assinatura no Mercado Pago
    try:
        resp = requests.get(
            f"{MP_BASE}/preapproval/{dados_id}",
            headers=_headers(),
            timeout=10,
        )
        if not resp.ok:
            return {"erro": f"Não consegui buscar preapproval {dados_id}"}
        assinatura = resp.json()
    except Exception as e:
        return {"erro": str(e)}

    status_mp = str(assinatura.get("status", "")).lower()
    empresa_id_ref = assinatura.get("external_reference")
    valor = (assinatura.get("auto_recurring") or {}).get("transaction_amount", 0)
    plano_detectado = _plano_por_valor(float(valor))

    if not empresa_id_ref:
        return {"ignorado": True, "motivo": "sem external_reference"}

    # Mapeia o status do MP pro status interno
    mapa_status = {
        "authorized": "ativa",
        "active": "ativa",
        "paused": "inadimplente",
        "cancelled": "cancelada",
        "pending": "pendente",
    }
    novo_status = mapa_status.get(status_mp, status_mp)

    criar_tabelas()
    db = SessionLocal()
    try:
        empresa = (
            db.query(EmpresaModel)
            .filter(EmpresaModel.id == int(empresa_id_ref))
            .first()
        )
        if not empresa:
            return {"erro": f"Empresa {empresa_id_ref} não encontrada"}

        empresa.assinatura_id = dados_id
        empresa.gateway_pagamento = "mercado_pago"
        empresa.assinatura_status = novo_status

        if novo_status == "ativa":
            empresa.plano = plano_detectado
            empresa.status = "ativo"
            empresa.limite_pedidos_mes = PLANOS[plano_detectado]["limite_pedidos_mes"]
            empresa.data_vencimento = datetime.utcnow() + timedelta(days=32)

        elif novo_status in ("cancelada", "inadimplente"):
            # Cai pro Free mas mantém o acesso (sem bloquear imediatamente)
            empresa.plano = PLANO_PADRAO
            empresa.status = "ativo" if novo_status == "inadimplente" else "cancelado"
            empresa.limite_pedidos_mes = PLANOS[PLANO_PADRAO]["limite_pedidos_mes"]

        db.commit()

    finally:
        db.close()

    return {
        "processado": True,
        "empresa_id": empresa_id_ref,
        "status_mp": status_mp,
        "status_interno": novo_status,
        "plano": plano_detectado if novo_status == "ativa" else PLANO_PADRAO,
    }


def cancelar_assinatura(empresa_id: int):
    """Cancela a assinatura ativa da empresa no Mercado Pago."""
    criar_tabelas()
    db = SessionLocal()
    try:
        empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
        if not empresa or not empresa.assinatura_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma assinatura encontrada para cancelar.",
            )
        assinatura_id = empresa.assinatura_id
    finally:
        db.close()

    resposta = requests.put(
        f"{MP_BASE}/preapproval/{assinatura_id}",
        json={"status": "cancelled"},
        headers=_headers(),
        timeout=10,
    )

    if not resposta.ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao cancelar no Mercado Pago: {resposta.text[:200]}",
        )

    # Atualiza localmente
    db = SessionLocal()
    try:
        empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
        if empresa:
            empresa.assinatura_status = "cancelada"
            empresa.plano = PLANO_PADRAO
            empresa.status = "cancelado"
            empresa.limite_pedidos_mes = PLANOS[PLANO_PADRAO]["limite_pedidos_mes"]
            db.commit()
    finally:
        db.close()

    return {"mensagem": "Assinatura cancelada com sucesso."}
