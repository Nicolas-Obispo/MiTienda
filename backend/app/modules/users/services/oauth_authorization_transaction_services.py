"""Owner de transacciones OAuth/OIDC one-use de FeedGo.

No conoce endpoints ni SDKs de providers. Prepara y protege la correlacion
persistente que el futuro callback backend necesitara para Google.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import secrets
from typing import Callable, Literal
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from sqlalchemy.orm import Session

from app.modules.users.models.identity_models import OAuthAuthorizationTransaction
from app.modules.users.services.feedgo_session_services import (
    FeedGoSessionInvalidError,
    get_valid_feedgo_session,
)


OAUTH_PURPOSE_SIGNUP = "signup"
OAUTH_PURPOSE_LOGIN = "login"
OAUTH_PURPOSE_LINK = "link"
OAUTH_PURPOSES = frozenset((OAUTH_PURPOSE_SIGNUP, OAUTH_PURPOSE_LOGIN, OAUTH_PURPOSE_LINK))
OAUTH_TRANSACTION_TTL = timedelta(minutes=10)


class OAuthAuthorizationTransactionError(RuntimeError):
    """Error de contrato seguro para el flujo OAuth/OIDC."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class OAuthAuthorizationMaterial:
    """Material efimero entregado solo al owner que inicia OAuth."""

    transaction_id: str
    state: str
    nonce: str
    pkce_challenge: str
    expires_at: datetime


@dataclass(frozen=True)
class ClaimedOAuthAuthorizationTransaction:
    """Material minimo reclamado por el callback; no sale de backend."""

    transaction_id: str
    purpose: Literal["signup", "login", "link"]
    nonce_digest: str
    pkce_verifier: str
    return_to: str | None
    legal_document_set_digest: str | None
    legal_accepted_at: datetime | None
    usuario_id: int | None = None
    feedgo_session_id: str | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(microsecond=0)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _token() -> str:
    return secrets.token_urlsafe(32)


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _fully_unquote(value: str) -> str:
    decoded_value = value
    for _ in range(3):
        decoded = unquote(decoded_value)
        if decoded == decoded_value:
            break
        decoded_value = decoded
    return decoded_value


