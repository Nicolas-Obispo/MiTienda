# app/routers/publicaciones_routers.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import obtener_usuario_actual_opcional
from app.core.database import get_db
from app.models.usuarios_models import Usuario
from app.schemas.publicaciones_schemas import (
    PublicacionCreate,
    PublicacionRead,
)
from app.services.publicaciones_services import (
    crear_publicacion,
    listar_publicaciones_por_comercio,
    obtener_publicacion_por_id_y_sumar_view,
)

router = APIRouter(
    prefix="/publicaciones",
    tags=["Publicaciones"],
)


def obtener_nombre_comercio(db: Session, publicacion) -> Optional[str]:
    """
    Obtiene el nombre real del comercio asociado a la publicación.

    Primero intenta usar la relación ORM.
    Si no funciona, consulta directo a la tabla comercios por comercio_id.
    """

    comercio_relacionado = getattr(publicacion, "comercio", None)

    if comercio_relacionado is not None:
        nombre = getattr(comercio_relacionado, "nombre", None)
        if nombre:
            return nombre

    comercio_id = getattr(publicacion, "comercio_id", None)

    if comercio_id is None:
        return None

    nombre = db.execute(
        text("SELECT nombre FROM comercios WHERE id = :comercio_id"),
        {"comercio_id": int(comercio_id)},
    ).scalar_one_or_none()

    return nombre


def construir_publicacion_read(
    db: Session,
    publicacion,
    usuario_actual: Optional[Usuario] = None,
) -> PublicacionRead:
    likes = publicacion.likes or []
    guardados = publicacion.usuarios_que_la_guardaron or []

    likes_count = len(likes)
    guardados_count = len(guardados)
    interacciones_count = likes_count + guardados_count

    comercio_nombre = obtener_nombre_comercio(db, publicacion)

    liked_by_me = False
    guardada_by_me = False

    if usuario_actual is not None:
        liked_by_me = any(
            like.usuario_id == usuario_actual.id
            for like in likes
        )

        guardada_by_me = any(
            guardado.usuario_id == usuario_actual.id
            for guardado in guardados
        )

    return PublicacionRead(
        id=publicacion.id,
        comercio_id=publicacion.comercio_id,
        comercio_nombre=comercio_nombre,
        titulo=publicacion.titulo,
        descripcion=publicacion.descripcion,
        seccion_id=publicacion.seccion_id,
        imagen_url=publicacion.imagen_url,
        is_activa=publicacion.is_activa,
        created_at=publicacion.created_at,
        updated_at=publicacion.updated_at,
        likes_count=likes_count,
        guardados_count=guardados_count,
        interacciones_count=interacciones_count,
        liked_by_me=liked_by_me,
        guardada_by_me=guardada_by_me,
    )


@router.post(
    "/comercios/{comercio_id}",
    response_model=PublicacionRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_publicacion_endpoint(
    comercio_id: int,
    publicacion_in: PublicacionCreate,
    db: Session = Depends(get_db),
    usuario_actual: Optional[Usuario] = Depends(obtener_usuario_actual_opcional),
):
    publicacion = crear_publicacion(
        db,
        comercio_id=comercio_id,
        publicacion_in=publicacion_in,
    )

    return construir_publicacion_read(
        db=db,
        publicacion=publicacion,
        usuario_actual=usuario_actual,
    )


@router.get(
    "/comercios/{comercio_id}",
    response_model=List[PublicacionRead],
)
def listar_publicaciones_por_comercio_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Optional[Usuario] = Depends(obtener_usuario_actual_opcional),
):
    publicaciones = listar_publicaciones_por_comercio(
        db,
        comercio_id=comercio_id,
    )

    return [
        construir_publicacion_read(
            db=db,
            publicacion=publicacion,
            usuario_actual=usuario_actual,
        )
        for publicacion in publicaciones
    ]


@router.get(
    "/{publicacion_id}",
    response_model=PublicacionRead,
)
def obtener_publicacion_detalle_endpoint(
    publicacion_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Optional[Usuario] = Depends(obtener_usuario_actual_opcional),
):
    publicacion = obtener_publicacion_por_id_y_sumar_view(
        db,
        publicacion_id=publicacion_id,
    )

    if not publicacion:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    return construir_publicacion_read(
        db=db,
        publicacion=publicacion,
        usuario_actual=usuario_actual,
    )