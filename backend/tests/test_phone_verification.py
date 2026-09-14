from datetime import datetime, timedelta, timezone
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import PhoneVerificationChallenge
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.phone_verification_services import (
    FakePhoneOtpDelivery, PhoneVerificationError, confirm_phone_challenge,
    derive_state, digest_code, issue_phone_challenge,
)
from app.modules.users.services.usuarios_services import actualizar_perfil_usuario

import_all_models()

class PhoneVerificationTests(unittest.TestCase):
    def setUp(self):
        self.old_phone_secret = settings.PHONE_VERIFICATION_HMAC_SECRET
        self.old_rate_secret = settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET
        self.old_identity_resend_secret = settings.IDENTITY_RESEND_API_KEY
        settings.PHONE_VERIFICATION_HMAC_SECRET = "phone-secret-for-tests"
        settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET = "rate-secret-for-tests"
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.user = Usuario(email="otp@example.com", hashed_password="x", modo_activo="usuario", onboarding_completo=False, telefono_e164="+5491123456789")
        self.db.add(self.user); self.db.commit()
        self.delivery = FakePhoneOtpDelivery([])
        self.now = datetime(2026, 9, 6, 12, tzinfo=timezone.utc)

    def tearDown(self):
        self.db.close(); Base.metadata.drop_all(self.engine); self.engine.dispose()
        settings.PHONE_VERIFICATION_HMAC_SECRET = self.old_phone_secret
        settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET = self.old_rate_secret
        settings.IDENTITY_RESEND_API_KEY = self.old_identity_resend_secret

    def test_phone_hmac_secret_cannot_reuse_identity_resend_key(self):
        settings.IDENTITY_RESEND_API_KEY = settings.PHONE_VERIFICATION_HMAC_SECRET
        with self.assertRaisesRegex(RuntimeError, "phone_verification_secret_reused"):
            digest_code(
                code="123456",
                issuance_id="issuance",
                usuario_id=self.user.id,
                phone=self.user.telefono_e164,
            )

    def test_issue_and_confirm_atomically(self):
        challenge_id = issue_phone_challenge(db=self.db, usuario_id=self.user.id, delivery=self.delivery, now=self.now)
        self.db.commit()
        message = self.delivery.messages[0]
        self.assertRegex(message["code"], r"^\d{6}$")
        row = self.db.get(PhoneVerificationChallenge, challenge_id)
        self.assertNotEqual(row.code_digest, message["code"])
        self.assertEqual(row.expires_at, self.now.replace(tzinfo=None) + timedelta(minutes=10))
        confirm_phone_challenge(db=self.db, usuario_id=self.user.id, challenge_id=challenge_id, code=message["code"], now=self.now)
        self.db.commit(); self.db.refresh(self.user)
        self.assertIsNotNone(self.user.telefono_verified_at)
        self.assertEqual(self.user.telefono_verification_source, "phone_otp")
        with self.assertRaises(PhoneVerificationError):
            confirm_phone_challenge(db=self.db, usuario_id=self.user.id, challenge_id=challenge_id, code=message["code"], now=self.now)

    def test_wrong_code_counts_and_fifth_exhausts(self):
        challenge_id = issue_phone_challenge(db=self.db, usuario_id=self.user.id, delivery=self.delivery, now=self.now); self.db.commit()
        for _ in range(5):
            with self.assertRaises(PhoneVerificationError):
                confirm_phone_challenge(db=self.db, usuario_id=self.user.id, challenge_id=challenge_id, code="000000", now=self.now)
            self.db.commit()
        row = self.db.get(PhoneVerificationChallenge, challenge_id)
        self.assertEqual(row.failed_attempts, 5)
        self.assertEqual(derive_state(row, now=self.now), "attempts_exhausted")

    def test_resend_supersedes_and_cooldown_blocks(self):
        first = issue_phone_challenge(db=self.db, usuario_id=self.user.id, delivery=self.delivery, now=self.now); self.db.commit()
        with self.assertRaises(PhoneVerificationError):
            issue_phone_challenge(db=self.db, usuario_id=self.user.id, delivery=self.delivery, now=self.now + timedelta(seconds=30))
        self.db.rollback()
        second = issue_phone_challenge(db=self.db, usuario_id=self.user.id, delivery=self.delivery, now=self.now + timedelta(seconds=60)); self.db.commit()
        self.assertEqual(self.db.get(PhoneVerificationChallenge, first).invalidation_reason, "superseded")
        self.assertNotEqual(first, second)

    def test_snapshot_mismatch_never_verifies_new_phone(self):
        challenge_id = issue_phone_challenge(
            db=self.db, usuario_id=self.user.id, delivery=self.delivery, now=self.now
        )
        self.db.commit()
        code = self.delivery.messages[0]["code"]
        self.user.telefono_e164 = "+5491134567890"
        self.db.commit()
        with self.assertRaises(PhoneVerificationError):
            confirm_phone_challenge(
                db=self.db, usuario_id=self.user.id,
                challenge_id=challenge_id, code=code, now=self.now,
            )
        self.db.rollback(); self.db.refresh(self.user)
        self.assertIsNone(self.user.telefono_verified_at)

    def test_normal_phone_change_clears_state_and_invalidates_challenge(self):
        challenge_id = issue_phone_challenge(
            db=self.db, usuario_id=self.user.id, delivery=self.delivery, now=self.now
        )
        self.db.commit()
        actualizar_perfil_usuario(
            self.db, self.user, {"telefono_e164": "+5491134567890"}
        )
        self.db.refresh(self.user)
        challenge = self.db.get(PhoneVerificationChallenge, challenge_id)
        self.assertIsNone(self.user.telefono_verified_at)
        self.assertIsNone(self.user.telefono_verification_source)
        self.assertEqual(challenge.invalidation_reason, "administrative")

if __name__ == "__main__": unittest.main()
