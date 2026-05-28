import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'profit_hub.db'}",
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = DATABASE_URL.startswith("postgresql")

if IS_POSTGRES:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# TIMESTAMP para Postgres; DATETIME para SQLite
TS = "TIMESTAMP" if IS_POSTGRES else "DATETIME"

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def coluna_existe(nome_tabela, nome_coluna):
    insp = inspect(engine)
    if nome_tabela not in insp.get_table_names():
        return False
    return nome_coluna in [c["name"] for c in insp.get_columns(nome_tabela)]


def tabela_existe(nome_tabela):
    return nome_tabela in inspect(engine).get_table_names()


def migrar_tabela_produtos():
    if not tabela_existe("produtos"):
        return
    with engine.begin() as cx:
        if not coluna_existe("produtos", "empresa_id"):
            cx.execute(
                text("ALTER TABLE produtos ADD COLUMN empresa_id INTEGER DEFAULT 1")
            )
        if not coluna_existe("produtos", "codigos_externos"):
            cx.execute(
                text("ALTER TABLE produtos ADD COLUMN codigos_externos TEXT DEFAULT ''")
            )
        cx.execute(text("UPDATE produtos SET empresa_id = 1 WHERE empresa_id IS NULL"))


def migrar_tabela_empresas():
    if not tabela_existe("empresas"):
        return
    with engine.begin() as cx:
        # Colunas de texto / inteiro (iguais em ambos os bancos)
        for col, tipo in [
            ("status", "VARCHAR(80) DEFAULT 'free'"),
            ("limite_pedidos_mes", "INTEGER DEFAULT 200"),
            ("gateway_pagamento", "VARCHAR(40) DEFAULT ''"),
            ("assinatura_id", "VARCHAR(120) DEFAULT ''"),
            ("assinatura_status", "VARCHAR(40) DEFAULT 'inativa'"),
            ("ml_seller_id", "VARCHAR(40) DEFAULT ''"),
            ("ml_access_token", "TEXT DEFAULT ''"),
            ("ml_refresh_token", "TEXT DEFAULT ''"),
        ]:
            if not coluna_existe("empresas", col):
                cx.execute(text(f"ALTER TABLE empresas ADD COLUMN {col} {tipo}"))

        # Colunas de data/hora — tipo varia por banco
        for col in [
            "data_inicio_teste",
            "data_fim_teste",
            "data_vencimento",
            "ml_token_expiry",
            "ml_ultimo_sync",
        ]:
            if not coluna_existe("empresas", col):
                cx.execute(text(f"ALTER TABLE empresas ADD COLUMN {col} {TS}"))

        # Garantir plano/status/limite consistentes
        cx.execute(
            text(
                "UPDATE empresas SET plano = 'free' "
                "WHERE plano IS NULL OR plano = '' OR plano = 'local'"
            )
        )
        cx.execute(
            text(
                "UPDATE empresas SET status = 'ativo' "
                "WHERE status IS NULL OR status = '' OR status = 'teste'"
            )
        )
        cx.execute(
            text(
                "UPDATE empresas SET limite_pedidos_mes = 200 "
                "WHERE limite_pedidos_mes IS NULL OR limite_pedidos_mes <= 0"
            )
        )


def criar_tabelas():
    from app.models.company_config_model import ConfiguracaoEmpresaModel  # noqa
    from app.models.company_model import EmpresaModel  # noqa
    from app.models.product_model import ProdutoModel  # noqa
    from app.models.user_model import UsuarioModel  # noqa

    Base.metadata.create_all(bind=engine)
    migrar_tabela_produtos()
    migrar_tabela_empresas()
