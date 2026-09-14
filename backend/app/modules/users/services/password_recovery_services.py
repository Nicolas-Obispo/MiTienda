"""Recuperacion publica uniforme y restablecimiento atomico de password."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.config import settings
from app.modules.communications.services.email_provider_factory import build_identity_email_provider
from app.modules.communications.services.identity_email_services import deliver_identity_email
from app.modules.communications.services.recovery_delivery_services import (
    EMAIL,
    RECOVERY_CHANNELS,
    SMS,
    WHATSAPP,
    build_phone_recovery_adapter,
    phone_channel_enabled,
)
from app.modules.users.models.identity_models import AccountActionToken, PasswordCredential
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_rate_limit_services import (
    LocalPublicRateLimiter,
    record_password_reset,
)
from app.modules.users.services.account_action_token_services import (
    PASSWORD_CHANGED,
    PASSWORD_RESET,
    AccountActionTokenInvalidError,
    consume_account_action_token,
    issue_account_action_token,
)
from app.modules.users.services.email_normalization import canonicalize_email
from app.modules.users.services.password_policy import validate_new_password
from app.modules.users.services.feedgo_session_services import (
    revoke_user_feedgo_sessions,
)

PUBLIC_RECOVERY_MESSAGE = (
    "Si ese usuario está registrado, te vamos a enviar un enlace para crear "
    "una nueva contraseña."
)

password_reset_local_limiter = LocalPublicRateLimiter()


class PasswordResetError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def derive_recovery_channel_availability(usuario: Usuario) -> dict[str, bool]:
    """Deriva canales sin persistir flags ni probar silenciosamente providers."""
    email_available = bool(
        usuario.email_verified_at is not None
        and settings.IDENTITY_EMAIL_ENABLED
        and settings.IDENTITY_EMAIL_PROVIDER.strip().lower() != "disabled"
    )
    verified_phone = bool(
        usuario.telefono_e164 and usuario.telefono_verified_at is not None
    )
    return {
        EMAIL: email_available,
        SMS: verified_phone and phone_channel_enabled(SMS),
        WHATSAPP: verified_phone and phone_channel_enabled(WHATSAPP),
    }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _naive(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def request_password_recovery(
    *, db: Session, email: str, client_host: str, clock=utc_now,
    local_limiter: LocalPublicRateLimiter = password_reset_local_limiter,
    channel: str = EMAIL,
) -> None:
    """Ejecuta siempre un contrato público uniforme y nunca revela existencia."""

    try:
        if channel not in RECOVERY_CHANNELS:
            return
        local = local_limiter.record_password_reset(client_host=client_host)
        if not local.allowed:
            return
        canonical = canonicalize_email(email)
        decision = record_password_reset(
            db,
            email_canonical=canonical,
            now=_naive(clock()),
        )
        if not decision.allowed:
            db.commit()
            return

        usuario = db.query(Usuario).filter(Usuario.email_canonical == canonical).first()
        if usuario is None or db.get(PasswordCredential, usuario.id) is None:
            db.commit()
            return

        availability = derive_recovery_channel_availability(usuario)
        if not availability[channel]:
            db.commit()
            return

        issued = issue_account_action_token(
            db=db,
            usuario_id=usuario.id,
            purpose=PASSWORD_RESET,
            clock=clock,
        )
        try:
            if channel == EMAIL:
                deliver_identity_email(
                    provider=build_identity_email_provider(),
                    recipient=usuario.email,
                    purpose=PASSWORD_RESET,
                    secret=issued.secret,
                    issuance_id=issued.issuance_id,
                )
            else:
                build_phone_recovery_adapter(channel).deliver(
                    recipient=usuario.telefono_e164,
                    purpose=PASSWORD_RESET,
                    secret=issued.secret,
                    issuance_id=issued.issuance_id,
                )
        finally:
            issued = None
    except Exception:
        db.rollback()
        # El contrato público es deliberadamente indistinguible.
        return


def reset_password_with_token(
    *, db: Session, secret: str, new_password: str, clock=utc_now
) -> None:
    """Cambia ambos owners legacy/nuevo y consume el token en un solo commit."""

    validate_new_password(new_password)
    current = clock()
    try:
        consumed = consume_account_action_token(
            db=db,
            secret=secret,
            purpose=PASSWORD_RESET,
            clock=clock,
            commit=False,
        )
        usuario = db.get(Usuario, consumed.usuario_id)
        credential = db.get(PasswordCredential, consumed.usuario_id)
        if usuario is None or credential is None:
            raise AccountActionTokenInvalidError()

        new_hash = hash_password(new_password)
        credential.password_hash = new_hash
        credential.hash_version = "bcrypt"
        usuario.hashed_password = new_hash

        siblings = (
            db.query(AccountActionToken)
            .filter(
                AccountActionToken.usuario_id == usuario.id,
                AccountActionToken.purpose == PASSWORD_RESET,
                AccountActionToken.id != consumed.id,
                AccountActionToken.consumed_at.is_(None),
                AccountActionToken.invalidated_at.is_(None),
                AccountActionToken.expires_at > current,
            )
            .with_for_update()
            .all()
        )
        for sibling in siblings:
            sibling.invalidated_at = current
            sibling.invalidation_reason = PASSWORD_CHANGED
        revoke_user_feedgo_sessions(
            db,
            usuario_id=usuario.id,
            clock=clock,
        )
        db.commit()
    except AccountActionTokenInvalidError:
        db.rollback()
        raise PasswordResetError("password_reset_link_invalid") from None
    except Exception:
        db.rollback()
        raise
