import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# DATABASE_URL vem do .env / variáveis de ambiente. Em desenvolvimento, cai no
# SQLite local. Em produção (Render/Railway/etc), defina DATABASE_URL apontando
# pro Postgres — o sistema detecta sozinho.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'profit_hub.db'}",
)

# Render/Heroku entregam URLs no formato antigo "postgres://"; o SQLAlchemy
# atual exige "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def coluna_existe(nome_tabela, nome_coluna):
    """Checa se uma coluna existe — funciona em SQLite, Postgres e MySQL."""
    insp = inspect(engine)
    if nome_tabela not in insp.get_table_names():
        return False
    colunas = [c["name"] for c in insp.get_columns(nome_tabela)]
    return nome_coluna in colunas


def tabela_existe(nome_tabela):
    """Checa se uma tabela existe — agnóstico ao banco."""
    return nome_tabela in inspect(engine).get_table_names()


def migrar_tabela_produtos():
    if not tabela_existe("produtos"):
        return

    with engine.begin() as conexao:
        if not coluna_existe("produtos", "empresa_id"):
            conexao.execute(
                text("ALTER TABLE produtos " "ADD COLUMN empresa_id INTEGER DEFAULT 1")
            )

        if not coluna_existe("produtos", "codigos_externos"):
            conexao.execute(
                text(
                    "ALTER TABLE produtos "
                    "ADD COLUMN codigos_externos TEXT DEFAULT ''"
                )
            )

        conexao.execute(
            text("UPDATE produtos " "SET empresa_id = 1 " "WHERE empresa_id IS NULL")
        )


def migrar_tabela_empresas():
    if not tabela_existe("empresas"):
        return

    with engine.begin() as conexao:
        if not coluna_existe("empresas", "status"):
            conexao.execute(
                text(
                    "ALTER TABLE empresas "
                    "ADD COLUMN status VARCHAR(80) DEFAULT 'teste'"
                )
            )

        if not coluna_existe("empresas", "limite_pedidos_mes"):
            conexao.execute(
                text(
                    "ALTER TABLE empresas "
                    "ADD COLUMN limite_pedidos_mes INTEGER DEFAULT 100"
                )
            )

        if not coluna_existe("empresas", "data_inicio_teste"):
            conexao.execute(
                text("ALTER TABLE empresas " "ADD COLUMN data_inicio_teste DATETIME")
            )

        if not coluna_existe("empresas", "data_fim_teste"):
            conexao.execute(
                text("ALTER TABLE empresas " "ADD COLUMN data_fim_teste DATETIME")
            )

        if not coluna_existe("empresas", "gateway_pagamento"):
            conexao.execute(
                text(
                    "ALTER TABLE empresas "
                    "ADD COLUMN gateway_pagamento VARCHAR(40) DEFAULT ''"
                )
            )

        if not coluna_existe("empresas", "assinatura_id"):
            conexao.execute(
                text(
                    "ALTER TABLE empresas "
                    "ADD COLUMN assinatura_id VARCHAR(120) DEFAULT ''"
                )
            )

        if not coluna_existe("empresas", "assinatura_status"):
            conexao.execute(
                text(
                    "ALTER TABLE empresas "
                    "ADD COLUMN assinatura_status VARCHAR(40) DEFAULT 'inativa'"
                )
            )

        if not coluna_existe("empresas", "data_vencimento"):
            conexao.execute(
                text("ALTER TABLE empresas " "ADD COLUMN data_vencimento DATETIME")
            )

        conexao.execute(
            text(
                "UPDATE empresas "
                "SET plano = 'teste' "
                "WHERE plano IS NULL OR plano = '' OR plano = 'local'"
            )
        )

        conexao.execute(
            text(
                "UPDATE empresas "
                "SET status = 'teste' "
                "WHERE status IS NULL OR status = ''"
            )
        )

        conexao.execute(
            text(
                "UPDATE empresas "
                "SET limite_pedidos_mes = 100 "
                "WHERE limite_pedidos_mes IS NULL OR limite_pedidos_mes <= 0"
            )
        )


def criar_tabelas():
    from app.models.company_model import EmpresaModel
    from app.models.company_config_model import ConfiguracaoEmpresaModel
    from app.models.product_model import ProdutoModel
    from app.models.user_model import UsuarioModel

    Base.metadata.create_all(bind=engine)
    migrar_tabela_produtos()
    migrar_tabela_empresas()
