# app/core/config.py
# -------------------
# Configuración global de MiTienda.
# Compatible con Pydantic v2 + pydantic-settings.

from datetime import datetime

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

    # Integracion geografica. La ausencia de key no impide iniciar FeedGo.
    GEOCODING_PROVIDER: str = "geoapify"
    GEOAPIFY_API_KEY: str | None = None
    GEOAPIFY_TIMEOUT_SECONDS: float = 5.0
    GEOAPIFY_RATE_LIMIT_RPS: int = 5

    # Canal operativo administrativo. El envio permanece deshabilitado salvo
    # configuracion explicita del entorno; nunca reutiliza emails de usuarios.
    ADMIN_EMAIL_ENABLED: bool = False
    ADMINISTRATIVE_OPERATIONAL_EMAIL: str | None = None
    EMAIL_FROM_ADDRESS: str | None = None
    EMAIL_PROVIDER: str = "disabled"
    RESEND_API_KEY: str | None = None
    RESEND_API_BASE_URL: str = "https://api.resend.com"
    RESEND_TIMEOUT_SECONDS: float = 5.0
    ADMIN_BASE_URL: str | None = None
    ADMIN_EMAIL_NOTIFY_SEV3_SEV4: bool = False
    ADMIN_EMAIL_MAX_ATTEMPTS: int = 3
    OPERATIONAL_EMAIL_DISPATCHER_ENABLED: bool = False
    OPERATIONAL_EMAIL_LEASE_SECONDS: int = 30
    OPERATIONAL_EMAIL_DISPATCHER_ACTIVATED_AT: datetime | None = None
    OPERATIONAL_EMAIL_BATCH_SIZE: int = 10
    OPERATIONAL_EMAIL_POLL_INTERVAL_SECONDS: float = 10.0
    OPERATIONAL_EMAIL_WORKER_STATE_FILE: str | None = None
    OPERATIONAL_EMAIL_WORKER_HEARTBEAT_TTL_SECONDS: float = 90.0

    class Config:
        env_file = ".env"


# Instancia exportable
settings = Settings()
