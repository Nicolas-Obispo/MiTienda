import logging
import re
from typing import Any

from app.core.request_context import get_correlation_id, get_request_id


LOGGER_NAME = "feedgo"

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

SENSITIVE_VALUE = "[REDACTED]"

_SENSITIVE_PATTERNS = [
    re.compile(
        r"(?i)\b(secret[_-]?key|authorization|bearer|jwt|token|password|passwd|cookie|set-cookie)\b\s*[:=]\s*[^,\s;]+"
    ),
    re.compile(r"(?i)\.env"),
    re.compile(r"(?i)eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),
]


class RequestContextLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.correlation_id = get_correlation_id() or "-"
        return True


def configure_logging(level: str = "INFO") -> None:
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s %(levelname)s %(name)s "
            "request_id=%(request_id)s correlation_id=%(correlation_id)s "
            "%(message)s"
        ),
    )
    _install_request_context_filter()


def _install_request_context_filter() -> None:
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if not any(isinstance(item, RequestContextLogFilter) for item in handler.filters):
            handler.addFilter(RequestContextLogFilter())


def get_operation_logger(component: str | None = None) -> logging.Logger:
    if not component:
        return logging.getLogger(LOGGER_NAME)

    safe_component = re.sub(r"[^a-zA-Z0-9_.-]", "_", component).strip("._-")
    if not safe_component:
        return logging.getLogger(LOGGER_NAME)

    return logging.getLogger(f"{LOGGER_NAME}.{safe_component}")


def sanitize_log_value(value: Any) -> str:
    text = str(value)
    for pattern in _SENSITIVE_PATTERNS:
        text = pattern.sub(lambda match: _redact_match(match.group(0)), text)
    return text


def _redact_match(match: str) -> str:
    if ".env" in match.lower():
        return SENSITIVE_VALUE
    return SENSITIVE_VALUE


def safe_error_class(exc: Exception) -> str:
    return exc.__class__.__name__
