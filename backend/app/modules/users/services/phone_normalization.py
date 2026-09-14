"""Owner backend unico de normalizacion de telefonos privados."""

from __future__ import annotations

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat


DEFAULT_PHONE_REGION = "AR"


class InvalidPhoneError(ValueError):
    """El valor no representa un numero telefonico valido."""


def canonicalize_phone(value: str, *, default_region: str = DEFAULT_PHONE_REGION) -> str:
    """Valida un telefono real y devuelve su representacion canonica E.164."""

    if not isinstance(value, str) or not value.strip():
        raise InvalidPhoneError("telefono_invalido")
    try:
        parsed = phonenumbers.parse(value, default_region)
    except NumberParseException as exc:
        raise InvalidPhoneError("telefono_invalido") from exc
    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhoneError("telefono_invalido")
    canonical = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    if len(canonical) > 16:
        raise InvalidPhoneError("telefono_invalido")
    return canonical
