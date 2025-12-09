"""
usuarios_routers.py
-------------------
Rutas HTTP relacionadas a Usuarios.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# DB
from app.core.database import get_db

# Schemas
from app.schemas.usuarios_schemas import UsuarioCreate, UsuarioLogin, UsuarioResponse

# Autenticación y seguridad
from fastapi.security import HTTPAuthorizationCredentials
from app.core.auth import obtener_usuario_actual, crear_token_jwt, bearer_scheme
from jose import jwt, JWTError
from datetime import datetime
from app.core.config import settings

# Modelo para logout
from app.models.tokens_models import TokenRevocado

# Services
from app.services.usuarios_services import (
    crear_usuario,
    autenticar_usuario,
    obtener_usuario_por_id
)


# ------------------------------------------------------------------
# 🔧 Router
# ------------------------------------------------------------------
router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


# =============================================================
#  REGISTRAR USUARIO
# =============================================================
@router.post("/registrar", response_model=UsuarioResponse)
def registrar_usuario_endpoint(payload: UsuarioCreate, db: Session = Depends(get_db)):
    usuario = crear_usuario(db, payload)

    if usuario is None:
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    return usuario


# =============================================================
#  LOGIN (AUTENTICACIÓN)
# =============================================================
@router.post("/login")
def login_endpoint(payload: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = autenticar_usuario(db, payload)

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # 🔥 SUB DEBE SER STRING (ESTA ERA LA CAUSA DE TODOS LOS 401)
    token = crear_token_jwt({"sub": str(usuario.id)})

    return {
        "mensaje": "Inicio de sesión exitoso ✅",
        "token": token,
        "usuario_id": usuario.id
    }


# =============================================================
#  LOGOUT (REVOCAR TOKEN)
# =============================================================
@router.post("/logout", summary="Cerrar sesión (logout real)")
def logout_endpoint(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    token = credenciales.credentials

    # Intentamos obtener la expiración
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        exp_timestamp = payload.get("exp")
        usuario_id = payload.get("sub")
    except JWTError:
        exp_timestamp = None
        usuario_id = None

    expira_en = datetime.utcfromtimestamp(exp_timestamp) if exp_timestamp else None

    token_revocado = TokenRevocado(
        token=token,
        usuario_id=int(usuario_id) if usuario_id else None,
        expira_en=expira_en,
    )

    db.add(token_revocado)
    db.commit()

    return {"mensaje": "Logout exitoso. El token fue revocado."}


# =============================================================
#  PERFIL DEL USUARIO AUTENTICADO
# =============================================================
@router.get("/me", response_model=UsuarioResponse)
def obtener_mi_perfil(usuario_actual=Depends(obtener_usuario_actual)):
    return usuario_actual


# =============================================================
#  OBTENER USUARIO POR ID
# =============================================================
@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario_endpoint(usuario_id: int, db: Session = Depends(get_db)):
    usuario = obtener_usuario_por_id(db, usuario_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario
