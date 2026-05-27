from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

from app.services.auth_service import (
    autenticar_usuario,
    cadastrar_usuario,
    obter_usuario_por_token,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])

security = HTTPBearer(auto_error=False)


class CadastroEntrada(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    nomeEmpresa: str = ""


class LoginEntrada(BaseModel):
    email: EmailStr
    senha: str


@router.post("/cadastro")
def rota_cadastrar_usuario(dados: CadastroEntrada):
    return cadastrar_usuario(dados.model_dump())


@router.post("/login")
def rota_login(dados: LoginEntrada):
    return autenticar_usuario(dados.email, dados.senha)


@router.get("/me")
def rota_usuario_logado(
    credenciais: HTTPAuthorizationCredentials = Depends(security),
):
    if not credenciais:
        raise HTTPException(status_code=401, detail="Token não enviado.")

    token = credenciais.credentials

    return obter_usuario_por_token(token)
