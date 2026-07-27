"""
Conversion temporal interna del modulo Agenda.

Agenda opera en UTC. MySQL almacena DATETIME sin timezone, por lo que la capa de
servicios convierte al escribir y al leer.
"""

from datetime import UTC, datetime


def asegurar_aware_utc(valor: datetime | None) -> datetime | None:
    if valor is None:
        return None

    if valor.tzinfo is None or valor.utcoffset() is None:
        raise ValueError("datetime debe incluir zona horaria")

    return valor.astimezone(UTC)


def datetime_para_db(valor: datetime | None) -> datetime | None:
    valor_utc = asegurar_aware_utc(valor)
    if valor_utc is None:
        return None

    return valor_utc.replace(tzinfo=None)


def datetime_desde_db(valor: datetime | None) -> datetime | None:
    if valor is None:
        return None

    if valor.tzinfo is None or valor.utcoffset() is None:
        return valor.replace(tzinfo=UTC)

    return valor.astimezone(UTC)
