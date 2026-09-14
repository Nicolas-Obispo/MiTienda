# app/core/auth.py
# ----------------

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.models.tokens_models import TokenRevocado
from app.modules.users.services.feedgo_session_services import (
    FeedGoSessionInvalidError,
    get_feedgo_session_for_logout,
    get_valid_feedgo_session,
)

# auto_error=False permite controlar manualmente el 401
bearer_scheme = HTTPBearer(auto_error=False)

LEGACY_REQUIRED_CLAIMS = frozenset({"sub", "exp"})
VERSIONED_JWT_CLAIMS = frozenset(
    {"sub", "sid", "iat", "exp", "issuer", "audience", "version"}
)
VERSIONED_ONLY_CLAIMS = VERSIONED_JWT_CLAIMS - LEGACY_REQUIRED_CLAIMS


@dataclass(frozen=True)
class AuthTokenContext:
    contract: str
    usuario_id: int
    sid: str | None = None
    expires_at: int | None = None


@dataclass(frozen=True)
class AuthenticatedUserContext:
    usuario: Usuario
    token: AuthTokenContext


# -----------------------------------------
# 🔥 Verificar si un token fue revocado
# -----------------------------------------
def token_esta_revocado(token: str, db: Session) -> bool:
    """
    Devuelve True si el token ya fue invalidado por logout.
    """
    return (
        db.query(TokenRevocado)
        .filter(TokenRevocado.token == token)
        .first()
        is not None
    )


