"""Motor persistente de limites para acciones de cuenta.

No conoce HTTP, mensajes visibles, correo, JWT ni sesiones. Los subjects se
pseudonimizan con un secreto dedicado y separación de dominio por bucket.
"""

from __future__ import annotations

import hashlib
import hmac
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.users.models.identity_models import AccountActionRateLimit

EMAIL_VERIFICATION = "email_verification"
PASSWORD_RESET = "password_reset"
CURRENT_PASSWORD = "current_password"
PHONE_VERIFICATION = "phone_verification"
GOOGLE_OAUTH = "google_oauth"
ALLOWED_ACTIONS = frozenset(
    {EMAIL_VERIFICATION, PASSWORD_RESET, CURRENT_PASSWORD, PHONE_VERIFICATION, GOOGLE_OAUTH}
)


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    reason: str | None = None
    retry_after_seconds: int | None = None


@dataclass(frozen=True)
class _Policy:
    scope: str
    duration: timedelta
    limit: int


def _utcnow() -> datetime:
    return datetime.utcnow()


def _secret_bytes(secret: str | None = None) -> bytes:
    value = secret if secret is not None else settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET
    if not value:
        raise RuntimeError("account_action_rate_limit_secret_missing")
    if value in {
        settings.SECRET_KEY,
        settings.RESEND_API_KEY,
        settings.IDENTITY_RESEND_API_KEY,
    }:
        raise RuntimeError("account_action_rate_limit_secret_reused")
    return value.encode("utf-8")


def subject_digest(*, action: str, scope: str, subject: str, secret: str | None = None) -> str:
    if action not in ALLOWED_ACTIONS:
        raise ValueError("account_action_unknown")
    payload = f"feedgo-rate-limit:v1:{action}:{scope}:{subject}".encode("utf-8")
    return hmac.new(_secret_bytes(secret), payload, hashlib.sha256).hexdigest()


def user_subject(usuario_id: int) -> str:
    if usuario_id <= 0:
        raise ValueError("account_action_subject_invalid")
    return f"user:{usuario_id}"


def canonical_destination_subject(email_canonical: str) -> str:
    if not email_canonical:
        raise ValueError("account_action_subject_invalid")
    return f"destination:{email_canonical}"


def client_subject(client_host: str) -> str:
    if not client_host:
        raise ValueError("account_action_client_missing")
    return f"client:{client_host}"


