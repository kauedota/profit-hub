from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base


class ProdutoModel(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, default=1, index=True, nullable=False)

    sku = Column(String(120), index=True, nullable=False)
    nome = Column(String(255), nullable=False)
    custo = Column(Float, default=0)
    imposto = Column(Float, default=0)
    tipo = Column(String(80), default="unitario")
    frete_gratis = Column(Float, default=0)
    observacao = Column(Text, default="")
    componentes = Column(Text, default="[]")

    # IDs do produto nos marketplaces (ex.: ID do anúncio na Shopee), separados
    # por vírgula. Usado para casar relatórios que só trazem o ID, não o SKU.
    codigos_externos = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
