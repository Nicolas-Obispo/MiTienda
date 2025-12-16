"""
usuarios_models.py
-------------------
Modelo ORM para la tabla 'usuarios'.

Este modelo es compartido entre MiTienda y MiPlaza.
Los campos agregados para MiPlaza fueron diseñados
para no romper compatibilidad con usuarios existentes.
"""

from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base
from sqlalchemy.orm import relationship



class Usuario(Base):
    __tablename__ = "usuarios"

    # -----------------------------
    # Campos existentes (MiTienda)
    # -----------------------------

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)

    # Contraseña hasheada (NO se modifica)
    hashed_password = Column(String(255), nullable=False)

    # -----------------------------
    # Campos agregados para MiPlaza
    # -----------------------------

    # Modo activo del usuario dentro de la plataforma
    # Valores esperados:
    # - "usuario"     → consumidor
    # - "publicador"  → comerciante / servicio
    # Default seguro para usuarios existentes
    modo_activo = Column(String(20), nullable=False, default="usuario")

    # Indica si el usuario completó el onboarding inicial
    # (selección de provincia y ciudad)
    onboarding_completo = Column(Boolean, nullable=False, default=False)

    # Ubicación base del usuario (descubrimiento local)
    # Son opcionales para no romper registros existentes
    provincia = Column(String(100), nullable=True)
    ciudad = Column(String(100), nullable=True)

    # -------------------------
    # Likes en publicaciones
    # -------------------------
    likes_publicaciones = relationship(
        "LikePublicacion",
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
