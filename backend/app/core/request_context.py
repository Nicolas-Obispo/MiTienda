import re
import uuid
from contextvars import ContextVar
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"

_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
_CORRELATION_ID: ContextVar[str | None] = ContextVar("correlation_id", default=None)
_SAFE_HEADER_VALUE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    correlation_id: str


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = _generate_id()
        correlation_id = _resolve_correlation_id(
            request.headers.get(CORRELATION_ID_HEADER)
        )

        request_token = _REQUEST_ID.set(request_id)
        correlation_token = _CORRELATION_ID.set(correlation_id)
        request.state.request_context = RequestContext(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            from app.core.error_handlers import unhandled_exception_handler

            response = await unhandled_exception_handler(request, exc)
        finally:
            current_request_id = _REQUEST_ID.get()
            current_correlation_id = _CORRELATION_ID.get()

        response.headers[REQUEST_ID_HEADER] = current_request_id or request_id
        response.headers[CORRELATION_ID_HEADER] = current_correlation_id or correlation_id
        _REQUEST_ID.reset(request_token)
        _CORRELATION_ID.reset(correlation_token)
        return response


def get_request_id() -> str | None:
    return _REQUEST_ID.get()


def get_correlation_id() -> str | None:
    return _CORRELATION_ID.get()


def get_current_request_context() -> RequestContext | None:
    request_id = get_request_id()
    correlation_id = get_correlation_id()
    if request_id is None or correlation_id is None:
        return None
    return RequestContext(request_id=request_id, correlation_id=correlation_id)


def _resolve_correlation_id(header_value: str | None) -> str:
    if header_value and _SAFE_HEADER_VALUE.fullmatch(header_value):
        return header_value
    return _generate_id()


def _generate_id() -> str:
    return uuid.uuid4().hex
