# app/core/auth.py
# ----------------

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from datetime import datetime, timedelta
from jose import jwt, JWTError

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.usuarios_models import Usuario
from app.models.tokens_models import TokenRevocado

# auto_error=False evita que FastAPI corte antes con "Not authenticated"
# y nos permite dar un error propio y controlado.
bearer_scheme = HTTPBearer(auto_error=False)



# -----------------------------------------
# 🔥 Verificar si un token fue revocado
# -----------------------------------------
def token_esta_revocado(token: str, db: Session) -> bool:
    """
    Devuelve True si el token YA fue invalidado por logout.
    """
    return (
        db.query(TokenRevocado)
        .filter(TokenRevocado.token == token)
        .first()
        is not None
    )


# -----------------------------------------
# 🔑 Crear token JWT
# -----------------------------------------
def crear_token_jwt(datos: dict) -> str:
    """
    Genera un token JWT válido por 60 minutos.
    """
    datos_a_codificar = datos.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=60)
    datos_a_codificar.update({"exp": expiracion})

    token = jwt.encode(
        datos_a_codificar,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return token


# -----------------------------------------
# 🧩 Obtener usuario actual desde JWT
# -----------------------------------------
def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Valida el token JWT, verifica expiración, revocación
    y devuelve el usuario autenticado.
    """

    # Si no viene Authorization: Bearer <token>, FastAPI entrega None
    if credenciales is None or not credenciales.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credenciales.credentials


    # 1. Decodificar token
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # 🔥 sub SIEMPRE VIENE COMO STRING → convertir a int
        usuario_id = payload.get("sub")
        if usuario_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        usuario_id = int(usuario_id)

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # 2. Verificar si está revocado
    if token_esta_revocado(token, db):
        raise HTTPException(status_code=401, detail="Token revocado")

    # 3. Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario
