"""Reautenticacion fuerte y rotacion de SID para operaciones sensibles."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy.orm import Session

from app.core.security import verificar_password
from app.modules.users.models.identity_models import ExternalIdentity, FeedGoSession, PasswordCredential
from app.modules.users.services.account_action_rate_limit_services import (
    check_current_password_allowed,
    clear_current_password_failures,
    record_current_password_failure,
)
from app.modules.users.services.authentication_method_services import (
    AuthenticationMethodError,
    _password_credential_is_usable,
)
from app.modules.users.services.feedgo_session_services import (
    GOOGLE,
    PASSWORD,
    FeedGoSessionInvalidError,
    create_feedgo_session,
    get_valid_feedgo_session,
)
from app.modules.users.services.google_oidc_services import GoogleOidcIdentity
from app.modules.users.services.oauth_authorization_transaction_services import (
    ClaimedOAuthAuthorizationTransaction,
    OAUTH_PURPOSE_REAUTH,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(microsecond=0)


def _current_session(
    db: Session, *, usuario_id: int, sid: str | None, clock: Callable[[], datetime]
) -> FeedGoSession:
    if not sid:
        raise AuthenticationMethodError("recent_reauthentication_required")
    try:
        return get_valid_feedgo_session(
            db, sid=sid, usuario_id=usuario_id, clock=clock, for_update=True
        )
    except FeedGoSessionInvalidError as exc:
        raise AuthenticationMethodError("recent_reauthentication_required") from exc


def _rotate_session(
    db: Session,
    *,
    current: FeedGoSession,
    authentication_method: str,
    external_identity_id: int | None,
    ttl: timedelta,
    clock: Callable[[], datetime],
) -> FeedGoSession:
    """Emite SID nuevo antes de invalidar el anterior, dentro de la misma UoW."""

    replacement = create_feedgo_session(
        db,
        usuario_id=current.usuario_id,
        authentication_method=authentication_method,
        external_identity_id=external_identity_id,
        ttl=ttl,
        clock=clock,
    )
    current.revoked_at = _naive_utc(clock())
    db.flush()
    return replacement


def reauthenticate_with_password(
    db: Session,
    *,
    usuario_id: int,
    feedgo_session_id: str | None,
    current_password: str,
    session_ttl: timedelta,
    clock: Callable[[], datetime] = utc_now,
) -> FeedGoSession:
    current = _current_session(db, usuario_id=usuario_id, sid=feedgo_session_id, clock=clock)
    credential = (
        db.query(PasswordCredential)
        .filter(PasswordCredential.usuario_id == usuario_id)
        .with_for_update()
        .one_or_none()
    )
    if not _password_credential_is_usable(credential):
        raise AuthenticationMethodError("authentication_method_operation_unavailable")
    allowed = check_current_password_allowed(db, usuario_id=usuario_id)
    if not allowed.allowed:
        raise AuthenticationMethodError("current_password_rate_limited")
    try:
        valid = verificar_password(current_password, credential.password_hash)
    except (TypeError, ValueError):
        valid = False
    if not valid:
        record_current_password_failure(db, usuario_id=usuario_id)
        raise AuthenticationMethodError("reauthentication_invalid")
    clear_current_password_failures(db, usuario_id=usuario_id)
    return _rotate_session(
        db,
        current=current,
        authentication_method=PASSWORD,
        external_identity_id=None,
        ttl=session_ttl,
        clock=clock,
    )


def reauthenticate_with_google(
    db: Session,
    *,
    claim: ClaimedOAuthAuthorizationTransaction,
    identity: GoogleOidcIdentity,
    session_ttl: timedelta,
    clock: Callable[[], datetime] = utc_now,
) -> FeedGoSession:
    if (
        claim.purpose != OAUTH_PURPOSE_REAUTH
        or claim.usuario_id is None
        or claim.feedgo_session_id is None
    ):
        raise AuthenticationMethodError("authentication_method_operation_unavailable")
    current = _current_session(
        db,
        usuario_id=claim.usuario_id,
        sid=claim.feedgo_session_id,
        clock=clock,
    )
    external_identity = (
        db.query(ExternalIdentity)
        .filter(
            ExternalIdentity.usuario_id == claim.usuario_id,
            ExternalIdentity.provider == GOOGLE,
            ExternalIdentity.provider_subject == identity.subject,
        )
        .with_for_update()
        .one_or_none()
    )
    if external_identity is None:
        raise AuthenticationMethodError("authentication_method_operation_unavailable")
    return _rotate_session(
        db,
        current=current,
        authentication_method=GOOGLE,
        external_identity_id=external_identity.id,
        ttl=session_ttl,
        clock=clock,
    )
