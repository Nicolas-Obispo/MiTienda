# productos_models.py
# --------------------
# Modelo ORM que representa la tabla "productos" en la base de datos.
# Este archivo forma parte de la capa MODELS del backend.
# Aquí solo definimos la estructura de la tabla usando SQLAlchemy.

from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base


class Producto(Base):
    """
    Modelo ORM del producto.
    Representa un ítem vendible dentro del sistema MiTienda.
    """
    __tablename__ = "productos"  # Nombre exacto de la tabla en la base de datos

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(500))
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