def _safe_internal_return_to(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.startswith("/") or value.startswith("//"):
        raise OAuthAuthorizationTransactionError("invalid_return_to")
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        raise OAuthAuthorizationTransactionError("invalid_return_to")
    decoded_path = _fully_unquote(parsed.path)
    if (
        not decoded_path.startswith("/")
        or decoded_path.startswith("//")
        or "\\" in decoded_path
        or any(ord(character) < 32 for character in decoded_path)
    ):
        raise OAuthAuthorizationTransactionError("invalid_return_to")
    safe_query = [
        (key, item)
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if _fully_unquote(key).lower()
        not in {
            "token",
            "code",
            "state",
            "nonce",
            "email",
            "telefono",
            "phone",
            "fecha_nacimiento",
            "dob",
        }
    ]
    return urlunsplit(("", "", parsed.path, urlencode(safe_query), ""))


def _validate_correlation(
    db: Session,
    *,
    purpose: str,
    usuario_id: int | None,
    feedgo_session_id: str | None,
    clock: Callable[[], datetime],
) -> None:
    if purpose not in OAUTH_PURPOSES:
        raise OAuthAuthorizationTransactionError("unsupported_purpose")
    is_link = purpose == OAUTH_PURPOSE_LINK
    if is_link != (usuario_id is not None and feedgo_session_id is not None):
        raise OAuthAuthorizationTransactionError("invalid_correlation")
    if is_link:
        try:
            get_valid_feedgo_session(
                db,
                sid=feedgo_session_id,
                usuario_id=usuario_id,
                clock=clock,
                for_update=True,
            )
        except FeedGoSessionInvalidError as exc:
            raise OAuthAuthorizationTransactionError("invalid_correlation") from exc


def create_oauth_authorization_transaction(
    db: Session,
    *,
    provider: str,
    purpose: Literal["signup", "login", "link"],
    usuario_id: int | None = None,
    feedgo_session_id: str | None = None,
    return_to: str | None = None,
    legal_document_set_digest: str | None = None,
    legal_accepted_at: datetime | None = None,
    ttl: timedelta = OAUTH_TRANSACTION_TTL,
    clock: Callable[[], datetime] = utc_now,
) -> OAuthAuthorizationMaterial:
    """Crea y hace flush; la unidad de trabajo externa conserva el commit."""

    if not isinstance(provider, str) or not provider.strip() or len(provider) > 32:
        raise OAuthAuthorizationTransactionError("invalid_provider")
    if ttl <= timedelta(0) or ttl > OAUTH_TRANSACTION_TTL:
        raise OAuthAuthorizationTransactionError("invalid_ttl")
    _validate_correlation(
        db,
        purpose=purpose,
        usuario_id=usuario_id,
        feedgo_session_id=feedgo_session_id,
        clock=clock,
    )
    legal_pair_present = (
        legal_document_set_digest is not None and legal_accepted_at is not None
    )
    if (legal_document_set_digest is None) != (legal_accepted_at is None):
        raise OAuthAuthorizationTransactionError("invalid_legal_acceptance")
    if legal_pair_present and (
        purpose != OAUTH_PURPOSE_SIGNUP
        or len(legal_document_set_digest or "") != 64
    ):
        raise OAuthAuthorizationTransactionError("invalid_legal_acceptance")
    now = _naive_utc(clock())
    state = _token()
    nonce = _token()
    verifier = _token()
    transaction = OAuthAuthorizationTransaction(
        id=_token(),
        provider=provider.strip().lower(),
        purpose=purpose,
        state_digest=_digest(state),
        nonce_digest=_digest(nonce),
        pkce_verifier=verifier,
        pkce_challenge=_pkce_challenge(verifier),
        usuario_id=usuario_id,
        feedgo_session_id=feedgo_session_id,
        return_to=_safe_internal_return_to(return_to),
        legal_document_set_digest=legal_document_set_digest,
        legal_accepted_at=(
            _naive_utc(legal_accepted_at) if legal_accepted_at is not None else None
        ),
        created_at=now,
        expires_at=now + ttl,
    )
    db.add(transaction)
    db.flush()
    return OAuthAuthorizationMaterial(
        transaction_id=transaction.id,
        state=state,
        nonce=nonce,
        pkce_challenge=transaction.pkce_challenge,
        expires_at=transaction.expires_at,
    )


def claim_oauth_authorization_transaction_by_state(
    db: Session,
    *,
    state: str,
    provider: str,
    allowed_purposes: frozenset[str],
    clock: Callable[[], datetime] = utc_now,
) -> ClaimedOAuthAuthorizationTransaction:
    """Reclama one-use por state antes del exchange y elimina el verifier."""

    if not state or not allowed_purposes:
        raise OAuthAuthorizationTransactionError("invalid_transaction")
    state_digest = _digest(state)
    transaction = (
        db.query(OAuthAuthorizationTransaction)
        .filter(OAuthAuthorizationTransaction.state_digest == state_digest)
        .with_for_update()
        .one_or_none()
    )
    now = _naive_utc(clock())
    if transaction is None:
        raise OAuthAuthorizationTransactionError("invalid_transaction")
    if transaction.expires_at <= now:
        if transaction.consumed_at is None and transaction.invalidated_at is None:
            transaction.invalidated_at = now
            transaction.invalidation_reason = "expired"
            transaction.pkce_verifier = None
        raise OAuthAuthorizationTransactionError("invalid_transaction")
    if (
        transaction.consumed_at is not None
        or transaction.invalidated_at is not None
        or transaction.pkce_verifier is None
        or not hmac.compare_digest(transaction.state_digest, state_digest)
        or transaction.provider != provider.strip().lower()
        or transaction.purpose not in allowed_purposes
    ):
        raise OAuthAuthorizationTransactionError("invalid_transaction")

    _validate_correlation(
        db,
        purpose=transaction.purpose,
        usuario_id=transaction.usuario_id,
        feedgo_session_id=transaction.feedgo_session_id,
        clock=clock,
    )

    verifier = transaction.pkce_verifier
    claimed = ClaimedOAuthAuthorizationTransaction(
        transaction_id=transaction.id,
        purpose=transaction.purpose,
        nonce_digest=transaction.nonce_digest,
        pkce_verifier=verifier,
        return_to=transaction.return_to,
        legal_document_set_digest=transaction.legal_document_set_digest,
        legal_accepted_at=transaction.legal_accepted_at,
        usuario_id=transaction.usuario_id,
        feedgo_session_id=transaction.feedgo_session_id,
    )
    transaction.consumed_at = now
    transaction.pkce_verifier = None
    return claimed


def validate_and_consume_oauth_authorization_transaction(
    db: Session,
    *,
    transaction_id: str,
    state: str,
    nonce: str,
    provider: str,
    purpose: Literal["signup", "login", "link"],
    usuario_id: int | None = None,
    feedgo_session_id: str | None = None,
    clock: Callable[[], datetime] = utc_now,
) -> OAuthAuthorizationTransaction:
    """Valida y consume atomically una transaccion, sin hacer commit."""

    _validate_correlation(
        db,
        purpose=purpose,
        usuario_id=usuario_id,
        feedgo_session_id=feedgo_session_id,
        clock=clock,
    )
    transaction = (
        db.query(OAuthAuthorizationTransaction)
        .filter(OAuthAuthorizationTransaction.id == transaction_id)
        .with_for_update()
        .one_or_none()
    )
    if transaction is None:
        raise OAuthAuthorizationTransactionError("invalid_transaction")
    now = _naive_utc(clock())
    if transaction.consumed_at is not None or transaction.invalidated_at is not None:
        raise OAuthAuthorizationTransactionError("invalid_transaction")
    if transaction.expires_at <= now:
        transaction.invalidated_at = now
        transaction.invalidation_reason = "expired"
        transaction.pkce_verifier = None
        raise OAuthAuthorizationTransactionError("invalid_transaction")
    if (
        not hmac.compare_digest(transaction.state_digest, _digest(state))
        or not hmac.compare_digest(transaction.nonce_digest, _digest(nonce))
        or transaction.provider != provider.strip().lower()
        or transaction.purpose != purpose
        or transaction.usuario_id != usuario_id
        or transaction.feedgo_session_id != feedgo_session_id
    ):
        raise OAuthAuthorizationTransactionError("invalid_transaction")
    transaction.consumed_at = now
    transaction.pkce_verifier = None
    return transaction


def invalidate_oauth_authorization_transaction(
    db: Session,
    *,
    transaction_id: str,
    reason: Literal["superseded", "administrative", "session_invalid"],
    clock: Callable[[], datetime] = utc_now,
) -> bool:
    """Invalida una transaccion activa y elimina su verifier, sin commit."""

    transaction = (
        db.query(OAuthAuthorizationTransaction)
        .filter(OAuthAuthorizationTransaction.id == transaction_id)
        .with_for_update()
        .one_or_none()
    )
    if (
        transaction is None
        or transaction.consumed_at is not None
        or transaction.invalidated_at is not None
    ):
        return False
    transaction.invalidated_at = _naive_utc(clock())
    transaction.invalidation_reason = reason
    transaction.pkce_verifier = None
    return True


def invalidate_expired_oauth_authorization_transactions(
    db: Session,
    *,
    clock: Callable[[], datetime] = utc_now,
) -> int:
    """Marca expiradas sin commit; permite limpieza server-side independiente."""

    now = _naive_utc(clock())
    return (
        db.query(OAuthAuthorizationTransaction)
        .filter(
            OAuthAuthorizationTransaction.consumed_at.is_(None),
            OAuthAuthorizationTransaction.invalidated_at.is_(None),
            OAuthAuthorizationTransaction.expires_at <= now,
        )
        .update(
            {
                OAuthAuthorizationTransaction.invalidated_at: now,
                OAuthAuthorizationTransaction.invalidation_reason: "expired",
                OAuthAuthorizationTransaction.pkce_verifier: None,
            },
            synchronize_session="fetch",
        )
    )