# -----------------------------------------
# 🔑 Crear token JWT
# -----------------------------------------
def crear_token_jwt(datos: dict) -> str:
    """
    Genera un token JWT legacy con la duracion configurada.
    """
    datos_a_codificar = datos.copy()
    expiracion = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    datos_a_codificar.update({"exp": expiracion})

    token = jwt.encode(
        datos_a_codificar,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return token


def crear_token_jwt_versionado(
    *, usuario_id: int, sid: str, issued_at: datetime, expires_at: datetime
) -> str:
    """Emite el contrato JWT asociado a una FeedGoSession."""

    return jwt.encode(
        {
            "sub": str(usuario_id),
            "sid": sid,
            "iat": _utc_epoch_seconds(issued_at),
            "exp": _utc_epoch_seconds(expires_at),
            "issuer": settings.JWT_ISSUER,
            "audience": settings.JWT_AUDIENCE,
            "version": settings.JWT_CONTRACT_VERSION,
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


# -----------------------------------------
# 🧩 Obtener usuario actual (OBLIGATORIO)
# -----------------------------------------
def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Valida el token JWT y devuelve el usuario autenticado.

    - Si no hay token → 401
    - Si es inválido / expirado / revocado → 401
    """

    if credenciales is None or not credenciales.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return _validar_token_y_obtener_usuario(
        token=credenciales.credentials,
        db=db,
    )


# -----------------------------------------
# 🧩 Obtener usuario actual (OPCIONAL)
# -----------------------------------------
def obtener_usuario_actual_opcional(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Versión opcional del usuario autenticado.

    - Si no hay token → devuelve None (NO 401)
    - Si hay token inválido → 401 (seguridad intacta)
    - Si token válido → devuelve Usuario
    """

    if credenciales is None or not credenciales.credentials:
        return None

    return _validar_token_y_obtener_usuario(
        token=credenciales.credentials,
        db=db,
    )


def obtener_contexto_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthenticatedUserContext:
    """Entrega Usuario y contrato de token a flujos backend que necesitan SID."""

    if credenciales is None or not credenciales.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _validar_token_y_obtener_contexto_usuario(
        token=credenciales.credentials,
        db=db,
    )


# -----------------------------------------
# 🔒 Lógica interna compartida
# -----------------------------------------
def _validar_token_y_obtener_usuario(token: str, db: Session) -> Usuario:
    """
    Función interna reutilizable:
    - Decodifica token
    - Verifica expiración
    - Verifica revocación
    - Devuelve usuario
    """

    return _validar_token_y_obtener_contexto_usuario(token, db).usuario


def _validar_token_y_obtener_contexto_usuario(
    token: str, db: Session
) -> AuthenticatedUserContext:
    context = _decodificar_contexto_token(token, db)
    if context.contract == "legacy" and token_esta_revocado(token, db):
        raise HTTPException(status_code=401, detail="Token revocado")

    usuario = db.query(Usuario).filter(Usuario.id == context.usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    return AuthenticatedUserContext(usuario=usuario, token=context)


def validar_token_para_logout(token: str, db: Session) -> AuthTokenContext:
    """Valida logout sin exigir que una sesion nueva siga sin revocar."""

    context = _decodificar_contexto_token(
        token, db, allow_revoked_versioned_session=True
    )
    if context.contract == "legacy" and token_esta_revocado(token, db):
        raise HTTPException(status_code=401, detail="Token revocado")
    usuario = db.query(Usuario.id).filter(Usuario.id == context.usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return context


def _decodificar_contexto_token(
    token: str,
    db: Session,
    *,
    allow_revoked_versioned_session: bool = False,
) -> AuthTokenContext:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if set(payload) & VERSIONED_ONLY_CLAIMS:
            usuario_id, sid = _validar_contrato_versionado(
                payload,
                db,
                allow_revoked_session=allow_revoked_versioned_session,
            )
            return AuthTokenContext("versioned", usuario_id, sid, payload["exp"])
        return AuthTokenContext(
            "legacy", _validar_contrato_legacy(payload), None, payload["exp"]
        )
    except (JWTError, FeedGoSessionInvalidError, TypeError, ValueError, OverflowError):
        raise HTTPException(
            status_code=401, detail="Token inválido o expirado"
        ) from None


def _validar_sub(payload: dict, *, allow_integer: bool = False) -> int:
    subject = payload.get("sub")
    if allow_integer and isinstance(subject, int) and not isinstance(subject, bool):
        if subject <= 0:
            raise ValueError("invalid subject")
        return subject
    if not isinstance(subject, str) or not subject.isdigit():
        raise ValueError("invalid subject")
    usuario_id = int(subject)
    if usuario_id <= 0:
        raise ValueError("invalid subject")
    return usuario_id


def _validar_contrato_legacy(payload: dict) -> int:
    if not LEGACY_REQUIRED_CLAIMS <= set(payload):
        raise ValueError("incomplete legacy contract")
    return _validar_sub(payload, allow_integer=True)


def _utc_epoch_seconds(value: datetime) -> int:
    """Normaliza DATETIME persistido como UTC a precision de segundos."""

    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return calendar.timegm(value.utctimetuple())


def _validar_contrato_versionado(
    payload: dict,
    db: Session,
    *,
    allow_revoked_session: bool = False,
) -> tuple[int, str]:
    if set(payload) != VERSIONED_JWT_CLAIMS:
        raise ValueError("incomplete or extended versioned contract")
    if payload["issuer"] != settings.JWT_ISSUER:
        raise ValueError("invalid issuer")
    if payload["audience"] != settings.JWT_AUDIENCE:
        raise ValueError("invalid audience")
    version = payload["version"]
    if isinstance(version, bool) or version != settings.JWT_CONTRACT_VERSION:
        raise ValueError("unsupported version")
    sid = payload["sid"]
    if not isinstance(sid, str) or not sid or len(sid) > 64:
        raise ValueError("invalid sid")
    issued_at = payload["iat"]
    expires_at = payload["exp"]
    if (
        isinstance(issued_at, bool)
        or isinstance(expires_at, bool)
        or not isinstance(issued_at, int)
        or not isinstance(expires_at, int)
        or expires_at <= issued_at
    ):
        raise ValueError("invalid token timestamps")

    usuario_id = _validar_sub(payload)
    session = (
        get_feedgo_session_for_logout(
            db,
            sid=sid,
            usuario_id=usuario_id,
            contract_version=version,
        )
        if allow_revoked_session
        else get_valid_feedgo_session(
            db,
            sid=sid,
            usuario_id=usuario_id,
            contract_version=version,
        )
    )
    if (
        issued_at != _utc_epoch_seconds(session.issued_at)
        or expires_at != _utc_epoch_seconds(session.expires_at)
    ):
        raise ValueError("session timestamp mismatch")
    return usuario_id, sid
