"""
usuarios_models.py
-------------------
Modelo ORM para la tabla 'usuarios'.
"""

from sqlalchemy import Column, Integer, String
from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)   # 👈 contraseña hasheada
