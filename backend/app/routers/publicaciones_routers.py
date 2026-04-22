# app/routers/publicaciones_routers.py
"""
Router HTTP: Publicaciones

Reglas:
- Routers = solo HTTP
- Sin lógica de negocio
- Llaman a services

ETAPA 57:
- Se enriquecen las respuestas con métricas calculadas
- Se calcula liked_by_me real
- Se calcula guardada_by_me real
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
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


# --------------------------------------------------
# Helper interno del router
# --------------------------------------------------

def construir_publicacion_read(
    publicacion,
    usuario_actual: Optional[Usuario] = None,
) -> PublicacionRead:
    """
    Construye manualmente la respuesta PublicacionRead
    agregando métricas calculadas y estado real del usuario actual.

    Esto permite que el frontend reciba:
    - likes_count real
    - guardados_count real
    - interacciones_count real
    - liked_by_me real
    - guardada_by_me real
    """

    # -----------------------------------------------
    # Métricas calculadas
    # -----------------------------------------------
    likes = publicacion.likes or []
    guardados = publicacion.usuarios_que_la_guardaron or []

    likes_count = len(likes)
    guardados_count = len(guardados)
    interacciones_count = likes_count + guardados_count

    # -----------------------------------------------
    # Nombre real del comercio
    # -----------------------------------------------
    comercio_nombre = (
        publicacion.comercio.nombre
        if getattr(publicacion, "comercio", None) is not None
        else None
    )

    # -----------------------------------------------
    # Estado real del usuario actual
    # -----------------------------------------------
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

    # -----------------------------------------------
    # Respuesta final serializada
    # -----------------------------------------------
    publicacion_read = PublicacionRead(
        id=publicacion.id,
        comercio_id=publicacion.comercio_id,
        titulo=publicacion.titulo,
        descripcion=publicacion.descripcion,
        seccion_id=publicacion.seccion_id,
        imagen_url=publicacion.imagen_url,
        is_activa=publicacion.is_activa,
        created_at=publicacion.created_at,
        updated_at=publicacion.updated_at,
        comercio_nombre=comercio_nombre,
        likes_count=likes_count,
        guardados_count=guardados_count,
        interacciones_count=interacciones_count,
        liked_by_me=liked_by_me,
    )

    # --------------------------------------------------
    # Campo adicional no declarado en schema original
    # Lo agregamos dinámicamente para que el frontend
    # pueda usarlo si ya lo espera.
    # --------------------------------------------------
    setattr(publicacion_read, "guardada_by_me", guardada_by_me)

    return publicacion_read


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
    """
    Crea una publicación para un comercio.
    """

    publicacion = crear_publicacion(
        db,
        comercio_id=comercio_id,
        publicacion_in=publicacion_in,
    )

    return construir_publicacion_read(
        publicacion,
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
    """
    Lista publicaciones de un comercio.
    """

    publicaciones = listar_publicaciones_por_comercio(
        db,
        comercio_id=comercio_id,
    )

    return [
        construir_publicacion_read(
            publicacion,
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
    """
    Devuelve el detalle de una publicación e incrementa su contador de vistas.
    """

    publicacion = obtener_publicacion_por_id_y_sumar_view(
        db,
        publicacion_id=publicacion_id,
    )

    if not publicacion:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    return construir_publicacion_read(
        publicacion,
        usuario_actual=usuario_actual,
    )