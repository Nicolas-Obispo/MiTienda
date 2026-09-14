"""Composicion y entrega efimera del correo transaccional de identidad."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, urlsplit
from ipaddress import ip_address

from app.core.config import settings
from app.modules.communications.providers.email_provider import (
    EmailDeliveryError,
    EmailMessage,
    EmailProvider,
)
from app.modules.communications.services.identity_email_templates import (
    EMAIL_VERIFICATION,
    PASSWORD_RESET,
    render_identity_email,
)


MAX_IDENTITY_EMAIL_ATTEMPTS = 2
IDENTITY_EMAIL_PATHS = {
    EMAIL_VERIFICATION: "/verificar-email",
    PASSWORD_RESET: "/restablecer-password",
}


class IdentityEmailDeliveryError(RuntimeError):
    """Error estable que no expone provider, destinatario, URL ni secreto."""

    def __init__(self):
        super().__init__("identity_email_delivery_failed")
        self.safe_code = "identity_email_delivery_failed"


@dataclass(frozen=True)
class IdentityEmailDeliveryResult:
    provider_reference: str
    attempts: int


def validate_identity_public_base_url(
    public_base_url: str | None,
    *,
    allow_loopback_http: bool = False,
) -> str:
    """Valida y normaliza la URL publica sin incluir secretos en errores."""

    base_url = (public_base_url or "").strip()
    parsed = urlsplit(base_url)
    try:
        loopback_host = bool(parsed.hostname and ip_address(parsed.hostname).is_loopback)
    except ValueError:
        loopback_host = parsed.hostname == "localhost"

    allowed_scheme = parsed.scheme == "https" or (
        allow_loopback_http and parsed.scheme == "http" and loopback_host
    )
    if (
        not allowed_scheme
        or not parsed.netloc
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError("identity_email_public_base_url_invalid")
    return base_url.rstrip("/")


def build_identity_action_link(
    *,
    purpose: str,
    secret: str,
    public_base_url: str | None = None,
) -> str:
    """Construye un enlace HTTPS cuyo secreto vive solamente en el fragment."""

    if purpose not in IDENTITY_EMAIL_PATHS:
        raise ValueError("identity_email_purpose_invalid")
    if not isinstance(secret, str) or not secret:
        raise ValueError("identity_email_secret_invalid")
    base_url = public_base_url or settings.IDENTITY_EMAIL_PUBLIC_BASE_URL
    parsed = urlsplit(base_url or "")
    try:
        loopback_host = bool(parsed.hostname and ip_address(parsed.hostname).is_loopback)
    except ValueError:
        loopback_host = parsed.hostname == "localhost"
    local_fake_http = (
        parsed.scheme == "http"
        and loopback_host
        and settings.RUNTIME_ENVIRONMENT.strip().lower() in {"local", "development", "test"}
        and settings.IDENTITY_FAKE_MAILBOX_ENABLED
        and settings.IDENTITY_EMAIL_ENABLED
        and settings.IDENTITY_EMAIL_PROVIDER.strip().lower() == "fake"
    )
    normalized_base = validate_identity_public_base_url(
        base_url,
        allow_loopback_http=local_fake_http,
    )
    encoded_secret = quote(secret, safe="")
    return f"{normalized_base}{IDENTITY_EMAIL_PATHS[purpose]}#token={encoded_secret}"


def deliver_identity_email(
    *,
    provider: EmailProvider | None,
    recipient: str,
    purpose: str,
    secret: str,
    issuance_id: str,
    sender: str | None = None,
    public_base_url: str | None = None,
    max_attempts: int = MAX_IDENTITY_EMAIL_ATTEMPTS,
) -> IdentityEmailDeliveryResult:
    """Envia en memoria con retry inmediato acotado y misma idempotencia."""

    if provider is None:
        raise IdentityEmailDeliveryError()
    if not isinstance(issuance_id, str) or not issuance_id:
        raise ValueError("identity_email_issuance_id_invalid")
    if max_attempts < 1 or max_attempts > MAX_IDENTITY_EMAIL_ATTEMPTS:
        raise ValueError("identity_email_attempts_invalid")
    from_address = (sender or settings.IDENTITY_EMAIL_FROM_ADDRESS or "").strip()
    if not from_address:
        raise ValueError("identity_email_sender_required")

    link = build_identity_action_link(
        purpose=purpose,
        secret=secret,
        public_base_url=public_base_url,
    )
    content = render_identity_email(purpose=purpose, link=link)
    message = EmailMessage(
        recipient=recipient,
        sender=from_address,
        subject=content.subject,
        body=content.body,
        idempotency_key=issuance_id,
    )

    for attempt in range(1, max_attempts + 1):
        try:
            reference = provider.send(message)
            return IdentityEmailDeliveryResult(
                provider_reference=reference,
                attempts=attempt,
            )
        except EmailDeliveryError as exc:
            if not exc.retryable or attempt == max_attempts:
                raise IdentityEmailDeliveryError() from None
        except Exception:
            raise IdentityEmailDeliveryError() from None

    raise IdentityEmailDeliveryError()
