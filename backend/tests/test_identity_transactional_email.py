import logging
from pathlib import Path
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.communications.providers.email_provider import (
    EmailDeliveryError,
    FakeEmailProvider,
)
from app.modules.communications.providers.resend_email_provider import ResendEmailProvider
from app.modules.communications.services.email_provider_factory import (
    build_identity_email_provider,
)
from app.modules.communications.services.identity_email_services import (
    IdentityEmailDeliveryError,
    build_identity_action_link,
    deliver_identity_email,
)
from app.modules.communications.services.identity_email_templates import (
    EMAIL_VERIFICATION,
    PASSWORD_RESET,
    render_identity_email,
)
from app.modules.users.models.identity_models import AccountActionToken
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.account_action_token_services import (
    issue_account_action_token,
)


import_all_models()


class SequencedProvider(FakeEmailProvider):
    def __init__(self, failures):
        super().__init__()
        self.failures = list(failures)
        self.calls = []

    def send(self, message):
        self.calls.append(message)
        if self.failures:
            failure = self.failures.pop(0)
            if failure is not None:
                raise failure
        return "provider:ok"


class IdentityTransactionalEmailTests(unittest.TestCase):
    def setUp(self):
        self.original = {
            name: getattr(settings, name)
            for name in (
                "ADMIN_EMAIL_ENABLED",
                "IDENTITY_EMAIL_ENABLED",
                "IDENTITY_EMAIL_PROVIDER",
                "IDENTITY_RESEND_API_KEY",
                "IDENTITY_EMAIL_FROM_ADDRESS",
                "IDENTITY_EMAIL_PUBLIC_BASE_URL",
                "IDENTITY_EMAIL_TIMEOUT_SECONDS",
                "RUNTIME_ENVIRONMENT",
            )
        }
        settings.IDENTITY_EMAIL_ENABLED = False
        settings.IDENTITY_EMAIL_PROVIDER = "disabled"
        settings.IDENTITY_RESEND_API_KEY = None
        settings.IDENTITY_EMAIL_FROM_ADDRESS = "cuentas@feedgo.example"
        settings.IDENTITY_EMAIL_PUBLIC_BASE_URL = "https://app.feedgo.example"
        settings.IDENTITY_EMAIL_TIMEOUT_SECONDS = 5.0
        settings.RUNTIME_ENVIRONMENT = "test"

    def tearDown(self):
        for name, value in self.original.items():
            setattr(settings, name, value)

    def test_composition_root_is_independent_from_admin_and_disabled(self):
        settings.ADMIN_EMAIL_ENABLED = True
        self.assertIsNone(build_identity_email_provider())
        settings.IDENTITY_EMAIL_ENABLED = True
        settings.IDENTITY_EMAIL_PROVIDER = "fake"
        self.assertIsInstance(build_identity_email_provider(), FakeEmailProvider)
        settings.ADMIN_EMAIL_ENABLED = False
        self.assertIsInstance(build_identity_email_provider(), FakeEmailProvider)

    def test_fake_provider_is_allowed_in_local_and_test_only(self):
        settings.IDENTITY_EMAIL_ENABLED = True
        settings.IDENTITY_EMAIL_PROVIDER = "fake"
        for runtime in ("local", "test"):
            with self.subTest(runtime=runtime):
                settings.RUNTIME_ENVIRONMENT = runtime
                self.assertIsInstance(build_identity_email_provider(), FakeEmailProvider)

    def test_fake_provider_is_rejected_outside_local_runtimes(self):
        settings.IDENTITY_EMAIL_PROVIDER = "fake"
        settings.RUNTIME_ENVIRONMENT = "production"
        for enabled in (False, True):
            with self.subTest(identity_email_enabled=enabled):
                settings.IDENTITY_EMAIL_ENABLED = enabled
                with self.assertRaisesRegex(ValueError, "identity_fake_email_provider_not_allowed"):
                    build_identity_email_provider()

    def test_resend_builds_only_with_complete_identity_configuration(self):
        settings.IDENTITY_EMAIL_ENABLED = True
        settings.IDENTITY_EMAIL_PROVIDER = "resend"
        settings.IDENTITY_RESEND_API_KEY = "test-identity-key-not-real"
        with patch.object(settings, "RESEND_API_KEY", "test-admin-key-not-real"):
            provider = build_identity_email_provider()
        self.assertIsInstance(provider, ResendEmailProvider)
        self.assertEqual(provider._api_key, "test-identity-key-not-real")

    def test_resend_missing_configuration_fails_closed_without_secret(self):
        settings.IDENTITY_EMAIL_ENABLED = True
        settings.IDENTITY_EMAIL_PROVIDER = "resend"
        secret = "test-identity-key-not-real"
        settings.IDENTITY_RESEND_API_KEY = secret
        for attribute, value, code in (
            ("IDENTITY_RESEND_API_KEY", None, "identity_resend_api_key_required"),
            ("IDENTITY_EMAIL_FROM_ADDRESS", None, "identity_email_from_address_invalid"),
            ("IDENTITY_EMAIL_FROM_ADDRESS", "cuentas@", "identity_email_from_address_invalid"),
            ("IDENTITY_EMAIL_PUBLIC_BASE_URL", None, "identity_email_public_base_url_invalid"),
            ("IDENTITY_EMAIL_TIMEOUT_SECONDS", 0, "identity_email_timeout_invalid"),
        ):
            with self.subTest(attribute=attribute):
                original = getattr(settings, attribute)
                setattr(settings, attribute, value)
                try:
                    with self.assertRaisesRegex(ValueError, code) as caught:
                        build_identity_email_provider()
                    self.assertNotIn(secret, str(caught.exception))
                finally:
                    setattr(settings, attribute, original)

    def test_resend_never_falls_back_to_fake(self):
        settings.IDENTITY_EMAIL_ENABLED = True
        settings.IDENTITY_EMAIL_PROVIDER = "resend"
        settings.IDENTITY_RESEND_API_KEY = None
        with self.assertRaisesRegex(ValueError, "identity_resend_api_key_required"):
            build_identity_email_provider()

    def test_resend_requires_https_public_base_url_in_production(self):
        settings.IDENTITY_EMAIL_ENABLED = True
        settings.IDENTITY_EMAIL_PROVIDER = "resend"
        settings.IDENTITY_RESEND_API_KEY = "test-identity-key-not-real"
        settings.RUNTIME_ENVIRONMENT = "production"
        settings.IDENTITY_EMAIL_PUBLIC_BASE_URL = "http://feedgo.example"
        with self.assertRaisesRegex(ValueError, "identity_email_public_base_url_invalid"):
            build_identity_email_provider()

    def test_resend_rejects_unknown_runtime(self):
        settings.IDENTITY_EMAIL_ENABLED = True
        settings.IDENTITY_EMAIL_PROVIDER = "resend"
        settings.IDENTITY_RESEND_API_KEY = "test-identity-key-not-real"
        settings.RUNTIME_ENVIRONMENT = "unknown"
        with self.assertRaisesRegex(ValueError, "identity_email_runtime_not_supported"):
            build_identity_email_provider()

    def test_provider_selection_rejects_unknown_value_safely(self):
        settings.IDENTITY_EMAIL_ENABLED = True
        settings.IDENTITY_EMAIL_PROVIDER = "unknown"
        with self.assertRaisesRegex(ValueError, "identity_email_provider_not_supported"):
                build_identity_email_provider()

    def test_auth_and_users_do_not_depend_on_resend_adapter(self):
        backend_root = Path(__file__).resolve().parents[1]
        owned_sources = [backend_root / "app" / "core" / "auth.py"]
        owned_sources.extend(
            (backend_root / "app" / "modules" / "users").rglob("*.py")
        )
        for source in owned_sources:
            content = source.read_text(encoding="utf-8").lower()
            self.assertNotIn("resendemailprovider", content, source)
            self.assertNotIn("resend_email_provider", content, source)

    def test_verification_template_is_minimal_and_has_correct_ttl(self):
        link = "https://app.feedgo.example/verificar-email#token=secret"
        content = render_identity_email(purpose=EMAIL_VERIFICATION, link=link)
        self.assertEqual(content.subject, "Verificá tu cuenta de FeedGo")
        self.assertIn(link, content.body)
        self.assertIn("24 horas", content.body)
        self.assertNotIn("password", content.body.lower())
        self.assertNotIn("usuario_id", content.body)

    def test_reset_template_is_minimal_and_has_correct_ttl(self):
        link = "https://app.feedgo.example/restablecer-password#token=secret"
        content = render_identity_email(purpose=PASSWORD_RESET, link=link)
        self.assertEqual(content.subject, "Creá una nueva contraseña de FeedGo")
        self.assertIn(link, content.body)
        self.assertIn("30 minutos", content.body)
        self.assertNotIn("email", content.body.lower())
        self.assertNotIn("usuario_id", content.body)

    def test_links_use_fragment_and_reject_unsafe_base(self):
        secret = "abc_DEF-123"
        self.assertEqual(
            build_identity_action_link(
                purpose=EMAIL_VERIFICATION,
                secret=secret,
                public_base_url="https://app.feedgo.example/",
            ),
            f"https://app.feedgo.example/verificar-email#token={secret}",
        )
        for unsafe in (
            "http://app.feedgo.example",
            "https://user:pass@app.feedgo.example",
            "https://app.feedgo.example?token=x",
            "https://app.feedgo.example#old",
        ):
            with self.assertRaisesRegex(ValueError, "identity_email_public_base_url_invalid"):
                build_identity_action_link(
                    purpose=EMAIL_VERIFICATION,
                    secret=secret,
                    public_base_url=unsafe,
                )

    def test_fake_delivery_uses_issuance_id_and_keeps_secret_only_in_message(self):
        provider = FakeEmailProvider()
        secret = "sensitive-secret"
        result = deliver_identity_email(
            provider=provider,
            recipient="persona@example.com",
            purpose=EMAIL_VERIFICATION,
            secret=secret,
            issuance_id="issuance-123",
        )
        self.assertEqual(result.attempts, 1)
        self.assertEqual(provider.messages[0].idempotency_key, "issuance-123")
        self.assertIn(f"#token={secret}", provider.messages[0].body)
        self.assertNotIn(secret, result.provider_reference)

    def test_retry_is_immediate_bounded_and_reuses_same_message(self):
        retryable = EmailDeliveryError("provider_timeout", retryable=True)
        provider = SequencedProvider([retryable, None])
        result = deliver_identity_email(
            provider=provider,
            recipient="persona@example.com",
            purpose=PASSWORD_RESET,
            secret="secret",
            issuance_id="same-id",
        )
        self.assertEqual(result.attempts, 2)
        self.assertEqual(len(provider.calls), 2)
        self.assertIs(provider.calls[0], provider.calls[1])
        self.assertEqual({call.idempotency_key for call in provider.calls}, {"same-id"})

    def test_permanent_and_exhausted_failures_are_safe(self):
        for failures in (
            [EmailDeliveryError("private-provider-detail", retryable=False)],
            [
                EmailDeliveryError("first-private", retryable=True),
                EmailDeliveryError("second-private", retryable=True),
            ],
        ):
            provider = SequencedProvider(failures)
            secret = "must-never-escape"
            with self.assertRaises(IdentityEmailDeliveryError) as raised:
                deliver_identity_email(
                    provider=provider,
                    recipient="persona@example.com",
                    purpose=EMAIL_VERIFICATION,
                    secret=secret,
                    issuance_id="issuance-safe",
                )
            self.assertEqual(str(raised.exception), "identity_email_delivery_failed")
            self.assertNotIn(secret, str(raised.exception))
            self.assertLessEqual(len(provider.calls), 2)

    def test_secret_is_not_logged(self):
        secret = "never-log-this-secret"
        provider = FakeEmailProvider(
            EmailDeliveryError("provider-private", retryable=False)
        )
        with patch.object(logging.Logger, "_log") as logger:
            with self.assertRaises(IdentityEmailDeliveryError):
                deliver_identity_email(
                    provider=provider,
                    recipient="persona@example.com",
                    purpose=EMAIL_VERIFICATION,
                    secret=secret,
                    issuance_id="issuance-log",
                )
        logger.assert_not_called()

    def test_delivery_does_not_persist_secret_body_or_url(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        db.add(
            Usuario(
                id=1,
                email="persona@example.com",
                email_canonical="persona@example.com",
                hashed_password="$2b$test",
            )
        )
        db.commit()
        issued = issue_account_action_token(
            db=db,
            usuario_id=1,
            purpose=EMAIL_VERIFICATION,
        )
        provider = FakeEmailProvider()
        deliver_identity_email(
            provider=provider,
            recipient="persona@example.com",
            purpose=EMAIL_VERIFICATION,
            secret=issued.secret,
            issuance_id=issued.issuance_id,
        )
        token = db.get(AccountActionToken, issued.token_id)
        persisted = "|".join(
            value
            for value in (
                token.token_digest,
                token.email_canonical_snapshot,
                token.issuance_id,
                token.invalidation_reason,
            )
            if value
        )
        self.assertNotIn(issued.secret, persisted)
        self.assertNotIn("#token=", persisted)
        db.close()
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
