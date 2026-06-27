"""
rubros_schemas.py
-----------------
Schemas Pydantic para Rubros (MiPlaza).

Solo lectura.
Los rubros son controlados por el sistema.
"""

from pydantic import BaseModel


class RubroResponse(BaseModel):
    id: int
    nombre: str

    model_config = {
        "from_attributes": True
    }


class RubroEspecialidadResponse(BaseModel):
    id: int
    slug: str
    nombre: str
    descripcion: str | None = None
    orden: int

    model_config = {
        "from_attributes": True
    }
