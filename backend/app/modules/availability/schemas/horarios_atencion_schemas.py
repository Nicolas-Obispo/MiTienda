"""
Schemas Pydantic para horarios habituales de atencion.
"""

from datetime import datetime, time
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EstadoHorario(str, Enum):
    abierto = "abierto"
    cerrado = "cerrado"
    sin_horarios = "sin_horarios"


class HorarioAtencionFranjaEntrada(BaseModel):
    dia_semana: int = Field(ge=0, le=6)
    hora_apertura: time
    hora_cierre: time

    @model_validator(mode="after")
    def validar_rango_horario(self):
        if self.hora_apertura >= self.hora_cierre:
            raise ValueError(
                "hora_apertura debe ser menor que hora_cierre; "
                "los cruces de medianoche no estan permitidos"
            )

        return self


class HorariosAtencionReemplazo(BaseModel):
    franjas: list[HorarioAtencionFranjaEntrada]


class HorarioAtencionFranjaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dia_semana: int
    hora_apertura: time
    hora_cierre: time


class EstadoHorarioResponse(BaseModel):
    estado: EstadoHorario
    texto: str
    zona_horaria: str
    evaluado_en: datetime | None = None
    cierre_actual: datetime | None = None
    proxima_apertura: datetime | None = None


class HorariosAtencionResponse(BaseModel):
    comercio_id: int
    zona_horaria: str
    franjas: list[HorarioAtencionFranjaResponse]
    estado_horario: EstadoHorarioResponse
