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
    RUNTIME_ENVIRONMENT: str = "production"

    # --------------------------
    # 🔐 Configuración JWT
    # --------------------------
    SECRET_KEY: str     # También se toma del .env si existe
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_ISSUER: str = "feedgo"
    JWT_AUDIENCE: str = "feedgo-web"
    JWT_CONTRACT_VERSION: int = 1

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

    # Canal transaccional de identidad. Permanece deshabilitado y separado del
    # correo administrativo hasta que su composition root sea implementado.
    IDENTITY_EMAIL_ENABLED: bool = False
    IDENTITY_EMAIL_PROVIDER: str = "disabled"
    # Credencial exclusiva del canal de identidad. No reutiliza la credencial
    # administrativa ni acepta la credencial historicamente expuesta.
    IDENTITY_RESEND_API_KEY: str | None = None
    IDENTITY_EMAIL_FROM_ADDRESS: str | None = None
    IDENTITY_EMAIL_PUBLIC_BASE_URL: str | None = None
    IDENTITY_EMAIL_TIMEOUT_SECONDS: float = 5.0
    IDENTITY_FAKE_MAILBOX_ENABLED: bool = False
    IDENTITY_FAKE_MAILBOX_TTL_SECONDS: int = 900
    IDENTITY_FAKE_MAILBOX_MAX_MESSAGES: int = 20
    PHONE_OTP_FAKE_MAILBOX_ENABLED: bool = False
    PHONE_OTP_FAKE_MAILBOX_TTL_SECONDS: int = 600
    PHONE_OTP_FAKE_MAILBOX_MAX_MESSAGES: int = 20
    IDENTITY_SMS_ENABLED: bool = False
    IDENTITY_SMS_PROVIDER: str = "disabled"
    IDENTITY_WHATSAPP_ENABLED: bool = False
    IDENTITY_WHATSAPP_PROVIDER: str = "disabled"

    # Enforcement comercial de ET99.7. Permanece apagado hasta completar el
    # gate operativo del canal real de verificacion de email.
    COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED: bool = False

    # Secreto dedicado a pseudonimizar subjects de limites de identidad.
    # No puede reutilizar JWT ni credenciales de providers.
    ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET: str | None = None
    PHONE_VERIFICATION_HMAC_SECRET: str | None = None

    class Config:
        env_file = ".env"


# Instancia exportable
settings = Settings()
