"""
comercios_embeddings_models.py
-----------------------------
Modelo ORM para embeddings del Comercio (IA v2).

Se separa en tabla propia para:
- mantener limpio el modelo principal de Comercio
- permitir versionado de embeddings (futuro)
- escalar a múltiples representaciones IA sin romper contratos
"""

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComercioEmbedding(Base):
    """
    Embedding persistido asociado 1 a 1 con un Comercio.

    - vector: representación serializada (por ahora TEXT)
    - model_version: permite versionar embeddings (v2, v3, etc.)
    """

    __tablename__ = "comercios_embeddings"

    id = Column(Integer, primary_key=True, index=True)

    comercio_id = Column(
        Integer,
        ForeignKey("comercios.id"),
        nullable=False,
        unique=True,
        index=True
    )

    # Vector serializado (por ahora JSON string dentro de TEXT)
    vector = Column(Text, nullable=False)

    # Versionado (para poder recalcular a futuro sin confundir)
    model_version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relación ORM (lado embedding -> comercio)
    comercio = relationship(
        "Comercio",
        back_populates="embedding",
        lazy="selectin",
    )