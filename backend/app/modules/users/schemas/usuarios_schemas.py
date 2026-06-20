"""
usuarios_schemas.py
--------------------
Schemas Pydantic para validar datos de usuarios.

Estos schemas son compartidos entre MiTienda y MiPlaza.
Los campos agregados son solo de salida (response),
para no romper flujos existentes.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# ---------------------------------
# Schema para registrar usuario
# (entrada del cliente)
# ---------------------------------
class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str  # 👈 el cliente envía la contraseña sin hash


# ---------------------------------
# Schema para login
# ---------------------------------
class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


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
    """
    provincia: Optional[str] = None
    ciudad: Optional[str] = None
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
