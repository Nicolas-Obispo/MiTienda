"""
rubros_routers.py
-----------------
Rutas HTTP para Rubros.

- Solo lectura
- Públicos (no requieren login)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.products.schemas.rubros_schemas import (
    RubroEspecialidadResponse,
    RubroResponse,
)
from app.modules.products.services.rubros_services import (
    listar_especialidades_por_rubro,
    listar_rubros,
    listar_rubros_secundarios_sugeridos,
    obtener_rubro_por_id
)

router = APIRouter(
    prefix="/rubros",
    tags=["Rubros"]
)


@router.get("/", response_model=list[RubroResponse])
def listar_rubros_endpoint(db: Session = Depends(get_db)):
    """
    Devuelve todos los rubros activos.
    """
    return listar_rubros(db)


@router.get("/{rubro_id}/secundarios", response_model=list[RubroResponse])
def listar_rubros_secundarios_endpoint(
    rubro_id: int,
    db: Session = Depends(get_db),
):
    """
    Devuelve rubros secundarios sugeridos por Discovery.
    """
    rubros = listar_rubros_secundarios_sugeridos(db, rubro_id)

    if rubros is None:
        raise HTTPException(status_code=404, detail="Rubro no encontrado")

    return rubros


@router.get(
    "/{rubro_id}/especialidades",
    response_model=list[RubroEspecialidadResponse],
)
def listar_especialidades_rubro_endpoint(
    rubro_id: int,
    db: Session = Depends(get_db),
):
    """
    Devuelve especialidades Discovery del rubro principal.
    """
    especialidades = listar_especialidades_por_rubro(db, rubro_id)

    if especialidades is None:
        raise HTTPException(status_code=404, detail="Rubro no encontrado")

    return especialidades


@router.get("/{rubro_id}", response_model=RubroResponse)
def obtener_rubro_endpoint(rubro_id: int, db: Session = Depends(get_db)):
    """
    Devuelve un rubro por ID.
    """
    rubro = obtener_rubro_por_id(db, rubro_id)

    if not rubro:
        raise HTTPException(status_code=404, detail="Rubro no encontrado")

    return rubro
