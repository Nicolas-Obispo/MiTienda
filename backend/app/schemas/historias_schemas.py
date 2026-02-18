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

    ETAPA 44:
    - Agregamos vista_by_me.
    - Este campo representa estado de negocio por usuario.
    - El backend debe resolverlo.
    - El frontend solo lo renderiza.
    """

    id: int
    comercio_id: int
    created_at: datetime
    updated_at: datetime

    # NUEVO — estado real por usuario
    vista_by_me: bool = False

    class Config:
        orm_mode = True

# --------------------------------------------------
# ETAPA 47 — Item para barra de historias
# --------------------------------------------------

class HistoriasBarItem(BaseModel):
    """
    Item agregado para la barra de historias.

    Representa un comercio que tiene al menos
    una historia activa y no expirada.
    """

    comercioId: int
    nombre: str

    # Importante:
    # El frontend espera "thumbnailUrl"
    # aunque en DB el campo sea "portada_url"
    thumbnailUrl: Optional[str] = None

    cantidad: int          # total de historias activas
    pendientes: int        # historias NO vistas por el usuario

