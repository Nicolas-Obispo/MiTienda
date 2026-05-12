"""
comercios_metricas_sociales_models.py
-------------------------------------
Métricas sociales persistentes de cada espacio/comercio.

Esta tabla funciona como una capa de analytics y cache
para evitar cálculos pesados en tiempo real.
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ComercioMetricasSociales(Base):
    """
    Métricas sociales acumuladas del espacio.
    """

    __tablename__ = "comercios_metricas_sociales"

    # -------------------------
    # ID
    # -------------------------
    id = Column(Integer, primary_key=True, index=True)

    # -------------------------
    # Comercio asociado
    # -------------------------
    comercio_id = Column(
        Integer,
        ForeignKey("comercios.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    # -------------------------
    # Métricas acumuladas
    # -------------------------
    total_seguidores = Column(Integer, default=0)

    total_publicaciones = Column(Integer, default=0)

    total_likes_publicaciones = Column(Integer, default=0)

    total_guardados_publicaciones = Column(Integer, default=0)

    total_historias = Column(Integer, default=0)

    total_vistas_historias = Column(Integer, default=0)

    total_likes_historias = Column(Integer, default=0)

    # -------------------------
    # Timestamp
    # -------------------------
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # -------------------------
    # Relación ORM
    # -------------------------
    comercio = relationship(
        "Comercio",
        back_populates="metricas_sociales",
    )