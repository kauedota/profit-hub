from datetime import datetime, timedelta
import os

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.database import SessionLocal, criar_tabelas
from app.models.company_config_model import ConfiguracaoEmpresaModel
from app.models.company_model import EmpresaModel
from app.models.user_model import UsuarioModel

load_dotenv()

# Em produção, defina SECRET_KEY no arquivo .env. O valor abaixo é só para
# desenvolvimento local.
SECRET_KEY = os.getenv(
    "SECRET_KEY", "profit-hub-chave-local-desenvolvimento-trocar-em-producao"
)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def gerar_hash_senha(senha):
    return pwd_context.hash(senha)


def verificar_senha(senha_digitada, senha_hash):
    return pwd_context.verify(senha_digitada, senha_hash)


def criar_token_acesso(dados):
    dados_para_token = dados.copy()
    expira = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_para_token.update({"exp": expira})

    return jwt.encode(dados_para_token, SECRET_KEY, algorithm=ALGORITHM)


def usuario_para_dict(usuario):
    return {
        "id": usuario.id,
        "empresa_id": usuario.empresa_id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil,
        "ativo": usuario.ativo,
        "created_at": usuario.created_at.isoformat() if usuario.created_at else None,
    }


def criar_empresa_para_usuario(db, nome_empresa):
    empresa = EmpresaModel(
        nome=nome_empresa or "Nova Empresa",
        documento="",
        plano="teste",
        ativo=True,
    )

    db.add(empresa)
    db.commit()
    db.refresh(empresa)

    configuracao = ConfiguracaoEmpresaModel(
        empresa_id=empresa.id,
        nome_empresa=empresa.nome,
        imposto_padrao=10,
        margem_minima=20,
    )

    db.add(configuracao)
    db.commit()

    return empresa


def cadastrar_usuario(dados):
    criar_tabelas()

    nome = str(dados.get("nome") or "").strip()
    email = str(dados.get("email") or "").strip().lower()
    senha = str(dados.get("senha") or "").strip()
    nome_empresa = str(dados.get("nomeEmpresa") or "").strip()

    if not nome:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome é obrigatório.",
        )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail é obrigatório.",
        )

    if len(senha) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha precisa ter pelo menos 6 caracteres.",
        )

    db = SessionLocal()

    try:
        usuario_existente = (
            db.query(UsuarioModel).filter(UsuarioModel.email == email).first()
        )

        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma conta com esse e-mail.",
            )

        empresa = criar_empresa_para_usuario(
            db,
            nome_empresa or f"Empresa de {nome}",
        )

        usuario = UsuarioModel(
            empresa_id=empresa.id,
            nome=nome,
            email=email,
            senha_hash=gerar_hash_senha(senha),
            perfil="admin",
            ativo=True,
        )

        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        token = criar_token_acesso(
            {
                "sub": str(usuario.id),
                "email": usuario.email,
                "empresa_id": usuario.empresa_id,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "usuario": usuario_para_dict(usuario),
            "empresa": {
                "id": empresa.id,
                "nome": empresa.nome,
                "plano": empresa.plano,
                "ativo": empresa.ativo,
            },
        }

    finally:
        db.close()


def autenticar_usuario(email, senha):
    criar_tabelas()

    email = str(email or "").strip().lower()

    db = SessionLocal()

    try:
        usuario = db.query(UsuarioModel).filter(UsuarioModel.email == email).first()

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos.",
            )

        if not usuario.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo.",
            )

        if not verificar_senha(senha, usuario.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos.",
            )

        token = criar_token_acesso(
            {
                "sub": str(usuario.id),
                "email": usuario.email,
                "empresa_id": usuario.empresa_id,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "usuario": usuario_para_dict(usuario),
        }

    finally:
        db.close()


def obter_usuario_por_token(token):
    criar_tabelas()

    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = payload.get("sub")

        if usuario_id is None:
            raise credenciais_invalidas

    except JWTError:
        raise credenciais_invalidas

    db = SessionLocal()

    try:
        usuario = (
            db.query(UsuarioModel).filter(UsuarioModel.id == int(usuario_id)).first()
        )

        if not usuario:
            raise credenciais_invalidas

        return usuario_para_dict(usuario)

    finally:
        db.close()
