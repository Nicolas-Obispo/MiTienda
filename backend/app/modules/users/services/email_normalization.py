"""Owner unico de canonicalizacion de email para identidad FeedGo."""

from email_validator import EmailNotValidError, validate_email


class InvalidEmailError(ValueError):
    """El valor no puede convertirse en un email canonico valido."""


def canonicalize_email(value: str) -> str:
    """Valida y canonicaliza sin aplicar reglas particulares de providers."""

    if not isinstance(value, str):
        raise InvalidEmailError("El email debe ser texto")

    try:
        normalized = validate_email(
            value.strip(),
            check_deliverability=False,
        ).normalized
    except EmailNotValidError as exc:
        raise InvalidEmailError("El email no es valido") from exc

    # FeedGo compara el identificador completo sin diferencias de casing. No
    # elimina puntos, aliases '+' ni aplica semantica especial de Google.
    return normalized.casefold()
