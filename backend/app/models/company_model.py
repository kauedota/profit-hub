from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

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

    # Assinatura Mercado Pago
    gateway_pagamento = Column(String(40), default="")
    assinatura_id = Column(String(120), default="")
    assinatura_status = Column(String(40), default="inativa")
    data_vencimento = Column(DateTime, nullable=True)

    # Integração Mercado Livre (OAuth)
    ml_seller_id = Column(String(40), default="")
    ml_access_token = Column(Text, default="")
    ml_refresh_token = Column(Text, default="")
    ml_token_expiry = Column(DateTime, nullable=True)
    ml_ultimo_sync = Column(DateTime, nullable=True)

    ativo = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
