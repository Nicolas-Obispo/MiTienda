"""
productos_services.py
---------------------
Servicios de lectura para productos legacy.

El dominio Productos e Inventario fue diferido por roadmap. Hasta que exista
ownership oficial para este recurso, sus mutaciones legacy permanecen
deshabilitadas en la capa de servicio.
"""

from sqlalchemy.orm import Session

from app.modules.products.models.productos_models import Producto
from app.modules.products.schemas.productos_schemas import (
    ProductoCreate,
    ProductoUpdate,
)


class ProductosLegacyMutacionesDeshabilitadasError(Exception):
    """Indica que las mutaciones legacy de productos no estan habilitadas."""


def obtener_todos_los_productos(db: Session):
    """Obtiene todos los registros de la tabla legacy 'productos'."""
    return db.query(Producto).all()


def crear_producto(db: Session, producto_data: ProductoCreate):
    """Bloquea la creacion legacy hasta definir ownership oficial."""
    raise ProductosLegacyMutacionesDeshabilitadasError


def obtener_producto_por_id(db: Session, producto_id: int):
    """Devuelve un producto legacy por ID o None si no existe."""
    return db.query(Producto).filter(Producto.id == producto_id).first()


def actualizar_producto(db: Session, producto_id: int, producto_data: ProductoUpdate):
    """Bloquea la actualizacion legacy hasta definir ownership oficial."""
    raise ProductosLegacyMutacionesDeshabilitadasError


def buscar_productos_por_nombre(db: Session, nombre: str):
    """Busca productos legacy cuyo nombre contenga el texto indicado."""
    return db.query(Producto).filter(Producto.nombre.like(f"%{nombre}%")).all()


def eliminar_producto(db: Session, producto_id: int):
    """Bloquea la eliminacion legacy hasta definir ownership oficial."""
    raise ProductosLegacyMutacionesDeshabilitadasError
