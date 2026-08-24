from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.health import build_default_health_registry
from app.core.operation_alerts import default_alert_rules, local_alert_sink
from app.core.operation_metrics import (
    METRIC_HTTP_RESPONSE_5XX_COUNT,
    METRIC_UPLOAD_ACCEPTED_COUNT,
    METRIC_UPLOAD_REJECTED_COUNT,
    local_metrics_sink,
)
from app.modules.posts.services.publicaciones_services import obtener_publicacion_para_inspeccion_operativa
from app.modules.spaces.services.comercios_services import obtener_comercio_para_inspeccion_operativa
from app.modules.stories.services.historias_services import obtener_historia_para_inspeccion_operativa
from app.modules.operations.services.operational_worker_state_services import read_sanitized_worker_state


ALLOWED_AGGREGATE_METRICS = frozenset({
    METRIC_HTTP_RESPONSE_5XX_COUNT,
    METRIC_UPLOAD_ACCEPTED_COUNT,
    METRIC_UPLOAD_REJECTED_COUNT,
})
RESOURCE_INSPECTORS = {
    "comercio": obtener_comercio_para_inspeccion_operativa,
    "publicacion": obtener_publicacion_para_inspeccion_operativa,
    "historia": obtener_historia_para_inspeccion_operativa,
}
LOCAL_ASSET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")
health_registry = build_default_health_registry()
SAFE_ALERT_RULES = {rule.name: rule for rule in default_alert_rules()}
SAFE_ALERT_STATUSES = frozenset({"active", "suppressed"})
OPAQUE_ALERT_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


class OperationalResourceNotFoundError(LookupError):
    pass


def build_operational_status() -> dict:
    liveness = health_registry.run_liveness()
    readiness = health_registry.run_readiness()
    components = [
        {"component": item.component, "status": item.status, "message": item.message}
        for item in readiness.checks
    ]
    component_status = {item.component: item.status for item in readiness.checks}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "process_local",
        "volatile": True,
        "historical": False,
        "global_status": False,
        "health": {
            "liveness": liveness.status,
            "readiness": readiness.status,
            "components": components,
        },
        "recovery_evidence": {
            "backup": _evidence_projection(component_status.get("backup_evidence", "unknown")),
            "restore": _evidence_projection(component_status.get("restore_evidence", "unknown")),
        },
        "operational_email_worker": read_sanitized_worker_state(),
        "aggregates": _safe_metric_aggregates(),
        "alerts": _safe_alert_events(),
    }


def inspect_resource_integrity(db: Session, *, resource_type: str, resource_id: int) -> dict:
    inspector = RESOURCE_INSPECTORS.get(resource_type)
    if inspector is None:
        raise ValueError("Tipo de recurso no soportado")
    resource = inspector(db, resource_id)
    if resource is None:
        raise OperationalResourceNotFoundError("Recurso no encontrado")
    asset = _inspect_asset_reference(resource["media_reference"])
    issues = []
    if asset["status"] == "missing":
        issues.append({"code": "local_asset_missing", "severity": "warning"})
    elif asset["status"] == "invalid_reference":
        issues.append({"code": "invalid_asset_reference", "severity": "warning"})
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "resource_type": resource_type,
        "resource_id": resource_id,
        "lifecycle": resource["lifecycle"],
        "moderation_hidden": resource["moderation_hidden"],
        "publicly_eligible": resource["publicly_eligible"],
        "asset": asset,
        "issues": issues,
    }


def _evidence_projection(status: str) -> dict[str, str]:
    meanings = {
        "healthy": "valid_evidence_available",
        "degraded": "evidence_unavailable_or_invalid",
        "unhealthy": "evidence_check_unavailable",
    }
    return {"status": status, "meaning": meanings.get(status, "unknown")}


def _safe_metric_aggregates() -> list[dict]:
    grouped: dict[str, dict[str, float | int]] = {}
    for sample in local_metrics_sink.snapshot():
        if (
            sample.name not in ALLOWED_AGGREGATE_METRICS
            or sample.kind != "counter"
            or not math.isfinite(sample.value)
        ):
            continue
        entry = grouped.setdefault(sample.name, {"value": 0.0, "sample_count": 0})
        entry["value"] = float(entry["value"]) + sample.value
        entry["sample_count"] = int(entry["sample_count"]) + 1
    return [
        {"name": name, "value": values["value"], "sample_count": values["sample_count"]}
        for name, values in sorted(grouped.items())
    ]


def _safe_alert_events(limit: int = 20) -> list[dict]:
    events = [
        event for event in local_alert_sink.snapshot()
        if event.rule_name in SAFE_ALERT_RULES
        and event.status in SAFE_ALERT_STATUSES
        and OPAQUE_ALERT_ID_RE.fullmatch(event.alert_id)
        and _is_iso_datetime(event.triggered_at_utc)
    ][-limit:]
    return [
        {
            "alert_id": event.alert_id,
            "rule_name": event.rule_name,
            "severity": SAFE_ALERT_RULES[event.rule_name].severity,
            "status": event.status,
            "triggered_at_utc": event.triggered_at_utc,
            "message": SAFE_ALERT_RULES[event.rule_name].description,
        }
        for event in reversed(events)
    ]


def _inspect_asset_reference(reference: str | None) -> dict[str, str]:
    if reference is None or not str(reference).strip():
        return {"kind": "none", "status": "not_applicable"}
    normalized = str(reference).strip()
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return {"kind": "external", "status": "not_verified"}
    if not normalized.startswith("/uploads/"):
        return {"kind": "invalid", "status": "invalid_reference"}
    filename = normalized.removeprefix("/uploads/")
    if not LOCAL_ASSET_RE.fullmatch(filename) or Path(filename).name != filename:
        return {"kind": "invalid", "status": "invalid_reference"}
    upload_dir = Path(__file__).resolve().parents[4] / "uploads"
    return {"kind": "local_upload", "status": "present" if (upload_dir / filename).is_file() else "missing"}


def _is_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True
