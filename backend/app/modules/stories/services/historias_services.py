# app/modules/stories/services/historias_services.py
"""
Service: Historias

Reglas:
- Services = lógica de negocio
- Sin HTTP
- Decisión temporal de producto:
  las historias permanecen visibles indefinidamente durante etapa temprana de adopción.
  La expiración de 24 horas se mantiene en la estructura de datos para futura reactivación.
- ETAPA 44: Resolver estado vista_by_me en backend (estado real por usuario)
"""

from typing import List, Optional
from urllib.parse import urlparse

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.stories.models.historias_models import Historia
from app.modules.stories.models.historias_vistas_models import HistoriaVista
from app.modules.stories.models.historias_likes_models import HistoriaLike
from app.modules.stories.schemas.historias_schemas import HistoriaCreate
from app.modules.spaces.models.comercios_models import Comercio


LOCAL_UPLOAD_HOSTS = {
    "http://localhost:8000",
    "http://127.0.0.1:8000",
}


def _normalizar_thumbnail_url(portada_url: Optional[str]) -> Optional[str]:
    if not portada_url:
        return portada_url

    for local_host in LOCAL_UPLOAD_HOSTS:
        if portada_url.startswith(local_host):
            parsed = urlparse(portada_url)
            return parsed.path

    return portada_url


def crear_historia(
    db: Session,
    *,
    comercio_id: int,
    historia_in: HistoriaCreate,
) -> Historia:
    """
    Crea una historia para un comercio.

    - Solo inserta en DB.
    - No resuelve lógica de vistas.
    """

    nueva_historia = Historia(
        comercio_id=comercio_id,
        media_url=historia_in.media_url,
        expira_en=historia_in.expira_en,
        publicacion_id=historia_in.publicacion_id,
        is_activa=historia_in.is_activa,
    )

    db.add(nueva_historia)
    db.commit()
    db.refresh(nueva_historia)

    return nueva_historia


def listar_historias_activas_por_comercio(
    db: Session,
    *,
    comercio_id: int,
    usuario_id: Optional[int] = None,  # NUEVO
) -> List[Historia]:
    """
    Devuelve historias activas de un comercio.

    ETAPA 44:
    - Si se recibe usuario_id:
        → Se resuelve vista_by_me para cada historia.
    - Si no hay usuario:
        → vista_by_me queda False (no autenticado).
    """

    historias = (
        db.query(Historia)
        .filter(
            Historia.comercio_id == comercio_id,
            Historia.is_activa.is_(True),
        )
        .order_by(Historia.created_at.desc())
        .all()
    )

    # Si no hay usuario autenticado, devolvemos estado público
    if not usuario_id:
        for h in historias:
            h.vista_by_me = False
            h.likes_count = len(h.likes or [])
            h.liked_by_me = False
        return historias
    
    # Obtener IDs de historias vistas por el usuario
    vistas_ids = (
        db.query(HistoriaVista.historia_id)
        .filter(HistoriaVista.usuario_id == usuario_id)
        .all()
    )

    # Obtener IDs de historias likeadas por el usuario
    likes_ids = (
        db.query(HistoriaLike.historia_id)
        .filter(HistoriaLike.usuario_id == usuario_id)
        .all()
    )

    # Convertimos listas de tuplas a set de ids
    vistas_set = {row[0] for row in vistas_ids}
    likes_set = {row[0] for row in likes_ids}

    # Marcamos cada historia con estado real por usuario
    for h in historias:
        h.vista_by_me = h.id in vistas_set
        h.likes_count = len(h.likes or [])
        h.liked_by_me = h.id in likes_set

    return historias

def listar_historias_bar(
    db: Session,
    *,
    usuario_id: Optional[int] = None,
) -> List[dict]:
    """
    Devuelve items para la barra de historias basados en comercios con historias activas.

    Reglas:
    - Solo comercios activos.
    - Solo comercios con al menos 1 historia activa.
    - Decisión temporal de producto:
      las historias permanecen visibles indefinidamente durante etapa temprana de adopción.
      La expiración de 24 horas se mantiene en la estructura de datos para futura reactivación.
    - Si hay usuario_id: pendientes se calcula con vista_by_me real.
    - Si no hay usuario: vista_by_me queda False y pendientes = cantidad.
    """

    # Traemos comercios que tienen al menos 1 historia activa.
    comercios = (
        db.query(Comercio)
        .join(Historia, Historia.comercio_id == Comercio.id)
        .filter(
            Comercio.activo.is_(True),
            Historia.is_activa.is_(True),
        )
        .distinct()
        .all()
    )

    comercio_ids = [c.id for c in comercios]

    if not comercio_ids:
        return []

    historias = (
        db.query(Historia)
        .filter(
            Historia.comercio_id.in_(comercio_ids),
            Historia.is_activa.is_(True),
        )
        .order_by(Historia.created_at.desc())
        .all()
    )

    historia_ids = [h.id for h in historias]

    if not historia_ids:
        return []

    likes_count_rows = (
        db.query(HistoriaLike.historia_id, func.count(HistoriaLike.id))
        .filter(HistoriaLike.historia_id.in_(historia_ids))
        .group_by(HistoriaLike.historia_id)
        .all()
    )

    likes_count_by_historia = {
        historia_id: int(total)
        for historia_id, total in likes_count_rows
    }

    vistas_set = set()
    likes_set = set()

    if usuario_id:
        vistas_ids = (
            db.query(HistoriaVista.historia_id)
            .filter(
                HistoriaVista.usuario_id == usuario_id,
                HistoriaVista.historia_id.in_(historia_ids),
            )
            .all()
        )

        likes_ids = (
            db.query(HistoriaLike.historia_id)
            .filter(
                HistoriaLike.usuario_id == usuario_id,
                HistoriaLike.historia_id.in_(historia_ids),
            )
            .all()
        )

        vistas_set = {row[0] for row in vistas_ids}
        likes_set = {row[0] for row in likes_ids}

    historias_por_comercio = {}

    for h in historias:
        h.vista_by_me = h.id in vistas_set if usuario_id else False
        h.likes_count = likes_count_by_historia.get(h.id, 0)
        h.liked_by_me = h.id in likes_set if usuario_id else False

        historias_por_comercio.setdefault(h.comercio_id, []).append(h)

    items: List[dict] = []

    for c in comercios:
        historias_comercio = historias_por_comercio.get(c.id, [])

        if not historias_comercio:
            continue

        pendientes = 0
        for h in historias_comercio:
            if not getattr(h, "vista_by_me", False):
                pendientes += 1

        items.append(
            {
                "comercioId": c.id,
                "nombre": c.nombre,
                # Frontend espera thumbnailUrl, usamos la portada del comercio
                "thumbnailUrl": _normalizar_thumbnail_url(c.portada_url),
                "cantidad": len(historias_comercio),
                "pendientes": pendientes,
            }
        )

    # Orden UX: pendientes primero, luego vistos
    items.sort(key=lambda x: (x["pendientes"] == 0, -x["pendientes"]))

    return items
