from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol

from app.core.operation_logging import get_operation_logger
from app.core.operation_metrics import (
    METRIC_BACKUP_RUN_COUNT,
    METRIC_HEALTH_CHECK_DURATION_MS,
    METRIC_HEALTH_READINESS_STATUS,
    METRIC_HTTP_RESPONSE_5XX_COUNT,
    METRIC_RESTORE_RUN_COUNT,
    METRIC_UPLOAD_REJECTED_COUNT,
    MetricSample,
    local_metrics_sink,
    register_metric_listener,
)


ALERT_SEVERITY_INFO = "info"
ALERT_SEVERITY_WARNING = "warning"
ALERT_SEVERITY_CRITICAL = "critical"

ALERT_STATUS_ACTIVE = "active"
ALERT_STATUS_SUPPRESSED = "suppressed"

ALERT_CONDITION_COUNT_AT_LEAST = "count_at_least"
ALERT_CONDITION_VALUE_AT_OR_BELOW = "value_at_or_below"
ALERT_CONDITION_RESULT_FAILED = "result_failed"
ALERT_CONDITION_STATUS_UNHEALTHY = "status_unhealthy"
ALERT_CONDITION_STATUS_NOT_HEALTHY = "status_not_healthy"

logger = get_operation_logger("alerts")


@dataclass(frozen=True)
class AlertRule:
    name: str
    metric_name: str
    condition: str
    severity: str
    window_seconds: int
    cooldown_seconds: int
    threshold: float | None = None
    tag_filters: dict[str, str] = field(default_factory=dict)
    context_tags: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class AlertEvent:
    alert_id: str
    rule_name: str
    severity: str
    status: str
    condition: str
    triggered_at_utc: str
    window_seconds: int
    cooldown_seconds: int
    deduplication_key: str
    context: dict[str, str]
    message: str


class AlertSink(Protocol):
    name: str

    def emit(self, event: AlertEvent) -> None:
        ...


class LocalAlertSink:
    name = "local"

    def __init__(self, max_events: int = 1000) -> None:
        self.max_events = max_events
        self._events: list[AlertEvent] = []
        self._lock = threading.Lock()

    def emit(self, event: AlertEvent) -> None:
        with self._lock:
            self._events.append(event)
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events:]

    def snapshot(self) -> list[AlertEvent]:
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


