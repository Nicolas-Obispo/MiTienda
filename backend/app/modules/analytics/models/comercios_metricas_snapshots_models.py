"""
comercios_metricas_snapshots_models.py
--------------------------------------
Snapshots diarios de métricas sociales de cada espacio.

Sirven para comparar avances reales:
- hoy vs ayer
- semana actual vs semana anterior
- evolución del espacio
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Date,
    DateTime,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ComercioMetricasSnapshot(Base):
    """
    Foto diaria de métricas sociales del espacio.

    No reemplaza comercios_metricas_sociales.
    Esta tabla guarda historial.
    """

    __tablename__ = "comercios_metricas_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "comercio_id",
            "fecha",
            name="uq_comercio_metricas_snapshot_fecha",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    comercio_id = Column(
        Integer,
        ForeignKey("comercios.id"),
        nullable=False,
        index=True,
    )

    fecha = Column(
        Date,
        nullable=False,
        index=True,
    )

    total_seguidores = Column(Integer, default=0)
    total_publicaciones = Column(Integer, default=0)
    total_likes_publicaciones = Column(Integer, default=0)
    total_guardados_publicaciones = Column(Integer, default=0)
    total_historias = Column(Integer, default=0)
    total_vistas_historias = Column(Integer, default=0)
    total_likes_historias = Column(Integer, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    comercio = relationship("Comercio")