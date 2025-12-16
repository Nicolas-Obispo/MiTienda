"""
usuarios_schemas.py
--------------------
Schemas Pydantic para validar datos de usuarios.

Estos schemas son compartidos entre MiTienda y MiPlaza.
Los campos agregados son solo de salida (response),
para no romper flujos existentes.
"""

from pydantic import BaseModel, EmailStr
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
    modo_activo: str
    onboarding_completo: bool
    provincia: Optional[str] = None
    ciudad: Optional[str] = None

    class Config:
        orm_mode = True


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
# Schema para cambio de modo
# ---------------------------------
class UsuarioCambioModo(BaseModel):
    """
    Datos requeridos para cambiar el modo activo del usuario.
    """
    modo: str
