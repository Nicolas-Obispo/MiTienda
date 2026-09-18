"""Owner backend de metodos de autenticacion y reautenticacion reciente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy.orm import Session

from app.core.security import hash_password, password_hash_is_usable
from app.modules.users.models.identity_models import (
    ExternalIdentity,
    FeedGoSession,
    PasswordCredential,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.email_normalization import (
    InvalidEmailError,
    canonicalize_email,
)
from app.modules.users.services.feedgo_session_services import (
    GOOGLE,
    FeedGoSessionInvalidError,
    get_valid_feedgo_session,
)
from app.modules.users.services.google_oidc_services import GoogleOidcIdentity
from app.modules.users.services.oauth_authorization_transaction_services import (
    ClaimedOAuthAuthorizationTransaction,
    OAUTH_PURPOSE_LINK,
)
from app.modules.users.services.password_policy import validate_new_password


RECENT_REAUTH_WINDOW = timedelta(seconds=600)


class AuthenticationMethodError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class AuthenticationMethodsStatus:
    has_password: bool
    google_linked: bool
    usable_methods: tuple[str, ...]
    can_unlink_google: bool


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _password_credential_is_usable(credential: PasswordCredential | None) -> bool:
    return bool(
        credential is not None
        and credential.hash_version == "bcrypt"
        and password_hash_is_usable(credential.password_hash)
    )


def derive_authentication_methods(
    db: Session,
    *,
    usuario_id: int,
) -> AuthenticationMethodsStatus:
    """Deriva metodos reales; nunca usa el hash legacy como autoridad."""

    credential = db.get(PasswordCredential, usuario_id)
    google_identity = (
        db.query(ExternalIdentity.id)
        .filter(
            ExternalIdentity.usuario_id == usuario_id,
            ExternalIdentity.provider == GOOGLE,
        )
        .first()
    )
    has_password = _password_credential_is_usable(credential)
    google_linked = google_identity is not None
    methods = tuple(
        method
        for method, available in (
            ("password", has_password),
            (GOOGLE, google_linked),
        )
        if available
    )
    return AuthenticationMethodsStatus(
        has_password=has_password,
        google_linked=google_linked,
        usable_methods=methods,
        can_unlink_google=google_linked and has_password,
    )


def require_recent_reauthentication(
    db: Session,
    *,
    usuario_id: int,
    feedgo_session_id: str | None,
    clock: Callable[[], datetime] = utc_now,
) -> FeedGoSession:
    """Exige una sesion FeedGo real emitida hace como maximo 600 segundos."""

    if not feedgo_session_id:
        raise AuthenticationMethodError("recent_reauthentication_required")
    usuario = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id)
        .with_for_update()
        .one_or_none()
    )
    if usuario is None:
        raise AuthenticationMethodError("authentication_method_operation_unavailable")
    try:
        session = get_valid_feedgo_session(
            db,
            sid=feedgo_session_id,
            usuario_id=usuario_id,
            clock=clock,
            for_update=True,
        )
    except FeedGoSessionInvalidError as exc:
        raise AuthenticationMethodError("recent_reauthentication_required") from exc
    age = _naive_utc(clock()) - session.issued_at
    if age < timedelta(0) or age > RECENT_REAUTH_WINDOW:
        raise AuthenticationMethodError("recent_reauthentication_required")
    return session


def ensure_google_link_available(
    db: Session,
    *,
    usuario_id: int,
) -> None:
    linked = (
        db.query(ExternalIdentity.id)
        .filter(
            ExternalIdentity.usuario_id == usuario_id,
            ExternalIdentity.provider == GOOGLE,
        )
        .first()
    )
    if linked is not None:
        raise AuthenticationMethodError("authentication_method_already_exists")


def link_google_identity(
    db: Session,
    *,
    claim: ClaimedOAuthAuthorizationTransaction,
    identity: GoogleOidcIdentity,
    clock: Callable[[], datetime] = utc_now,
) -> ExternalIdentity:
    """Vincula por subject estable bajo sesion reciente; no cambia el email."""

    if (
        claim.purpose != OAUTH_PURPOSE_LINK
        or claim.usuario_id is None
        or claim.feedgo_session_id is None
    ):
        raise AuthenticationMethodError("authentication_method_operation_unavailable")
    require_recent_reauthentication(
        db,
        usuario_id=claim.usuario_id,
        feedgo_session_id=claim.feedgo_session_id,
        clock=clock,
    )
    subject_owner = (
        db.query(ExternalIdentity)
        .filter(
            ExternalIdentity.provider == GOOGLE,
            ExternalIdentity.provider_subject == identity.subject,
        )
        .with_for_update()
        .one_or_none()
    )
    existing_google = (
        db.query(ExternalIdentity)
        .filter(
            ExternalIdentity.usuario_id == claim.usuario_id,
            ExternalIdentity.provider == GOOGLE,
        )
        .with_for_update()
        .one_or_none()
    )
    if subject_owner is not None or existing_google is not None:
        raise AuthenticationMethodError("google_link_unavailable")
    try:
        email_snapshot = canonicalize_email(identity.email)
    except InvalidEmailError as exc:
        raise AuthenticationMethodError("google_link_unavailable") from exc
    now = _naive_utc(clock()).replace(microsecond=0)
    linked = ExternalIdentity(
        usuario_id=claim.usuario_id,
        provider=GOOGLE,
        provider_subject=identity.subject,
        provider_email_snapshot=email_snapshot,
        provider_email_verified_snapshot=True,
        linked_at=now,
        last_used_at=now,
    )
    db.add(linked)
    db.flush()
    return linked


def google_link_collision_exists(
    db: Session,
    *,
    usuario_id: int,
    provider_subject: str,
) -> bool:
    return (
        db.query(ExternalIdentity.id)
        .filter(
            ExternalIdentity.provider == GOOGLE,
            ExternalIdentity.provider_subject == provider_subject,
        )
        .first()
        is not None
        or db.query(ExternalIdentity.id)
        .filter(
            ExternalIdentity.usuario_id == usuario_id,
            ExternalIdentity.provider == GOOGLE,
        )
        .first()
        is not None
    )


def unlink_google_identity(
    db: Session,
    *,
    usuario_id: int,
    feedgo_session_id: str | None,
    clock: Callable[[], datetime] = utc_now,
) -> int:
    """Quita Google si password sigue utilizable y revoca sus sesiones."""

    require_recent_reauthentication(
        db,
        usuario_id=usuario_id,
        feedgo_session_id=feedgo_session_id,
        clock=clock,
    )
    credential = (
        db.query(PasswordCredential)
        .filter(PasswordCredential.usuario_id == usuario_id)
        .with_for_update()
        .one_or_none()
    )
    identity = (
        db.query(ExternalIdentity)
        .filter(
            ExternalIdentity.usuario_id == usuario_id,
            ExternalIdentity.provider == GOOGLE,
        )
        .with_for_update()
        .one_or_none()
    )
    if identity is None:
        raise AuthenticationMethodError("authentication_method_operation_unavailable")
    if not _password_credential_is_usable(credential):
        raise AuthenticationMethodError("cannot_remove_last_authentication_method")

    now = _naive_utc(clock()).replace(microsecond=0)
    revoked = (
        db.query(FeedGoSession)
        .filter(
            FeedGoSession.usuario_id == usuario_id,
            FeedGoSession.authentication_method == GOOGLE,
            FeedGoSession.external_identity_id == identity.id,
            FeedGoSession.revoked_at.is_(None),
            FeedGoSession.expires_at > now,
        )
        .update({FeedGoSession.revoked_at: now}, synchronize_session="fetch")
    )
    db.delete(identity)
    db.flush()
    return int(revoked)


def add_password_credential(
    db: Session,
    *,
    usuario_id: int,
    feedgo_session_id: str | None,
    new_password: str,
    clock: Callable[[], datetime] = utc_now,
) -> PasswordCredential:
    """Agrega password real con la politica unica y dual-write legacy."""

    validate_new_password(new_password)
    require_recent_reauthentication(
        db,
        usuario_id=usuario_id,
        feedgo_session_id=feedgo_session_id,
        clock=clock,
    )
    existing = (
        db.query(PasswordCredential)
        .filter(PasswordCredential.usuario_id == usuario_id)
        .with_for_update()
        .one_or_none()
    )
    if existing is not None:
        raise AuthenticationMethodError("authentication_method_already_exists")
    password_hash = hash_password(new_password)
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise AuthenticationMethodError("authentication_method_operation_unavailable")
    credential = PasswordCredential(
        usuario_id=usuario_id,
        password_hash=password_hash,
        hash_version="bcrypt",
    )
    db.add(credential)
    usuario.hashed_password = password_hash
    db.flush()
    return credential
