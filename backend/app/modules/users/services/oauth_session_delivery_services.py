"""Entrega one-use de una FeedGoSession luego de un callback OAuth valido."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Callable, Literal

from sqlalchemy.orm import Session

from app.modules.users.models.identity_models import (
    OAuthAuthorizationTransaction,
    OAuthSessionDeliveryHandle,
)
from app.modules.users.services.feedgo_session_services import (
    FeedGoSessionInvalidError,
    get_valid_feedgo_session,
)


SESSION_READY = "session_ready"
AUTHENTICATION_UNAVAILABLE = "authentication_unavailable"
RESULT_HANDLE_TTL = timedelta(minutes=2)


class OAuthSessionDeliveryError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class OAuthSessionDeliveryMaterial:
    handle: str
    expires_at: datetime


@dataclass(frozen=True)
class ConsumedOAuthSessionDelivery:
    outcome: Literal["session_ready", "authentication_unavailable"]
    usuario_id: int | None
    feedgo_session_id: str | None
    return_to: str | None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(microsecond=0)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_oauth_session_delivery(
    db: Session,
    *,
    transaction_id: str,
    outcome: Literal["session_ready", "authentication_unavailable"],
    usuario_id: int | None = None,
    feedgo_session_id: str | None = None,
    return_to: str | None = None,
    ttl: timedelta = RESULT_HANDLE_TTL,
    clock: Callable[[], datetime] = utc_now,
) -> OAuthSessionDeliveryMaterial:
    """Crea un handle CSPRNG; persiste solo su digest y nunca el JWT."""

    if ttl <= timedelta(0) or ttl > RESULT_HANDLE_TTL:
        raise OAuthSessionDeliveryError("invalid_result_ttl")
    ready = outcome == SESSION_READY
    if (
        outcome not in {SESSION_READY, AUTHENTICATION_UNAVAILABLE}
        or (ready and (usuario_id is None or feedgo_session_id is None))
        or (not ready and (usuario_id is not None or feedgo_session_id is not None))
    ):
        raise OAuthSessionDeliveryError("invalid_result_correlation")
    if ready:
        try:
            get_valid_feedgo_session(
                db,
                sid=feedgo_session_id or "",
                usuario_id=usuario_id,
                clock=clock,
            )
        except FeedGoSessionInvalidError as exc:
            raise OAuthSessionDeliveryError("invalid_result_correlation") from exc

    now = _naive_utc(clock())
    handle = secrets.token_urlsafe(32)
    row = OAuthSessionDeliveryHandle(
        id=secrets.token_urlsafe(32),
        handle_digest=_digest(handle),
        transaction_id=transaction_id,
        outcome=outcome,
        usuario_id=usuario_id,
        feedgo_session_id=feedgo_session_id,
        return_to=return_to,
        created_at=now,
        expires_at=now + ttl,
    )
    db.add(row)
    db.flush()
    return OAuthSessionDeliveryMaterial(handle=handle, expires_at=row.expires_at)


def consume_oauth_session_delivery(
    db: Session,
    *,
    handle: str,
    allowed_purposes: frozenset[str],
    clock: Callable[[], datetime] = utc_now,
) -> ConsumedOAuthSessionDelivery:
    """Consume atomicamente el resultado y valida de nuevo la FeedGoSession."""

    if not handle:
        raise OAuthSessionDeliveryError("invalid_result_handle")
    digest = _digest(handle)
    row = (
        db.query(OAuthSessionDeliveryHandle)
        .filter(OAuthSessionDeliveryHandle.handle_digest == digest)
        .with_for_update()
        .one_or_none()
    )
    now = _naive_utc(clock())
    if row is None:
        raise OAuthSessionDeliveryError("invalid_result_handle")
    if row.expires_at <= now:
        if row.consumed_at is None and row.invalidated_at is None:
            row.invalidated_at = now
            row.invalidation_reason = "expired"
        raise OAuthSessionDeliveryError("invalid_result_handle")
    if (
        row.consumed_at is not None
        or row.invalidated_at is not None
        or not hmac.compare_digest(row.handle_digest, digest)
    ):
        raise OAuthSessionDeliveryError("invalid_result_handle")
    if not allowed_purposes:
        raise OAuthSessionDeliveryError("invalid_result_handle")
    transaction = db.get(OAuthAuthorizationTransaction, row.transaction_id)
    if transaction is None or transaction.purpose not in allowed_purposes:
        raise OAuthSessionDeliveryError("invalid_result_handle")
    if row.outcome == SESSION_READY:
        try:
            get_valid_feedgo_session(
                db,
                sid=row.feedgo_session_id or "",
                usuario_id=row.usuario_id,
                clock=clock,
                for_update=True,
            )
        except FeedGoSessionInvalidError as exc:
            row.invalidated_at = now
            row.invalidation_reason = "administrative"
            raise OAuthSessionDeliveryError("invalid_result_handle") from exc

    row.consumed_at = now
    return ConsumedOAuthSessionDelivery(
        outcome=row.outcome,
        usuario_id=row.usuario_id,
        feedgo_session_id=row.feedgo_session_id,
        return_to=row.return_to,
    )
