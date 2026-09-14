from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.communications.providers.email_provider import FakeEmailProvider
from app.modules.users.models.identity_models import AccountActionToken, PasswordCredential
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.schemas.usuarios_schemas import PasswordRecoveryRequest
from app.modules.users.services.account_action_rate_limit_services import LocalPublicRateLimiter
from app.modules.users.services.password_recovery_services import (
    derive_recovery_channel_availability,
    request_password_recovery,
)

import_all_models()


class PasswordRecoveryMultichannelTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
        Base.metadata.create_all(self.engine); self.Session=sessionmaker(bind=self.engine)
        with self.Session.begin() as db:
            db.add(Usuario(id=1,email="person@example.com",email_canonical="person@example.com",email_verified_at=datetime(2026,1,1,tzinfo=timezone.utc),hashed_password="x",telefono_e164="+5491123456789",telefono_verified_at=datetime(2026,1,1,tzinfo=timezone.utc),telefono_verification_source="phone_otp"))
            db.add(PasswordCredential(usuario_id=1,password_hash="x",hash_version="bcrypt"))
        self.provider=FakeEmailProvider(); self.local=LocalPublicRateLimiter(secret="local-rate")
        self.patches=[
            patch("app.modules.users.services.account_action_rate_limit_services.settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET","rate-secret"),
            patch("app.modules.users.services.password_recovery_services.build_identity_email_provider",return_value=self.provider),
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_EMAIL_ENABLED",True),
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_EMAIL_PROVIDER","fake"),
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_SMS_ENABLED",False),
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_WHATSAPP_ENABLED",False),
            patch("app.modules.communications.services.identity_email_services.settings.IDENTITY_EMAIL_FROM_ADDRESS","hola@feedgo.test"),
            patch("app.modules.communications.services.identity_email_services.settings.IDENTITY_EMAIL_PUBLIC_BASE_URL","https://feedgo.test"),
        ]
        for item in self.patches:item.start()

    def tearDown(self):
        for item in reversed(self.patches):item.stop()
        self.engine.dispose()

    def request(self,email="person@example.com",channel="email"):
        with self.Session() as db:
            request_password_recovery(db=db,email=email,channel=channel,client_host="203.0.113.1",local_limiter=self.local)

    def test_request_legacy_defaults_to_email_and_explicit_email_works(self):
        self.assertEqual(PasswordRecoveryRequest(email="x@example.com").channel,"email")
        self.assertEqual(
            PasswordRecoveryRequest(email="x@example.com", channel="email").channel,
            "email",
        )
        self.request(); self.assertEqual(len(self.provider.messages),1)
        with self.Session() as db:self.assertEqual(db.query(AccountActionToken).count(),1)

    def test_verified_phone_does_not_enable_sms_or_whatsapp(self):
        with self.Session() as db:
            available=derive_recovery_channel_availability(db.get(Usuario,1))
        self.assertTrue(available["email"]); self.assertFalse(available["sms"]); self.assertFalse(available["whatsapp"])
        self.request(channel="sms"); self.request(channel="whatsapp")
        with self.Session() as db:self.assertEqual(db.query(AccountActionToken).count(),0)

    def test_nonexistent_invalid_and_unavailable_are_silent(self):
        self.request(email="missing@example.com")
        self.request(email="not-an-email")
        self.request(channel="sms")
        self.assertEqual(self.provider.messages,[])

    def test_no_phone_provider_or_probe_is_called(self):
        with patch("app.modules.users.services.password_recovery_services.build_phone_recovery_adapter") as adapter:
            self.request(channel="whatsapp")
        adapter.assert_not_called()

    def test_configuration_alone_cannot_enable_missing_adapters(self):
        with (
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_SMS_ENABLED",True),
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_SMS_PROVIDER","future"),
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_WHATSAPP_ENABLED",True),
            patch("app.modules.users.services.password_recovery_services.settings.IDENTITY_WHATSAPP_PROVIDER","future"),
            self.Session() as db,
        ):
            available=derive_recovery_channel_availability(db.get(Usuario,1))
        self.assertFalse(available["sms"]); self.assertFalse(available["whatsapp"])


if __name__=="__main__":unittest.main()
