"""
seguidores_models.py

ETAPA 60 — Seguidores

Relación:
- Un usuario puede seguir múltiples espacios (comercios)
- Un espacio puede tener múltiples seguidores

Reglas:
- No se permiten duplicados (usuario_id + comercio_id)
- Eliminación física (no soft delete por ahora)

Esto será base para:
- Contador de seguidores
- Feed social en el futuro
- Engagement real
"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Seguidores(Base):
    __tablename__ = "seguidores"

    id = Column(Integer, primary_key=True, index=True)

    # Usuario que sigue
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Espacio (comercio) que es seguido
    comercio_id = Column(Integer, ForeignKey("comercios.id"), nullable=False)

    # Fecha de creación
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Evita duplicados (un usuario no puede seguir 2 veces el mismo espacio)
    __table_args__ = (
        UniqueConstraint("usuario_id", "comercio_id", name="unique_seguidor"),
    )
    