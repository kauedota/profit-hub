from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.database import SessionLocal, criar_tabelas
from app.models.user_model import UsuarioModel
from app.services.auth_service import ALGORITHM, SECRET_KEY
from app.services.company_plan_service import validar_empresa_pode_usar_sistema

security = HTTPBearer(auto_error=False)


def obter_usuario_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(security),
):
    if not credenciais:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não enviado.",
        )

    token = credenciais.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = payload.get("sub")

        if not usuario_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido.",
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    criar_tabelas()

    db = SessionLocal()

    try:
        usuario = (
            db.query(UsuarioModel).filter(UsuarioModel.id == int(usuario_id)).first()
        )

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado.",
            )

        if not usuario.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo.",
            )

        validar_empresa_pode_usar_sistema(usuario.empresa_id)

        return usuario

    finally:
        db.close()


def obter_empresa_id_atual(usuario: UsuarioModel = Depends(obter_usuario_atual)):
    return usuario.empresa_id
