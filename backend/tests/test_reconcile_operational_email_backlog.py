import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.communications.services.operational_email_services import (
    OperationalEmailConflictError,
    reconcile_pre_activation_report_intentions,
)
from app.modules.notifications.models.operational_notification_outbox_models import OperationalNotificationOutbox
from app.modules.notifications.services.operational_notification_services import enqueue_report_created
from reconcile_operational_email_backlog import (
    GATE_ENV,
    GATE_VALUE,
    SUPPRESSED_BY,
    audit_backlog,
    main,
)


import_all_models()


class ReconcileOperationalEmailBacklogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        db = self.Session()
        for report_id in (2, 3, 4, 5):
            enqueue_report_created(
                db=db,
                report=SimpleNamespace(
                    id=report_id, recurso_tipo="comercio",
                    recurso_id=report_id, motivo="spam",
                ),
            )
        db.commit()
        db.close()

    def test_audit_is_read_only_and_accepts_only_expected_three(self):
        db = self.Session()
        before = [(row.id, row.status, row.attempt_count) for row in db.query(OperationalNotificationOutbox).order_by(OperationalNotificationOutbox.id)]
        result = audit_backlog(db=db, report_ids=frozenset({2, 3, 4}))
        after = [(row.id, row.status, row.attempt_count) for row in db.query(OperationalNotificationOutbox).order_by(OperationalNotificationOutbox.id)]
        db.close()
        self.assertTrue(result.valid)
        self.assertEqual((result.matched, result.pending, result.suppressed), (3, 3, 0))
        self.assertEqual(before, after)

    def test_report_five_is_rejected_before_opening_database_session(self):
        output = io.StringIO()
        with patch("reconcile_operational_email_backlog.SessionLocal", side_effect=AssertionError("must-not-open")), redirect_stderr(output):
            result = main(["--audit", "--report-ids", "2", "3", "4", "5"])
        self.assertEqual(result, 2)
        self.assertIn("allowlist_required", output.getvalue())

    def test_suppress_requires_exact_gate(self):
        output = io.StringIO()
        with patch.dict("os.environ", {}, clear=True), patch("reconcile_operational_email_backlog.SessionLocal", side_effect=AssertionError("must-not-open")), redirect_stderr(output):
            result = main(["--suppress", "--report-ids", "2", "3", "4"])
        self.assertEqual(result, 2)
        self.assertIn("explicit_gate_required", output.getvalue())

    def test_atomic_suppression_preserves_rows_payloads_and_deduplication(self):
        db = self.Session()
        before = {
            row.aggregate_id: (row.payload_json, row.payload_fingerprint, row.deduplication_key)
            for row in db.query(OperationalNotificationOutbox).all()
        }
        result = reconcile_pre_activation_report_intentions(
            db=db, report_ids=frozenset({2, 3, 4}),
            suppressed_by=SUPPRESSED_BY,
        )
        self.assertEqual((result.matched, result.suppressed_now, result.already_suppressed), (3, 3, 0))
        rows = db.query(OperationalNotificationOutbox).order_by(OperationalNotificationOutbox.id).all()
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertEqual(
                (row.payload_json, row.payload_fingerprint, row.deduplication_key),
                before[row.aggregate_id],
            )
            if row.aggregate_id in {"2", "3", "4"}:
                self.assertEqual(row.status, "suppressed")
                self.assertEqual(row.suppression_reason, "pre_activation_synthetic")
                self.assertEqual(row.attempt_count, 0)
            else:
                self.assertEqual(row.aggregate_id, "5")
                self.assertEqual(row.status, "pending")
        db.close()

    def test_repeated_suppression_is_idempotent(self):
        db = self.Session()
        reconcile_pre_activation_report_intentions(
            db=db, report_ids=frozenset({2, 3, 4}), suppressed_by=SUPPRESSED_BY,
        )
        second = reconcile_pre_activation_report_intentions(
            db=db, report_ids=frozenset({2, 3, 4}), suppressed_by=SUPPRESSED_BY,
        )
        self.assertEqual((second.suppressed_now, second.already_suppressed), (0, 3))
        self.assertEqual(db.query(OperationalNotificationOutbox).count(), 4)
        db.close()

    def test_validation_failure_rolls_back_all_three(self):
        db = self.Session()
        invalid = db.query(OperationalNotificationOutbox).filter_by(aggregate_id="3").one()
        invalid.attempt_count = 1
        db.commit()
        with self.assertRaises(OperationalEmailConflictError):
            reconcile_pre_activation_report_intentions(
                db=db, report_ids=frozenset({2, 3, 4}), suppressed_by=SUPPRESSED_BY,
            )
        statuses = {
            row.aggregate_id: row.status
            for row in db.query(OperationalNotificationOutbox).all()
        }
        self.assertEqual(statuses, {"2": "pending", "3": "pending", "4": "pending", "5": "pending"})
        db.close()

    def test_cli_suppression_and_repeat_have_sanitized_output(self):
        first_output = io.StringIO()
        with patch.dict("os.environ", {GATE_ENV: GATE_VALUE}, clear=True), patch("reconcile_operational_email_backlog.SessionLocal", self.Session), redirect_stdout(first_output):
            first = main(["--suppress", "--report-ids", "2", "3", "4"])
        second_output = io.StringIO()
        with patch.dict("os.environ", {GATE_ENV: GATE_VALUE}, clear=True), patch("reconcile_operational_email_backlog.SessionLocal", self.Session), redirect_stdout(second_output):
            second = main(["--suppress", "--report-ids", "2", "3", "4"])
        self.assertEqual((first, second), (0, 0))
        self.assertIn("suppressed_now=3", first_output.getvalue())
        self.assertIn("already_suppressed=3", second_output.getvalue())
        serialized = first_output.getvalue() + second_output.getvalue()
        self.assertNotIn("payload", serialized.lower())
        self.assertNotIn("deduplication", serialized.lower())


if __name__ == "__main__":
    unittest.main()
