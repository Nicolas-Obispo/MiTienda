"""Owner no sensible de disponibilidad real de Google Identity."""

from app.core.config import Settings, settings
from app.modules.users.services.google_oidc_services import (
    GoogleOidcError,
    google_oidc_configuration,
)


def google_identity_is_available(source: Settings = settings) -> bool:
    """Devuelve disponibilidad efectiva, sin revelar la causa de un NO."""

    try:
        google_oidc_configuration(source)
    except (GoogleOidcError, ValueError):
        return False
    return True
