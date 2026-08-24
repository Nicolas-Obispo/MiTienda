import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.communications.providers.email_provider import EmailDeliveryError, EmailMessage, FakeEmailProvider
from app.modules.communications.providers.resend_email_provider import HttpResponse, ResendEmailProvider
from app.modules.communications.services.email_provider_factory import build_configured_email_provider
from app.modules.communications.services.operational_email_services import deliver_pending_operational_email
from app.modules.notifications.services.operational_notification_services import enqueue_report_created

import_all_models()


class StubTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, **request):
        self.calls.append(request)
        return self.response


class ResendEmailProviderTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.original = {
            key: getattr(settings, key)
            for key in ("ADMIN_EMAIL_ENABLED", "ADMINISTRATIVE_OPERATIONAL_EMAIL", "EMAIL_FROM_ADDRESS", "EMAIL_PROVIDER", "RESEND_API_KEY")
        }
        settings.ADMIN_EMAIL_ENABLED = True
        settings.ADMINISTRATIVE_OPERATIONAL_EMAIL = "ops@example.test"
        settings.EMAIL_FROM_ADDRESS = "feedgo@example.test"

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        for key, value in self.original.items():
            setattr(settings, key, value)

    def _outbox(self, report_id):
        item = enqueue_report_created(
            db=self.db,
            report=type("Report", (), {"id": report_id, "recurso_tipo": "publicacion", "recurso_id": 10, "motivo": "spam"})(),
        )
        self.db.commit()
        return item

    def test_fake_and_resend_are_substitutable_through_email_provider_contract(self):
        fake_item = self._outbox(1)
        fake = FakeEmailProvider()
        self.assertTrue(deliver_pending_operational_email(db=self.db, outbox_id=fake_item.id, provider=fake))

        resend_item = self._outbox(2)
        transport = StubTransport(HttpResponse(200, b'{"id":"external-generic-2"}'))
        resend = ResendEmailProvider(
            api_key="test-key-not-real",
            base_url="https://api.resend.test",
            timeout_seconds=1,
            transport=transport,
        )
        self.assertTrue(deliver_pending_operational_email(db=self.db, outbox_id=resend_item.id, provider=resend))
        self.assertEqual(resend_item.provider_reference, "external-generic-2")
        self.assertEqual(resend_item.status, "sent")
        request = transport.calls[0]
        self.assertEqual(request["headers"]["Idempotency-Key"], resend_item.deduplication_key)
        self.assertEqual(request["headers"]["User-Agent"], "FeedGo/1.0")
        self.assertEqual(json.loads(request["body"])["to"], ["ops@example.test"])

    def test_resend_details_do_not_escape_adapter_or_persistence(self):
        item = self._outbox(3)
        transport = StubTransport(HttpResponse(429, b'{"name":"rate_limit_exceeded","message":"vendor detail"}'))
        provider = ResendEmailProvider(api_key="test-key-not-real", base_url="https://api.resend.test", timeout_seconds=1, transport=transport)
        self.assertFalse(deliver_pending_operational_email(db=self.db, outbox_id=item.id, provider=provider))
        self.assertEqual(item.last_error_code, "email_provider_temporarily_unavailable")
        self.assertNotIn("rate_limit", item.last_error_code)
        self.assertNotIn("vendor detail", item.payload_json)

    def test_provider_configuration_is_environment_owned_and_disabled_by_default(self):
        settings.ADMIN_EMAIL_ENABLED = False
        settings.EMAIL_PROVIDER = "resend"
        settings.RESEND_API_KEY = "test-key-not-real"
        self.assertIsNone(build_configured_email_provider())
        settings.ADMIN_EMAIL_ENABLED = True
        self.assertIsInstance(build_configured_email_provider(), ResendEmailProvider)

    def test_http_categories_are_mapped_to_sanitized_generic_errors(self):
        for status, body, expected_code, retryable in (
            (400, b'{"message":"must-not-persist"}', "email_provider_request_invalid", False),
            (422, b'{"message":"must-not-persist"}', "email_provider_request_invalid", False),
            (401, b'{"message":"must-not-persist"}', "email_provider_authentication_failed", False),
            (403, b'{"message":"must-not-persist"}', "email_provider_sender_not_authorized", False),
            (404, b'{"message":"must-not-persist"}', "email_provider_rejected", False),
            (418, b'{"message":"must-not-persist"}', "email_provider_rejected", False),
            (408, b'{"message":"must-not-persist"}', "email_provider_temporarily_unavailable", True),
            (425, b'{"message":"must-not-persist"}', "email_provider_temporarily_unavailable", True),
            (429, b'{"message":"must-not-persist"}', "email_provider_temporarily_unavailable", True),
            (409, b'{"name":"invalid_idempotent_request","message":"must-not-persist"}', "email_provider_idempotency_conflict", False),
            (409, b'{"name":"concurrent_idempotent_requests","message":"must-not-persist"}', "email_provider_idempotency_conflict", True),
            (503, b'{"message":"must-not-persist"}', "email_provider_temporarily_unavailable", True),
        ):
            provider = ResendEmailProvider(
                api_key="test-key-not-real",
                base_url="https://api.resend.test",
                timeout_seconds=1,
                transport=StubTransport(HttpResponse(status, body)),
            )
            with self.assertRaises(EmailDeliveryError) as raised:
                provider.send(EmailMessage(
                    sender="from@example.test",
                    recipient="to@example.test",
                    subject="subject",
                    body="body",
                    idempotency_key="event:1",
                ))
            self.assertEqual(raised.exception.safe_code, expected_code)
            self.assertEqual(raised.exception.retryable, retryable)
            self.assertNotIn("must-not-persist", str(raised.exception))

    def test_user_agent_is_fixed_for_rejected_requests_without_leaking_response(self):
        transport = StubTransport(HttpResponse(403, b'{"message":"private-provider-detail"}'))
        provider = ResendEmailProvider(
            api_key="test-key-not-real",
            base_url="https://api.resend.test",
            timeout_seconds=1,
            transport=transport,
        )
        with self.assertRaises(EmailDeliveryError) as raised:
            provider.send(EmailMessage(
                sender="from@example.test",
                recipient="to@example.test",
                subject="subject",
                body="body",
                idempotency_key="event:ua-test",
            ))
        self.assertEqual(transport.calls[0]["headers"]["User-Agent"], "FeedGo/1.0")
        self.assertEqual(raised.exception.safe_code, "email_provider_sender_not_authorized")
        self.assertNotIn("private-provider-detail", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
