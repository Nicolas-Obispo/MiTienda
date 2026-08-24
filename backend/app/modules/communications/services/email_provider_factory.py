from app.core.config import settings
from app.modules.communications.providers.email_provider import EmailProvider
from app.modules.communications.providers.resend_email_provider import ResendEmailProvider


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
