from app.database import SessionLocal, criar_tabelas
from app.models.company_config_model import ConfiguracaoEmpresaModel
from app.models.company_model import EmpresaModel

EMPRESA_PADRAO_ID = 1
EMPRESA_PADRAO_NOME = "Empresa Local"


def garantir_empresa(db, empresa_id=EMPRESA_PADRAO_ID):
    empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()

    if empresa:
        return empresa

    empresa = EmpresaModel(
        id=empresa_id,
        nome=EMPRESA_PADRAO_NOME,
        documento="",
        plano="local",
        ativo=True,
    )

    db.add(empresa)
    db.commit()
    db.refresh(empresa)

    return empresa


def configuracao_para_dict(configuracao):
    return {
        "id": configuracao.id,
        "empresa_id": configuracao.empresa_id,
        "nomeEmpresa": configuracao.nome_empresa,
        "impostoPadrao": configuracao.imposto_padrao,
        "margemMinima": configuracao.margem_minima,
        "created_at": (
            configuracao.created_at.isoformat() if configuracao.created_at else None
        ),
        "updated_at": (
            configuracao.updated_at.isoformat() if configuracao.updated_at else None
        ),
    }


def garantir_configuracao_empresa(db, empresa_id=EMPRESA_PADRAO_ID):
    empresa = garantir_empresa(db, empresa_id)

    configuracao = (
        db.query(ConfiguracaoEmpresaModel)
        .filter(ConfiguracaoEmpresaModel.empresa_id == empresa_id)
        .first()
    )

    if configuracao:
        return configuracao

    configuracao = ConfiguracaoEmpresaModel(
        empresa_id=empresa_id,
        nome_empresa=empresa.nome or EMPRESA_PADRAO_NOME,
        imposto_padrao=10,
        margem_minima=20,
    )

    db.add(configuracao)
    db.commit()
    db.refresh(configuracao)

    return configuracao


def obter_configuracoes(empresa_id=EMPRESA_PADRAO_ID):
    criar_tabelas()

    db = SessionLocal()

    try:
        configuracao = garantir_configuracao_empresa(db, empresa_id)
        return configuracao_para_dict(configuracao)

    finally:
        db.close()


def atualizar_configuracoes(dados, empresa_id=EMPRESA_PADRAO_ID):
    criar_tabelas()

    db = SessionLocal()

    try:
        configuracao = garantir_configuracao_empresa(db, empresa_id)

        nome_empresa = dados.get("nomeEmpresa", "")
        imposto_padrao = float(dados.get("impostoPadrao") or 10)
        margem_minima = float(dados.get("margemMinima") or 20)

        configuracao.nome_empresa = nome_empresa
        configuracao.imposto_padrao = imposto_padrao
        configuracao.margem_minima = margem_minima

        empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()

        if empresa and nome_empresa:
            empresa.nome = nome_empresa

        db.commit()
        db.refresh(configuracao)

        return configuracao_para_dict(configuracao)

    finally:
        db.close()
