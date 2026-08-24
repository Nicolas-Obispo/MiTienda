import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.communications.providers.email_provider import EmailDeliveryError, FakeEmailProvider
from app.modules.notifications.models.operational_notification_outbox_models import OperationalNotificationOutbox
from smoke_operational_email import (
    EXPECTED_COLUMNS,
    audit_outbox_schema,
    main,
    run_single_smoke,
)

import_all_models()


class OperationalEmailSmokeTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.original_enabled = settings.ADMIN_EMAIL_ENABLED
        self.original_recipient = settings.ADMINISTRATIVE_OPERATIONAL_EMAIL
        self.original_sender = settings.EMAIL_FROM_ADDRESS
        settings.ADMIN_EMAIL_ENABLED = True
        settings.ADMINISTRATIVE_OPERATIONAL_EMAIL = "ops@example.test"
        settings.EMAIL_FROM_ADDRESS = "feedgo@example.test"

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        settings.ADMIN_EMAIL_ENABLED = self.original_enabled
        settings.ADMINISTRATIVE_OPERATIONAL_EMAIL = self.original_recipient
        settings.EMAIL_FROM_ADDRESS = self.original_sender

    def test_audit_is_read_only_when_table_is_missing(self):
        before = set(inspect(self.engine).get_table_names())
        result = audit_outbox_schema(self.engine)
        after = set(inspect(self.engine).get_table_names())
        self.assertEqual(before, after)
        self.assertFalse(result.table_present)

    def test_audit_confirms_physical_contract_without_mutation(self):
        Base.metadata.create_all(self.engine)
        result = audit_outbox_schema(self.engine)
        self.assertTrue(result.table_present)
        self.assertTrue(result.metadata_match)
        self.assertTrue(result.unique_deduplication)
        self.assertEqual(len(EXPECTED_COLUMNS), 19)

    def test_gate_is_exact_and_creates_nothing_when_rejected(self):
        Base.metadata.create_all(self.engine)
        with self.assertRaises(PermissionError):
            run_single_smoke(db=self.db, provider=FakeEmailProvider(), gate_value="SEND-ONE")
        self.assertEqual(self.db.query(OperationalNotificationOutbox).count(), 0)

    def test_smoke_sends_exactly_one_row_through_fake_provider(self):
        Base.metadata.create_all(self.engine)
        provider = FakeEmailProvider()
        result = run_single_smoke(db=self.db, provider=provider, gate_value="send-one", smoke_id="smoke-test-1")
        self.assertTrue(result.delivered)
        self.assertEqual(result.status, "sent")
        self.assertEqual(result.attempt_count, 1)
        self.assertTrue(result.external_reference_present)
        self.assertEqual(len(provider.messages), 1)
        rows = self.db.query(OperationalNotificationOutbox).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].event_type, "operations.email.smoke")

    def test_failure_is_single_attempt_without_automatic_retry(self):
        Base.metadata.create_all(self.engine)
        provider = FakeEmailProvider(EmailDeliveryError("provider_timeout", retryable=True))
        result = run_single_smoke(db=self.db, provider=provider, gate_value="send-one", smoke_id="smoke-test-2")
        self.assertFalse(result.delivered)
        self.assertEqual(result.attempt_count, 1)
        self.assertEqual(result.status, "retryable_failed")
        self.assertFalse(result.external_reference_present)
        self.assertEqual(self.db.query(OperationalNotificationOutbox).count(), 1)

    def test_cli_without_gate_is_sanitized_and_does_not_expose_configuration(self):
        output, errors = io.StringIO(), io.StringIO()
        with patch.dict("os.environ", {}, clear=True), redirect_stdout(output), redirect_stderr(errors):
            result = main(["--send-one"])
        serialized = (output.getvalue() + errors.getvalue()).lower()
        self.assertEqual(result, 2)
        self.assertIn("explicit_gate_required", serialized)
        self.assertNotIn("example.test", serialized)
        self.assertNotIn("api_key", serialized)


if __name__ == "__main__":
    unittest.main()
