"""Owner backend del ciclo de vida persistente de FeedGoSession.

No emite ni persiste JWT y no realiza commits: la transaccion pertenece al
flujo que crea, valida o revoca la sesion.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from typing import Callable

from sqlalchemy.orm import Session

from app.modules.users.models.identity_models import ExternalIdentity, FeedGoSession
from app.modules.users.models.usuarios_models import Usuario


PASSWORD = "password"
GOOGLE = "google"
SUPPORTED_AUTHENTICATION_METHODS = frozenset({PASSWORD, GOOGLE})
CURRENT_CONTRACT_VERSION = 1
DEFAULT_SESSION_TTL = timedelta(minutes=60)


class FeedGoSessionError(RuntimeError):
    """Base para errores internos del contrato de sesion."""


class FeedGoSessionInvalidError(FeedGoSessionError):
    """La sesion no existe o no satisface el contrato esperado."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_session_id() -> str:
    """Genera 256 bits CSPRNG en Base64URL sin padding."""

    return secrets.token_urlsafe(32)


def _naive(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _canonical_session_timestamp(value: datetime) -> datetime:
    """Normaliza el instante persistido al contrato UTC de DATETIME(0)."""

    return _naive(value).replace(microsecond=0)


def _validate_method_identity(
    db: Session,
    *,
    usuario_id: int,
    authentication_method: str,
    external_identity_id: int | None,
) -> None:
    if authentication_method not in SUPPORTED_AUTHENTICATION_METHODS:
        raise FeedGoSessionInvalidError("unsupported_authentication_method")
    if authentication_method == PASSWORD:
        if external_identity_id is not None:
            raise FeedGoSessionInvalidError("password_session_has_external_identity")
        return
    if external_identity_id is None:
        raise FeedGoSessionInvalidError("google_session_missing_external_identity")
    identity = db.get(ExternalIdentity, external_identity_id)
    if identity is None or identity.usuario_id != usuario_id or identity.provider != GOOGLE:
        raise FeedGoSessionInvalidError("external_identity_mismatch")


def create_feedgo_session(
    db: Session,
    *,
    usuario_id: int,
    authentication_method: str,
    external_identity_id: int | None = None,
    ttl: timedelta = DEFAULT_SESSION_TTL,
    contract_version: int = CURRENT_CONTRACT_VERSION,
    clock: Callable[[], datetime] = utc_now,
    sid_factory: Callable[[], str] = generate_session_id,
) -> FeedGoSession:
    """Crea y hace flush de una sesion sin apropiarse del commit."""

    if contract_version != CURRENT_CONTRACT_VERSION or ttl <= timedelta(0):
        raise FeedGoSessionInvalidError("invalid_session_contract")
    if db.get(Usuario, usuario_id) is None:
        raise FeedGoSessionInvalidError("user_not_found")
    _validate_method_identity(
        db,
        usuario_id=usuario_id,
        authentication_method=authentication_method,
        external_identity_id=external_identity_id,
    )
    now = _canonical_session_timestamp(clock())
    session = FeedGoSession(
        id=sid_factory(),
        usuario_id=usuario_id,
        authentication_method=authentication_method,
        external_identity_id=external_identity_id,
        issued_at=now,
        expires_at=now + ttl,
        contract_version=contract_version,
    )
    db.add(session)
    db.flush()
    return session


def get_valid_feedgo_session(
    db: Session,
    *,
    sid: str,
    usuario_id: int | None = None,
    contract_version: int = CURRENT_CONTRACT_VERSION,
    clock: Callable[[], datetime] = utc_now,
    for_update: bool = False,
) -> FeedGoSession:
    """Obtiene una sesion vigente; no transforma el resultado en autorizacion."""

    query = db.query(FeedGoSession).filter(FeedGoSession.id == sid)
    if for_update:
        query = query.with_for_update()
    session = query.first()
    now = _naive(clock())
    if (
        session is None
        or session.contract_version != contract_version
        or session.revoked_at is not None
        or session.expires_at <= now
        or (usuario_id is not None and session.usuario_id != usuario_id)
    ):
        raise FeedGoSessionInvalidError("invalid_session")
    _validate_method_identity(
        db,
        usuario_id=session.usuario_id,
        authentication_method=session.authentication_method,
        external_identity_id=session.external_identity_id,
    )
    return session


def get_feedgo_session_for_logout(
    db: Session,
    *,
    sid: str,
    usuario_id: int,
    contract_version: int = CURRENT_CONTRACT_VERSION,
    clock: Callable[[], datetime] = utc_now,
) -> FeedGoSession:
    """Valida identidad y contrato, permitiendo revocacion previa idempotente."""

    session = db.query(FeedGoSession).filter(FeedGoSession.id == sid).first()
    now = _naive(clock())
    if (
        session is None
        or session.usuario_id != usuario_id
        or session.contract_version != contract_version
        or session.expires_at <= now
    ):
        raise FeedGoSessionInvalidError("invalid_session")
    _validate_method_identity(
        db,
        usuario_id=session.usuario_id,
        authentication_method=session.authentication_method,
        external_identity_id=session.external_identity_id,
    )
    return session


def revoke_feedgo_session(
    db: Session,
    *,
    sid: str,
    usuario_id: int | None = None,
    clock: Callable[[], datetime] = utc_now,
) -> bool:
    """Revoca atomicamente una sesion activa; no realiza commit."""

    now = _naive(clock())
    query = db.query(FeedGoSession).filter(
        FeedGoSession.id == sid,
        FeedGoSession.revoked_at.is_(None),
        FeedGoSession.expires_at > now,
    )
    if usuario_id is not None:
        query = query.filter(FeedGoSession.usuario_id == usuario_id)
    return bool(query.update({FeedGoSession.revoked_at: now}, synchronize_session="fetch"))


def revoke_user_feedgo_sessions(
    db: Session,
    *,
    usuario_id: int,
    except_sid: str | None = None,
    clock: Callable[[], datetime] = utc_now,
) -> int:
    """Revoca sesiones activas del usuario, opcionalmente preservando una."""

    now = _naive(clock())
    query = db.query(FeedGoSession).filter(
        FeedGoSession.usuario_id == usuario_id,
        FeedGoSession.revoked_at.is_(None),
        FeedGoSession.expires_at > now,
    )
    if except_sid is not None:
        query = query.filter(FeedGoSession.id != except_sid)
    return query.update({FeedGoSession.revoked_at: now}, synchronize_session="fetch")
