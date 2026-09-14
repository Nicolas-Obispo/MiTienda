"""Owner backend del challenge OTP para verificar telefono privado."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
import uuid
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.users.models.identity_models import PhoneVerificationChallenge
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_rate_limit_services import record_phone_verification

TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5
SOURCE = "phone_otp"

class PhoneVerificationError(ValueError):
    pass

class PhoneOtpDelivery(Protocol):
    def send(self, *, phone_e164: str, code: str, issuance_id: str) -> None: ...

@dataclass
class FakePhoneOtpDelivery:
    messages: list[dict[str, str]]
    def send(self, *, phone_e164: str, code: str, issuance_id: str) -> None:
        self.messages.append({"phone_e164": phone_e164, "code": code, "issuance_id": issuance_id})

def utc_now() -> datetime:
    return datetime.utcnow()

def _naive_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

def _secret() -> bytes:
    value = settings.PHONE_VERIFICATION_HMAC_SECRET
    if not value:
        raise RuntimeError("phone_verification_secret_missing")
    if value in {
        settings.SECRET_KEY,
        settings.RESEND_API_KEY,
        settings.IDENTITY_RESEND_API_KEY,
        settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET,
    }:
        raise RuntimeError("phone_verification_secret_reused")
    return value.encode()

def digest_code(*, code: str, issuance_id: str, usuario_id: int, phone: str) -> str:
    payload = f"feedgo-phone-otp:v1:{issuance_id}:{usuario_id}:{phone}:{code}".encode()
    return hmac.new(_secret(), payload, hashlib.sha256).hexdigest()

def derive_state(challenge: PhoneVerificationChallenge, *, now: datetime) -> str:
    now = _naive_utc(now)
    if challenge.consumed_at is not None: return "consumed"
    if challenge.revoked_at is not None: return "revoked"
    if challenge.failed_attempts >= MAX_ATTEMPTS: return "attempts_exhausted"
    if _naive_utc(challenge.expires_at) <= now: return "expired"
    return "active"

def issue_phone_challenge(*, db: Session, usuario_id: int, delivery: PhoneOtpDelivery, now: datetime | None = None) -> str:
    current = _naive_utc(now) if now is not None else utc_now()
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).with_for_update().one_or_none()
    if usuario is None or not usuario.telefono_e164 or usuario.telefono_verified_at is not None:
        raise PhoneVerificationError("phone_verification_unavailable")
    decision = record_phone_verification(db, usuario_id=usuario_id, now=current)
    if not decision.allowed: raise PhoneVerificationError("phone_verification_limited")
    active = db.query(PhoneVerificationChallenge).filter(
        PhoneVerificationChallenge.usuario_id == usuario_id,
        PhoneVerificationChallenge.consumed_at.is_(None),
        PhoneVerificationChallenge.revoked_at.is_(None),
        PhoneVerificationChallenge.expires_at > current,
    ).with_for_update().all()
    for previous in active:
        previous.revoked_at = current; previous.invalidation_reason = "superseded"
    challenge_id, issuance_id = secrets.token_urlsafe(32), uuid.uuid4().hex
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = PhoneVerificationChallenge(
        id=challenge_id, usuario_id=usuario_id, phone_e164_snapshot=usuario.telefono_e164,
        code_digest=digest_code(code=code, issuance_id=issuance_id, usuario_id=usuario_id, phone=usuario.telefono_e164),
        issuance_id=issuance_id, created_at=current, expires_at=current + TTL,
    )
    db.add(challenge); db.flush()
    delivery.send(phone_e164=usuario.telefono_e164, code=code, issuance_id=issuance_id)
    return challenge_id

def confirm_phone_challenge(*, db: Session, usuario_id: int, challenge_id: str, code: str, now: datetime | None = None) -> None:
    current = _naive_utc(now) if now is not None else utc_now()
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).with_for_update().one_or_none()
    challenge = db.query(PhoneVerificationChallenge).filter(PhoneVerificationChallenge.id == challenge_id).with_for_update().one_or_none()
    if usuario is None or challenge is None or challenge.usuario_id != usuario_id:
        raise PhoneVerificationError("phone_verification_invalid")
    if derive_state(challenge, now=current) != "active" or challenge.phone_e164_snapshot != usuario.telefono_e164:
        raise PhoneVerificationError("phone_verification_invalid")
    expected = digest_code(code=code, issuance_id=challenge.issuance_id, usuario_id=usuario_id, phone=challenge.phone_e164_snapshot)
    if not hmac.compare_digest(expected, challenge.code_digest):
        challenge.failed_attempts += 1; db.flush()
        raise PhoneVerificationError("phone_verification_invalid")
    challenge.consumed_at = current
    usuario.telefono_verified_at = current
    usuario.telefono_verification_source = SOURCE
    db.flush()
