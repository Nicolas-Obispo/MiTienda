# app/models/tokens_models.py
# ---------------------------
# Modelos ORM para manejar tokens JWT revocados.
# Esta tabla se usa para implementar un "logout real":
# Si un token aparece aquí, el backend lo considera inválido
# aunque todavía no haya llegado su fecha de expiración (exp).

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class TokenRevocado(Base):
    """
    Representa un token JWT que fue marcado como revocado (logout).

    Campos:
    - id: clave primaria interna.
    - token: el string completo del JWT (header.payload.firma).
    - usuario_id: ID del usuario dueño del token.
    - fecha_revocado: fecha y hora en la que se hizo logout.
    - expira_en: fecha y hora en la que el token iba a expirar naturalmente.
    """

    __tablename__ = "tokens_revocados"

    # ID autoincremental (clave primaria)
    id = Column(Integer, primary_key=True, index=True)

    # Token JWT completo (lo guardamos como texto)
    token = Column(String(512), unique=True, index=True, nullable=False)

    # Relación con la tabla de usuarios (usuarios.id)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Momento en el que se revocó el token (se hace logout)
    fecha_revocado = Column(
        DateTime,
        default=datetime.utcnow,  # Se setea automáticamente al momento de insertar
        nullable=False,
    )

    # Momento en el que el token expiraría de forma natural (campo opcional)
    expira_en = Column(DateTime, nullable=True)

    # Relación ORM para poder acceder al usuario desde el token si lo necesitamos
    usuario = relationship("Usuario", backref="tokens_revocados")
