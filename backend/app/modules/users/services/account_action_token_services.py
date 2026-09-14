"""Motor backend de tokens de accion de cuenta de ETAPA 99.3-B.

Este modulo es el unico owner de generacion, digest, expiracion, emision,
invalidacion, consumo y estado derivado. No conoce HTTP, frontend ni correo.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Callable
import uuid

from sqlalchemy.orm import Session

from app.modules.users.models.identity_models import AccountActionToken
from app.modules.users.models.usuarios_models import Usuario


EMAIL_VERIFICATION = "email_verification"
PASSWORD_RESET = "password_reset"
ACCOUNT_ACTION_PURPOSES = frozenset({EMAIL_VERIFICATION, PASSWORD_RESET})

SUPERSEDED = "superseded"
PASSWORD_CHANGED = "password_changed"
ADMINISTRATIVE = "administrative"
ACCOUNT_ACTION_INVALIDATION_REASONS = frozenset(
    {SUPERSEDED, PASSWORD_CHANGED, ADMINISTRATIVE}
)

TOKEN_ENTROPY_BYTES = 32
TOKEN_TTLS = {
    EMAIL_VERIFICATION: timedelta(hours=24),
    PASSWORD_RESET: timedelta(minutes=30),
}

Clock = Callable[[], datetime]
RandomBytes = Callable[[int], bytes]
IssuanceIdFactory = Callable[[], str]


def _new_issuance_id() -> str:
    return uuid.uuid4().hex


class AccountActionTokenError(ValueError):
    """Error seguro del motor; nunca incorpora secretos ni datos personales."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class AccountActionPurposeInvalidError(AccountActionTokenError):
    def __init__(self):
        super().__init__("account_action_purpose_invalid")


class AccountActionInvalidationReasonError(AccountActionTokenError):
    def __init__(self):
        super().__init__("account_action_invalidation_reason_invalid")


class AccountActionUserNotFoundError(AccountActionTokenError):
    def __init__(self):
        super().__init__("account_action_user_not_found")


class AccountActionTokenInvalidError(AccountActionTokenError):
    def __init__(self):
        super().__init__("account_action_token_invalid")


@dataclass(frozen=True)
class IssuedAccountActionToken:
    """Resultado efimero: el caller debe mantener `secret` solo en memoria."""

    token_id: int
    secret: str
    issuance_id: str
    expires_at: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _now(clock: Clock) -> datetime:
    return _as_utc(clock())


def _validate_purpose(purpose: str) -> None:
    if purpose not in ACCOUNT_ACTION_PURPOSES:
        raise AccountActionPurposeInvalidError()


def _validate_invalidation_reason(reason: str) -> None:
    if reason not in ACCOUNT_ACTION_INVALIDATION_REASONS:
        raise AccountActionInvalidationReasonError()


def generate_token_secret(
    *,
    random_bytes: RandomBytes = secrets.token_bytes,
    entropy_bytes: int = TOKEN_ENTROPY_BYTES,
) -> str:
    """Genera Base64URL sin padding con un minimo real de 256 bits."""

    if entropy_bytes < TOKEN_ENTROPY_BYTES:
        raise ValueError("account_action_token_entropy_too_small")
    raw = random_bytes(entropy_bytes)
    if not isinstance(raw, bytes) or len(raw) != entropy_bytes:
        raise ValueError("account_action_token_random_source_invalid")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def digest_token_secret(secret: str) -> str:
    """Deriva el unico valor persistible del secreto."""

    if not isinstance(secret, str) or not secret:
        raise AccountActionTokenInvalidError()
    try:
        encoded = secret.encode("ascii")
    except UnicodeEncodeError:
        raise AccountActionTokenInvalidError() from None
    return hashlib.sha256(encoded).hexdigest()


def derive_token_state(
    token: AccountActionToken,
    *,
    now: datetime | None = None,
    clock: Clock = utc_now,
) -> str:
    """Calcula el estado sin persistirlo."""

    current = _as_utc(now) if now is not None else _now(clock)
    if token.consumed_at is not None:
        return "consumed"
    if token.invalidated_at is not None:
        return "invalidated"
    if _as_utc(token.expires_at) <= current:
        return "expired"
    return "active"


