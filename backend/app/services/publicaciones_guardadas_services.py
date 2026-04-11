"""
Servicios para manejar publicaciones guardadas.

Contiene toda la lógica de negocio:
- Guardar publicaciones
- Evitar duplicados sin romper frontend
- Quitar guardados
- Listar publicaciones guardadas por usuario

Optimización ETAPA 55:
- Evita recalcular embedding innecesariamente
- Usa ventana temporal (5 min)

ETAPA 56:
- guardar_publicacion pasa a ser idempotente
- Si ya existe el guardado, no tira error 400
"""

from sqlalchemy.orm import Session

from app.models.publicaciones_guardadas_models import PublicacionGuardada
from app.models.publicaciones_models import Publicacion
from app.services.usuarios_embeddings_services import (
    regenerar_embedding_usuario_si_corresponde,
)


def guardar_publicacion(
    db: Session,
    usuario_id: int,
    publicacion_id: int
) -> PublicacionGuardada:
    """
    Guarda una publicación para un usuario.

    Validaciones:
    - La publicación debe existir
    - Si ya estaba guardada, devuelve el registro existente
      (comportamiento idempotente para no romper frontend)
    """

    # Verificar que la publicación exista
    publicacion = (
        db.query(Publicacion)
        .filter(Publicacion.id == publicacion_id)
        .first()
    )

    if not publicacion:
        raise ValueError("La publicación no existe")

    # Si ya estaba guardada, devolvemos el existente y NO rompemos
    guardado_existente = (
        db.query(PublicacionGuardada)
        .filter(
            PublicacionGuardada.usuario_id == usuario_id,
            PublicacionGuardada.publicacion_id == publicacion_id
        )
        .first()
    )

    if guardado_existente:
        return guardado_existente

    guardado = PublicacionGuardada(
        usuario_id=usuario_id,
        publicacion_id=publicacion_id
    )

    db.add(guardado)
    db.commit()
    db.refresh(guardado)

    # Recalcular embedding solo si corresponde
    regenerar_embedding_usuario_si_corresponde(
        db=db,
        usuario_id=usuario_id
    )

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

    # Recalcular embedding solo si corresponde
    regenerar_embedding_usuario_si_corresponde(
        db=db,
        usuario_id=usuario_id
    )


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