# productos_routers.py
# ---------------------
# Rutas HTTP para Productos.
# Esta capa solo recibe requests HTTP y delega la lógica a productos_services.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.auth import obtener_usuario_actual      # 🔐 Protección JWT
from app.core.database import get_db

# Esquemas Pydantic
from app.schemas.productos_schemas import (
    ProductoCreate,
    ProductoUpdate,
    ProductoInDB
)

# Servicios (lógica de negocio)
from app.services.productos_services import (
    obtener_todos_los_productos,
    crear_producto,
    obtener_producto_por_id,
    actualizar_producto,
    eliminar_producto,
    buscar_productos_por_nombre
)

# Crear router
router = APIRouter(
    prefix="/productos",
    tags=["Productos"]
)


# -----------------------------------------
# 🔍 Buscar productos por nombre
# -----------------------------------------
@router.get("/buscar", response_model=list[ProductoInDB])
def buscar_productos(nombre: str, db: Session = Depends(get_db)):
    """
    Busca productos cuyo nombre contenga el texto dado.
    """
    return buscar_productos_por_nombre(db, nombre)


# -----------------------------------------
# 🏓 Ping
# -----------------------------------------
@router.get("/ping")
def ping():
    return {"mensaje": "✅ Productos funcionando"}


# -----------------------------------------
# 📌 Listar todos los productos (PROTEGIDO)
# -----------------------------------------
@router.get("/", response_model=list[ProductoInDB])
def listar_productos(
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    """
    Lista todos los productos — requiere token válido.
    """
    return obtener_todos_los_productos(db)


# -----------------------------------------
# ➕ Crear producto (PROTEGIDO)
# -----------------------------------------
@router.post("/crear", response_model=ProductoInDB)
def crear_nuevo_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    """
    Crea un nuevo producto — requiere token válido.
    """
    return crear_producto(db, producto)


# -----------------------------------------
# 🔎 Obtener producto por ID (PROTEGIDO)
# -----------------------------------------
@router.get("/{producto_id}", response_model=ProductoInDB)
def obtener_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    """
    Obtiene un producto específico — requiere token válido.
    """
    producto = obtener_producto_por_id(db, producto_id)

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return producto


# -----------------------------------------
# ✏️ Actualizar producto (PROTEGIDO)
# -----------------------------------------
@router.put("/{producto_id}", response_model=ProductoInDB)
def actualizar_producto_existente(
    producto_id: int,
    producto: ProductoUpdate,
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    """
    Actualiza un producto — requiere token válido.
    """
    producto_actualizado = actualizar_producto(db, producto_id, producto)

    if not producto_actualizado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return producto_actualizado


# -----------------------------------------
# 🗑️ Eliminar producto (PROTEGIDO)
# -----------------------------------------
@router.delete("/{producto_id}")
def eliminar_producto_existente(
    producto_id: int,
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    """
    Elimina un producto — requiere token válido.
    """
    producto_eliminado = eliminar_producto(db, producto_id)

    if not producto_eliminado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return {"mensaje": "Producto eliminado correctamente"}
