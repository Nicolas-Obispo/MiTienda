# app/core/security.py
# --------------------
# Funciones de seguridad: hash y verificación de contraseñas.
# Toda la lógica de JWT vive en app/core/auth.py (NO acá).

from passlib.context import CryptContext

# Configuración del hash bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash bcrypt valido y precomputado para igualar el trabajo criptografico
# cuando no existe una credencial utilizable. No corresponde a una cuenta ni
# contiene material secreto y nunca se persiste.
DUMMY_BCRYPT_HASH = (
    "$2b$12$7TKafIulPAEyHN1k54/2YuIORtHQjfr8i6IBTj7aWp.7ZAIJst2te"
)


def verificar_password(password_plano: str, password_hashed: str) -> bool:
    """
    Verifica si la contraseña ingresada coincide con la hasheada.
    """
    return pwd_context.verify(password_plano, password_hashed)


def hash_password(password: str) -> str:
    """
    Hashea contraseñas usando bcrypt.
    """
    return pwd_context.hash(password)


def password_hash_is_usable(password_hashed: str | None) -> bool:
    """Confirma que el material almacenado es un hash bcrypt parseable."""

    if not isinstance(password_hashed, str) or not password_hashed:
        return False
    if pwd_context.identify(password_hashed) != "bcrypt":
        return False
    try:
        pwd_context.handler("bcrypt").from_string(password_hashed)
    except (TypeError, ValueError):
        return False
    return True


def verificar_password_o_dummy(
    password_plano: str,
    password_hashed: str | None,
) -> bool:
    """Ejecuta exactamente un bcrypt y solo acepta un hash real utilizable."""

    usable = password_hash_is_usable(password_hashed)
    selected_hash = password_hashed if usable else DUMMY_BCRYPT_HASH
    verified = verificar_password(password_plano, selected_hash)
    return bool(usable and verified)
