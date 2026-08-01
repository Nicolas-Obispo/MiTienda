from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Mapping

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.operation_logging import get_operation_logger, safe_error_class
from app.core.request_context import get_correlation_id, get_request_id


METRIC_KIND_COUNTER = "counter"
METRIC_KIND_DURATION = "duration"
METRIC_KIND_GAUGE = "gauge"

METRIC_HTTP_REQUEST_COUNT = "http.request.count"
METRIC_HTTP_REQUEST_DURATION_MS = "http.request.duration_ms"
METRIC_HTTP_RESPONSE_4XX_COUNT = "http.response.4xx.count"
METRIC_HTTP_RESPONSE_5XX_COUNT = "http.response.5xx.count"
METRIC_HTTP_UNHANDLED_ERROR_COUNT = "http.unhandled_error.count"
METRIC_AUTH_FAILURE_COUNT = "auth.failure.count"
METRIC_AUTHORIZATION_FAILURE_COUNT = "authorization.failure.count"
METRIC_HEALTH_READINESS_STATUS = "health.readiness.status"
METRIC_HEALTH_CHECK_DURATION_MS = "health.check.duration_ms"
METRIC_BACKUP_RUN_COUNT = "backup.run.count"
METRIC_BACKUP_RUN_DURATION_MS = "backup.run.duration_ms"
METRIC_RESTORE_RUN_COUNT = "restore.run.count"
METRIC_RESTORE_RUN_DURATION_MS = "restore.run.duration_ms"
METRIC_UPLOAD_ACCEPTED_COUNT = "upload.accepted.count"
METRIC_UPLOAD_REJECTED_COUNT = "upload.rejected.count"
METRIC_UPLOAD_DURATION_MS = "upload.duration_ms"
METRIC_SEARCH_NO_RESULTS_COUNT = "search.no_results.count"

METRIC_CATALOG = frozenset(
    {
        METRIC_HTTP_REQUEST_COUNT,
        METRIC_HTTP_REQUEST_DURATION_MS,
        METRIC_HTTP_RESPONSE_4XX_COUNT,
        METRIC_HTTP_RESPONSE_5XX_COUNT,
        METRIC_HTTP_UNHANDLED_ERROR_COUNT,
        METRIC_AUTH_FAILURE_COUNT,
        METRIC_AUTHORIZATION_FAILURE_COUNT,
        METRIC_HEALTH_READINESS_STATUS,
        METRIC_HEALTH_CHECK_DURATION_MS,
        METRIC_BACKUP_RUN_COUNT,
        METRIC_BACKUP_RUN_DURATION_MS,
        METRIC_RESTORE_RUN_COUNT,
        METRIC_RESTORE_RUN_DURATION_MS,
        METRIC_UPLOAD_ACCEPTED_COUNT,
        METRIC_UPLOAD_REJECTED_COUNT,
        METRIC_UPLOAD_DURATION_MS,
        METRIC_SEARCH_NO_RESULTS_COUNT,
    }
)

_TAG_KEY_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.-]{0,63}$")
_TAG_VALUE_RE = re.compile(r"^[a-zA-Z0-9_.:/-]{0,128}$")
_SENSITIVE_TAG_KEYS = {
    "authorization",
    "cookie",
    "email",
    "jwt",
    "password",
    "secret",
    "secret_key",
    "token",
}

MetricListener = Callable[["MetricSample"], None]
logger = get_operation_logger("metrics")
_metric_listeners: list[MetricListener] = []


@dataclass(frozen=True)
class MetricSample:
    name: str
    kind: str
    value: float
    unit: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    recorded_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    request_id: str | None = None
    correlation_id: str | None = None


class LocalMetricsSink:
    name = "local"

    def __init__(self, max_samples: int = 1000) -> None:
        self.max_samples = max_samples
        self._samples: list[MetricSample] = []
        self._lock = threading.Lock()

    def emit(self, sample: MetricSample) -> None:
        with self._lock:
            self._samples.append(sample)
            if len(self._samples) > self.max_samples:
                self._samples = self._samples[-self.max_samples:]

    def snapshot(self) -> list[MetricSample]:
        with self._lock:
            return list(self._samples)

    def clear(self) -> None:
        with self._lock:
            self._samples.clear()


