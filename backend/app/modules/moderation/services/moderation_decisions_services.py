import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.moderation.constants import (
    ACCION_OCULTAR_RECURSO,
    ACCION_RESTAURAR_RECURSO,
    ACCION_RESOLVER_SIN_ACCION,
    ESTADO_DENUNCIA_RECIBIDA,
    ESTADO_DENUNCIA_RESUELTA,
    RECURSO_TIPO_COMERCIO,
    RECURSO_TIPO_HISTORIA,
    RECURSO_TIPO_PUBLICACION,
    RESULTADO_APLICADO,
    RESULTADO_SIN_CAMBIO,
)
from app.modules.moderation.models.contenido_denuncias_models import ContenidoDenuncia
from app.modules.moderation.models.moderation_decisions_models import ModerationDecision
from app.modules.posts.services.publicaciones_services import (
    aplicar_ocultamiento_moderacion_publicacion,
    obtener_publicacion_para_moderacion,
    restaurar_ocultamiento_moderacion_publicacion,
)
from app.modules.spaces.services.comercios_services import (
    aplicar_ocultamiento_moderacion_comercio,
    obtener_comercio_para_moderacion,
    restaurar_ocultamiento_moderacion_comercio,
)
from app.modules.stories.services.historias_services import (
    aplicar_ocultamiento_moderacion_historia,
    obtener_historia_para_moderacion,
    restaurar_ocultamiento_moderacion_historia,
)


class ModerationDecisionNotFoundError(ValueError): pass
class ModerationDecisionConflictError(ValueError): pass
class ModerationResourceNotFoundError(ValueError): pass


