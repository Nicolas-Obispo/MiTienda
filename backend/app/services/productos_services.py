"""
productos_services.py
-----------------------
Este módulo contiene TODA la lógica de negocio relacionada a los productos.

✅ IMPORTANTE:
- Acá NO se manejan rutas HTTP (eso lo hace el router).
- Acá NO se hacen validaciones de entrada (eso lo hace schemas).
- Acá SÍ se accede a la base de datos.
- Acá SÍ se implementan funciones que manipulan productos.

El objetivo es que este archivo sea limpio, ordenado y fácil de mantener.
"""

# Importamos Session para leer/escribir datos en la DB
from sqlalchemy.orm import Session

# Modelo ORM → representa la tabla 'productos' en la base de datos
from app.models.productos_models import Producto

# Schema para crear productos → valida qué datos deben venir del frontend
from app.schemas.productos_schemas import (
    ProductoCreate,
    ProductoUpdate
)





def obtener_todos_los_productos(db: Session):
    """
    Obtiene todos los registros de la tabla 'productos'.

    ✅ Recibe:
        db: sesión de base de datos (inyectada por FastAPI)

    ✅ Devuelve:
        Lista con objetos Producto provenientes de la DB.
    """
    return db.query(Producto).all()


def crear_producto(db: Session, producto_data: ProductoCreate):
    """
    Crea un nuevo producto en la base de datos.

    ✅ Recibe:
        db: sesión de base de datos
        producto_data: datos validados del frontend (ProductoCreate)

    ✅ Proceso:
        - Construye un objeto Producto (modelo ORM)
        - Lo agrega a la sesión
        - Commit para guardar
        - Refresh para obtener el ID generado

    ✅ Devuelve:
        El producto recién creado, incluyendo su 'id'
    """

    nuevo_producto = Producto(
        nombre=producto_data.nombre,
        descripcion=producto_data.descripcion,
        precio=producto_data.precio,
        stock=producto_data.stock
    )

    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)

    return nuevo_producto

# ✅ Obtener un producto por ID
def obtener_producto_por_id(db: Session, producto_id: int):
    """
    Devuelve un producto según su ID.

    Si no existe, devuelve None.
    """
    return db.query(Producto).filter(Producto.id == producto_id).first()


def actualizar_producto(db: Session, producto_id: int, datos: ProductoUpdate):
    """
    Actualiza un producto existente en la base de datos.

    ✅ Recibe:
        db: sesión de base de datos
        producto_id: ID del producto a modificar
        datos: campos a actualizar (ProductoUpdate)

    ✅ Proceso:
        - Buscar el producto por ID
        - Si no existe → devolver None
        - Actualizar solo los campos enviados
        - Guardar cambios en DB

    ✅ Devuelve:
        Producto actualizado
    """
    producto = db.query(Producto).filter(Producto.id == producto_id).first()

    if not producto:
        return None

    # Solo actualizamos campos enviados
    if datos.nombre is not None:
        producto.nombre = datos.nombre

    if datos.descripcion is not None:
        producto.descripcion = datos.descripcion

    if datos.precio is not None:
        producto.precio = datos.precio

    if datos.stock is not None:
        producto.stock = datos.stock

    db.commit()
    db.refresh(producto)

    return producto


def actualizar_producto(db: Session, producto_id: int, producto_data: ProductoUpdate):
    """
    Actualiza parcialmente un producto existente en la base de datos.

    ✅ Recibe:
        db: sesión de base de datos
        producto_id: ID del producto a modificar
        producto_data: datos nuevos validados (ProductoUpdate)

    ✅ Proceso:
        - Busca el producto por ID
        - Si no existe → devuelve None
        - Actualiza solo los campos enviados (PATCH/PUT parcial)

    ✅ Devuelve:
        El producto actualizado
    """

    # Buscar producto existente
    producto = db.query(Producto).filter(Producto.id == producto_id).first()

    if not producto:
        return None  # El router lo convertirá en error HTTP

    # Actualización parcial: solo los campos enviados
    if producto_data.nombre is not None:
        producto.nombre = producto_data.nombre

    if producto_data.descripcion is not None:
        producto.descripcion = producto_data.descripcion

    if producto_data.precio is not None:
        producto.precio = producto_data.precio

    if producto_data.stock is not None:
        producto.stock = producto_data.stock

    # Guardar cambios en la DB
    db.commit()
    db.refresh(producto)

    return producto

def buscar_productos_por_nombre(db: Session, nombre: str):
    """
    Busca productos cuyo nombre contenga el texto ingresado (búsqueda parcial).

    ✅ Ejemplo:
        'zap' → Zapatillas Nike, Zapatillas AirMax, etc.
    """

    return db.query(Producto).filter(Producto.nombre.like(f"%{nombre}%")).all()

def eliminar_producto(db: Session, producto_id: int):
    """
    Elimina un producto por su ID.
    Si no existe, devuelve None.
    """

    producto = db.query(Producto).filter(Producto.id == producto_id).first()

    if not producto:
        return None

    db.delete(producto)
    db.commit()

    return True
