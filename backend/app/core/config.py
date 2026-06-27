# app/core/config.py
# -------------------
# Configuración global de MiTienda.
# Compatible con Pydantic v2 + pydantic-settings.

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuración general de la aplicación.
    Valores obtenidos desde .env
    """

    # --------------------------
    # 🗄️ Configuración Base de Datos
    # --------------------------
    DATABASE_URL: str   # ← SIN VALOR POR DEFECTO (usa .env)

    # --------------------------
    # 🔐 Configuración JWT
    # --------------------------
    SECRET_KEY: str     # También se toma del .env si existe
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # --------------------------
    # 🤖 Configuración IA
    # --------------------------
    EMBEDDINGS_PROVIDER: str = "simulated"
    EMBEDDINGS_LOCAL_MODEL_PATH: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"


# Instancia exportable
settings = Settings()
