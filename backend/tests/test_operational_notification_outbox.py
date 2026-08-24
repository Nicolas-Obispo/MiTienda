import json
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.communications.providers.email_provider import EmailDeliveryError, FakeEmailProvider
from app.modules.communications.services.operational_email_services import (
    OperationalEmailBacklogError,
    OperationalEmailConflictError,
    assert_dispatcher_activation_ready,
    claim_due_operational_emails,
    deliver_claimed_operational_email,
    deliver_due_operational_emails,
    deliver_pending_operational_email,
    suppress_operational_email,
)
from app.modules.notifications.models.operational_notification_outbox_models import OperationalNotificationOutbox
from app.modules.notifications.services.operational_notification_services import (
    enqueue_incident_escalated,
    enqueue_incident_opened,
    enqueue_report_created,
)

import_all_models()


class OperationalNotificationOutboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.db = self.Session()
        self.original = {
            "ADMIN_EMAIL_ENABLED": settings.ADMIN_EMAIL_ENABLED,
            "ADMINISTRATIVE_OPERATIONAL_EMAIL": settings.ADMINISTRATIVE_OPERATIONAL_EMAIL,
            "EMAIL_FROM_ADDRESS": settings.EMAIL_FROM_ADDRESS,
            "ADMIN_EMAIL_NOTIFY_SEV3_SEV4": settings.ADMIN_EMAIL_NOTIFY_SEV3_SEV4,
            "ADMIN_EMAIL_MAX_ATTEMPTS": settings.ADMIN_EMAIL_MAX_ATTEMPTS,
        }

    def tearDown(self):
        self.db.close()
        for key, value in self.original.items():
            setattr(settings, key, value)

    def test_report_payload_is_minimal_and_deduplicated(self):
        report = SimpleNamespace(id=7, recurso_tipo="publicacion", recurso_id=12, motivo="spam", usuario_id=99, detalle="privado")
        first = enqueue_report_created(db=self.db, report=report)
        self.db.flush()
        second = enqueue_report_created(db=self.db, report=report)
        self.db.commit()
        self.assertEqual(first.id, second.id)
        self.assertEqual(self.db.query(OperationalNotificationOutbox).count(), 1)
        payload = json.loads(first.payload_json)
        self.assertEqual(payload, {"reason_code": "spam", "report_id": 7, "resource_id": 12, "resource_type": "publicacion"})
        self.assertNotIn("usuario", first.payload_json)
        self.assertNotIn("privado", first.payload_json)

    def test_incident_policy_and_escalation(self):
        low = SimpleNamespace(public_id="INC-LOW", incident_type="availability", severity="sev3_medium", version=1)
        self.assertIsNone(enqueue_incident_opened(db=self.db, incident=low))
        high = SimpleNamespace(public_id="INC-HIGH", incident_type="security", severity="sev2_high", version=1)
        self.assertIsNotNone(enqueue_incident_opened(db=self.db, incident=high))
        high.version = 2
        self.assertIsNotNone(enqueue_incident_escalated(db=self.db, incident=high, previous_severity="sev3_medium"))
        high.severity = "sev1_critical"; high.version = 3
        self.assertIsNotNone(enqueue_incident_escalated(db=self.db, incident=high, previous_severity="sev2_high"))
        high.severity = "sev2_high"; high.version = 4
        self.assertIsNone(enqueue_incident_escalated(db=self.db, incident=high, previous_severity="sev1_critical"))

    def test_delivery_is_disabled_by_default(self):
        item = enqueue_report_created(db=self.db, report=SimpleNamespace(id=1, recurso_tipo="historia", recurso_id=2, motivo="otro"))
        self.db.commit()
        provider = FakeEmailProvider()
        self.assertFalse(deliver_pending_operational_email(db=self.db, outbox_id=item.id, provider=provider))
        self.assertEqual(provider.messages, [])
        self.assertEqual(item.status, "pending")

    def test_fake_provider_delivery_and_sanitized_failure(self):
        settings.ADMIN_EMAIL_ENABLED = True
        settings.ADMINISTRATIVE_OPERATIONAL_EMAIL = "ops@example.test"
        settings.EMAIL_FROM_ADDRESS = "feedgo@example.test"
        item = enqueue_report_created(db=self.db, report=SimpleNamespace(id=2, recurso_tipo="comercio", recurso_id=3, motivo="fraude"))
        self.db.commit()
        provider = FakeEmailProvider()
        self.assertTrue(deliver_pending_operational_email(db=self.db, outbox_id=item.id, provider=provider))
        self.assertEqual(item.status, "sent")
        self.assertEqual(len(provider.messages), 1)
        self.assertNotIn("denunciante", provider.messages[0].body.lower())

        failed = enqueue_report_created(db=self.db, report=SimpleNamespace(id=3, recurso_tipo="comercio", recurso_id=4, motivo="spam"))
        self.db.commit()
        error_provider = FakeEmailProvider(EmailDeliveryError("provider_timeout", retryable=True))
        self.assertFalse(deliver_pending_operational_email(db=self.db, outbox_id=failed.id, provider=error_provider))
        self.assertEqual(failed.last_error_code, "provider_timeout")
        self.assertEqual(failed.status, "retryable_failed")

    def test_invalid_configuration_is_sanitized(self):
        settings.ADMIN_EMAIL_ENABLED = True
        settings.ADMINISTRATIVE_OPERATIONAL_EMAIL = ""
        settings.EMAIL_FROM_ADDRESS = ""
        item = enqueue_report_created(db=self.db, report=SimpleNamespace(id=4, recurso_tipo="historia", recurso_id=8, motivo="otro"))
        self.db.commit()
        self.assertFalse(deliver_pending_operational_email(db=self.db, outbox_id=item.id, provider=FakeEmailProvider()))
        self.assertEqual(item.status, "permanent_failed")
        self.assertEqual(item.last_error_code, "email_configuration_invalid")

    def test_dispatcher_processes_due_items_without_network_provider(self):
        settings.ADMIN_EMAIL_ENABLED = True
        settings.ADMINISTRATIVE_OPERATIONAL_EMAIL = "ops@example.test"
        settings.EMAIL_FROM_ADDRESS = "feedgo@example.test"
        enqueue_report_created(db=self.db, report=SimpleNamespace(id=5, recurso_tipo="publicacion", recurso_id=9, motivo="spam"))
        enqueue_report_created(db=self.db, report=SimpleNamespace(id=6, recurso_tipo="historia", recurso_id=10, motivo="otro"))
        self.db.commit()
        provider = FakeEmailProvider()
        self.assertEqual(deliver_due_operational_emails(db=self.db, provider=provider), 2)
        self.assertEqual(deliver_due_operational_emails(db=self.db, provider=provider), 0)
        self.assertEqual(len(provider.messages), 2)

    def test_claim_is_durable_and_provider_runs_after_claim_commit(self):
        settings.ADMIN_EMAIL_ENABLED = True
        settings.ADMINISTRATIVE_OPERATIONAL_EMAIL = "ops@example.test"
        settings.EMAIL_FROM_ADDRESS = "feedgo@example.test"
        item = enqueue_report_created(db=self.db, report=SimpleNamespace(id=8, recurso_tipo="historia", recurso_id=2, motivo="otro"))
        self.db.commit()
        original_key = item.deduplication_key
        claims = claim_due_operational_emails(
            db=self.db, claimed_by="worker.test-1", lease_seconds=60,
        )
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].deduplication_key, original_key)
        observed = self.Session().get(OperationalNotificationOutbox, item.id)
        self.assertEqual(observed.status, "processing")
        self.assertEqual(observed.claimed_by, "worker.test-1")
        self.assertIsNotNone(observed.lease_expires_at)

        class InspectingProvider(FakeEmailProvider):
            def send(inner_self, message):
                check = self.Session()
                try:
                    persisted = check.get(OperationalNotificationOutbox, item.id)
                    self.assertEqual(persisted.status, "processing")
                finally:
                    check.close()
                return super().send(message)

        self.assertTrue(deliver_claimed_operational_email(
            db=self.db, claim=claims[0], provider=InspectingProvider(),
        ))
        self.db.refresh(item)
        self.assertEqual(item.status, "sent")
        self.assertIsNone(item.claimed_by)
        self.assertIsNone(item.lease_expires_at)
        self.assertEqual(item.deduplication_key, original_key)

    def test_expired_lease_is_recovered_with_same_idempotency_key(self):
        item = enqueue_report_created(db=self.db, report=SimpleNamespace(id=9, recurso_tipo="comercio", recurso_id=3, motivo="spam"))
        self.db.commit()
        key = item.deduplication_key
        item.status = "processing"
        item.claimed_by = "dead-worker"
        item.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        item.attempt_count = 1
        self.db.commit()
        claims = claim_due_operational_emails(db=self.db, claimed_by="recovery-worker")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].attempt_count, 2)
        self.assertEqual(claims[0].deduplication_key, key)

    def test_retry_backoff_and_max_attempts_are_bounded(self):
        settings.ADMIN_EMAIL_ENABLED = True
        settings.ADMINISTRATIVE_OPERATIONAL_EMAIL = "ops@example.test"
        settings.EMAIL_FROM_ADDRESS = "feedgo@example.test"
        settings.ADMIN_EMAIL_MAX_ATTEMPTS = 2
        item = enqueue_report_created(db=self.db, report=SimpleNamespace(id=10, recurso_tipo="comercio", recurso_id=4, motivo="spam"))
        self.db.commit()
        first = claim_due_operational_emails(db=self.db, claimed_by="retry-worker", lease_seconds=10)[0]
        self.assertFalse(deliver_claimed_operational_email(
            db=self.db, claim=first,
            provider=FakeEmailProvider(EmailDeliveryError("provider_timeout", retryable=True)),
        ))
        self.db.refresh(item)
        self.assertEqual(item.status, "retryable_failed")
        self.assertIsNotNone(item.next_attempt_at)
        item.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.db.commit()
        second = claim_due_operational_emails(db=self.db, claimed_by="retry-worker", lease_seconds=10)[0]
        self.assertFalse(deliver_claimed_operational_email(
            db=self.db, claim=second,
            provider=FakeEmailProvider(EmailDeliveryError("provider_timeout", retryable=True)),
        ))
        self.db.refresh(item)
        self.assertEqual(item.status, "permanent_failed")
        self.assertEqual(item.attempt_count, 2)
        self.assertIsNone(item.next_attempt_at)
        self.assertEqual(claim_due_operational_emails(db=self.db, claimed_by="retry-worker"), [])

    def test_suppression_is_terminal_audited_and_does_not_delete(self):
        item = enqueue_report_created(db=self.db, report=SimpleNamespace(id=11, recurso_tipo="historia", recurso_id=8, motivo="otro"))
        self.db.commit()
        suppressed = suppress_operational_email(
            db=self.db, outbox_id=item.id, suppressed_by="operator.local-32",
            reason="pre_activation_synthetic",
        )
        self.assertEqual(suppressed.status, "suppressed")
        self.assertEqual(suppressed.suppressed_by, "operator.local-32")
        self.assertEqual(suppressed.suppression_reason, "pre_activation_synthetic")
        self.assertIsNotNone(suppressed.suppressed_at)
        self.assertEqual(self.db.query(OperationalNotificationOutbox).count(), 1)
        self.assertEqual(claim_due_operational_emails(db=self.db, claimed_by="worker.test"), [])
        with self.assertRaises(OperationalEmailConflictError):
            suppress_operational_email(
                db=self.db, outbox_id=item.id, suppressed_by="operator.local-32",
                reason="operator_requested",
            )

    def test_activation_is_blocked_until_previous_backlog_is_reconciled(self):
        item = enqueue_report_created(db=self.db, report=SimpleNamespace(id=12, recurso_tipo="publicacion", recurso_id=9, motivo="spam"))
        self.db.commit()
        activation = datetime.now(timezone.utc) + timedelta(seconds=1)
        with self.assertRaises(OperationalEmailBacklogError):
            assert_dispatcher_activation_ready(db=self.db, activated_at=activation)
        suppress_operational_email(
            db=self.db, outbox_id=item.id, suppressed_by="operator.local-32",
            reason="pre_activation_synthetic",
        )
        assert_dispatcher_activation_ready(db=self.db, activated_at=activation)


if __name__ == "__main__":
    unittest.main()
