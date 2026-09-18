"""
usuarios_schemas.py
--------------------
Schemas Pydantic para validar datos de usuarios.

Estos schemas son compartidos entre MiTienda y MiPlaza.
Los campos agregados son solo de salida (response),
para no romper flujos existentes.
"""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal, Optional

from app.modules.users.services.password_policy import validate_new_password


# ---------------------------------
# Schema para registrar usuario
# (entrada del cliente)
# ---------------------------------
class UsuarioCreate(BaseModel):
    email: EmailStr
    acepta_terminos: Literal[True]
    acepta_privacidad: Literal[True]
    password: str  # 👈 el cliente envía la contraseña sin hash

    @field_validator("password")
    @classmethod
    def validar_password_nuevo(cls, value: str) -> str:
        return validate_new_password(value)


# ---------------------------------
# Schema para login
# ---------------------------------
class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class EmailAvailabilityRequest(BaseModel):
    email: EmailStr


class EmailAvailabilityResponse(BaseModel):
    disponible: bool


class EmailVerificationConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class EmailVerificationResponse(BaseModel):
    status: Literal["verified", "sent", "already_verified"]


class PasswordRecoveryRequest(BaseModel):
    # El endpoint publico debe entregar la misma respuesta para cualquier
    # cadena, incluso cuando no pueda canonicalizarse. La validacion segura y
    # uniforme pertenece al service de recuperacion, no a Pydantic/HTTP.
    email: str
    channel: Literal["email", "sms", "whatsapp"] = "email"


class PasswordRecoveryResponse(BaseModel):
    message: str


class PasswordResetRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validar_password_nuevo(cls, value: str) -> str:
        return validate_new_password(value)


class PasswordResetResponse(BaseModel):
    status: Literal["password_updated"]


class AuthenticatedPasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=512)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validar_password_nuevo(cls, value: str) -> str:
        return validate_new_password(value)


class AuthenticatedPasswordChangeResponse(BaseModel):
    status: Literal["password_updated"]


class AuthenticationMethodConfirmationRequest(BaseModel):
    confirm: Literal[True]


class AddPasswordCredentialRequest(AuthenticationMethodConfirmationRequest):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validar_password_nuevo(cls, value: str) -> str:
        return validate_new_password(value)


class AuthenticationMethodMutationResponse(BaseModel):
    status: Literal["password_added", "google_unlinked"]


class PasswordReauthenticationRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=512)


class ReauthenticationResponse(BaseModel):
    token: str


class PhoneVerificationIssueResponse(BaseModel):
    challenge_id: str
    status: Literal["sent"]


class PhoneVerificationConfirmRequest(BaseModel):
    challenge_id: str = Field(min_length=20, max_length=64)
    code: str = Field(pattern=r"^\d{6}$")


class PhoneVerificationConfirmResponse(BaseModel):
    status: Literal["verified"]


# ---------------------------------
# Schema para devolver usuario
# ---------------------------------
class UsuarioResponse(BaseModel):
    # Campos existentes (MiTienda)
    id: int
    email: EmailStr

    # Campos agregados para MiPlaza
    avatar_url: Optional[str] = None  # ETAPA 49
    color_fondo: Optional[str] = None
    modo_activo: str
    onboarding_completo: bool
    provincia: Optional[str] = None
    ciudad: Optional[str] = None
    email_verified_at: Optional[datetime] = None
    email_verification_source: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    telefono_e164: Optional[str] = None
    telefono_verified_at: Optional[datetime] = None
    telefono_verification_source: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class UsuarioRegistrationResponse(UsuarioResponse):
    email_verification_status: Literal["sent", "delivery_failed"]


class CommercialCapabilitiesResponse(BaseModel):
    puede_crear_espacio: bool
    puede_administrar_espacios: bool
    puede_publicar_en_espacios: bool


class AuthenticationMethodsResponse(BaseModel):
    has_password: bool
    google_linked: bool
    usable_methods: list[Literal["password", "google"]]
    can_unlink_google: bool


class UsuarioMeResponse(UsuarioResponse):
    perfil_completo: bool
    campos_perfil_faltantes: list[
        Literal[
            "provincia",
              "ciudad",
              "fecha_nacimiento",
              "telefono",
              "email_verificado",
        ]
    ]
    capabilities: CommercialCapabilitiesResponse
    pendientes_comerciales: list[
        Literal[
            "perfil_incompleto",
            "aceptaciones_legales_pendientes",
            "mayoria_edad_requerida",
        ]
    ]
    authentication_methods: AuthenticationMethodsResponse


# ---------------------------------
# Schema publico para devolver usuario
# ---------------------------------
class UsuarioPublicResponse(BaseModel):
    id: int

    model_config = {
        "from_attributes": True
    }


# ---------------------------------
# Schema para onboarding de usuario
# ---------------------------------
class UsuarioOnboarding(BaseModel):
    """
    Datos requeridos para completar el onboarding inicial.
    """
    provincia: str
    ciudad: str


# ---------------------------------
# Schema para editar perfil basico
# ---------------------------------
class UsuarioPerfilUpdate(BaseModel):
    """
    Datos editables desde Mi Perfil.

    No permite modificar email, password, avatar, modo_activo ni onboarding.
    Un telefono ya verificado requiere el flujo futuro de reemplazo seguro.
    """
    provincia: Optional[str] = None
    ciudad: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    telefono_e164: Optional[str] = Field(default=None, max_length=64)
    color_fondo: Optional[str] = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )


# ---------------------------------
# Schema para cambio de modo
# ---------------------------------
class UsuarioCambioModo(BaseModel):
    """
    Datos requeridos para cambiar el modo activo del usuario.
    """
    modo: str


# ---------------------------------
# Schema para actualizar avatar (ETAPA 49)
# ---------------------------------
class UsuarioAvatarUpdate(BaseModel):
    """
    Datos requeridos para actualizar la foto de perfil del usuario.

    - avatar_url: URL pública devuelta por /media/upload
    """
    avatar_url: str


class DocumentoPublicoVigenteResponse(BaseModel):
    tipo: str
    version: str
    referencia: str
    url: str
