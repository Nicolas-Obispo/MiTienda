"""
usuarios_schemas.py
--------------------
Schemas Pydantic para validar datos de usuarios.
"""

from pydantic import BaseModel, EmailStr


# Schema para registrar usuario (entrada del cliente)
class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str  # 👈 el cliente envía la contraseña sin hash


# Schema para login (lo vamos a usar en el siguiente paso)
class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


# Schema para devolver usuario al cliente
class UsuarioResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True
