"""
sugerencias_busqueda_schemas.py
-------------------------------
Schemas para sugerencias predictivas del buscador.
"""

from typing import Literal

from pydantic import BaseModel


class SugerenciaBusqueda(BaseModel):
    type: Literal["rubro", "categoria", "subcategoria", "especialidad"]
    id: int
    label: str
    score: float


class SugerenciasBusquedaResponse(BaseModel):
    query: str
    suggestions: list[SugerenciaBusqueda]