def _fingerprint(denuncia_id: int, payload) -> str:
    raw = json.dumps({"denuncia_id": denuncia_id, **payload.model_dump()}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_resource(db: Session, resource_type: str, resource_id: int):
    if resource_type == RECURSO_TIPO_COMERCIO:
        return obtener_comercio_para_moderacion(db, resource_id)
    if resource_type == RECURSO_TIPO_PUBLICACION:
        return obtener_publicacion_para_moderacion(db, resource_id)
    if resource_type == RECURSO_TIPO_HISTORIA:
        return obtener_historia_para_moderacion(db, resource_id)
    return None


def _hide(resource_type: str, resource, decision_id: int) -> None:
    if resource_type == RECURSO_TIPO_COMERCIO:
        aplicar_ocultamiento_moderacion_comercio(resource, decision_id)
    elif resource_type == RECURSO_TIPO_PUBLICACION:
        aplicar_ocultamiento_moderacion_publicacion(resource, decision_id)
    else:
        aplicar_ocultamiento_moderacion_historia(resource, decision_id)


def _restore(resource_type: str, resource) -> None:
    if resource_type == RECURSO_TIPO_COMERCIO:
        restaurar_ocultamiento_moderacion_comercio(resource)
    elif resource_type == RECURSO_TIPO_PUBLICACION:
        restaurar_ocultamiento_moderacion_publicacion(resource)
    else:
        restaurar_ocultamiento_moderacion_historia(resource)


def create_moderation_decision(*, db: Session, denuncia_id: int, operador_usuario_id: int, payload) -> ModerationDecision:
    fingerprint = _fingerprint(denuncia_id, payload)
    try:
        report = db.query(ContenidoDenuncia).filter(ContenidoDenuncia.id == denuncia_id).with_for_update().first()
        if report is None:
            raise ModerationDecisionNotFoundError("Denuncia no encontrada")

        # The report lock serializes exact concurrent retries before checking
        # versions. A retry can therefore observe and return the committed
        # decision instead of reporting a stale-version conflict.
        existing = db.query(ModerationDecision).filter(ModerationDecision.idempotency_key == payload.idempotency_key).first()
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise ModerationDecisionConflictError("idempotency_key_conflict")
            return existing
        if report.version != payload.expected_denuncia_version:
            raise ModerationDecisionConflictError("denuncia_version_conflict")

        resource = _load_resource(db, report.recurso_tipo, report.recurso_id)
        if resource is None:
            raise ModerationResourceNotFoundError("Recurso no encontrado")
        revision_before = int(resource.moderation_revision or 0)
        hidden_before = bool(resource.moderation_hidden)
        if payload.expected_resource_revision is not None and payload.expected_resource_revision != revision_before:
            raise ModerationDecisionConflictError("resource_revision_conflict")

        if payload.accion in {ACCION_RESOLVER_SIN_ACCION, ACCION_OCULTAR_RECURSO} and report.estado != ESTADO_DENUNCIA_RECIBIDA:
            raise ModerationDecisionConflictError("invalid_report_transition")
        if payload.accion == ACCION_RESTAURAR_RECURSO and report.estado != ESTADO_DENUNCIA_RESUELTA:
            raise ModerationDecisionConflictError("invalid_report_transition")
        if payload.accion == ACCION_OCULTAR_RECURSO and hidden_before:
            raise ModerationDecisionConflictError("resource_already_hidden")

        reversed_decision = None
        if payload.accion == ACCION_RESTAURAR_RECURSO:
            reversed_decision = db.get(ModerationDecision, payload.reverses_decision_id)
            valid_reversal = (
                reversed_decision is not None
                and reversed_decision.denuncia_id == report.id
                and reversed_decision.recurso_tipo == report.recurso_tipo
                and reversed_decision.recurso_id == report.recurso_id
                and reversed_decision.accion == ACCION_OCULTAR_RECURSO
                and reversed_decision.resultado == RESULTADO_APLICADO
                and hidden_before
                and resource.moderation_hidden_by_decision_id == reversed_decision.id
                and revision_before == reversed_decision.resource_revision_resultante
            )
            if not valid_reversal:
                raise ModerationDecisionConflictError("stale_or_invalid_reversal")

        decision = ModerationDecision(
            denuncia_id=report.id, operador_usuario_id=operador_usuario_id,
            accion=payload.accion, motivo_codigo=payload.motivo_codigo,
            fundamento=payload.fundamento, evidencia_resumen=payload.evidencia_resumen,
            evidencia_referencia=payload.evidencia_referencia,
            resultado=RESULTADO_SIN_CAMBIO if payload.accion == ACCION_RESOLVER_SIN_ACCION else RESULTADO_APLICADO,
            recurso_tipo=report.recurso_tipo, recurso_id=report.recurso_id,
            estado_recurso_anterior="oculto" if hidden_before else "visible",
            estado_recurso_resultante="oculto" if hidden_before else "visible",
            expected_denuncia_version=payload.expected_denuncia_version,
            denuncia_version_resultante=report.version + 1,
            expected_resource_revision=payload.expected_resource_revision,
            resource_revision_anterior=revision_before,
            resource_revision_resultante=revision_before,
            reverses_decision_id=payload.reverses_decision_id,
            idempotency_key=payload.idempotency_key,
            request_fingerprint=fingerprint,
        )
        db.add(decision)
        db.flush()

        if payload.accion == ACCION_OCULTAR_RECURSO:
            _hide(report.recurso_tipo, resource, decision.id)
        elif payload.accion == ACCION_RESTAURAR_RECURSO:
            _restore(report.recurso_tipo, resource)

        report.estado = ESTADO_DENUNCIA_RESUELTA
        report.version += 1
        report.resuelta_en = report.resuelta_en or datetime.now(timezone.utc)
        decision.denuncia_version_resultante = report.version
        decision.resource_revision_resultante = int(resource.moderation_revision or 0)
        decision.estado_recurso_resultante = "oculto" if resource.moderation_hidden else "visible"
        db.commit()
        db.refresh(decision)
        return decision
    except IntegrityError:
        db.rollback()
        existing = db.query(ModerationDecision).filter(ModerationDecision.idempotency_key == payload.idempotency_key).first()
        if existing is not None and existing.request_fingerprint == fingerprint:
            return existing
        raise ModerationDecisionConflictError("idempotency_key_conflict")
    except Exception:
        db.rollback()
        raise


def list_moderation_decisions(*, db: Session, denuncia_id: int) -> list[ModerationDecision]:
    if db.get(ContenidoDenuncia, denuncia_id) is None:
        raise ModerationDecisionNotFoundError("Denuncia no encontrada")
    return db.query(ModerationDecision).filter(ModerationDecision.denuncia_id == denuncia_id).order_by(ModerationDecision.id.asc()).all()
