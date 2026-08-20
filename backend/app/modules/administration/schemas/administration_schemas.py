from pydantic import BaseModel


class MyAdministrativeCapabilitiesResponse(BaseModel):
    es_operador: bool
    capacidades: list[str]
