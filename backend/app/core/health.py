from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.operation_logging import get_operation_logger, safe_error_class


HEALTHY = "healthy"
DEGRADED = "degraded"
UNHEALTHY = "unhealthy"
UNKNOWN = "unknown"

SAFE_MESSAGE_OK = "Componente disponible."
SAFE_MESSAGE_DEGRADED = "Componente disponible con capacidad reducida."
SAFE_MESSAGE_UNHEALTHY = "Componente no disponible."

logger = get_operation_logger("health")


@dataclass(frozen=True)
class HealthCheckResult:
    component: str
    status: str
    duration_ms: float
    message: str

    def to_public_dict(self) -> dict[str, object]:
        return {
            "component": self.component,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "message": self.message,
        }


@dataclass(frozen=True)
class HealthReport:
    status: str
    checked_at: str
    checks: list[HealthCheckResult]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "checked_at": self.checked_at,
            "checks": [check.to_public_dict() for check in self.checks],
        }


HealthCheck = Callable[[], HealthCheckResult]


class HealthRegistry:
    def __init__(self) -> None:
        self._liveness_checks: list[HealthCheck] = []
        self._readiness_checks: list[HealthCheck] = []

    def register_liveness(self, check: HealthCheck) -> None:
        self._liveness_checks.append(check)

    def register_readiness(self, check: HealthCheck) -> None:
        self._readiness_checks.append(check)

    def run_liveness(self) -> HealthReport:
        return _build_report([_safe_run_check(check) for check in self._liveness_checks])

    def run_readiness(self) -> HealthReport:
        return _build_report([_safe_run_check(check) for check in self._readiness_checks])


def _build_report(checks: list[HealthCheckResult]) -> HealthReport:
    status = _aggregate_status(checks)
    return HealthReport(
        status=status,
        checked_at=datetime.now(timezone.utc).isoformat(),
        checks=checks,
    )


def _aggregate_status(checks: list[HealthCheckResult]) -> str:
    statuses = {check.status for check in checks}
    if UNHEALTHY in statuses:
        return UNHEALTHY
    if DEGRADED in statuses:
        return DEGRADED
    if UNKNOWN in statuses:
        return UNKNOWN
    return HEALTHY


def _safe_run_check(check: HealthCheck) -> HealthCheckResult:
    try:
        return check()
    except Exception as exc:
        logger.error(
            "health_check_unhandled_error component=unknown error_class=%s",
            safe_error_class(exc),
        )
        return HealthCheckResult(
            component="unknown",
            status=UNHEALTHY,
            duration_ms=0.0,
            message=SAFE_MESSAGE_UNHEALTHY,
        )


def _timed_check(component: str, operation: Callable[[], tuple[str, str]]) -> HealthCheckResult:
    started = time.perf_counter()
    try:
        status, message = operation()
    except Exception as exc:
        logger.warning(
            "health_check_failed component=%s error_class=%s",
            component,
            safe_error_class(exc),
        )
        status, message = UNHEALTHY, SAFE_MESSAGE_UNHEALTHY
    duration_ms = round((time.perf_counter() - started) * 1000, 3)
    return HealthCheckResult(
        component=component,
        status=status,
        duration_ms=duration_ms,
        message=message,
    )


def api_liveness_check() -> HealthCheckResult:
    return _timed_check("api", lambda: (HEALTHY, SAFE_MESSAGE_OK))


def database_connectivity_check() -> HealthCheckResult:
    def operation() -> tuple[str, str]:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return HEALTHY, SAFE_MESSAGE_OK

    return _timed_check("database", operation)


def database_schema_check() -> HealthCheckResult:
    def operation() -> tuple[str, str]:
        from check_database_schema import check_schema

        result = check_schema()
        if result.ok:
            return HEALTHY, "Schema compatible."
        return UNHEALTHY, "Diferencias de schema detectadas."

    return _timed_check("database_schema", operation)


def uploads_storage_check(upload_dir: Path | None = None) -> HealthCheckResult:
    def operation() -> tuple[str, str]:
        target = upload_dir or _default_upload_dir()
        if not target.exists() or not target.is_dir():
            return UNHEALTHY, SAFE_MESSAGE_UNHEALTHY
        if not os.access(target, os.W_OK):
            return DEGRADED, SAFE_MESSAGE_DEGRADED
        return HEALTHY, SAFE_MESSAGE_OK

    return _timed_check("uploads_storage", operation)


def embeddings_check() -> HealthCheckResult:
    def operation() -> tuple[str, str]:
        provider = (settings.EMBEDDINGS_PROVIDER or "simulated").strip().lower()
        if provider in {"simulated", "local"}:
            return HEALTHY, SAFE_MESSAGE_OK
        return DEGRADED, "Provider de embeddings no disponible."

    return _timed_check("embeddings", operation)


def backup_evidence_check(backup_dir: Path | None = None) -> HealthCheckResult:
    def operation() -> tuple[str, str]:
        target = backup_dir or Path(os.environ.get("FEEDGO_BACKUP_DIR", "backups/mysql"))
        return _latest_json_evidence_status(
            target,
            "*.sql.gz.json",
            required_result="ok",
        )

    return _timed_check("backup_evidence", operation)


def restore_evidence_check(evidence_dir: Path | None = None) -> HealthCheckResult:
    def operation() -> tuple[str, str]:
        target = evidence_dir or Path(
            os.environ.get("FEEDGO_RESTORE_EVIDENCE_DIR", "restore_tmp/evidence")
        )
        return _latest_json_evidence_status(
            target,
            "*restore.json",
            required_result="ok",
        )

    return _timed_check("restore_evidence", operation)


def _latest_json_evidence_status(
    directory: Path,
    pattern: str,
    required_result: str,
) -> tuple[str, str]:
    if not directory.exists() or not directory.is_dir():
        return DEGRADED, "Evidencia operativa no disponible."

    evidence_files = sorted(
        directory.glob(pattern),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not evidence_files:
        return DEGRADED, "Evidencia operativa no disponible."

    latest = evidence_files[0]
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEGRADED, "Evidencia operativa no legible."

    if payload.get("result") == required_result:
        return HEALTHY, "Evidencia operativa valida."
    return DEGRADED, "Ultima evidencia operativa no exitosa."


def _default_upload_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "uploads"


def build_default_health_registry() -> HealthRegistry:
    registry = HealthRegistry()
    registry.register_liveness(api_liveness_check)
    registry.register_readiness(api_liveness_check)
    registry.register_readiness(database_connectivity_check)
    registry.register_readiness(database_schema_check)
    registry.register_readiness(uploads_storage_check)
    registry.register_readiness(embeddings_check)
    registry.register_readiness(backup_evidence_check)
    registry.register_readiness(restore_evidence_check)
    return registry
