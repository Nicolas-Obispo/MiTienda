"""
comercios_models.py
-------------------
Modelo ORM para la entidad Comercio.

Representa un negocio o servicio publicado en MiPlaza.
No es un producto, no maneja stock ni ventas.
Es la unidad principal de descubrimiento.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Comercio(Base):
    """
    Modelo ORM del Comercio.

    Un comercio pertenece a un usuario (modo publicador)
    y representa un negocio o servicio real.
    """

    __tablename__ = "comercios"

    # -----------------------------
    # Identificación
    # -----------------------------
    id = Column(Integer, primary_key=True, index=True)

    # Usuario dueño del comercio
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True
    )

    # -----------------------------
    # Datos principales
    # -----------------------------
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(500))

    # Imagen principal (obligatoria)
    portada_url = Column(String(500), nullable=False)

    # -----------------------------
    # Clasificación / ubicación
    # -----------------------------
    rubro_id = Column(Integer, nullable=False, index=True)

    provincia = Column(String(100), nullable=False)
    ciudad = Column(String(100), nullable=False)
    direccion = Column(String(255))

    # -----------------------------
    # Contacto
    # -----------------------------
    whatsapp = Column(String(50))
    instagram = Column(String(255))
    maps_url = Column(String(500))

    # -----------------------------
    # Estado
    # -----------------------------
    activo = Column(Boolean, default=True)

    # -----------------------------
    # Timestamps
    # -----------------------------
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
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
        back_populates="comercio",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # -------------------------
    # Historias
    # -------------------------
    historias = relationship(
        "Historia",
        back_populates="comercio",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # -------------------------
    # Embedding IA (1 a 1)
    # -------------------------
    embedding = relationship(
        "ComercioEmbedding",
        back_populates="comercio",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )