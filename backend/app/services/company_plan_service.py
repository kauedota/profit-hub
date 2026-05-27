from datetime import datetime, timedelta

from fastapi import HTTPException, status

from app.database import SessionLocal, criar_tabelas
from app.models.company_model import EmpresaModel

PLANOS = {
    "teste": {
        "nome": "Teste",
        "limite_pedidos_mes": 100,
        "descricao": "Plano de teste gratuito",
    },
    "inicial": {
        "nome": "Inicial",
        "limite_pedidos_mes": 500,
        "descricao": "Até 500 pedidos por mês",
    },
    "profissional": {
        "nome": "Profissional",
        "limite_pedidos_mes": 2000,
        "descricao": "Até 2.000 pedidos por mês",
    },
    "avancado": {
        "nome": "Avançado",
        "limite_pedidos_mes": 10000,
        "descricao": "Até 10.000 pedidos por mês",
    },
}


def empresa_para_dict(empresa):
    plano = empresa.plano or "teste"
    dados_plano = PLANOS.get(plano, PLANOS["teste"])

    return {
        "id": empresa.id,
        "nome": empresa.nome,
        "documento": empresa.documento,
        "plano": plano,
        "plano_nome": dados_plano["nome"],
        "plano_descricao": dados_plano["descricao"],
        "status": empresa.status or "teste",
        "ativo": bool(empresa.ativo),
        "limite_pedidos_mes": empresa.limite_pedidos_mes
        or dados_plano["limite_pedidos_mes"],
        "data_inicio_teste": (
            empresa.data_inicio_teste.isoformat() if empresa.data_inicio_teste else None
        ),
        "data_fim_teste": (
            empresa.data_fim_teste.isoformat() if empresa.data_fim_teste else None
        ),
        "gateway_pagamento": getattr(empresa, "gateway_pagamento", "") or "",
        "assinatura_id": getattr(empresa, "assinatura_id", "") or "",
        "assinatura_status": getattr(empresa, "assinatura_status", "inativa")
        or "inativa",
        "data_vencimento": (
            empresa.data_vencimento.isoformat()
            if getattr(empresa, "data_vencimento", None)
            else None
        ),
        "created_at": empresa.created_at.isoformat() if empresa.created_at else None,
        "updated_at": empresa.updated_at.isoformat() if empresa.updated_at else None,
    }


def obter_empresa(empresa_id):
    criar_tabelas()

    db = SessionLocal()

    try:
        empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()

        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada.",
            )

        return empresa

    finally:
        db.close()


def obter_dados_empresa(empresa_id):
    criar_tabelas()

    db = SessionLocal()

    try:
        empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()

        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada.",
            )

        return empresa_para_dict(empresa)

    finally:
        db.close()


def validar_empresa_pode_usar_sistema(empresa_id):
    criar_tabelas()

    db = SessionLocal()

    try:
        empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()

        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Empresa não encontrada.",
            )

        if not empresa.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Empresa inativa.",
            )

        if empresa.status == "bloqueado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Empresa bloqueada. Verifique seu plano.",
            )

        if empresa.status == "cancelado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Plano cancelado.",
            )

        return empresa_para_dict(empresa)

    finally:
        db.close()


def validar_limite_pedidos(empresa_id, total_pedidos):
    dados_empresa = validar_empresa_pode_usar_sistema(empresa_id)

    limite = int(dados_empresa.get("limite_pedidos_mes") or 100)
    plano_nome = dados_empresa.get("plano_nome") or "Teste"

    if total_pedidos > limite:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Seu plano {plano_nome} permite até {limite} pedidos por relatório. "
                f"Este arquivo possui {total_pedidos} pedidos. "
                "Atualize o plano para importar relatórios maiores."
            ),
        )

    return True


def atualizar_plano_empresa(
    empresa_id,
    plano,
    status_empresa="ativo",
):
    criar_tabelas()

    if plano not in PLANOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plano inválido.",
        )

    db = SessionLocal()

    try:
        empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()

        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada.",
            )

        empresa.plano = plano
        empresa.status = status_empresa
        empresa.limite_pedidos_mes = PLANOS[plano]["limite_pedidos_mes"]

        if not empresa.data_inicio_teste:
            empresa.data_inicio_teste = datetime.utcnow()

        if plano == "teste" and not empresa.data_fim_teste:
            empresa.data_fim_teste = datetime.utcnow() + timedelta(days=7)

        db.commit()
        db.refresh(empresa)

        return empresa_para_dict(empresa)

    finally:
        db.close()
