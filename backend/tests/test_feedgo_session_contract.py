import re
import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import migrate_feedgo_session_contract as migration
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import ExternalIdentity, FeedGoSession
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.feedgo_session_services import (
    FeedGoSessionInvalidError,
    create_feedgo_session,
    generate_session_id,
    get_valid_feedgo_session,
    revoke_feedgo_session,
    revoke_user_feedgo_sessions,
)


import_all_models()


class FeedGoSessionContractTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.now = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)
        db = self.Session()
        db.add_all([
            Usuario(id=1, email="one@example.com", hashed_password="$2b$one"),
            Usuario(id=2, email="two@example.com", hashed_password="$2b$two"),
        ])
        db.commit()
        db.close()

    def tearDown(self):
        self.engine.dispose()

    def create(self, db, *, user=1, sid=None, ttl=timedelta(minutes=60)):
        return create_feedgo_session(
            db,
            usuario_id=user,
            authentication_method="password",
            ttl=ttl,
            clock=lambda: self.now,
            sid_factory=(lambda: sid) if sid else generate_session_id,
        )

    def test_creation_uses_opaque_unpredictable_sid_and_no_bearer_column(self):
        db = self.Session()
        first = self.create(db)
        second = self.create(db)
        self.assertNotEqual(first.id, second.id)
        self.assertRegex(first.id, re.compile(r"^[A-Za-z0-9_-]{43}$"))
        self.assertEqual(first.expires_at - first.issued_at, timedelta(minutes=60))
        self.assertFalse({"jwt", "token", "bearer"} & set(FeedGoSession.__table__.columns.keys()))
        db.rollback()
        db.close()

    def test_creation_canonicalizes_utc_seconds_and_preserves_exact_ttl(self):
        db = self.Session()
        expected = datetime(2026, 9, 6, 12, 0)
        for microsecond in (0, 499999, 500000, 999999):
            observed = datetime(
                2026, 9, 6, 12, 0, 0, microsecond, tzinfo=timezone.utc
            )
            session = create_feedgo_session(
                db,
                usuario_id=1,
                authentication_method="password",
                ttl=timedelta(minutes=17),
                clock=lambda observed=observed: observed,
            )
            self.assertEqual(session.issued_at, expected)
            self.assertEqual(session.expires_at, expected + timedelta(minutes=17))
            self.assertEqual(session.expires_at - session.issued_at, timedelta(minutes=17))

        argentina = timezone(timedelta(hours=-3))
        local_time = datetime(
            2026, 9, 6, 9, 0, 0, 999999, tzinfo=argentina
        )
        normalized = create_feedgo_session(
            db,
            usuario_id=1,
            authentication_method="password",
            clock=lambda: local_time,
        )
        self.assertEqual(normalized.issued_at, expected)
        self.assertIsNone(normalized.issued_at.tzinfo)
        db.rollback()
        db.close()

    def test_validation_rejects_missing_wrong_user_expired_revoked_and_version(self):
        db = self.Session()
        session = self.create(db, sid="session-one")
        db.commit()
        self.assertEqual(get_valid_feedgo_session(db, sid=session.id, usuario_id=1, clock=lambda: self.now).id, session.id)
        for kwargs in (
            {"sid": "missing"},
            {"sid": session.id, "usuario_id": 2},
            {"sid": session.id, "contract_version": 2},
            {"sid": session.id, "clock": lambda: self.now + timedelta(minutes=60)},
        ):
            with self.assertRaises(FeedGoSessionInvalidError):
                get_valid_feedgo_session(db, **kwargs)
        self.assertTrue(revoke_feedgo_session(db, sid=session.id, clock=lambda: self.now))
        with self.assertRaises(FeedGoSessionInvalidError):
            get_valid_feedgo_session(db, sid=session.id, clock=lambda: self.now)
        db.rollback()
        db.close()

    def test_revoke_all_and_all_except_current_only_touch_active_user_sessions(self):
        db = self.Session()
        current = self.create(db, sid="current")
        other = self.create(db, sid="other")
        second_user = self.create(db, user=2, sid="second-user")
        expired = self.create(db, sid="expired", ttl=timedelta(seconds=1))
        db.commit()
        later = self.now + timedelta(seconds=2)
        self.assertEqual(revoke_user_feedgo_sessions(db, usuario_id=1, except_sid=current.id, clock=lambda: later), 1)
        db.commit()
        db.refresh(current); db.refresh(other); db.refresh(second_user); db.refresh(expired)
        self.assertIsNone(current.revoked_at)
        self.assertIsNotNone(other.revoked_at)
        self.assertIsNone(second_user.revoked_at)
        self.assertIsNone(expired.revoked_at)
        self.assertEqual(revoke_user_feedgo_sessions(db, usuario_id=1, clock=lambda: later), 1)
        db.commit()
        db.refresh(current)
        self.assertIsNotNone(current.revoked_at)
        db.close()

    def test_google_identity_must_exist_belong_to_user_and_match_provider(self):
        db = self.Session()
        identity = ExternalIdentity(
            id=10, usuario_id=1, provider="google", provider_subject="subject"
        )
        wrong_provider = ExternalIdentity(
            id=11, usuario_id=1, provider="oidc", provider_subject="other"
        )
        db.add_all([identity, wrong_provider]); db.commit()
        with self.assertRaises(FeedGoSessionInvalidError):
            create_feedgo_session(
                db, usuario_id=1, authentication_method="google",
                clock=lambda: self.now,
            )
        with self.assertRaises(FeedGoSessionInvalidError):
            create_feedgo_session(
                db, usuario_id=1, authentication_method="password",
                external_identity_id=10, clock=lambda: self.now,
            )
        with self.assertRaises(FeedGoSessionInvalidError):
            create_feedgo_session(
                db, usuario_id=1, authentication_method="google",
                external_identity_id=11, clock=lambda: self.now,
            )
        session = create_feedgo_session(
            db, usuario_id=1, authentication_method="google",
            external_identity_id=10, clock=lambda: self.now,
        )
        self.assertEqual(session.external_identity_id, 10)
        with self.assertRaises(FeedGoSessionInvalidError):
            create_feedgo_session(
                db, usuario_id=2, authentication_method="google",
                external_identity_id=10, clock=lambda: self.now,
            )
        db.rollback(); db.close()

    def test_active_google_session_without_identity_is_invalid(self):
        db = self.Session()
        db.add(ExternalIdentity(
            id=10, usuario_id=1, provider="google", provider_subject="subject"
        ))
        db.commit()
        session = create_feedgo_session(
            db, usuario_id=1, authentication_method="google",
            external_identity_id=10, clock=lambda: self.now,
        )
        db.commit()
        session.external_identity_id = None
        db.commit()
        with self.assertRaises(FeedGoSessionInvalidError):
            get_valid_feedgo_session(db, sid=session.id, clock=lambda: self.now)
        db.close()

    def test_constraints_and_sid_uniqueness_are_physical(self):
        checks = {item["name"] for item in inspect(self.engine).get_check_constraints("feedgo_sessions")}
        self.assertEqual(set(migration.CHECKS), checks)
        indexes = {item["name"] for item in inspect(self.engine).get_indexes("feedgo_sessions")}
        self.assertIn(migration.ACTIVE_INDEX, indexes)
        db = self.Session()
        self.create(db, sid="duplicate"); db.commit()
        with self.assertRaises(IntegrityError):
            self.create(db, user=2, sid="duplicate")
        db.rollback(); db.close()

    def test_migration_is_additive_and_idempotent(self):
        with self.engine.begin() as connection:
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertEqual(first["preflight"], {"sessions": 0, "invalid": 0})
        self.assertEqual(first["changes"], [])
        self.assertEqual(second["changes"], [])

    def test_migration_adds_only_missing_index_to_partial_schema(self):
        engine = create_engine("sqlite://")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE feedgo_sessions ("
                "id VARCHAR(64) PRIMARY KEY, usuario_id INTEGER NOT NULL, "
                "authentication_method VARCHAR(32) NOT NULL, "
                "external_identity_id INTEGER NULL, issued_at DATETIME NOT NULL, "
                "expires_at DATETIME NOT NULL, revoked_at DATETIME NULL, "
                "contract_version INTEGER NOT NULL DEFAULT 1)"
            )
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertEqual(first["changes"], [migration.ACTIVE_INDEX])
        self.assertEqual(second["changes"], [])
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
