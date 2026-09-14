from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import threading
import unittest

from sqlalchemy import select

from app.core.config import settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import AccountActionRateLimit, PhoneVerificationChallenge
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.phone_verification_services import (
    FakePhoneOtpDelivery, PhoneVerificationError,
    confirm_phone_challenge, issue_phone_challenge,
)
from app.modules.users.services.usuarios_services import actualizar_perfil_usuario
from migrate_phone_verification_challenges import upgrade
from tests.mysql_stage97_test_support import isolated_mysql_test_engine

import_all_models()


class PhoneVerificationMySQLConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session = isolated_mysql_test_engine()
        cls.old_phone = settings.PHONE_VERIFICATION_HMAC_SECRET
        cls.old_rate = settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET
        settings.PHONE_VERIFICATION_HMAC_SECRET = "phone-mysql-test-secret"
        settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET = "rate-mysql-test-secret"

    @classmethod
    def tearDownClass(cls):
        settings.PHONE_VERIFICATION_HMAC_SECRET = cls.old_phone
        settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET = cls.old_rate
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        db = self.Session()
        user = Usuario(email="otp-mysql@example.com", hashed_password="x", modo_activo="usuario", onboarding_completo=False, telefono_e164="+5491123456789")
        db.add(user); db.flush(); self.user_id = user.id; db.commit(); db.close()

    def _issue(self):
        db = self.Session(); delivery = FakePhoneOtpDelivery([])
        cid = issue_phone_challenge(db=db, usuario_id=self.user_id, delivery=delivery)
        db.commit(); code = delivery.messages[0]["code"]; db.close()
        return cid, code

    def test_two_confirmations_have_one_winner(self):
        cid, code = self._issue(); barrier = threading.Barrier(2)
        def worker():
            db = self.Session(); barrier.wait()
            try:
                confirm_phone_challenge(db=db, usuario_id=self.user_id, challenge_id=cid, code=code); db.commit(); return True
            except PhoneVerificationError:
                db.rollback(); return False
            finally: db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(results.count(True), 1)

    def test_concurrent_resend_allows_only_one(self):
        barrier = threading.Barrier(2)
        def worker():
            db = self.Session(); delivery = FakePhoneOtpDelivery([]); barrier.wait()
            try:
                issue_phone_challenge(db=db, usuario_id=self.user_id, delivery=delivery); db.commit(); return True
            except Exception:
                db.rollback(); return False
            finally: db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(results.count(True), 1)
        db=self.Session(); self.assertEqual(db.query(PhoneVerificationChallenge).count(), 1); db.close()

    def test_concurrent_wrong_attempts_are_not_lost(self):
        cid, code = self._issue(); wrong_code = "000001" if code == "000000" else "000000"; barrier = threading.Barrier(5)
        def worker():
            db=self.Session(); barrier.wait()
            try: confirm_phone_challenge(db=db, usuario_id=self.user_id, challenge_id=cid, code=wrong_code)
            except PhoneVerificationError: db.commit()
            finally: db.close()
        with ThreadPoolExecutor(max_workers=5) as pool: list(pool.map(lambda _: worker(), range(5)))
        db=self.Session(); self.assertEqual(db.get(PhoneVerificationChallenge,cid).failed_attempts,5); db.close()

    def test_phone_change_and_confirmation_remain_consistent(self):
        cid, code = self._issue(); barrier=threading.Barrier(2)
        def confirm():
            db=self.Session(); barrier.wait()
            try: confirm_phone_challenge(db=db,usuario_id=self.user_id,challenge_id=cid,code=code); db.commit()
            except PhoneVerificationError: db.rollback()
            finally: db.close()
        def change():
            db=self.Session(); barrier.wait()
            try: actualizar_perfil_usuario(db,db.get(Usuario,self.user_id),{"telefono_e164":"+5491134567890"})
            except ValueError: db.rollback()
            finally: db.close()
        with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(lambda fn: fn(), (confirm,change)))
        db=self.Session(); user=db.get(Usuario,self.user_id)
        self.assertFalse(user.telefono_e164=="+5491134567890" and user.telefono_verified_at is not None)
        db.close()

if __name__ == "__main__": unittest.main()
