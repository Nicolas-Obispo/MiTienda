"""Cambio autenticado de password con dual-write transaccional."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password, verificar_password
from app.modules.users.models.identity_models import AccountActionToken, PasswordCredential
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_rate_limit_services import (
    check_current_password_allowed,
    clear_current_password_failures,
    record_current_password_failure,
)
from app.modules.users.services.account_action_token_services import PASSWORD_CHANGED, PASSWORD_RESET
from app.modules.users.services.password_policy import validate_new_password
from app.modules.users.services.feedgo_session_services import (
    revoke_user_feedgo_sessions,
)


class AuthenticatedPasswordChangeError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _naive(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def change_authenticated_password(
    *, db: Session, usuario: Usuario, current_password: str,
    new_password: str, current_session_sid: str | None = None, clock=utc_now,
) -> None:
    """Valida literal y cambia credenciales/tokens bajo un unico commit."""

    validate_new_password(new_password)
    current = clock()
    rate_now = _naive(current)
    try:
        allowed = check_current_password_allowed(
            db, usuario_id=usuario.id, now=rate_now
        )
        if not allowed.allowed:
            db.commit()
            raise AuthenticatedPasswordChangeError("current_password_rate_limited")

        credential = (
            db.query(PasswordCredential)
            .filter(PasswordCredential.usuario_id == usuario.id)
            .with_for_update()
            .first()
        )
        if credential is None or not verificar_password(
            current_password, credential.password_hash
        ):
            record_current_password_failure(
                db, usuario_id=usuario.id, now=rate_now
            )
            db.commit()
            raise AuthenticatedPasswordChangeError("current_password_incorrect")

        clear_current_password_failures(db, usuario_id=usuario.id, now=rate_now)
        new_hash = hash_password(new_password)
        credential.password_hash = new_hash
        credential.hash_version = "bcrypt"
        usuario.hashed_password = new_hash

        tokens = (
            db.query(AccountActionToken)
            .filter(
                AccountActionToken.usuario_id == usuario.id,
                AccountActionToken.purpose == PASSWORD_RESET,
                AccountActionToken.consumed_at.is_(None),
                AccountActionToken.invalidated_at.is_(None),
                AccountActionToken.expires_at > current,
            )
            .with_for_update()
            .all()
        )
        for token in tokens:
            token.invalidated_at = current
            token.invalidation_reason = PASSWORD_CHANGED
        revoke_user_feedgo_sessions(
            db,
            usuario_id=usuario.id,
            except_sid=current_session_sid,
            clock=clock,
        )
        db.commit()
    except AuthenticatedPasswordChangeError:
        raise
    except Exception:
        db.rollback()
        raise
