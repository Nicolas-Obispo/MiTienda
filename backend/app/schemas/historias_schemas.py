# app/schemas/historias_schemas.py
"""
Schemas Pydantic: Historias

Reglas:
- Schemas = validación y serialización
- Sin lógica de negocio
- Pydantic v1 (migración a v2 pendiente)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HistoriaBase(BaseModel):
    """
    Campos comunes a creación y lectura.
    """

    media_url: str
    expira_en: datetime
    publicacion_id: Optional[int] = None
    is_activa: bool = True


class HistoriaCreate(HistoriaBase):
    """
    Schema para crear una historia.
    El comercio se obtiene del contexto (no del body).
    """

    pass


class HistoriaRead(HistoriaBase):
    """
    Schema de lectura de historia.
    """

    id: int
    comercio_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
