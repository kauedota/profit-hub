from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base


class EmpresaModel(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String(255), nullable=False)
    documento = Column(String(50), default="")

    plano = Column(String(80), default="teste")
    status = Column(String(80), default="teste")
    limite_pedidos_mes = Column(Integer, default=100)

    data_inicio_teste = Column(DateTime, default=datetime.utcnow)
    data_fim_teste = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=7),
    )

    # Preparação para pagamento (Mercado Pago / Stripe) — ainda sem cobrança real.
    gateway_pagamento = Column(String(40), default="")        # "mercado_pago" | "stripe" | ""
    assinatura_id = Column(String(120), default="")           # id da assinatura no gateway
    assinatura_status = Column(String(40), default="inativa") # inativa | ativa | cancelada | inadimplente
    data_vencimento = Column(DateTime, nullable=True)

    ativo = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
