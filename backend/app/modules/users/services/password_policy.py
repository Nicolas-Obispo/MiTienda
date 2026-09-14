"""Politica backend unica para contrasenas nuevas de FeedGo."""

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_UTF8_BYTES = 72


class PasswordPolicyError(ValueError):
    """La contrasena nueva no cumple el contrato de seguridad vigente."""


def validate_new_password(value: str) -> str:
    """Valida altas y los futuros cambios/recoveries sin transformar secretos."""

    if not isinstance(value, str):
        raise PasswordPolicyError("La contrasena debe ser texto")
    if len(value) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"La contrasena debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"
        )
    if not any(character.isupper() for character in value):
        raise PasswordPolicyError("La contrasena debe incluir una letra mayuscula")
    if not any(character.islower() for character in value):
        raise PasswordPolicyError("La contrasena debe incluir una letra minuscula")
    if not any(character.isdecimal() for character in value):
        raise PasswordPolicyError("La contrasena debe incluir un numero")
    if any(character.isspace() for character in value):
        raise PasswordPolicyError("La contrasena no puede contener espacios")
    if len(value.encode("utf-8")) > MAX_PASSWORD_UTF8_BYTES:
        raise PasswordPolicyError(
            "La contrasena excede el limite seguro del algoritmo actual"
        )
    return value
