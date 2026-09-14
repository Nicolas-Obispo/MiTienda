"""Reglas backend de verificacion de email y reenvio de enlaces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.communications.services.email_provider_factory import (
    build_identity_email_provider,
)
from app.modules.communications.services.identity_email_services import (
    IdentityEmailDeliveryError,
    deliver_identity_email,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_rate_limit_services import (
    record_email_verification,
)
from app.modules.users.services.account_action_token_services import (
    EMAIL_VERIFICATION,
    AccountActionTokenInvalidError,
    consume_account_action_token,
    issue_account_action_token,
)

EMAIL_LINK_SOURCE = "email_link"


class EmailVerificationError(RuntimeError):
    def __init__(self, code: str, *, retry_after_seconds: int | None = None):
        super().__init__(code)
        self.code = code
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class EmailVerificationDelivery:
    status: str
    retry_after_seconds: int | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _rate_limit_now(clock) -> datetime:
    value = clock()
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def confirm_email_verification(
    *, db: Session, secret: str, clock=utc_now
) -> Usuario:
    """Consume el enlace y actualiza Usuario dentro de una sola transaccion."""

    try:
        token = consume_account_action_token(
            db=db,
            secret=secret,
            purpose=EMAIL_VERIFICATION,
            clock=clock,
            commit=False,
        )
        usuario = db.get(Usuario, token.usuario_id)
        if usuario is None:
            raise AccountActionTokenInvalidError()
        if usuario.email_verified_at is None:
            usuario.email_verified_at = clock()
            usuario.email_verification_source = EMAIL_LINK_SOURCE
        db.commit()
        db.refresh(usuario)
        return usuario
    except AccountActionTokenInvalidError:
        db.rollback()
        raise EmailVerificationError("email_verification_link_invalid") from None
    except Exception:
        db.rollback()
        raise


def send_email_verification(
    *, db: Session, usuario: Usuario, clock=utc_now
) -> EmailVerificationDelivery:
    """Aplica limites, emite/commit y luego entrega el secreto en memoria."""

    if usuario.email_verified_at is not None:
        return EmailVerificationDelivery("already_verified")

    decision = record_email_verification(
        db,
        usuario_id=usuario.id,
        now=_rate_limit_now(clock),
    )
    if not decision.allowed:
        db.commit()
        raise EmailVerificationError(
            "email_verification_rate_limited",
            retry_after_seconds=decision.retry_after_seconds,
        )

    issued = issue_account_action_token(
        db=db,
        usuario_id=usuario.id,
        purpose=EMAIL_VERIFICATION,
        clock=clock,
    )
    try:
        deliver_identity_email(
            provider=build_identity_email_provider(),
            recipient=usuario.email,
            purpose=EMAIL_VERIFICATION,
            secret=issued.secret,
            issuance_id=issued.issuance_id,
        )
    except (IdentityEmailDeliveryError, ValueError, RuntimeError):
        raise EmailVerificationError("email_verification_delivery_failed") from None
    finally:
        issued = None
    return EmailVerificationDelivery("sent")


def send_registration_verification(
    *, db: Session, usuario: Usuario, clock=utc_now
) -> EmailVerificationDelivery:
    """Best-effort post-commit: una falla nunca elimina la cuenta creada."""

    try:
        return send_email_verification(db=db, usuario=usuario, clock=clock)
    except Exception:
        db.rollback()
        return EmailVerificationDelivery("delivery_failed")
