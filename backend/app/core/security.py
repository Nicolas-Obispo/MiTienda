# app/core/security.py
# --------------------
# Funciones de seguridad: hash y verificación de contraseñas.
# Toda la lógica de JWT vive en app/core/auth.py (NO acá).

from passlib.context import CryptContext

# Configuración del hash bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