def _ensure_bucket(db: Session, *, action: str, digest: str, now: datetime) -> None:
    values = dict(
        action=action,
        subject_digest=digest,
        window_started_at=now,
        attempt_count=0,
        blocked_until=None,
    )
    dialect = db.get_bind().dialect.name
    table = AccountActionRateLimit.__table__
    if dialect == "mysql":
        statement = mysql_insert(table).values(**values)
        statement = statement.on_duplicate_key_update(id=table.c.id)
    elif dialect == "sqlite":
        statement = sqlite_insert(table).values(**values).on_conflict_do_nothing(
            index_elements=["action", "subject_digest"]
        )
    else:
        existing = db.execute(
            select(AccountActionRateLimit.id).where(
                AccountActionRateLimit.action == action,
                AccountActionRateLimit.subject_digest == digest,
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(AccountActionRateLimit(**values))
            db.flush()
        return
    db.execute(statement)


def _lock_buckets(
    db: Session,
    *,
    action: str,
    subject: str,
    policies: tuple[_Policy, ...],
    now: datetime,
    secret: str | None,
) -> list[tuple[_Policy, AccountActionRateLimit]]:
    keys = sorted(
        (subject_digest(action=action, scope=p.scope, subject=subject, secret=secret), p)
        for p in policies
    )
    for digest, _ in keys:
        _ensure_bucket(db, action=action, digest=digest, now=now)
    rows = []
    for digest, policy in keys:
        row = db.execute(
            select(AccountActionRateLimit)
            .where(
                AccountActionRateLimit.action == action,
                AccountActionRateLimit.subject_digest == digest,
            )
            .with_for_update()
        ).scalar_one()
        if now >= row.window_started_at + policy.duration:
            row.window_started_at = now
            row.attempt_count = 0
            row.blocked_until = None
        rows.append((policy, row))
    return rows


def _seconds(until: datetime, now: datetime) -> int:
    return max(1, int((until - now).total_seconds() + 0.999))


def _record(
    db: Session,
    *,
    action: str,
    subject: str,
    policies: tuple[_Policy, ...],
    cooldown: timedelta | None = None,
    now: datetime | None = None,
    secret: str | None = None,
) -> RateLimitDecision:
    current = now or _utcnow()
    rows = _lock_buckets(
        db, action=action, subject=subject, policies=policies,
        now=current, secret=secret,
    )
    for policy, row in rows:
        if row.blocked_until and current < row.blocked_until:
            return RateLimitDecision(False, "blocked", _seconds(row.blocked_until, current))
        if row.attempt_count >= policy.limit:
            until = row.window_started_at + policy.duration
            row.blocked_until = until
            db.flush()
            return RateLimitDecision(False, "limit", _seconds(until, current))
    for _, row in rows:
        row.attempt_count += 1
    if cooldown:
        # El primer bucket es siempre el horario por orden de definición lógica.
        hourly = next(row for policy, row in rows if policy.scope == "hour")
        hourly.blocked_until = current + cooldown
    db.flush()
    return RateLimitDecision(True)


def record_email_verification(
    db: Session, *, usuario_id: int, now: datetime | None = None,
    secret: str | None = None,
) -> RateLimitDecision:
    return _record(
        db, action=EMAIL_VERIFICATION, subject=user_subject(usuario_id),
        policies=(
            _Policy("hour", timedelta(hours=1), 5),
            _Policy("day", timedelta(days=1), 10),
        ),
        cooldown=timedelta(seconds=60), now=now, secret=secret,
    )


def record_password_reset(
    db: Session, *, email_canonical: str, now: datetime | None = None,
    secret: str | None = None,
) -> RateLimitDecision:
    return _record(
        db, action=PASSWORD_RESET,
        subject=canonical_destination_subject(email_canonical),
        policies=(_Policy("hour", timedelta(hours=1), 5),),
        now=now, secret=secret,
    )


def record_phone_verification(
    db: Session, *, usuario_id: int, now: datetime | None = None,
    secret: str | None = None,
) -> RateLimitDecision:
    return _record(
        db, action=PHONE_VERIFICATION, subject=user_subject(usuario_id),
        policies=(
            _Policy("hour", timedelta(hours=1), 5),
            _Policy("day", timedelta(days=1), 10),
        ),
        cooldown=timedelta(seconds=60), now=now, secret=secret,
    )


def record_google_oauth_authorization(
    db: Session,
    *,
    client_host: str,
    limit_per_hour: int,
    now: datetime | None = None,
    secret: str | None = None,
) -> RateLimitDecision:
    if limit_per_hour <= 0:
        raise ValueError("google_oauth_rate_limit_invalid")
    return _record(
        db,
        action=GOOGLE_OAUTH,
        subject=client_subject(client_host),
        policies=(_Policy("hour", timedelta(hours=1), limit_per_hour),),
        now=now,
        secret=secret,
    )


def record_current_password_failure(
    db: Session, *, usuario_id: int, now: datetime | None = None,
    secret: str | None = None,
) -> RateLimitDecision:
    return _record(
        db, action=CURRENT_PASSWORD, subject=user_subject(usuario_id),
        policies=(_Policy("15m", timedelta(minutes=15), 5),),
        now=now, secret=secret,
    )


def check_current_password_allowed(
    db: Session, *, usuario_id: int, now: datetime | None = None,
    secret: str | None = None,
) -> RateLimitDecision:
    """Consulta el bloqueo persistente sin registrar un nuevo fallo."""

    current = now or _utcnow()
    policy = _Policy("15m", timedelta(minutes=15), 5)
    row = _lock_buckets(
        db,
        action=CURRENT_PASSWORD,
        subject=user_subject(usuario_id),
        policies=(policy,),
        now=current,
        secret=secret,
    )[0][1]
    if row.blocked_until and current < row.blocked_until:
        return RateLimitDecision(False, "blocked", _seconds(row.blocked_until, current))
    if row.attempt_count >= policy.limit:
        until = row.window_started_at + policy.duration
        row.blocked_until = until
        db.flush()
        return RateLimitDecision(False, "limit", _seconds(until, current))
    return RateLimitDecision(True)


def clear_current_password_failures(
    db: Session, *, usuario_id: int, now: datetime | None = None,
    secret: str | None = None,
) -> None:
    """Reinicia el bucket tras una comprobacion correcta de la password actual."""

    current = now or _utcnow()
    rows = _lock_buckets(
        db,
        action=CURRENT_PASSWORD,
        subject=user_subject(usuario_id),
        policies=(_Policy("15m", timedelta(minutes=15), 5),),
        now=current,
        secret=secret,
    )
    row = rows[0][1]
    row.window_started_at = current
    row.attempt_count = 0
    row.blocked_until = None
    db.flush()


class LocalPublicRateLimiter:
    """Defensa secundaria por host resuelto; nunca interpreta proxy headers."""

    def __init__(self, *, secret: str | None = None, clock: Callable[[], datetime] = _utcnow):
        self._secret = secret
        self._clock = clock
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[datetime, int]] = {}

    def record_password_reset(self, *, client_host: str) -> RateLimitDecision:
        if not client_host:
            raise ValueError("account_action_client_missing")
        now = self._clock()
        digest = subject_digest(
            action=PASSWORD_RESET, scope="client-hour", subject=client_host,
            secret=self._secret,
        )
        with self._lock:
            started, count = self._buckets.get(digest, (now, 0))
            if now >= started + timedelta(hours=1):
                started, count = now, 0
            if count >= 20:
                self._buckets[digest] = (started, count)
                return RateLimitDecision(False, "local_limit", _seconds(started + timedelta(hours=1), now))
            self._buckets[digest] = (started, count + 1)
            return RateLimitDecision(True)
