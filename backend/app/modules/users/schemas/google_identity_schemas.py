"""Contratos HTTP minimos para Google OIDC backend."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GoogleAuthorizationStartRequest(BaseModel):
    purpose: Literal["login", "signup"]
    return_to: str | None = Field(default=None, max_length=512)
    acepta_terminos: bool = Field(default=False, strict=True)
    acepta_privacidad: bool = Field(default=False, strict=True)


class GoogleAuthorizationStartResponse(BaseModel):
    authorization_url: str
    expires_at: datetime


class GoogleLinkAuthorizationStartRequest(BaseModel):
    confirm_link: Literal[True]
    return_to: str | None = Field(default=None, max_length=512)


class GoogleSessionExchangeRequest(BaseModel):
    handle: str = Field(min_length=32, max_length=128)


class GoogleSessionExchangeResponse(BaseModel):
    status: Literal["authenticated", "action_required"]
    token: str | None = None
    usuario_id: int | None = None
    return_to: str | None = None
