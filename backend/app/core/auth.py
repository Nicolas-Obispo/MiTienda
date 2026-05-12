# app/core/auth.py
# ----------------

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from datetime import datetime, timedelta
from jose import jwt, JWTError

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.models.tokens_models import TokenRevocado

# auto_error=False permite controlar manualmente el 401
bearer_scheme = HTTPBearer(auto_error=False)


# -----------------------------------------
# 🔥 Verificar si un token fue revocado
# -----------------------------------------
def token_esta_revocado(token: str, db: Session) -> bool:
    """
    Devuelve True si el token ya fue invalidado por logout.
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
# 🧩 Obtener usuario actual (OBLIGATORIO)
# -----------------------------------------
def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Valida el token JWT y devuelve el usuario autenticado.

    - Si no hay token → 401
    - Si es inválido / expirado / revocado → 401
    """

    if credenciales is None or not credenciales.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return _validar_token_y_obtener_usuario(
        token=credenciales.credentials,
        db=db,
    )


# -----------------------------------------
# 🧩 Obtener usuario actual (OPCIONAL)
# -----------------------------------------
def obtener_usuario_actual_opcional(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Versión opcional del usuario autenticado.

    - Si no hay token → devuelve None (NO 401)
    - Si hay token inválido → 401 (seguridad intacta)
    - Si token válido → devuelve Usuario
    """

    if credenciales is None or not credenciales.credentials:
        return None

    return _validar_token_y_obtener_usuario(
        token=credenciales.credentials,
        db=db,
    )


# -----------------------------------------
# 🔒 Lógica interna compartida
# -----------------------------------------
def _validar_token_y_obtener_usuario(token: str, db: Session) -> Usuario:
    """
    Función interna reutilizable:
    - Decodifica token
    - Verifica expiración
    - Verifica revocación
    - Devuelve usuario
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        usuario_id = payload.get("sub")
        if usuario_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        usuario_id = int(usuario_id)

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    if token_esta_revocado(token, db):
        raise HTTPException(status_code=401, detail="Token revocado")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario
