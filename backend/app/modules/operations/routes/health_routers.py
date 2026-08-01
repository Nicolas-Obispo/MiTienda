from fastapi import APIRouter, Response, status

from app.core.health import HEALTHY, UNHEALTHY, HealthRegistry, build_default_health_registry
from app.core.operation_logging import get_operation_logger
from app.core.operation_metrics import (
    METRIC_HEALTH_CHECK_DURATION_MS,
    METRIC_HEALTH_READINESS_STATUS,
    record_duration,
    record_gauge,
)


router = APIRouter(prefix="/health", tags=["Health"])
logger = get_operation_logger("health")
health_registry = build_default_health_registry()


@router.get("/live")
def liveness(response: Response):
    report = health_registry.run_liveness()
    response.status_code = _status_code_for_report(report.status)
    logger.info("health_liveness status=%s", report.status)
    return report.to_public_dict()


@router.get("/ready")
def readiness(response: Response):
    report = health_registry.run_readiness()
    response.status_code = _status_code_for_report(report.status)
    _record_readiness_metrics(report)
    log_method = logger.warning if report.status == UNHEALTHY else logger.info
    log_method("health_readiness status=%s", report.status)
    return report.to_public_dict()


def _status_code_for_report(report_status: str) -> int:
    if report_status == UNHEALTHY:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    return status.HTTP_200_OK


def _record_readiness_metrics(report) -> None:
    record_gauge(
        METRIC_HEALTH_READINESS_STATUS,
        _readiness_status_value(report.status),
        tags={"status": report.status},
    )
    for check in report.checks:
        record_duration(
            METRIC_HEALTH_CHECK_DURATION_MS,
            check.duration_ms,
            tags={"component": check.component, "status": check.status},
        )


def _readiness_status_value(report_status: str) -> float:
    if report_status == HEALTHY:
        return 1.0
    if report_status == UNHEALTHY:
        return 0.0
    return 0.5
