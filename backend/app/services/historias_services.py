# app/services/historias_services.py
"""
Service: Historias

Reglas:
- Services = lógica de negocio
- Sin HTTP
- Maneja expiración de historias
"""

from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.historias_models import Historia
from app.schemas.historias_schemas import HistoriaCreate


def crear_historia(
    db: Session,
    *,
    comercio_id: int,
    historia_in: HistoriaCreate,
) -> Historia:
    """
    Crea una historia para un comercio.
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
) -> List[Historia]:
    """
    Devuelve las historias activas y no expiradas de un comercio.
    """

    ahora = datetime.utcnow()

    return (
        db.query(Historia)
        .filter(
            Historia.comercio_id == comercio_id,
            Historia.is_activa.is_(True),
            Historia.expira_en > ahora,
        )
        .order_by(Historia.created_at.desc())
        .all()
    )
