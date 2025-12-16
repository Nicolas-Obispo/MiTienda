# app/models/publicaciones_models.py
"""
Modelo ORM: Publicaciones

Reglas:
- Models = solo SQLAlchemy (sin lógica de negocio)
- created_at / updated_at incluidos desde ahora
- Relaciones explícitas y consistentes
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship


from app.core.database import Base


class Publicacion(Base):
    """
    Representa una publicación perteneciente a un comercio.
    Puede (opcionalmente) estar asociada a una sección del comercio.

    Nota: MiPlaza NO es marketplace.
    Una publicación es contenido publicitario / descubrimiento.
    """

    __tablename__ = "publicaciones"

    # -------------------------
    # PK
    # -------------------------
    id = Column(Integer, primary_key=True, index=True)

    # -------------------------
    # Relaciones (FK)
    # -------------------------
    comercio_id = Column(
        Integer,
        ForeignKey("comercios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Una publicación puede estar en una sección, pero no es obligatorio
    seccion_id = Column(
        Integer,
        ForeignKey("secciones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # -------------------------
    # Contenido
    # -------------------------
    titulo = Column(String(120), nullable=False)
    descripcion = Column(Text, nullable=True)

    # Señales / control (NO social)
    # Likes = señal de interés, no “me gusta social”
    is_activa = Column(Boolean, nullable=False, server_default="1")

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
        back_populates="publicaciones",
        lazy="selectin",
    )

    seccion = relationship(
        "Seccion",
        back_populates="publicaciones",
        lazy="selectin",
    )

    # -------------------------
    # Historias
    # -------------------------
    historias = relationship(
        "Historia",
        back_populates="publicacion",
        lazy="selectin",
    )

    # -------------------------
    # Likes (señal de interés)
    # -------------------------
    likes = relationship(
        "LikePublicacion",
        back_populates="publicacion",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # -------------------------
    # Métricas
    # -------------------------
    views_count = Column(
        Integer,
        nullable=False,
        server_default="0",
    )
