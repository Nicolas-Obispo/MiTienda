"""
Modelo ORM para las publicaciones guardadas por los usuarios.

Este módulo define la tabla intermedia que representa
las publicaciones que un usuario guarda para ver más tarde.

Características:
- Uso personal (no social)
- No impacta en ranking ni feed
- Relación muchos a muchos entre usuarios y publicaciones
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class PublicacionGuardada(Base):
    """
    Representa una publicación guardada por un usuario.

    Un usuario puede guardar muchas publicaciones,
    pero no puede guardar la misma publicación más de una vez.
    """

    __tablename__ = "publicaciones_guardadas"

    # Clave primaria
    id = Column(Integer, primary_key=True, index=True)

    # Usuario que guarda la publicación
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Publicación guardada
    publicacion_id = Column(
        Integer,
        ForeignKey("publicaciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Fecha en la que se guardó la publicación
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Evita que un usuario guarde dos veces la misma publicación
    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "publicacion_id",
            name="uq_usuario_publicacion_guardada"
        ),
    )

    # Relación con el usuario
    usuario = relationship(
        "Usuario",
        back_populates="publicaciones_guardadas"
    )

    # Relación con la publicación
    publicacion = relationship(
        "Publicacion",
        back_populates="usuarios_que_la_guardaron"
    )
