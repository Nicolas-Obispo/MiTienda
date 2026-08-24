import json
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.modules.communications.providers.email_provider import (
    EmailDeliveryError,
    EmailMessage,
)


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes


class ResendTransport(Protocol):
    def post(self, *, url: str, headers: dict[str, str], body: bytes, timeout: float) -> HttpResponse: ...


class UrllibResendTransport:
    def post(self, *, url: str, headers: dict[str, str], body: bytes, timeout: float) -> HttpResponse:
        request = Request(url=url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310 - destino configurado y controlado
                return HttpResponse(status=response.status, body=response.read())
        except HTTPError as exc:
            return HttpResponse(status=exc.code, body=exc.read())
        except (URLError, TimeoutError, OSError) as exc:
            raise EmailDeliveryError("email_provider_unavailable", retryable=True) from exc


class ResendEmailProvider:
    """Adapter Resend. Ningun contrato fuera de Comunicaciones conoce su API."""

    def __init__(self, *, api_key: str, base_url: str, timeout_seconds: float,
                 transport: ResendTransport | None = None):
        if not api_key.strip():
            raise ValueError("resend_api_key_required")
        normalized_url = base_url.strip().rstrip("/")
        if not normalized_url.startswith("https://"):
            raise ValueError("resend_https_base_url_required")
        if timeout_seconds <= 0:
            raise ValueError("resend_timeout_must_be_positive")
        self._api_key = api_key
        self._base_url = normalized_url
        self._timeout_seconds = timeout_seconds
        self._transport = transport or UrllibResendTransport()

    def send(self, message: EmailMessage) -> str:
        response = self._transport.post(
            url=f"{self._base_url}/emails",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": message.idempotency_key[:256],
                "User-Agent": "FeedGo/1.0",
            },
            body=json.dumps({
                "from": message.sender,
                "to": [message.recipient],
                "subject": message.subject,
                "text": message.body,
            }, separators=(",", ":")).encode("utf-8"),
            timeout=self._timeout_seconds,
        )
        if 200 <= response.status < 300:
            try:
                external_id = json.loads(response.body.decode("utf-8"))["id"]
            except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise EmailDeliveryError("email_provider_invalid_response", retryable=True) from exc
            if not isinstance(external_id, str) or not external_id.strip():
                raise EmailDeliveryError("email_provider_invalid_response", retryable=True)
            return external_id.strip()
        if response.status in {408, 425, 429} or response.status >= 500:
            raise EmailDeliveryError("email_provider_temporarily_unavailable", retryable=True)
        if response.status == 409:
            try:
                provider_error = json.loads(response.body.decode("utf-8")).get("name")
            except (AttributeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
                provider_error = None
            retryable = provider_error == "concurrent_idempotent_requests"
            raise EmailDeliveryError("email_provider_idempotency_conflict", retryable=retryable)
        if response.status in {400, 422}:
            raise EmailDeliveryError("email_provider_request_invalid", retryable=False)
        if response.status == 401:
            raise EmailDeliveryError("email_provider_authentication_failed", retryable=False)
        if response.status == 403:
            raise EmailDeliveryError("email_provider_sender_not_authorized", retryable=False)
        raise EmailDeliveryError("email_provider_rejected", retryable=False)
