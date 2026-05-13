"""
rubros_models.py
----------------
Modelo ORM para la entidad Rubro.

Un rubro representa una clasificación general y controlada
para los comercios dentro de MiPlaza.

Ejemplos:
- Gastronomía
- Ropa y calzado
- Servicios profesionales
- Automotor
- Mascotas

Los rubros:
- NO los crean los usuarios
- NO son categorías internas del comercio
- Son una lista curada por el sistema
"""

from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base


class Rubro(Base):
    """
    Modelo ORM del Rubro.
    """

    __tablename__ = "rubros"

    id = Column(Integer, primary_key=True, index=True)

    # Nombre visible del rubro
    nombre = Column(String(100), nullable=False, unique=True)

    # Descripción opcional (para admin / futuro)
    descripcion = Column(String(255))

    # Estado del rubro (permitir ocultarlo sin borrar)
    activo = Column(Boolean, default=True)
