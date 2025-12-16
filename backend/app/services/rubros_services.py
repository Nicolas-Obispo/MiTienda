"""
rubros_services.py
------------------
Lógica de negocio para Rubros.

- Los rubros son de solo lectura
- No se crean ni editan desde la app
"""

from sqlalchemy.orm import Session
from app.models.rubros_models import Rubro


def listar_rubros(db: Session) -> list[Rubro]:
    """
    Devuelve todos los rubros activos.
    """
    return (
        db.query(Rubro)
        .filter(Rubro.activo == True)
        .order_by(Rubro.nombre.asc())
        .all()
    )


def obtener_rubro_por_id(db: Session, rubro_id: int) -> Rubro | None:
    """
    Devuelve un rubro por ID si está activo.
    """
    return (
        db.query(Rubro)
        .filter(
            Rubro.id == rubro_id,
            Rubro.activo == True
        )
        .first()
    )
