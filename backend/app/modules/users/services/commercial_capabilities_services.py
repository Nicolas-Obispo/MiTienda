"""Owner backend de readiness y capabilities comerciales personales."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.documentos_aceptacion_services import (
    tiene_aceptaciones_obligatorias_vigentes,
)


COMMERCIAL_CAPABILITY_NAMES = frozenset(
    {
        "puede_crear_espacio",
        "puede_administrar_espacios",
        "puede_publicar_en_espacios",
    }
)
COMMERCIAL_CAPABILITY_REQUIRED_CODE = "commercial_capability_required"


class UnknownCommercialCapabilityError(ValueError):
    """La ruta solicitante debe usar solamente capabilities comerciales oficiales."""


class CommercialCapabilityRequiredError(PermissionError):
    """Rechazo de dominio sin exponer el requisito comercial faltante."""

    public_code = COMMERCIAL_CAPABILITY_REQUIRED_CODE
from app.modules.users.services.profile_status_services import (
    ProfileStatus,
    calculate_age,
    derive_profile_status,
)


@dataclass(frozen=True)
class CommercialCapabilities:
    puede_crear_espacio: bool
    puede_administrar_espacios: bool
    puede_publicar_en_espacios: bool


@dataclass(frozen=True)
class CommercialReadiness:
    capabilities: CommercialCapabilities
    pendientes_comerciales: tuple[str, ...]
    profile_status: ProfileStatus


def derive_commercial_readiness(
    db: Session,
    usuario: Usuario,
    *,
    today: date | None = None,
) -> CommercialReadiness:
    """Deriva readiness personal sin persistirla ni aplicar reglas de recurso."""
    profile_status = derive_profile_status(usuario, today=today)
    legal_current = tiene_aceptaciones_obligatorias_vigentes(db, usuario.id)
    try:
        age = calculate_age(usuario.fecha_nacimiento, today=today)
    except ValueError:
        age = None

    account_enabled = usuario.id is not None
    adult = age is not None and age >= 18
    allowed = (
        account_enabled
        and legal_current
        and profile_status.perfil_completo
        and adult
    )
    capabilities = CommercialCapabilities(
        puede_crear_espacio=allowed,
        puede_administrar_espacios=allowed,
        puede_publicar_en_espacios=allowed,
    )

    pending: list[str] = []
    if not profile_status.perfil_completo:
        pending.append("perfil_incompleto")
    if not legal_current:
        pending.append("aceptaciones_legales_pendientes")
    if not adult:
        pending.append("mayoria_edad_requerida")

    return CommercialReadiness(
        capabilities=capabilities,
        pendientes_comerciales=tuple(pending),
        profile_status=profile_status,
    )


def commercial_capability_http_detail() -> dict[str, str]:
    """Detalle opt-in para que la capa HTTP exponga solo el codigo aprobado."""
    return {
        "message": "No autorizado",
        "public_code": COMMERCIAL_CAPABILITY_REQUIRED_CODE,
    }


def require_commercial_capability(
    db: Session,
    usuario: Usuario,
    capability: str,
    *,
    today: date | None = None,
) -> CommercialReadiness:
    """Exige una capability solo cuando el enforcement backend esta activado.

    Este guard no autentica, no resuelve recursos ni comprueba ownership. Las
    rutas futuras deben llamarlo despues de esos owners cuando exista recurso.
    """
    if capability not in COMMERCIAL_CAPABILITY_NAMES:
        raise UnknownCommercialCapabilityError("commercial_capability_unknown")

    readiness = derive_commercial_readiness(db, usuario, today=today)
    if not settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED:
        return readiness

    if not getattr(readiness.capabilities, capability):
        raise CommercialCapabilityRequiredError("commercial_capability_required")

    return readiness
