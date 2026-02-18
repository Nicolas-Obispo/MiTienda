# app/services/historias_services.py
"""
Service: Historias

Reglas:
- Services = lógica de negocio
- Sin HTTP
- Maneja expiración de historias
- ETAPA 44: Resolver estado vista_by_me en backend (estado real por usuario)
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.historias_models import Historia
from app.models.historias_vistas_models import HistoriaVista
from app.schemas.historias_schemas import HistoriaCreate
from app.models.comercios_models import Comercio



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
    Devuelve historias activas y no expiradas de un comercio.

    ETAPA 44:
    - Si se recibe usuario_id:
        → Se resuelve vista_by_me para cada historia.
    - Si no hay usuario:
        → vista_by_me queda False (no autenticado).
    """

    ahora = datetime.utcnow()

    historias = (
        db.query(Historia)
        .filter(
            Historia.comercio_id == comercio_id,
            Historia.is_activa.is_(True),
            Historia.expira_en > ahora,
        )
        .order_by(Historia.created_at.desc())
        .all()
    )

    # Si no hay usuario autenticado, devolvemos sin modificar
    if not usuario_id:
        for h in historias:
            h.vista_by_me = False
        return historias

    # Obtener IDs de historias vistas por el usuario
    vistas_ids = (
        db.query(HistoriaVista.historia_id)
        .filter(HistoriaVista.usuario_id == usuario_id)
        .all()
    )

    # Convertimos lista de tuplas a set de ids
    vistas_set = {row[0] for row in vistas_ids}

    # Marcamos cada historia
    for h in historias:
        h.vista_by_me = h.id in vistas_set

    return historias

def listar_historias_bar(
    db: Session,
    *,
    usuario_id: Optional[int] = None,
) -> List[dict]:
    """
    Devuelve items para la barra de historias basados en comercios con historias activas/no expiradas.

    Reglas:
    - Solo comercios activos.
    - Solo comercios con al menos 1 historia activa y no expirada.
    - Si hay usuario_id: pendientes se calcula con vista_by_me real.
    - Si no hay usuario: vista_by_me queda False y pendientes = cantidad.
    """

    ahora = datetime.utcnow()

    # Traemos comercios que tienen al menos 1 historia activa/no expirada
    comercios = (
        db.query(Comercio)
        .join(Historia, Historia.comercio_id == Comercio.id)
        .filter(
            Comercio.activo.is_(True),
            Historia.is_activa.is_(True),
            Historia.expira_en > ahora,
        )
        .distinct()
        .all()
    )

    items: List[dict] = []

    for c in comercios:
        # Reutilizamos lógica existente (resuelve vista_by_me)
        historias = listar_historias_activas_por_comercio(
            db,
            comercio_id=c.id,
            usuario_id=usuario_id,
        )

        if not historias:
            continue

        pendientes = 0
        for h in historias:
            if not getattr(h, "vista_by_me", False):
                pendientes += 1

        items.append(
            {
                "comercioId": c.id,
                "nombre": c.nombre,
                # Frontend espera thumbnailUrl, usamos la portada del comercio
                "thumbnailUrl": c.portada_url,
                "cantidad": len(historias),
                "pendientes": pendientes,
            }
        )

    # Orden UX: pendientes primero, luego vistos
    items.sort(key=lambda x: (x["pendientes"] == 0, -x["pendientes"]))

    return items
