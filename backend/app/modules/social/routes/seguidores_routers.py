"""
seguidores_routers.py

ETAPA 60 — Endpoints de seguidores

Responsabilidades:
- Exponer acciones HTTP para seguir/dejar de seguir espacios
- Consultar si el usuario actual sigue un espacio
- Consultar cantidad de seguidores de un espacio

Regla de oro:
- Router = HTTP puro.
- La lógica de negocio vive en services.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import obtener_usuario_actual
from app.modules.users.models.usuarios_models import Usuario
from app.modules.social.services.seguidores_services import (
    seguir_espacio,
    dejar_de_seguir_espacio,
    usuario_sigue_espacio,
    contar_seguidores,
)
from app.modules.spaces.services.comercios_services import _calcular_distancia_km

router = APIRouter(
    prefix="/seguidores",
    tags=["Seguidores"],
)


@router.post("/espacios/{comercio_id}")
def seguir_espacio_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Sigue un espacio.

    Requiere sesión.
    """
    seguimiento = seguir_espacio(
        db=db,
        usuario_id=usuario_actual.id,
        comercio_id=comercio_id,
    )

    return {
        "message": "Espacio seguido correctamente.",
        "comercio_id": comercio_id,
        "siguiendo": True,
        "seguidores_count": contar_seguidores(db=db, comercio_id=comercio_id),
        "id": seguimiento.id if seguimiento else None,
    }


@router.delete("/espacios/{comercio_id}")
def dejar_de_seguir_espacio_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Deja de seguir un espacio.

    Requiere sesión.
    """
    dejar_de_seguir_espacio(
        db=db,
        usuario_id=usuario_actual.id,
        comercio_id=comercio_id,
    )

    return {
        "message": "Dejaste de seguir este espacio.",
        "comercio_id": comercio_id,
        "siguiendo": False,
        "seguidores_count": contar_seguidores(db=db, comercio_id=comercio_id),
    }


@router.get("/espacios/{comercio_id}/estado")
def obtener_estado_seguimiento_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Indica si el usuario actual sigue un espacio.

    Requiere sesión.
    """
    siguiendo = usuario_sigue_espacio(
        db=db,
        usuario_id=usuario_actual.id,
        comercio_id=comercio_id,
    )

    return {
        "comercio_id": comercio_id,
        "siguiendo": siguiendo,
        "seguidores_count": contar_seguidores(db=db, comercio_id=comercio_id),
    }


@router.get("/espacios/{comercio_id}/contador")
def obtener_contador_seguidores_endpoint(
    comercio_id: int,
    db: Session = Depends(get_db),
):
    """
    Devuelve la cantidad de seguidores de un espacio.

    Público.
    """
    return {
        "comercio_id": comercio_id,
        "seguidores_count": contar_seguidores(db=db, comercio_id=comercio_id),
    }

# ==========================================================
# Espacios seguidos por el usuario actual
# ==========================================================
from app.modules.social.services.seguidores_services import listar_espacios_seguidos_por_usuario


@router.get("/mis-espacios")
def obtener_espacios_seguidos(
    lat: float | None = Query(default=None),
    lng: float | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Devuelve los espacios que sigue el usuario autenticado.
    """

    espacios = listar_espacios_seguidos_por_usuario(
        db=db,
        usuario_id=usuario_actual.id,
    )

    resultado = []

    for c in espacios:
        distancia_km = None

        if lat is not None and lng is not None:
            distancia_km = _calcular_distancia_km(
                lat_origen=lat,
                lng_origen=lng,
                lat_destino=getattr(c, "latitud", None),
                lng_destino=getattr(c, "longitud", None),
            )

        resultado.append({
            "id": c.id,
            "nombre": c.nombre,
            "descripcion": c.descripcion,
            "imagen_url": c.portada_url,
            "distancia_km": distancia_km,
        })

    return resultado
