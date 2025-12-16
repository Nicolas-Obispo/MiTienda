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

    class Config:
        orm_mode = True
