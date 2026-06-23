"""
rubros_services.py
------------------
Lógica de negocio para Rubros.

- Los rubros son de solo lectura
- No se crean ni editan desde la app
"""

from sqlalchemy.orm import Session
from app.modules.products.models.rubros_models import Rubro


CATALOGO_RUBROS_INICIAL = [
    "Gastronomía",
    "Kiosco",
    "Supermercado",
    "Tienda de ropa",
    "Zapatería",
    "Deportes",
    "Servicios de limpieza",
    "Servicios de construcción",
    "Estudio contable",
    "Estudio jurídico / abogado",
    "Tecnología",
    "Salud y bienestar",
    "Educación",
    "Mascotas",
    "Automotor",
    "Inmobiliaria",
]


def asegurar_catalogo_rubros(db: Session) -> None:
    """
    Crea o reactiva los rubros base sin borrar ni renombrar datos existentes.
    """
    rubros_existentes = {
        rubro.nombre.strip().lower(): rubro
        for rubro in db.query(Rubro).all()
        if rubro.nombre
    }

    hubo_cambios = False

    for nombre in CATALOGO_RUBROS_INICIAL:
        key = nombre.strip().lower()
        rubro = rubros_existentes.get(key)

        if rubro:
            if not rubro.activo:
                rubro.activo = True
                hubo_cambios = True
            continue

        db.add(Rubro(nombre=nombre, activo=True))
        hubo_cambios = True

    if hubo_cambios:
        db.commit()


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
