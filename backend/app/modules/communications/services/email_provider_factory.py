from email.utils import parseaddr
from math import isfinite

from app.core.config import settings
from app.modules.communications.providers.email_provider import (
    EmailProvider,
    FakeEmailProvider,
)
from app.modules.communications.providers.resend_email_provider import ResendEmailProvider
from app.modules.communications.services.local_identity_mailbox import (
    LocalIdentityMailboxProvider,
)
from app.modules.communications.services.identity_email_services import (
    validate_identity_public_base_url,
)


_local_identity_mailbox_provider: LocalIdentityMailboxProvider | None = None
_LOCAL_RUNTIME_ENVIRONMENTS = frozenset({"local", "development", "dev", "test"})
_REAL_EMAIL_RUNTIME_ENVIRONMENTS = frozenset(
    {"local", "development", "dev", "test", "staging", "production"}
)


def _runtime_environment() -> str:
    return settings.RUNTIME_ENVIRONMENT.strip().lower()


def _validate_identity_sender(value: str | None) -> None:
    sender = (value or "").strip()
    _, address = parseaddr(sender)
    local_part, separator, domain = address.rpartition("@")
    if (
        not sender
        or not address
        or not separator
        or not local_part
        or not domain
        or any(character.isspace() for character in address)
    ):
        raise ValueError("identity_email_from_address_invalid")


def _validate_identity_timeout(value: float) -> None:
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        raise ValueError("identity_email_timeout_invalid") from None
    if not isfinite(timeout) or timeout <= 0:
        raise ValueError("identity_email_timeout_invalid")


def _build_identity_resend_provider() -> ResendEmailProvider:
    runtime = _runtime_environment()
    if runtime not in _REAL_EMAIL_RUNTIME_ENVIRONMENTS:
        raise ValueError("identity_email_runtime_not_supported")

    api_key = (settings.IDENTITY_RESEND_API_KEY or "").strip()
    if not api_key:
        raise ValueError("identity_resend_api_key_required")
    _validate_identity_sender(settings.IDENTITY_EMAIL_FROM_ADDRESS)
    _validate_identity_timeout(settings.IDENTITY_EMAIL_TIMEOUT_SECONDS)
    # Un provider real siempre requiere HTTPS. El unico HTTP permitido para
    # enlaces de identidad es el harness fake local, que no llega a esta rama.
    validate_identity_public_base_url(settings.IDENTITY_EMAIL_PUBLIC_BASE_URL)
    return ResendEmailProvider(
        api_key=api_key,
        base_url=settings.RESEND_API_BASE_URL,
        timeout_seconds=float(settings.IDENTITY_EMAIL_TIMEOUT_SECONDS),
    )


def build_configured_email_provider() -> EmailProvider | None:
    """Composition root: la seleccion por entorno queda fuera de los dominios."""
    provider_name = settings.EMAIL_PROVIDER.strip().lower()
    if not settings.ADMIN_EMAIL_ENABLED or provider_name == "disabled":
        return None
    if provider_name == "resend":
        return ResendEmailProvider(
            api_key=settings.RESEND_API_KEY or "",
            base_url=settings.RESEND_API_BASE_URL,
            timeout_seconds=settings.RESEND_TIMEOUT_SECONDS,
        )
    raise ValueError("email_provider_not_supported")


def build_identity_email_provider() -> EmailProvider | None:
    """Composition root exclusivo del correo transaccional de identidad."""

    provider_name = settings.IDENTITY_EMAIL_PROVIDER.strip().lower()
    if provider_name == "fake" and _runtime_environment() not in _LOCAL_RUNTIME_ENVIRONMENTS:
        raise ValueError("identity_fake_email_provider_not_allowed")
    if not settings.IDENTITY_EMAIL_ENABLED or provider_name == "disabled":
        return None
    if provider_name == "fake":
        if (
            settings.IDENTITY_FAKE_MAILBOX_ENABLED
        ):
            return get_local_identity_mailbox_provider()
        return FakeEmailProvider()
    if provider_name == "resend":
        return _build_identity_resend_provider()
    raise ValueError("identity_email_provider_not_supported")


def get_local_identity_mailbox_provider() -> LocalIdentityMailboxProvider:
    """Dev/test only: conserva mensajes fake en memoria de proceso."""

    global _local_identity_mailbox_provider
    if _local_identity_mailbox_provider is None:
        _local_identity_mailbox_provider = LocalIdentityMailboxProvider(
            ttl_seconds=settings.IDENTITY_FAKE_MAILBOX_TTL_SECONDS,
            max_messages=settings.IDENTITY_FAKE_MAILBOX_MAX_MESSAGES,
        )
    return _local_identity_mailbox_provider
