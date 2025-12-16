"""
secciones_models.py
-------------------
Modelo ORM para las Secciones internas de un Comercio.

Una Sección organiza las publicaciones dentro de un comercio
(ej: Remeras, Promociones, Servicios, Ofertas, etc.).

- Pertenece exclusivamente a un Comercio
- Tiene orden configurable
- Puede activarse / desactivarse
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Seccion(Base):
    __tablename__ = "secciones"

    id = Column(Integer, primary_key=True, index=True)

    # Relación con comercio
    comercio_id = Column(
        Integer,
        ForeignKey("comercios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Datos principales
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))

    # Orden visual dentro del comercio
    orden = Column(Integer, nullable=False, default=0)

    # Estado
    activo = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # -------------------------
    # Publicaciones
    # -------------------------
    publicaciones = relationship(
        "Publicacion",
        back_populates="seccion",
        lazy="selectin",
    )
