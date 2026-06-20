"""
usuarios_services.py
--------------------
Lógica de negocio para Usuarios.
"""

import re

from sqlalchemy.orm import Session
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.schemas.usuarios_schemas import UsuarioCreate, UsuarioLogin

# Funciones de seguridad
from app.core.security import hash_password, verificar_password

COLOR_FONDO_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# ✔️ IMPORTANTE: ya NO importamos auth aquí
# Cada capa cumple su propia responsabilidad


def crear_usuario(db: Session, usuario: UsuarioCreate) -> Usuario | None:
    existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if existente:
        return None

    hashed = hash_password(usuario.password)

    nuevo_usuario = Usuario(
        email=usuario.email,
        hashed_password=hashed
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


def autenticar_usuario(db: Session, data: UsuarioLogin) -> Usuario | None:
    usuario = db.query(Usuario).filter(Usuario.email == data.email).first()
    if not usuario:
        return None

    if not verificar_password(data.password, usuario.hashed_password):
        return None

    return usuario


def obtener_usuario_por_id(db: Session, usuario_id: int) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def completar_onboarding_usuario(
    db: Session,
    usuario: Usuario,
    provincia: str,
    ciudad: str
) -> Usuario:
    """
    Completa el onboarding inicial del usuario.

    - Guarda provincia y ciudad
    - Marca onboarding_completo = True
    - No crea usuario nuevo
    - No toca autenticación ni tokens

    Se espera que el usuario ya esté autenticado.
    """

    usuario.provincia = provincia
    usuario.ciudad = ciudad
    usuario.onboarding_completo = True

    db.commit()
    db.refresh(usuario)

    return usuario


def actualizar_perfil_usuario(
    db: Session,
    usuario: Usuario,
    campos: dict
) -> Usuario:
    """
    Actualiza solo los campos editables del perfil personal.

    Campos permitidos:
    - provincia
    - ciudad
    - color_fondo
    """

    campos_permitidos = {"provincia", "ciudad", "color_fondo"}

    for campo, valor in campos.items():
        if campo not in campos_permitidos:
            continue

        if isinstance(valor, str):
            valor = valor.strip()

        if campo == "color_fondo" and valor is not None:
            if not COLOR_FONDO_HEX_RE.fullmatch(valor):
                raise ValueError("color_fondo debe ser un HEX valido (#RRGGBB)")

        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)

    return usuario


def cambiar_modo_usuario(
    db: Session,
    usuario: Usuario,
    nuevo_modo: str
) -> Usuario:
    """
    Cambia el modo activo del usuario.

    Modos permitidos:
    - "usuario"
    - "publicador"

    Reglas:
    - No crea nuevas cuentas
    - No genera nuevos tokens
    - Solo actualiza el estado del usuario autenticado
    """

    modos_permitidos = {"usuario", "publicador"}

    if nuevo_modo not in modos_permitidos:
        raise ValueError("Modo inválido")

    usuario.modo_activo = nuevo_modo

    db.commit()
    db.refresh(usuario)

    return usuario
