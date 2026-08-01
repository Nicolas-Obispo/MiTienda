from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.operation_logging import (
    get_operation_logger,
    safe_error_class,
    sanitize_log_value,
)
from app.core.operation_metrics import (
    METRIC_HTTP_UNHANDLED_ERROR_COUNT,
    increment_counter,
    record_auth_failure,
)
from app.core.request_context import get_correlation_id, get_request_id


logger = get_operation_logger("errors")

_DEFAULT_MESSAGES = {
    400: "Solicitud invalida",
    401: "No autenticado",
    403: "No autorizado",
    404: "Recurso no encontrado",
    409: "Conflicto de estado",
    413: "Archivo demasiado grande",
    422: "Payload invalido",
}


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    status_code = exc.status_code
    detail = _safe_public_detail(status_code, exc.detail)
    log_level = "warning" if status_code < 500 else "error"
    getattr(logger, log_level)(
        "http_exception request_id=%s correlation_id=%s status=%s method=%s path=%s detail=%s",
        get_request_id() or "-",
        get_correlation_id() or "-",
        status_code,
        request.method,
        request.url.path,
        sanitize_log_value(exc.detail),
    )
    record_auth_failure(
        status_code,
        tags={"method": request.method, "route": _safe_request_path(request)},
    )
    response = JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers=exc.headers,
    )
    return _with_context_headers(response)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(
        "validation_error request_id=%s correlation_id=%s method=%s path=%s error_count=%s",
        get_request_id() or "-",
        get_correlation_id() or "-",
        request.method,
        request.url.path,
        len(exc.errors()),
    )
    return _with_context_headers(
        JSONResponse(status_code=422, content={"detail": _DEFAULT_MESSAGES[422]})
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    increment_counter(
        METRIC_HTTP_UNHANDLED_ERROR_COUNT,
        tags={
            "method": request.method,
            "route": _safe_request_path(request),
            "error_class": safe_error_class(exc),
        },
    )
    logger.error(
        "unhandled_exception request_id=%s correlation_id=%s method=%s path=%s error_class=%s",
        get_request_id() or "-",
        get_correlation_id() or "-",
        request.method,
        request.url.path,
        safe_error_class(exc),
    )
    response = JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )
    return _with_context_headers(response)


def _safe_public_detail(status_code: int, detail: Any) -> str:
    if _contains_sensitive_data(detail):
        return _DEFAULT_MESSAGES.get(status_code, "Error de solicitud")

    if isinstance(detail, str) and detail.strip():
        return detail

    if isinstance(detail, Mapping):
        public_message = detail.get("message") or detail.get("detail")
        if isinstance(public_message, str) and public_message.strip():
            return public_message

    return _DEFAULT_MESSAGES.get(status_code, "Error de solicitud")


def _contains_sensitive_data(value: Any) -> bool:
    lowered = str(value).lower()
    sensitive_markers = (
        "secret_key",
        "authorization",
        "bearer ",
        "jwt",
        "token",
        "password",
        "passwd",
        "cookie",
        ".env",
        "traceback",
    )
    return any(marker in lowered for marker in sensitive_markers)


def _with_context_headers(response: JSONResponse) -> JSONResponse:
    request_id = get_request_id()
    correlation_id = get_correlation_id()
    if request_id:
        response.headers["X-Request-ID"] = request_id
    if correlation_id:
        response.headers["X-Correlation-ID"] = correlation_id
    return response


def _safe_request_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return "unmatched"
