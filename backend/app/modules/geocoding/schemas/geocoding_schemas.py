import math
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ForwardGeocodingRequest(BaseModel):
    query: str = Field(min_length=3, max_length=200)
    ciudad: Optional[str] = Field(default=None, max_length=100)
    provincia: Optional[str] = Field(default=None, max_length=100)
    pais: str = Field(default="Argentina", max_length=100)
    limit: int = Field(default=5, ge=1, le=5)

    @field_validator("query", "ciudad", "provincia", "pais")
    @classmethod
    def normalizar_texto(cls, value):
        if value is None:
            return None
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("el texto no puede estar vacio")
        return normalized

    @field_validator("pais")
    @classmethod
    def validar_pais(cls, value: str) -> str:
        if value.casefold() != "argentina":
            raise ValueError("el contexto soportado es Argentina")
        return "Argentina"


class ReverseGeocodingRequest(BaseModel):
    latitud: float
    longitud: float

    @field_validator("latitud")
    @classmethod
    def validar_latitud(cls, value: float) -> float:
        if not math.isfinite(value) or not -90 <= value <= 90:
            raise ValueError("latitud invalida")
        return value

    @field_validator("longitud")
    @classmethod
    def validar_longitud(cls, value: float) -> float:
        if not math.isfinite(value) or not -180 <= value <= 180:
            raise ValueError("longitud invalida")
        return value


class GeocodingLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    latitud: float
    longitud: float
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    pais: Optional[str] = None
    precision: Literal["address", "street", "locality", "region", "unknown"] = "unknown"
    confidence: Optional[float] = Field(default=None, ge=0, le=1)

    @field_validator("latitud")
    @classmethod
    def validar_latitud(cls, value: float) -> float:
        if not math.isfinite(value) or not -90 <= value <= 90:
            raise ValueError("latitud invalida")
        return value

    @field_validator("longitud")
    @classmethod
    def validar_longitud(cls, value: float) -> float:
        if not math.isfinite(value) or not -180 <= value <= 180:
            raise ValueError("longitud invalida")
        return value


class GeocodingAttribution(BaseModel):
    label: str
    url: str


class ForwardGeocodingResponse(BaseModel):
    alternativas: list[GeocodingLocation]
    attribution: Optional[GeocodingAttribution] = None


class ReverseGeocodingResponse(BaseModel):
    propuesta: Optional[GeocodingLocation] = None
    attribution: Optional[GeocodingAttribution] = None


class TerritoryResolutionResponse(BaseModel):
    city_key: str
    province_code: str
    country_code: Literal["AR"] = "AR"
    city: str
    province: str
    country: str = "Argentina"
    attribution: Optional[GeocodingAttribution] = None
