"""Templates de texto minimo para el correo transaccional de identidad."""

from dataclasses import dataclass


EMAIL_VERIFICATION = "email_verification"
PASSWORD_RESET = "password_reset"


@dataclass(frozen=True)
class IdentityEmailContent:
    subject: str
    body: str


def render_identity_email(*, purpose: str, link: str) -> IdentityEmailContent:
    if purpose == EMAIL_VERIFICATION:
        return IdentityEmailContent(
            subject="Verificá tu cuenta de FeedGo",
            body=(
                "Hola,\n\n"
                "Verificá tu cuenta de FeedGo desde este enlace:\n"
                f"{link}\n\n"
                "El enlace es válido por 24 horas.\n\n"
                "FeedGo"
            ),
        )
    if purpose == PASSWORD_RESET:
        return IdentityEmailContent(
            subject="Creá una nueva contraseña de FeedGo",
            body=(
                "Hola,\n\n"
                "Creá una nueva contraseña de FeedGo desde este enlace:\n"
                f"{link}\n\n"
                "El enlace es válido por 30 minutos.\n\n"
                "FeedGo"
            ),
        )
    raise ValueError("identity_email_purpose_invalid")
