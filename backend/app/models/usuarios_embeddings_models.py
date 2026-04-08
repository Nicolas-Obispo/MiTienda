# backend/app/models/usuarios_embeddings_models.py

# Importamos las columnas y tipos que vamos a usar en la tabla
from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, func

# Importamos la base declarativa del proyecto
from app.core.database import Base


class UsuarioEmbedding(Base):
    """
    Modelo ORM para persistir el embedding semántico de un usuario.

    Regla de diseño:
    - 1 usuario -> 1 embedding
    - El vector se guarda serializado en texto
    - model_version permite regenerar embeddings a futuro
    """

    __tablename__ = "usuarios_embeddings"

    # ID interno de la tabla
    id = Column(Integer, primary_key=True, index=True)

    # Relación 1 a 1 con usuario:
    # unique=True garantiza un solo embedding por usuario
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Vector serializado (por ejemplo JSON en string)
    vector = Column(Text, nullable=False)

    # Versión del modelo/proceso que generó el embedding
    model_version = Column(Integer, nullable=False, default=1)

    # Fecha de creación automática
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Fecha de última actualización automática
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )