import unittest

from sqlalchemy import create_engine, inspect

import migrate_operational_notification_outbox as migration


class OperationalNotificationOutboxMigrationTests(unittest.TestCase):
    def test_upgrade_is_idempotent(self):
        engine = create_engine("sqlite://")
        with engine.begin() as connection:
            self.assertEqual(migration.upgrade(connection), [migration.TABLE_NAME])
            self.assertEqual(migration.upgrade(connection), [])
            inspector = inspect(connection)
            self.assertIn(migration.TABLE_NAME, inspector.get_table_names())
            columns = {column["name"] for column in inspector.get_columns(migration.TABLE_NAME)}
            self.assertTrue({"event_type", "deduplication_key", "payload_json", "status", "attempt_count", "last_error_code"} <= columns)
            unique_columns = {
                tuple(constraint["column_names"])
                for constraint in inspector.get_unique_constraints(migration.TABLE_NAME)
            }
            self.assertIn(("deduplication_key",), unique_columns)

    def test_upgrade_adds_dispatch_columns_to_existing_table(self):
        engine = create_engine("sqlite://")
        with engine.begin() as connection:
            connection.exec_driver_sql("""
                CREATE TABLE operational_notification_outbox (
                    id INTEGER PRIMARY KEY,
                    event_type VARCHAR(80) NOT NULL,
                    aggregate_type VARCHAR(40) NOT NULL,
                    aggregate_id VARCHAR(80) NOT NULL,
                    deduplication_key VARCHAR(190) NOT NULL UNIQUE,
                    payload_json TEXT NOT NULL,
                    payload_fingerprint VARCHAR(64) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    next_attempt_at DATETIME NULL,
                    provider_reference VARCHAR(190) NULL,
                    last_error_code VARCHAR(80) NULL,
                    created_at DATETIME NOT NULL,
                    sent_at DATETIME NULL
                )
            """)
            connection.exec_driver_sql("""
                INSERT INTO operational_notification_outbox (
                    id, event_type, aggregate_type, aggregate_id,
                    deduplication_key, payload_json, payload_fingerprint,
                    status, attempt_count, created_at
                ) VALUES (
                    1, 'moderation.report.created', 'moderation_report', '1',
                    'legacy-key', '{}', 'fingerprint', 'pending', 0,
                    CURRENT_TIMESTAMP
                )
            """)
            changes = migration.upgrade(connection)
            self.assertEqual(migration.upgrade(connection), [])
            self.assertTrue({
                "lease_expires_at", "claimed_by", "suppressed_at",
                "suppressed_by", "suppression_reason",
                "ix_operational_notification_outbox_dispatch",
            } <= set(changes))
            inspector = inspect(connection)
            columns = {column["name"] for column in inspector.get_columns(migration.TABLE_NAME)}
            self.assertTrue({"lease_expires_at", "claimed_by", "suppressed_at", "suppressed_by", "suppression_reason"} <= columns)
            self.assertIn(
                "ix_operational_notification_outbox_dispatch",
                {index["name"] for index in inspector.get_indexes(migration.TABLE_NAME)},
            )
            preserved = connection.exec_driver_sql(
                "SELECT status, deduplication_key FROM operational_notification_outbox WHERE id = 1"
            ).one()
            self.assertEqual(tuple(preserved), ("pending", "legacy-key"))


if __name__ == "__main__":
    unittest.main()
