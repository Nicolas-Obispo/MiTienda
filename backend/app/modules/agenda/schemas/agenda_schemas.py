"""
Schemas Pydantic para contratos privados del modulo Agenda.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.agenda.models.agenda_models import (
    EstadoContextoAgendable,
    EstadoElementoAgenda,
    TipoElementoAgenda,
)


def _normalizar_texto(valor: str | None) -> str | None:
    if valor is None:
        return None

    valor_normalizado = " ".join(valor.strip().split())
    return valor_normalizado or None


def _normalizar_datetime_utc(valor: datetime | None) -> datetime | None:
    if valor is None:
        return None

    if valor.tzinfo is None or valor.utcoffset() is None:
        raise ValueError("datetime debe incluir zona horaria")

    return valor.astimezone(UTC)


def _validar_rango_temporal(inicio: datetime | None, fin: datetime | None) -> None:
    if inicio is not None and fin is not None and fin <= inicio:
        raise ValueError("fin debe ser posterior a inicio")


def _validar_reglas_por_tipo(
    *,
    tipo: TipoElementoAgenda | None,
    inicio: datetime | None,
    fin: datetime | None,
    todo_el_dia: bool | None,
    validar_requeridos: bool,
) -> None:
    _validar_rango_temporal(inicio, fin)

    if todo_el_dia is True and inicio is None:
        raise ValueError("todo_el_dia requiere inicio")

    if not validar_requeridos or tipo is None:
        return

    if tipo in (TipoElementoAgenda.evento, TipoElementoAgenda.recordatorio) and inicio is None:
        raise ValueError(f"{tipo.value} requiere inicio")

    if tipo == TipoElementoAgenda.bloqueo and (inicio is None or fin is None):
        raise ValueError("bloqueo requiere inicio y fin")


class AgendaSchemaBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContextoAgendableResponse(AgendaSchemaBase):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    estado: EstadoContextoAgendable
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def normalizar_datetime(cls, valor: datetime) -> datetime:
        return _normalizar_datetime_utc(valor)


class ContextoAgendableCambioEstado(AgendaSchemaBase):
    estado: EstadoContextoAgendable


class ElementoAgendaCreate(AgendaSchemaBase):
    tipo: TipoElementoAgenda
    titulo: str = Field(min_length=1)
    descripcion: str | None = None
    inicio: datetime | None = None
    fin: datetime | None = None
    todo_el_dia: bool = False

    @field_validator("titulo")
    @classmethod
    def normalizar_titulo(cls, valor: str) -> str:
        valor_normalizado = _normalizar_texto(valor)
        if valor_normalizado is None:
            raise ValueError("titulo no puede estar vacio")
        return valor_normalizado

    @field_validator("descripcion")
    @classmethod
    def normalizar_descripcion(cls, valor: str | None) -> str | None:
        return _normalizar_texto(valor)

    @field_validator("inicio", "fin")
    @classmethod
    def normalizar_datetime(cls, valor: datetime | None) -> datetime | None:
        return _normalizar_datetime_utc(valor)

    @model_validator(mode="after")
    def validar_reglas(self):
        _validar_reglas_por_tipo(
            tipo=self.tipo,
            inicio=self.inicio,
            fin=self.fin,
            todo_el_dia=self.todo_el_dia,
            validar_requeridos=True,
        )
        return self


class ElementoAgendaUpdate(AgendaSchemaBase):
    version_esperada: int = Field(ge=1)
    tipo: TipoElementoAgenda | None = None
    estado: EstadoElementoAgenda | None = None
    titulo: str | None = None
    descripcion: str | None = None
    inicio: datetime | None = None
    fin: datetime | None = None
    todo_el_dia: bool | None = None

    @field_validator("titulo")
    @classmethod
    def normalizar_titulo(cls, valor: str | None) -> str | None:
        valor_normalizado = _normalizar_texto(valor)
        if valor is not None and valor_normalizado is None:
            raise ValueError("titulo no puede estar vacio")
        return valor_normalizado

    @field_validator("descripcion")
    @classmethod
    def normalizar_descripcion(cls, valor: str | None) -> str | None:
        return _normalizar_texto(valor)

    @field_validator("inicio", "fin")
    @classmethod
    def normalizar_datetime(cls, valor: datetime | None) -> datetime | None:
        return _normalizar_datetime_utc(valor)

    @model_validator(mode="after")
    def validar_reglas(self):
        _validar_reglas_por_tipo(
            tipo=self.tipo,
            inicio=self.inicio,
            fin=self.fin,
            todo_el_dia=self.todo_el_dia,
            validar_requeridos=self.tipo is not None,
        )
        return self


class ElementoAgendaCambioEstado(AgendaSchemaBase):
    version_esperada: int = Field(ge=1)
    estado: EstadoElementoAgenda


class ElementoAgendaFiltros(AgendaSchemaBase):
    tipo: TipoElementoAgenda | None = None
    estado: EstadoElementoAgenda | None = None
    inicio: datetime | None = None
    fin: datetime | None = None
    todo_el_dia: bool | None = None
    incluir_sin_fecha: bool = False

    @field_validator("inicio", "fin")
    @classmethod
    def normalizar_datetime(cls, valor: datetime | None) -> datetime | None:
        return _normalizar_datetime_utc(valor)

    @model_validator(mode="after")
    def validar_rango(self):
        _validar_rango_temporal(self.inicio, self.fin)
        return self


class ElementoAgendaResponse(AgendaSchemaBase):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    contexto_id: int
    tipo: TipoElementoAgenda
    estado: EstadoElementoAgenda
    version: int
    titulo: str
    descripcion: str | None = None
    inicio: datetime | None = None
    fin: datetime | None = None
    todo_el_dia: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("inicio", "fin", "created_at", "updated_at")
    @classmethod
    def normalizar_datetime(cls, valor: datetime | None) -> datetime | None:
        return _normalizar_datetime_utc(valor)
