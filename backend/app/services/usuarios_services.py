"""
usuarios_services.py
--------------------
Lógica de negocio para Usuarios.
"""

from sqlalchemy.orm import Session
from app.models.usuarios_models import Usuario
from app.schemas.usuarios_schemas import UsuarioCreate, UsuarioLogin

# Funciones de seguridad
from app.core.security import hash_password, verificar_password

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