def issue_account_action_token(
    *,
    db: Session,
    usuario_id: int,
    purpose: str,
    clock: Clock = utc_now,
    random_bytes: RandomBytes = secrets.token_bytes,
    issuance_id_factory: IssuanceIdFactory = _new_issuance_id,
) -> IssuedAccountActionToken:
    """Emite atomicamente y reemplaza el token activo anterior del proposito."""

    _validate_purpose(purpose)
    current = _now(clock)
    expires_at = current + TOKEN_TTLS[purpose]
    secret = generate_token_secret(random_bytes=random_bytes)
    token_digest = digest_token_secret(secret)
    issuance_id = issuance_id_factory()
    if not isinstance(issuance_id, str) or not issuance_id:
        raise ValueError("account_action_issuance_id_invalid")

    try:
        usuario = (
            db.query(Usuario)
            .filter(Usuario.id == usuario_id)
            .with_for_update()
            .first()
        )
        if usuario is None:
            raise AccountActionUserNotFoundError()
        if not usuario.email_canonical:
            raise AccountActionTokenInvalidError()

        active_tokens = (
            db.query(AccountActionToken)
            .filter(
                AccountActionToken.usuario_id == usuario_id,
                AccountActionToken.purpose == purpose,
                AccountActionToken.consumed_at.is_(None),
                AccountActionToken.invalidated_at.is_(None),
                AccountActionToken.expires_at > current,
            )
            .with_for_update()
            .all()
        )
        for active_token in active_tokens:
            active_token.invalidated_at = current
            active_token.invalidation_reason = SUPERSEDED

        token = AccountActionToken(
            usuario_id=usuario_id,
            purpose=purpose,
            token_digest=token_digest,
            email_canonical_snapshot=usuario.email_canonical,
            created_at=current,
            expires_at=expires_at,
            issuance_id=issuance_id,
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return IssuedAccountActionToken(
            token_id=token.id,
            secret=secret,
            issuance_id=issuance_id,
            expires_at=_as_utc(token.expires_at),
        )
    except Exception:
        db.rollback()
        raise


def consume_account_action_token(
    *,
    db: Session,
    secret: str,
    purpose: str,
    clock: Clock = utc_now,
    commit: bool = True,
) -> AccountActionToken:
    """Consume una vez, serializando con emisiones mediante el lock de Usuario."""

    _validate_purpose(purpose)
    token_digest = digest_token_secret(secret)
    current = _now(clock)

    try:
        candidate = (
            db.query(AccountActionToken)
            .filter(AccountActionToken.token_digest == token_digest)
            .first()
        )
        if candidate is None:
            raise AccountActionTokenInvalidError()

        usuario = (
            db.query(Usuario)
            .filter(Usuario.id == candidate.usuario_id)
            .with_for_update()
            .first()
        )
        if usuario is None:
            raise AccountActionTokenInvalidError()

        token = (
            db.query(AccountActionToken)
            .filter(AccountActionToken.id == candidate.id)
            .with_for_update()
            .populate_existing()
            .first()
        )
        if (
            token is None
            or token.purpose != purpose
            or derive_token_state(token, now=current) != "active"
            or token.email_canonical_snapshot != usuario.email_canonical
        ):
            raise AccountActionTokenInvalidError()

        token.consumed_at = current
        if commit:
            db.commit()
            db.refresh(token)
        else:
            db.flush()
        return token
    except Exception:
        db.rollback()
        raise


def invalidate_account_action_tokens(
    *,
    db: Session,
    usuario_id: int,
    purpose: str,
    reason: str,
    clock: Clock = utc_now,
) -> int:
    """Invalida tokens activos por un motivo cerrado y devuelve su cantidad."""

    _validate_purpose(purpose)
    _validate_invalidation_reason(reason)
    current = _now(clock)
    try:
        usuario = (
            db.query(Usuario)
            .filter(Usuario.id == usuario_id)
            .with_for_update()
            .first()
        )
        if usuario is None:
            raise AccountActionUserNotFoundError()
        tokens = (
            db.query(AccountActionToken)
            .filter(
                AccountActionToken.usuario_id == usuario_id,
                AccountActionToken.purpose == purpose,
                AccountActionToken.consumed_at.is_(None),
                AccountActionToken.invalidated_at.is_(None),
                AccountActionToken.expires_at > current,
            )
            .with_for_update()
            .all()
        )
        for token in tokens:
            token.invalidated_at = current
            token.invalidation_reason = reason
        db.commit()
        return len(tokens)
    except Exception:
        db.rollback()
        raise
