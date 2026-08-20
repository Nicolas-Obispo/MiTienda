from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.administration.capabilities import (
    ADMINISTRATIVE_CAPABILITIES,
    validate_administrative_capability,
)
from app.modules.administration.models.administrative_capability_events_models import (
    AdministrativeCapabilityEvent,
)
from app.modules.users.models.usuarios_models import Usuario

GRANT_ACTION = "grant"
REVOKE_ACTION = "revoke"
VALID_ACTIONS = frozenset({GRANT_ACTION, REVOKE_ACTION})
BOOTSTRAP_SOURCE = "local_bootstrap"


class AdministrativeUserNotFoundError(ValueError):
    pass


def _latest_events_query(db: Session, usuario_id: int):
    latest_ids = (
        db.query(func.max(AdministrativeCapabilityEvent.id).label("event_id"))
        .filter(AdministrativeCapabilityEvent.usuario_id == usuario_id)
        .group_by(AdministrativeCapabilityEvent.capability)
        .subquery()
    )
    return db.query(AdministrativeCapabilityEvent).join(
        latest_ids,
        AdministrativeCapabilityEvent.id == latest_ids.c.event_id,
    )


def list_active_administrative_capabilities(
    db: Session,
    *,
    usuario_id: int,
) -> list[str]:
    events = _latest_events_query(db, usuario_id).all()
    return sorted(
        event.capability
        for event in events
        if event.action == GRANT_ACTION
        and event.capability in ADMINISTRATIVE_CAPABILITIES
    )


def user_has_administrative_capability(
    db: Session,
    *,
    usuario_id: int,
    capability: str,
) -> bool:
    validate_administrative_capability(capability)
    latest_event = (
        db.query(AdministrativeCapabilityEvent)
        .filter(
            AdministrativeCapabilityEvent.usuario_id == usuario_id,
            AdministrativeCapabilityEvent.capability == capability,
        )
        .order_by(AdministrativeCapabilityEvent.id.desc())
        .first()
    )
    return latest_event is not None and latest_event.action == GRANT_ACTION


def record_administrative_capability_change(
    db: Session,
    *,
    usuario_id: int,
    capability: str,
    action: str,
    source: str,
    reason: str,
    actor_usuario_id: int | None = None,
) -> tuple[AdministrativeCapabilityEvent | None, bool]:
    validate_administrative_capability(capability)
    if action not in VALID_ACTIONS:
        raise ValueError(f"Accion administrativa desconocida: {action}")
    if not source.strip():
        raise ValueError("source es obligatorio")
    if not reason.strip():
        raise ValueError("reason es obligatorio")
    if len(source.strip()) > 40:
        raise ValueError("source excede 40 caracteres")
    if len(reason.strip()) > 500:
        raise ValueError("reason excede 500 caracteres")

    if db.get(Usuario, usuario_id) is None:
        raise AdministrativeUserNotFoundError("Usuario no encontrado")
    if actor_usuario_id is not None and db.get(Usuario, actor_usuario_id) is None:
        raise AdministrativeUserNotFoundError("Actor no encontrado")

    latest_event = (
        db.query(AdministrativeCapabilityEvent)
        .filter(
            AdministrativeCapabilityEvent.usuario_id == usuario_id,
            AdministrativeCapabilityEvent.capability == capability,
        )
        .order_by(AdministrativeCapabilityEvent.id.desc())
        .first()
    )
    if latest_event is not None and latest_event.action == action:
        return latest_event, False
    if latest_event is None and action == REVOKE_ACTION:
        return None, False

    event = AdministrativeCapabilityEvent(
        usuario_id=usuario_id,
        capability=capability,
        action=action,
        actor_usuario_id=actor_usuario_id,
        source=source.strip(),
        reason=reason.strip(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event, True
