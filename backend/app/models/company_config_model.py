from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database import Base


class ConfiguracaoEmpresaModel(Base):
    __tablename__ = "configuracoes_empresa"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, unique=True, index=True, nullable=False)

    nome_empresa = Column(String(255), default="")
    imposto_padrao = Column(Float, default=10)
    margem_minima = Column(Float, default=20)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
