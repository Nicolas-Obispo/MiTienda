"""Owner de negocio para login/signup Google sin auto-link por email."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy.orm import Session

from app.modules.users.models.identity_models import ExternalIdentity
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.documentos_aceptacion_services import (
    crear_evidencias_aceptacion_registro,
    digest_documentos_obligatorios_registro,
)
from app.modules.users.services.email_normalization import (
    InvalidEmailError,
    canonicalize_email,
)
from app.modules.users.services.feedgo_session_services import GOOGLE, create_feedgo_session
from app.modules.users.services.google_oidc_services import GoogleOidcIdentity
from app.modules.users.services.oauth_authorization_transaction_services import (
    ClaimedOAuthAuthorizationTransaction,
    OAUTH_PURPOSE_LOGIN,
    OAUTH_PURPOSE_SIGNUP,
)
from app.modules.users.services.oauth_session_delivery_services import (
    AUTHENTICATION_UNAVAILABLE,
    SESSION_READY,
    OAuthSessionDeliveryMaterial,
    create_oauth_session_delivery,
)


@dataclass(frozen=True)
class GoogleIdentityProcessingResult:
    delivery: OAuthSessionDeliveryMaterial
    authenticated: bool


class GoogleIdentityError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(microsecond=0)


def _unavailable(
    db: Session,
    *,
    claim: ClaimedOAuthAuthorizationTransaction,
    result_ttl: timedelta,
    clock: Callable[[], datetime],
) -> GoogleIdentityProcessingResult:
    return GoogleIdentityProcessingResult(
        delivery=create_oauth_session_delivery(
            db,
            transaction_id=claim.transaction_id,
            outcome=AUTHENTICATION_UNAVAILABLE,
            return_to=claim.return_to,
            ttl=result_ttl,
            clock=clock,
        ),
        authenticated=False,
    )


def _find_usuario_by_canonical_email(
    db: Session,
    *,
    canonical_email: str,
) -> Usuario | None:
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email_canonical == canonical_email)
        .with_for_update()
        .one_or_none()
    )
    if usuario is not None:
        return usuario
    legacy_candidates = (
        db.query(Usuario)
        .filter(Usuario.email_canonical.is_(None))
        .with_for_update()
        .all()
    )
    for candidate in legacy_candidates:
        try:
            if canonicalize_email(candidate.email) == canonical_email:
                return candidate
        except InvalidEmailError:
            continue
    return None


def google_signup_collision_exists(
    db: Session,
    *,
    identity: GoogleOidcIdentity,
) -> bool:
    """Clasifica sólo constraints esperables; otros IntegrityError se propagan."""

    subject_exists = (
        db.query(ExternalIdentity.id)
        .filter(
            ExternalIdentity.provider == GOOGLE,
            ExternalIdentity.provider_subject == identity.subject,
        )
        .first()
        is not None
    )
    if subject_exists:
        return True
    try:
        canonical_email = canonicalize_email(identity.email)
    except InvalidEmailError:
        return False
    return _find_usuario_by_canonical_email(
        db,
        canonical_email=canonical_email,
    ) is not None


def process_google_identity(
    db: Session,
    *,
    claim: ClaimedOAuthAuthorizationTransaction,
    identity: GoogleOidcIdentity,
    session_ttl: timedelta,
    result_ttl: timedelta,
    clock: Callable[[], datetime] = utc_now,
) -> GoogleIdentityProcessingResult:
    """Aplica purpose sin usar email como identidad estable ni hacer commit."""

    now = _naive_utc(clock())
    external_identity = (
        db.query(ExternalIdentity)
        .filter(
            ExternalIdentity.provider == GOOGLE,
            ExternalIdentity.provider_subject == identity.subject,
        )
        .with_for_update()
        .one_or_none()
    )

    if claim.purpose == OAUTH_PURPOSE_LOGIN:
        if external_identity is None:
            return _unavailable(db, claim=claim, result_ttl=result_ttl, clock=clock)
        usuario = db.get(Usuario, external_identity.usuario_id)
        if usuario is None:
            raise GoogleIdentityError("google_identity_inconsistent")
    elif claim.purpose == OAUTH_PURPOSE_SIGNUP:
        if (
            claim.legal_document_set_digest is None
            or claim.legal_accepted_at is None
            or claim.legal_document_set_digest
            != digest_documentos_obligatorios_registro()
        ):
            raise GoogleIdentityError("google_signup_legal_acceptance_invalid")
        if external_identity is not None:
            return _unavailable(db, claim=claim, result_ttl=result_ttl, clock=clock)
        try:
            canonical_email = canonicalize_email(identity.email)
        except InvalidEmailError as exc:
            raise GoogleIdentityError("google_oidc_email_invalid") from exc
        email_owner = _find_usuario_by_canonical_email(
            db,
            canonical_email=canonical_email,
        )
        if email_owner is not None:
            return _unavailable(db, claim=claim, result_ttl=result_ttl, clock=clock)
        usuario = Usuario(
            email=identity.email,
            email_canonical=canonical_email,
            hashed_password=None,
            email_verified_at=now,
            email_verification_source="google_oidc",
        )
        db.add(usuario)
        db.flush()
        crear_evidencias_aceptacion_registro(
            db,
            usuario,
            aceptado_en=claim.legal_accepted_at or now,
        )
        external_identity = ExternalIdentity(
            usuario_id=usuario.id,
            provider=GOOGLE,
            provider_subject=identity.subject,
            provider_email_snapshot=canonical_email,
            provider_email_verified_snapshot=True,
            linked_at=now,
            last_used_at=now,
        )
        db.add(external_identity)
        db.flush()
    else:
        raise GoogleIdentityError("google_oauth_purpose_invalid")

    try:
        email_snapshot = canonicalize_email(identity.email)
    except InvalidEmailError as exc:
        raise GoogleIdentityError("google_oidc_email_invalid") from exc
    external_identity.provider_email_snapshot = email_snapshot
    external_identity.provider_email_verified_snapshot = True
    external_identity.last_used_at = now
    feedgo_session = create_feedgo_session(
        db,
        usuario_id=usuario.id,
        authentication_method=GOOGLE,
        external_identity_id=external_identity.id,
        ttl=session_ttl,
        clock=clock,
    )
    delivery = create_oauth_session_delivery(
        db,
        transaction_id=claim.transaction_id,
        outcome=SESSION_READY,
        usuario_id=usuario.id,
        feedgo_session_id=feedgo_session.id,
        return_to=claim.return_to,
        ttl=result_ttl,
        clock=clock,
    )
    return GoogleIdentityProcessingResult(delivery=delivery, authenticated=True)