class MetricsRecorder:
    def __init__(self, sink: LocalMetricsSink) -> None:
        self.sink = sink

    def counter(
        self,
        name: str,
        value: float = 1,
        tags: Mapping[str, object] | None = None,
    ) -> MetricSample:
        return self._record(name, METRIC_KIND_COUNTER, value, None, tags)

    def duration(
        self,
        name: str,
        duration_ms: float,
        tags: Mapping[str, object] | None = None,
    ) -> MetricSample:
        return self._record(name, METRIC_KIND_DURATION, duration_ms, "ms", tags)

    def gauge(
        self,
        name: str,
        value: float,
        tags: Mapping[str, object] | None = None,
    ) -> MetricSample:
        return self._record(name, METRIC_KIND_GAUGE, value, None, tags)

    def _record(
        self,
        name: str,
        kind: str,
        value: float,
        unit: str | None,
        tags: Mapping[str, object] | None,
    ) -> MetricSample:
        sample = MetricSample(
            name=_safe_metric_name(name),
            kind=kind,
            value=float(value),
            unit=unit,
            tags=_safe_tags(tags),
            request_id=get_request_id(),
            correlation_id=get_correlation_id(),
        )
        self.sink.emit(sample)
        _notify_metric_listeners(sample)
        return sample


local_metrics_sink = LocalMetricsSink()
metrics = MetricsRecorder(local_metrics_sink)


def increment_counter(
    name: str,
    value: float = 1,
    tags: Mapping[str, object] | None = None,
) -> MetricSample:
    return metrics.counter(name, value, tags)


def record_duration(
    name: str,
    duration_ms: float,
    tags: Mapping[str, object] | None = None,
) -> MetricSample:
    return metrics.duration(name, duration_ms, tags)


def record_gauge(
    name: str,
    value: float,
    tags: Mapping[str, object] | None = None,
) -> MetricSample:
    return metrics.gauge(name, value, tags)


def record_auth_failure(status_code: int, tags: Mapping[str, object] | None = None) -> None:
    if status_code == 401:
        increment_counter(METRIC_AUTH_FAILURE_COUNT, tags=tags)
    elif status_code == 403:
        increment_counter(METRIC_AUTHORIZATION_FAILURE_COUNT, tags=tags)


def register_metric_listener(listener: MetricListener) -> None:
    if listener not in _metric_listeners:
        _metric_listeners.append(listener)


def clear_metric_listeners() -> None:
    _metric_listeners.clear()


class OperationalMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        tags: dict[str, object] = {
            "method": request.method,
            "route": "unknown",
            "status": "500",
        }
        try:
            response = await call_next(request)
        except Exception as exc:
            tags["route"] = _route_template(request)
            tags["error_class"] = safe_error_class(exc)
            increment_counter(METRIC_HTTP_REQUEST_COUNT, tags=tags)
            increment_counter(METRIC_HTTP_RESPONSE_5XX_COUNT, tags=tags)
            record_duration(
                METRIC_HTTP_REQUEST_DURATION_MS,
                _elapsed_ms(started),
                tags=tags,
            )
            raise

        tags["route"] = _route_template(request)
        tags["status"] = str(response.status_code)
        increment_counter(METRIC_HTTP_REQUEST_COUNT, tags=tags)
        if 400 <= response.status_code < 500:
            increment_counter(METRIC_HTTP_RESPONSE_4XX_COUNT, tags=tags)
        elif response.status_code >= 500:
            increment_counter(METRIC_HTTP_RESPONSE_5XX_COUNT, tags=tags)
        record_duration(METRIC_HTTP_REQUEST_DURATION_MS, _elapsed_ms(started), tags=tags)
        return response


def _safe_metric_name(name: str) -> str:
    normalized = str(name or "").strip()
    if normalized in METRIC_CATALOG:
        return normalized
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", normalized)[:128] or "metric.unknown"


def _safe_tags(tags: Mapping[str, object] | None) -> dict[str, str]:
    safe: dict[str, str] = {}
    if not tags:
        return safe
    for key, value in tags.items():
        key_text = str(key).strip()
        if not _TAG_KEY_RE.fullmatch(key_text):
            continue
        if key_text.lower() in _SENSITIVE_TAG_KEYS:
            continue
        value_text = str(value).strip()
        if not _TAG_VALUE_RE.fullmatch(value_text):
            continue
        safe[key_text] = value_text
    return safe


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return "unmatched"


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)


def _notify_metric_listeners(sample: MetricSample) -> None:
    for listener in list(_metric_listeners):
        try:
            listener(sample)
        except Exception as exc:
            logger.warning(
                "metric_listener_failed listener=%s error_class=%s",
                listener.__class__.__name__,
                safe_error_class(exc),
            )
