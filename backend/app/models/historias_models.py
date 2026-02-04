# app/models/historias_models.py
"""
Modelo ORM: Historias

Reglas:
- Models = solo SQLAlchemy
- Historias con expiración
- NO social, contenido efímero de comercios
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Historia(Base):
    """
    Representa una historia efímera de un comercio.
    """

    __tablename__ = "historias"

    # -------------------------
    # PK
    # -------------------------
    id = Column(Integer, primary_key=True, index=True)

    # -------------------------
    # Relaciones
    # -------------------------
    comercio_id = Column(
        Integer,
        ForeignKey("comercios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Asociación opcional a una publicación
    publicacion_id = Column(
        Integer,
        ForeignKey("publicaciones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # -------------------------
    # Contenido
    # -------------------------
    # media_url puede ser largo (CDN, query params, etc.)
    # Por eso NO usamos 255, que rompe con URLs reales.
    media_url = Column(String(2048), nullable=False)

    is_activa = Column(Boolean, nullable=False, server_default="1")

    # Fecha de expiración (clave)
    expira_en = Column(DateTime(timezone=True), nullable=False)

    # -------------------------
    # Auditoría
    # -------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # -------------------------
    # ORM relationships
    # -------------------------
    comercio = relationship(
        "Comercio",
        back_populates="historias",
        lazy="selectin",
    )

    publicacion = relationship(
        "Publicacion",
        back_populates="historias",
        lazy="selectin",
    )
