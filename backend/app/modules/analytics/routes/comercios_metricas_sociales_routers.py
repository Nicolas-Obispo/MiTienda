"""
comercios_metricas_sociales_routers.py
--------------------------------------
Endpoints para consultar métricas sociales
persistentes de los espacios.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual
from app.modules.spaces.services.comercios_ownership_services import (
    ComercioNoEncontradoError,
    ComercioUsuarioNoPropietarioError,
    obtener_comercio_propio_o_error,
)

from app.modules.analytics.services.comercios_metricas_sociales_services import (
    recalcular_metricas_comercio,
    generar_snapshot_metricas_comercio,
    obtener_comparacion_metricas_comercio,
)


router = APIRouter(
    prefix="/comercios-metricas-sociales",
    tags=["Comercios métricas sociales"],
)


def _validar_comercio_propio_http(
    db: Session,
    *,
    comercio_id: int,
    usuario_actual,
):
    try:
        obtener_comercio_propio_o_error(
            db,
            comercio_id=comercio_id,
            usuario_autenticado=usuario_actual,
        )
    except ComercioNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ComercioUsuarioNoPropietarioError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/espacios/{comercio_id}")
def obtener_metricas_sociales_espacio(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    """
    Devuelve las métricas sociales reales de un espacio.

    Por ahora recalcula desde la base de datos real
    para asegurar consistencia antes de optimizar.
    """

    _validar_comercio_propio_http(
        db,
        comercio_id=comercio_id,
        usuario_actual=usuario_actual,
    )

    metricas = recalcular_metricas_comercio(
        db=db,
        comercio_id=comercio_id,
    )

    return {
        "comercio_id": metricas.comercio_id,
        "total_seguidores": metricas.total_seguidores,
        "total_publicaciones": metricas.total_publicaciones,
        "total_likes_publicaciones": metricas.total_likes_publicaciones,
        "total_guardados_publicaciones": metricas.total_guardados_publicaciones,
        "total_historias": metricas.total_historias,
        "total_vistas_historias": metricas.total_vistas_historias,
        "total_likes_historias": metricas.total_likes_historias,
        "updated_at": metricas.updated_at,
    }

@router.post("/espacios/{comercio_id}/snapshot")
def generar_snapshot_espacio(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    """
    Genera o actualiza snapshot diario
    de métricas sociales del espacio.
    """

    _validar_comercio_propio_http(
        db,
        comercio_id=comercio_id,
        usuario_actual=usuario_actual,
    )

    snapshot = generar_snapshot_metricas_comercio(
        db=db,
        comercio_id=comercio_id,
    )

    return {
        "snapshot_id": snapshot.id,
        "comercio_id": snapshot.comercio_id,
        "fecha": snapshot.fecha,
        "total_seguidores": snapshot.total_seguidores,
        "total_publicaciones": snapshot.total_publicaciones,
        "total_likes_publicaciones": snapshot.total_likes_publicaciones,
        "total_guardados_publicaciones": snapshot.total_guardados_publicaciones,
        "total_historias": snapshot.total_historias,
        "total_vistas_historias": snapshot.total_vistas_historias,
        "total_likes_historias": snapshot.total_likes_historias,
    }

@router.get("/espacios/{comercio_id}/comparacion")
def obtener_comparacion_espacio(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual=Depends(obtener_usuario_actual),
):
    """
    Devuelve comparación real de métricas:
    snapshot actual vs snapshot anterior.
    """

    _validar_comercio_propio_http(
        db,
        comercio_id=comercio_id,
        usuario_actual=usuario_actual,
    )

    return obtener_comparacion_metricas_comercio(
        db=db,
        comercio_id=comercio_id,
    )
