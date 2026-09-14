import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from app.core.database import Base
from app.core.auth import crear_token_jwt_versionado, validar_token_para_logout
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import FeedGoSession
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.feedgo_session_services import (
    create_feedgo_session,
    revoke_feedgo_session,
    revoke_user_feedgo_sessions,
)
from tests.mysql_stage97_test_support import isolated_mysql_test_engine
import migrate_feedgo_session_contract as migration


import_all_models()


class FeedGoSessionMySQLConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session = isolated_mysql_test_engine()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.now = datetime.now(timezone.utc)
        db = self.Session()
        db.add(Usuario(id=1, email="one@example.com", hashed_password="$2b$one"))
        db.commit()
        for sid in ("one", "two", "three"):
            create_feedgo_session(
                db, usuario_id=1, authentication_method="password",
                sid_factory=lambda value=sid: value, clock=lambda: self.now,
            )
        db.commit(); db.close()

    def test_concurrent_bulk_revocation_is_idempotent_without_partial_state(self):
        barrier = threading.Barrier(2)

        def revoke():
            db = self.Session()
            try:
                barrier.wait(timeout=5)
                count = revoke_user_feedgo_sessions(
                    db, usuario_id=1, clock=lambda: self.now + timedelta(seconds=1)
                )
                db.commit()
                return count
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            counts = list(executor.map(lambda _: revoke(), range(2)))
        self.assertEqual(sum(counts), 3)
        db = self.Session()
        self.assertEqual(db.query(FeedGoSession).filter(FeedGoSession.revoked_at.is_(None)).count(), 0)
        db.close()

    def test_two_concurrent_logouts_revoke_one_session_once(self):
        db = self.Session()
        session = db.get(FeedGoSession, "one")
        token = crear_token_jwt_versionado(
            usuario_id=1,
            sid=session.id,
            issued_at=session.issued_at,
            expires_at=session.expires_at,
        )
        db.close()
        barrier = threading.Barrier(2)

        def logout():
            worker = self.Session()
            try:
                barrier.wait(timeout=5)
                context = validar_token_para_logout(token, worker)
                changed = revoke_feedgo_session(
                    worker, sid=context.sid, usuario_id=context.usuario_id,
                    clock=lambda: self.now + timedelta(seconds=1),
                )
                worker.commit()
                return changed
            finally:
                worker.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: logout(), range(2)))
        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 1)
        db = self.Session()
        self.assertIsNotNone(db.get(FeedGoSession, "one").revoked_at)
        db.close()

    def test_migration_recognizes_partial_state_and_is_idempotent(self):
        with self.engine.begin() as connection:
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertEqual(first["changes"], [])
        self.assertEqual(second["changes"], [])

    def test_migration_from_schema_without_contract_is_idempotent(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                f"DROP INDEX {migration.ACTIVE_INDEX} ON feedgo_sessions"
            )
            for name in migration.CHECKS:
                connection.exec_driver_sql(
                    f"ALTER TABLE feedgo_sessions DROP CHECK {name}"
                )
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertEqual(
            set(first["changes"]),
            {migration.ACTIVE_INDEX, *migration.CHECKS},
        )
        self.assertEqual(second["changes"], [])


if __name__ == "__main__":
    unittest.main()
