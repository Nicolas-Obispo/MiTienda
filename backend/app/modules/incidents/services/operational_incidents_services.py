import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.administration.capabilities import OPERATIONS_INCIDENTS_MANAGE
from app.modules.administration.services.administrative_authorization_services import user_has_administrative_capability
from app.modules.incidents.constants import TRANSITIONS
from app.modules.incidents.models.operational_incidents_models import OperationalIncident, OperationalIncidentEvent
from app.modules.users.models.usuarios_models import Usuario
from app.modules.notifications.services.operational_notification_services import (
    enqueue_incident_escalated,
    enqueue_incident_opened,
)


class IncidentNotFoundError(ValueError): pass
class IncidentConflictError(ValueError): pass
class IncidentOwnerInvalidError(ValueError): pass


def _fingerprint(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _owner_is_operator(db: Session, usuario_id: int) -> bool:
    return db.get(Usuario, usuario_id) is not None and user_has_administrative_capability(
        db, usuario_id=usuario_id, capability=OPERATIONS_INCIDENTS_MANAGE
    )


def _source_fields(source) -> dict:
    if source is None:
        return {"evidence_type": None, "evidence_reference": None, "request_id": None, "correlation_id": None, "alert_id": None}
    return source.model_dump()


def create_incident(*, db: Session, actor_usuario_id: int, payload):
    fingerprint = _fingerprint(payload.model_dump())
    existing = db.query(OperationalIncident).filter(OperationalIncident.idempotency_key == payload.idempotency_key).first()
    if existing:
        if existing.request_fingerprint != fingerprint: raise IncidentConflictError("idempotency_key_conflict")
        event = db.query(OperationalIncidentEvent).filter(OperationalIncidentEvent.incident_id == existing.id).order_by(OperationalIncidentEvent.id.asc()).first()
        return existing, event, False
    if not _owner_is_operator(db, payload.owner_usuario_id):
        raise IncidentOwnerInvalidError("incident_owner_must_be_authorized")
    incident = OperationalIncident(
        public_id=f"INC-{uuid.uuid4().hex.upper()}", title=payload.title,
        summary_sanitized=payload.summary, incident_type=payload.incident_type,
        severity=payload.severity, status="open", owner_usuario_id=payload.owner_usuario_id,
        opened_by_usuario_id=actor_usuario_id, version=1,
        operational_deadline_at=payload.operational_deadline_at,
        idempotency_key=payload.idempotency_key, request_fingerprint=fingerprint,
    )
    try:
        db.add(incident); db.flush()
        source = _source_fields(payload.source)
        event = OperationalIncidentEvent(
            incident_id=incident.id, event_type="opened", actor_usuario_id=actor_usuario_id,
            status_before=None, status_after="open", severity_before=None, severity_after=incident.severity,
            owner_before_usuario_id=None, owner_after_usuario_id=incident.owner_usuario_id,
            safe_summary=payload.summary, expected_incident_version=0, resulting_incident_version=1,
            idempotency_key=payload.idempotency_key, request_fingerprint=fingerprint, **source,
        )
        db.add(event)
        enqueue_incident_opened(db=db, incident=incident)
        db.commit(); db.refresh(incident); db.refresh(event)
        return incident, event, True
    except IntegrityError:
        db.rollback()
        existing = db.query(OperationalIncident).filter(OperationalIncident.idempotency_key == payload.idempotency_key).first()
        if existing and existing.request_fingerprint == fingerprint:
            event = db.query(OperationalIncidentEvent).filter(OperationalIncidentEvent.incident_id == existing.id).order_by(OperationalIncidentEvent.id.asc()).first()
            return existing, event, False
        raise IncidentConflictError("idempotency_key_conflict")
    except Exception:
        db.rollback(); raise


def _validate_action(incident: OperationalIncident, payload, db: Session) -> tuple[str, dict]:
    action = payload.action
    if incident.status == "reviewed":
        raise IncidentConflictError("reviewed_incident_is_terminal")
    new_status = incident.status
    details: dict[str, object] = {}
    if action in TRANSITIONS:
        allowed, target = TRANSITIONS[action]
        if incident.status not in allowed: raise IncidentConflictError("invalid_incident_transition")
        new_status = target
    if action == "change_severity":
        if payload.severity is None: raise IncidentConflictError("severity_required")
        if payload.severity == incident.severity: raise IncidentConflictError("severity_unchanged")
        details["severity_reason"] = payload.summary
    elif payload.severity is not None:
        raise IncidentConflictError("severity_only_for_change")
    if action == "assign_owner":
        if payload.owner_usuario_id is None: raise IncidentConflictError("owner_required")
        if not _owner_is_operator(db, payload.owner_usuario_id): raise IncidentOwnerInvalidError("incident_owner_must_be_authorized")
    elif payload.owner_usuario_id is not None:
        raise IncidentConflictError("owner_only_for_assignment")
    if action == "resolve":
        if payload.residual_risk_level is None or payload.residual_risk_summary is None:
            raise IncidentConflictError("residual_risk_required")
        if payload.residual_risk_level == "medium" and (payload.residual_risk_owner_usuario_id is None or payload.residual_risk_review_at is None):
            raise IncidentConflictError("medium_risk_requires_owner_and_review_date")
    if action == "review":
        if incident.residual_risk_level in {"high", "critical"}:
            raise IncidentConflictError("residual_risk_blocks_review")
        if incident.residual_risk_level == "medium" and (incident.residual_risk_owner_usuario_id is None or incident.residual_risk_review_at is None):
            raise IncidentConflictError("medium_risk_requires_owner_and_review_date")
    if action == "record_legal_assessment":
        required = (payload.legal_assessment_status, payload.personal_data_impact, payload.user_communication_status, payload.authority_communication_status)
        if any(value is None for value in required): raise IncidentConflictError("legal_assessment_fields_required")
    if action == "record_evidence_reference":
        if payload.source is None or payload.source.evidence_reference is None:
            raise IncidentConflictError("evidence_reference_required")
    details.update({
        key: value for key, value in {
            "residual_risk_level": payload.residual_risk_level,
            "residual_risk_owner_usuario_id": payload.residual_risk_owner_usuario_id,
            "residual_risk_review_at": payload.residual_risk_review_at,
            "legal_assessment_status": payload.legal_assessment_status,
            "personal_data_impact": payload.personal_data_impact,
            "legal_owner_usuario_id": payload.legal_owner_usuario_id,
            "user_communication_status": payload.user_communication_status,
            "authority_communication_status": payload.authority_communication_status,
            "legal_deadline_at": payload.legal_deadline_at,
            "operational_deadline_at": payload.operational_deadline_at,
        }.items() if value is not None
    })
    return new_status, details


def apply_incident_action(*, db: Session, public_id: str, actor_usuario_id: int, payload):
    fingerprint = _fingerprint({"public_id": public_id, **payload.model_dump()})
    try:
        incident = db.query(OperationalIncident).filter(OperationalIncident.public_id == public_id).with_for_update().first()
        if incident is None: raise IncidentNotFoundError("Incidente no encontrado")
        # Serialize an exact concurrent retry on the incident before checking
        # its expected version, so both callers receive the single event.
        existing_event = db.query(OperationalIncidentEvent).filter(OperationalIncidentEvent.idempotency_key == payload.idempotency_key).first()
        if existing_event:
            if existing_event.request_fingerprint != fingerprint: raise IncidentConflictError("idempotency_key_conflict")
            return incident, existing_event
        if incident.version != payload.expected_version: raise IncidentConflictError("incident_version_conflict")
        new_status, details = _validate_action(incident, payload, db)
        before_status, before_severity, before_owner = incident.status, incident.severity, incident.owner_usuario_id
        now = datetime.now(timezone.utc)
        if payload.action == "change_severity": incident.severity = payload.severity
        if payload.action == "assign_owner": incident.owner_usuario_id = payload.owner_usuario_id
        if payload.operational_deadline_at is not None: incident.operational_deadline_at = payload.operational_deadline_at
        if payload.action == "contain": incident.contained_at = now
        if payload.action == "resolve":
            incident.resolved_at = now
            incident.residual_risk_level = payload.residual_risk_level
            incident.residual_risk_summary = payload.residual_risk_summary
            incident.residual_risk_owner_usuario_id = payload.residual_risk_owner_usuario_id
            incident.residual_risk_review_at = payload.residual_risk_review_at
        if payload.action == "review": incident.reviewed_at = now
        if payload.action == "reopen": incident.resolved_at = None; incident.reviewed_at = None
        if payload.action == "record_legal_assessment":
            incident.legal_assessment_status = payload.legal_assessment_status
            incident.personal_data_impact = payload.personal_data_impact
            incident.legal_owner_usuario_id = payload.legal_owner_usuario_id
            incident.user_communication_status = payload.user_communication_status
            incident.authority_communication_status = payload.authority_communication_status
            incident.legal_deadline_at = payload.legal_deadline_at
        incident.status = new_status; incident.version += 1
        source = _source_fields(payload.source)
        event = OperationalIncidentEvent(
            incident_id=incident.id, event_type=payload.action, actor_usuario_id=actor_usuario_id,
            status_before=before_status, status_after=incident.status,
            severity_before=before_severity, severity_after=incident.severity,
            owner_before_usuario_id=before_owner, owner_after_usuario_id=incident.owner_usuario_id,
            safe_summary=payload.summary, safe_details_json=json.dumps(details, default=str, sort_keys=True) if details else None,
            expected_incident_version=payload.expected_version, resulting_incident_version=incident.version,
            idempotency_key=payload.idempotency_key, request_fingerprint=fingerprint, **source,
        )
        db.add(event)
        if payload.action == "change_severity":
            enqueue_incident_escalated(
                db=db,
                incident=incident,
                previous_severity=before_severity,
            )
        db.commit(); db.refresh(incident); db.refresh(event)
        return incident, event
    except IntegrityError:
        db.rollback()
        event = db.query(OperationalIncidentEvent).filter(OperationalIncidentEvent.idempotency_key == payload.idempotency_key).first()
        if event and event.request_fingerprint == fingerprint: return db.get(OperationalIncident, event.incident_id), event
        raise IncidentConflictError("idempotency_key_conflict")
    except Exception:
        db.rollback(); raise


def get_incident(*, db: Session, public_id: str) -> OperationalIncident:
    incident = db.query(OperationalIncident).filter(OperationalIncident.public_id == public_id).first()
    if incident is None: raise IncidentNotFoundError("Incidente no encontrado")
    return incident


def list_incidents(*, db: Session, limit: int, cursor: int | None, status: str | None, severity: str | None, owner_usuario_id: int | None):
    query = db.query(OperationalIncident)
    if cursor is not None: query = query.filter(OperationalIncident.id < cursor)
    if status: query = query.filter(OperationalIncident.status == status)
    if severity: query = query.filter(OperationalIncident.severity == severity)
    if owner_usuario_id: query = query.filter(OperationalIncident.owner_usuario_id == owner_usuario_id)
    rows = query.order_by(OperationalIncident.id.desc()).limit(limit + 1).all()
    return rows[:limit], rows[limit - 1].id if len(rows) > limit else None


def list_incident_events(*, db: Session, incident_id: int):
    return db.query(OperationalIncidentEvent).filter(OperationalIncidentEvent.incident_id == incident_id).order_by(OperationalIncidentEvent.id.asc()).all()
