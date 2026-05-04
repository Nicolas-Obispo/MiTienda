"""
seguidores_services.py

ETAPA 60 — Lógica de seguidores

Responsabilidades:
- Seguir espacio
- Dejar de seguir
- Saber si ya sigue
- Contar seguidores

Reglas:
- No duplicar relaciones
- Operaciones idempotentes (no rompen si ya existe/no existe)
"""

from sqlalchemy.orm import Session
from app.models.seguidores_models import Seguidores


# ==========================================================
# Seguir espacio
# ==========================================================
def seguir_espacio(db: Session, usuario_id: int, comercio_id: int):
    """
    Crea relación usuario → comercio (seguir)

    Si ya existe, no hace nada (idempotente)
    """

    existente = (
        db.query(Seguidores)
        .filter(
            Seguidores.usuario_id == usuario_id,
            Seguidores.comercio_id == comercio_id,
        )
        .first()
    )

    if existente:
        return existente  # ya sigue

    nuevo = Seguidores(
        usuario_id=usuario_id,
        comercio_id=comercio_id,
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo


# ==========================================================
# Dejar de seguir
# ==========================================================
def dejar_de_seguir_espacio(db: Session, usuario_id: int, comercio_id: int):
    """
    Elimina relación usuario → comercio

    Si no existe, no rompe (idempotente)
    """

    existente = (
        db.query(Seguidores)
        .filter(
            Seguidores.usuario_id == usuario_id,
            Seguidores.comercio_id == comercio_id,
        )
        .first()
    )

    if not existente:
        return None

    db.delete(existente)
    db.commit()

    return True


# ==========================================================
# Saber si sigue
# ==========================================================
def usuario_sigue_espacio(db: Session, usuario_id: int, comercio_id: int) -> bool:
    """
    Devuelve True si el usuario sigue el espacio
    """

    existente = (
        db.query(Seguidores)
        .filter(
            Seguidores.usuario_id == usuario_id,
            Seguidores.comercio_id == comercio_id,
        )
        .first()
    )

    return existente is not None


# ==========================================================
# Contar seguidores
# ==========================================================
def contar_seguidores(db: Session, comercio_id: int) -> int:
    """
    Devuelve cantidad de seguidores de un espacio
    """

    total = (
        db.query(Seguidores)
        .filter(Seguidores.comercio_id == comercio_id)
        .count()
    )

    return total

# ==========================================================
# Listar espacios seguidos por usuario
# ==========================================================
def listar_espacios_seguidos_por_usuario(db: Session, usuario_id: int):
    """
    Devuelve los espacios que sigue un usuario.

    Retorna objetos Comercio usando la relación:
    Seguidores.comercio_id -> Comercios.id
    """

    from app.models.comercios_models import Comercio

    espacios = (
        db.query(Comercio)
        .join(Seguidores, Seguidores.comercio_id == Comercio.id)
        .filter(Seguidores.usuario_id == usuario_id)
        .order_by(Seguidores.created_at.desc())
        .all()
    )

    return espacios