class AlertEngine:
    def __init__(
        self,
        rules: list[AlertRule],
        sink: AlertSink,
        metrics_snapshot_provider: Callable[[], list[MetricSample]],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.rules = rules
        self.sink = sink
        self.metrics_snapshot_provider = metrics_snapshot_provider
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._last_active_by_key: dict[str, datetime] = {}

    def evaluate_metric_sample(self, sample: MetricSample) -> list[AlertEvent]:
        events: list[AlertEvent] = []
        if not _metric_sample_is_safe(sample):
            return events

        samples = self.metrics_snapshot_provider()
        for rule in self.rules:
            if sample.name != rule.metric_name or not _matches_filters(sample, rule):
                continue
            if not _rule_matches(rule, sample, samples, self.clock()):
                continue
            event = self._build_event(rule, sample)
            self.sink.emit(event)
            events.append(event)
        return events

    def clear_state(self) -> None:
        self._last_active_by_key.clear()

    def _build_event(self, rule: AlertRule, sample: MetricSample) -> AlertEvent:
        now = self.clock()
        deduplication_key = _deduplication_key(rule, sample)
        last_active = self._last_active_by_key.get(deduplication_key)
        status = ALERT_STATUS_ACTIVE
        if last_active and now - last_active < timedelta(seconds=rule.cooldown_seconds):
            status = ALERT_STATUS_SUPPRESSED
        else:
            self._last_active_by_key[deduplication_key] = now

        context = _safe_context(rule, sample)
        return AlertEvent(
            alert_id=_alert_id(rule.name, deduplication_key, now),
            rule_name=rule.name,
            severity=rule.severity,
            status=status,
            condition=rule.condition,
            triggered_at_utc=now.isoformat(),
            window_seconds=rule.window_seconds,
            cooldown_seconds=rule.cooldown_seconds,
            deduplication_key=deduplication_key,
            context=context,
            message=_safe_message(rule),
        )


def default_alert_rules() -> list[AlertRule]:
    return [
        AlertRule(
            name="readiness_unhealthy",
            metric_name=METRIC_HEALTH_READINESS_STATUS,
            condition=ALERT_CONDITION_VALUE_AT_OR_BELOW,
            threshold=0,
            severity=ALERT_SEVERITY_CRITICAL,
            window_seconds=60,
            cooldown_seconds=300,
            context_tags=("status",),
            description="Readiness informa estado unhealthy.",
        ),
        AlertRule(
            name="http_5xx_repeated",
            metric_name=METRIC_HTTP_RESPONSE_5XX_COUNT,
            condition=ALERT_CONDITION_COUNT_AT_LEAST,
            threshold=3,
            severity=ALERT_SEVERITY_CRITICAL,
            window_seconds=300,
            cooldown_seconds=300,
            context_tags=("method", "route", "status"),
            description="Errores 5xx repetidos dentro de la ventana operativa.",
        ),
        AlertRule(
            name="backup_failed",
            metric_name=METRIC_BACKUP_RUN_COUNT,
            condition=ALERT_CONDITION_RESULT_FAILED,
            severity=ALERT_SEVERITY_CRITICAL,
            window_seconds=3600,
            cooldown_seconds=3600,
            tag_filters={"result": "failed"},
            context_tags=("provider", "result"),
            description="Proceso de backup finalizo con error.",
        ),
        AlertRule(
            name="backup_evidence_not_healthy",
            metric_name=METRIC_HEALTH_CHECK_DURATION_MS,
            condition=ALERT_CONDITION_STATUS_NOT_HEALTHY,
            severity=ALERT_SEVERITY_WARNING,
            window_seconds=300,
            cooldown_seconds=3600,
            tag_filters={"component": "backup_evidence"},
            context_tags=("component", "status"),
            description="La evidencia de backup no esta disponible o no es valida.",
        ),
        AlertRule(
            name="restore_failed",
            metric_name=METRIC_RESTORE_RUN_COUNT,
            condition=ALERT_CONDITION_RESULT_FAILED,
            severity=ALERT_SEVERITY_CRITICAL,
            window_seconds=3600,
            cooldown_seconds=3600,
            tag_filters={"result": "failed"},
            context_tags=("provider", "result"),
            description="Proceso de restore finalizo con error.",
        ),
        AlertRule(
            name="uploads_rejected_repeated",
            metric_name=METRIC_UPLOAD_REJECTED_COUNT,
            condition=ALERT_CONDITION_COUNT_AT_LEAST,
            threshold=5,
            severity=ALERT_SEVERITY_WARNING,
            window_seconds=300,
            cooldown_seconds=300,
            context_tags=("reason", "media_type"),
            description="Uploads rechazados repetidos dentro de la ventana operativa.",
        ),
    ]


local_alert_sink = LocalAlertSink()
alert_engine = AlertEngine(
    rules=default_alert_rules(),
    sink=local_alert_sink,
    metrics_snapshot_provider=local_metrics_sink.snapshot,
)


def configure_default_alerting() -> None:
    register_metric_listener(alert_engine.evaluate_metric_sample)


def _rule_matches(
    rule: AlertRule,
    current_sample: MetricSample,
    samples: list[MetricSample],
    now: datetime,
) -> bool:
    if rule.condition == ALERT_CONDITION_VALUE_AT_OR_BELOW:
        return (
            rule.threshold is not None
            and current_sample.value <= rule.threshold
        )

    if rule.condition == ALERT_CONDITION_RESULT_FAILED:
        return current_sample.tags.get("result") == "failed"

    if rule.condition == ALERT_CONDITION_STATUS_UNHEALTHY:
        return current_sample.tags.get("status") == "unhealthy"

    if rule.condition == ALERT_CONDITION_STATUS_NOT_HEALTHY:
        return current_sample.tags.get("status") not in {"", "healthy"}

    if rule.condition == ALERT_CONDITION_COUNT_AT_LEAST:
        if rule.threshold is None:
            return False
        return (
            _matching_counter_total(rule, current_sample, samples, now)
            >= rule.threshold
        )

    return False


def _matching_counter_total(
    rule: AlertRule,
    current_sample: MetricSample,
    samples: list[MetricSample],
    now: datetime,
) -> float:
    window_start = now - timedelta(seconds=rule.window_seconds)
    total = 0.0
    for sample in samples:
        if sample.name != rule.metric_name or not _matches_filters(sample, rule):
            continue
        if _deduplication_key(rule, sample) != _deduplication_key(rule, current_sample):
            continue
        sample_time = _parse_utc(sample.recorded_at_utc)
        if sample_time and sample_time >= window_start:
            total += sample.value
    return total


def _matches_filters(sample: MetricSample, rule: AlertRule) -> bool:
    return all(sample.tags.get(key) == value for key, value in rule.tag_filters.items())


def _deduplication_key(rule: AlertRule, sample: MetricSample) -> str:
    parts = [rule.name]
    for key in rule.context_tags:
        value = sample.tags.get(key)
        if value:
            parts.append(f"{key}:{value}")
    return "|".join(parts)


def _safe_context(rule: AlertRule, sample: MetricSample) -> dict[str, str]:
    context = {
        key: value
        for key, value in sample.tags.items()
        if key in set(rule.context_tags) | set(rule.tag_filters.keys())
    }
    if sample.request_id:
        context["request_id"] = sample.request_id
    if sample.correlation_id:
        context["correlation_id"] = sample.correlation_id
    return context


def _metric_sample_is_safe(sample: MetricSample) -> bool:
    serialized = repr(sample)
    sensitive_markers = (
        "secret_key",
        "authorization",
        "bearer ",
        "jwt",
        "token",
        "password",
        "cookie",
        ".env",
    )
    return not any(marker in serialized.lower() for marker in sensitive_markers)


def _safe_message(rule: AlertRule) -> str:
    return rule.description or f"Alerta operativa: {rule.name}"


def _alert_id(rule_name: str, deduplication_key: str, occurred_at: datetime) -> str:
    raw = f"{rule_name}:{deduplication_key}:{occurred_at.isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
