"""Derivaciones backend del perfil privado del Usuario."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.phone_normalization import InvalidPhoneError, canonicalize_phone
BUSINESS_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")
PROFILE_FIELD_ORDER = (
    "provincia",
    "ciudad",
    "fecha_nacimiento",
    "telefono",
    "email_verificado",
)


@dataclass(frozen=True)
class ProfileStatus:
    perfil_completo: bool
    campos_perfil_faltantes: tuple[str, ...]


def business_date(*, now: datetime | None = None) -> date:
    instant = now or datetime.now(tz=BUSINESS_TIMEZONE)
    if instant.tzinfo is None:
        raise ValueError("now_debe_tener_timezone")
    return instant.astimezone(BUSINESS_TIMEZONE).date()


def calculate_age(birth_date: date | None, *, today: date | None = None) -> int | None:
    if birth_date is None:
        return None
    current_date = today or business_date()
    if birth_date > current_date:
        raise ValueError("fecha_nacimiento_futura")
    return current_date.year - birth_date.year - (
        (current_date.month, current_date.day) < (birth_date.month, birth_date.day)
    )


def _valid_text(value: str | None) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_phone(value: str | None) -> bool:
    if value is None:
        return False
    try:
        return canonicalize_phone(value) == value
    except InvalidPhoneError:
        return False


def derive_profile_status(usuario: Usuario, *, today: date | None = None) -> ProfileStatus:
    missing: list[str] = []
    if not _valid_text(usuario.provincia):
        missing.append("provincia")
    if not _valid_text(usuario.ciudad):
        missing.append("ciudad")
    try:
        valid_birth_date = calculate_age(usuario.fecha_nacimiento, today=today) is not None
    except ValueError:
        valid_birth_date = False
    if not valid_birth_date:
        missing.append("fecha_nacimiento")
    if not _valid_phone(usuario.telefono_e164):
        missing.append("telefono")
    if usuario.email_verified_at is None:
        missing.append("email_verificado")
    return ProfileStatus(
        perfil_completo=not missing,
        campos_perfil_faltantes=tuple(missing),
    )
