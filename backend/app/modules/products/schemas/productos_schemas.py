# productos_schemas.py
# ----------------------
# Esquemas (Pydantic) usados para validar datos de entrada y salida
# relacionados con productos dentro de MiTienda.
# Esta capa NO interactúa con la base de datos; solo define reglas de validación.

from pydantic import BaseModel
from typing import Optional


class ProductoBase(BaseModel):
    """
    Esquema base con atributos compartidos entre creación,
    lectura y actualización de productos.
    """
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int


class ProductoCreate(ProductoBase):
    """Esquema para crear un nuevo producto."""
    pass


class ProductoUpdate(BaseModel):
    """Esquema para actualizar parcialmente un producto existente."""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    stock: Optional[int] = None


class ProductoInDB(ProductoBase):
    """
    Esquema que representa un producto almacenado en la base de datos.
    Incluye el campo id autogenerado por la DB.
    """
    id: int

    class Config:
        from_attributes = True  # Permite convertir modelos ORM → Pydantic
