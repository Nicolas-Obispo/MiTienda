# app/core/config.py
# -------------------
# Configuración global de MiTienda.
# Compatible con Pydantic v2 + pydantic-settings.

from datetime import datetime

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from urllib.parse import urlsplit


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

    # Fundacion OAuth de ET99.8. Permanece fail-closed hasta que la integracion
    # Google/OIDC, sus secretos y redirects exactos sean habilitados expresamente.
    GOOGLE_IDENTITY_ENABLED: bool = False
    GOOGLE_OAUTH_TRANSACTION_TTL_SECONDS: int = Field(default=600, ge=1, le=600)
    GOOGLE_OAUTH_PUBLIC_RATE_LIMIT_PER_HOUR: int = Field(default=10, ge=1)
    GOOGLE_OAUTH_LINK_RATE_LIMIT_PER_HOUR: int = Field(default=10, ge=1)
    GOOGLE_RECENT_REAUTH_SECONDS: int = Field(default=600, ge=1, le=600)
    GOOGLE_OIDC_CLIENT_ID: str | None = None
    GOOGLE_OIDC_CLIENT_SECRET: str | None = None
    GOOGLE_OIDC_DISCOVERY_URL: str = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    GOOGLE_OIDC_ALLOWED_ISSUER: str = "https://accounts.google.com"
    GOOGLE_OIDC_REDIRECT_URI: str | None = None
    GOOGLE_OIDC_PUBLIC_BASE_URL: str | None = None
    GOOGLE_OIDC_FRONTEND_RESULT_PATH: str = "/auth/google/resultado"
    GOOGLE_OIDC_TIMEOUT_SECONDS: float = Field(default=5.0, gt=0, le=30)
    GOOGLE_OIDC_RESULT_HANDLE_TTL_SECONDS: int = Field(default=120, ge=1, le=120)

    @model_validator(mode="after")
    def validate_google_oidc_configuration(self):
        if not self.GOOGLE_IDENTITY_ENABLED:
            return self

        required = {
            "GOOGLE_OIDC_CLIENT_ID": self.GOOGLE_OIDC_CLIENT_ID,
            "GOOGLE_OIDC_CLIENT_SECRET": self.GOOGLE_OIDC_CLIENT_SECRET,
            "GOOGLE_OIDC_REDIRECT_URI": self.GOOGLE_OIDC_REDIRECT_URI,
            "GOOGLE_OIDC_PUBLIC_BASE_URL": self.GOOGLE_OIDC_PUBLIC_BASE_URL,
            "ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET": (
                self.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET
            ),
        }
        missing = [name for name, value in required.items() if not value or not value.strip()]
        if missing:
            raise ValueError("google_oidc_configuration_incomplete")
        if self.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET in {
            self.SECRET_KEY,
            self.RESEND_API_KEY,
            self.IDENTITY_RESEND_API_KEY,
        }:
            raise ValueError("google_oidc_rate_limit_secret_reused")
        if self.GOOGLE_OIDC_DISCOVERY_URL != (
            "https://accounts.google.com/.well-known/openid-configuration"
        ):
            raise ValueError("google_oidc_discovery_not_allowed")
        if self.GOOGLE_OIDC_ALLOWED_ISSUER != "https://accounts.google.com":
            raise ValueError("google_oidc_issuer_not_allowed")

        redirect = urlsplit(self.GOOGLE_OIDC_REDIRECT_URI or "")
        public_base = urlsplit(self.GOOGLE_OIDC_PUBLIC_BASE_URL or "")
        if (
            redirect.scheme != "https"
            or not redirect.netloc
            or redirect.username is not None
            or redirect.password is not None
            or redirect.query
            or redirect.fragment
            or redirect.path != "/usuarios/google/callback"
        ):
            raise ValueError("google_oidc_redirect_uri_invalid")
        if (
            public_base.scheme != "https"
            or not public_base.netloc
            or public_base.username is not None
            or public_base.password is not None
            or public_base.path not in {"", "/"}
            or public_base.query
            or public_base.fragment
        ):
            raise ValueError("google_oidc_public_base_url_invalid")
        result_path = self.GOOGLE_OIDC_FRONTEND_RESULT_PATH
        if (
            not result_path.startswith("/")
            or result_path.startswith("//")
            or "\\" in result_path
            or urlsplit(result_path).query
            or urlsplit(result_path).fragment
        ):
            raise ValueError("google_oidc_frontend_result_path_invalid")
        return self

    class Config:
        env_file = ".env"


# Instancia exportable
settings = Settings()
