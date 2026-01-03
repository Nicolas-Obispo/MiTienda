"""
Servicios para manejar publicaciones guardadas.

Contiene toda la lógica de negocio:
- Guardar publicaciones
- Evitar duplicados
- Quitar guardados
- Listar publicaciones guardadas por usuario
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.publicaciones_guardadas_models import PublicacionGuardada
from app.models.publicaciones_models import Publicacion


def guardar_publicacion(
    db: Session,
    usuario_id: int,
    publicacion_id: int
) -> PublicacionGuardada:
    """
    Guarda una publicación para un usuario.

    Validaciones:
    - La publicación debe existir
    - No se puede guardar dos veces la misma publicación
    """

    # Verificar que la publicación exista
    publicacion = (
        db.query(Publicacion)
        .filter(Publicacion.id == publicacion_id)
        .first()
    )

    if not publicacion:
        raise ValueError("La publicación no existe")

    guardado = PublicacionGuardada(
        usuario_id=usuario_id,
        publicacion_id=publicacion_id
    )

    db.add(guardado)

    try:
        db.commit()
        db.refresh(guardado)
    except IntegrityError:
        db.rollback()
        # Se produce cuando el usuario intenta guardar la misma publicación dos veces
        raise ValueError("La publicación ya está guardada")

    return guardado


def quitar_publicacion_guardada(
    db: Session,
    usuario_id: int,
    publicacion_id: int
) -> None:
    """
    Quita una publicación de los guardados del usuario.
    """

    guardado = (
        db.query(PublicacionGuardada)
        .filter(
            PublicacionGuardada.usuario_id == usuario_id,
            PublicacionGuardada.publicacion_id == publicacion_id
        )
        .first()
    )

    if not guardado:
        raise ValueError("La publicación no está guardada")

    db.delete(guardado)
    db.commit()


def listar_publicaciones_guardadas(
    db: Session,
    usuario_id: int
):
    """
    Devuelve todas las publicaciones guardadas por el usuario,
    ordenadas desde la más reciente a la más antigua.
    """

    return (
        db.query(PublicacionGuardada)
        .filter(PublicacionGuardada.usuario_id == usuario_id)
        .order_by(PublicacionGuardada.created_at.desc())
        .all()
    )
