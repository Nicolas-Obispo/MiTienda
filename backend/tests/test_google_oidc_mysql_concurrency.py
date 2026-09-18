import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import threading
import unittest

from sqlalchemy import inspect
from sqlalchemy.exc import DBAPIError, IntegrityError

import migrate_google_oidc as migration
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import (
    ExternalIdentity,
    OAuthAuthorizationTransaction,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.authentication_method_services import (
    AuthenticationMethodError,
    link_google_identity,
)
from app.modules.users.services.feedgo_session_services import create_feedgo_session
from app.modules.users.services.google_oidc_services import GoogleOidcIdentity
from app.modules.users.services.oauth_authorization_transaction_services import (
    ClaimedOAuthAuthorizationTransaction,
    OAuthAuthorizationTransactionError,
    claim_oauth_authorization_transaction_by_state,
    create_oauth_authorization_transaction,
)
from app.modules.users.services.oauth_session_delivery_services import (
    AUTHENTICATION_UNAVAILABLE,
    OAuthSessionDeliveryError,
    consume_oauth_session_delivery,
    create_oauth_session_delivery,
)
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


import_all_models()


@unittest.skipUnless(
    os.environ.get("FEEDGO_STAGE97_TEST_DATABASE_URL"),
    "requiere FEEDGO_STAGE97_TEST_DATABASE_URL aislada",
)
class GoogleOidcMySQLConcurrencyTests(unittest.TestCase):
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
        self.now = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)

    def test_callback_claim_has_exactly_one_winner(self):
        db = self.Session()
        material = create_oauth_authorization_transaction(
            db,
            provider="google",
            purpose="login",
            clock=lambda: self.now,
        )
        db.commit()
        db.close()
        barrier = threading.Barrier(2)

        def claim():
            worker = self.Session()
            try:
                barrier.wait(timeout=5)
                claim_oauth_authorization_transaction_by_state(
                    worker,
                    state=material.state,
                    provider="google",
                    allowed_purposes=frozenset({"login", "signup"}),
                    clock=lambda: self.now + timedelta(seconds=1),
                )
                worker.commit()
                return True
            except OAuthAuthorizationTransactionError:
                worker.rollback()
                return False
            finally:
                worker.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))
        self.assertEqual(results.count(True), 1)

    def test_link_callback_claim_has_exactly_one_winner(self):
        db = self.Session()
        db.add(Usuario(id=1, email="link@test.local", hashed_password=None))
        db.flush()
        session = create_feedgo_session(
            db,
            usuario_id=1,
            authentication_method="password",
            clock=lambda: self.now,
            ttl=timedelta(hours=1),
            sid_factory=lambda: "link-password-session",
        )
        material = create_oauth_authorization_transaction(
            db,
            provider="google",
            purpose="link",
            usuario_id=1,
            feedgo_session_id=session.id,
            clock=lambda: self.now,
        )
        db.commit()
        db.close()
        barrier = threading.Barrier(2)

        def claim():
            worker = self.Session()
            try:
                barrier.wait(timeout=5)
                claim_oauth_authorization_transaction_by_state(
                    worker,
                    state=material.state,
                    provider="google",
                    allowed_purposes=frozenset({"link"}),
                    clock=lambda: self.now + timedelta(seconds=1),
                )
                worker.commit()
                return True
            except OAuthAuthorizationTransactionError:
                worker.rollback()
                return False
            finally:
                worker.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))
        self.assertEqual(results.count(True), 1)

    def test_same_google_subject_links_to_exactly_one_user(self):
        db = self.Session()
        for user_id in (1, 2):
            db.add(
                Usuario(
                    id=user_id,
                    email=f"link-{user_id}@test.local",
                    hashed_password=None,
                )
            )
            db.flush()
            create_feedgo_session(
                db,
                usuario_id=user_id,
                authentication_method="password",
                clock=lambda: self.now,
                ttl=timedelta(hours=1),
                sid_factory=lambda user_id=user_id: f"link-session-{user_id}",
            )
        db.commit()
        db.close()
        barrier = threading.Barrier(2)

        def link(user_id):
            worker = self.Session()
            claim = ClaimedOAuthAuthorizationTransaction(
                transaction_id=f"link-transaction-{user_id}",
                purpose="link",
                nonce_digest="1" * 64,
                pkce_verifier="verifier",
                return_to=None,
                legal_document_set_digest=None,
                legal_accepted_at=None,
                usuario_id=user_id,
                feedgo_session_id=f"link-session-{user_id}",
            )
            try:
                barrier.wait(timeout=5)
                link_google_identity(
                    worker,
                    claim=claim,
                    identity=GoogleOidcIdentity(
                        subject="shared-subject",
                        email="shared@test.local",
                        email_verified=True,
                    ),
                    clock=lambda: self.now + timedelta(seconds=1),
                )
                worker.commit()
                return True
            except (AuthenticationMethodError, IntegrityError, DBAPIError):
                worker.rollback()
                return False
            finally:
                worker.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(link, (1, 2)))
        self.assertEqual(results.count(True), 1)
        db = self.Session()
        self.assertEqual(
            db.query(ExternalIdentity)
            .filter(
                ExternalIdentity.provider == "google",
                ExternalIdentity.provider_subject == "shared-subject",
            )
            .count(),
            1,
        )
        db.close()

    def test_migration_is_clean_and_idempotent(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE oauth_session_delivery_handles")
            connection.exec_driver_sql(
                "ALTER TABLE account_action_rate_limits "
                "DROP CHECK ck_account_action_rate_limits_action"
            )
            connection.exec_driver_sql(
                "ALTER TABLE account_action_rate_limits ADD CONSTRAINT "
                "ck_account_action_rate_limits_action CHECK (action IN "
                "('email_verification','password_reset','current_password',"
                "'phone_verification'))"
            )
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertIn("oauth_session_delivery_handles", first["changes"])
        self.assertIn(
            "ck_account_action_rate_limits_action.google_oauth", first["changes"]
        )
        self.assertEqual(second["changes"], [])
        self.assertIn(
            "oauth_session_delivery_handles",
            inspect(self.engine).get_table_names(),
        )

    def test_migration_recovers_empty_partial_result_table_idempotently(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE oauth_session_delivery_handles")
            connection.exec_driver_sql(
                "CREATE TABLE oauth_session_delivery_handles "
                "(id VARCHAR(64) NOT NULL PRIMARY KEY)"
            )
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertIn(
            "oauth_session_delivery_handles.recovered",
            first["changes"],
        )
        self.assertEqual(second["changes"], [])
        expected = set(
            Base.metadata.tables["oauth_session_delivery_handles"].columns.keys()
        )
        actual = {
            column["name"]
            for column in inspect(self.engine).get_columns(
                "oauth_session_delivery_handles"
            )
        }
        self.assertEqual(actual, expected)

    def test_migration_never_rebuilds_partial_result_table_with_data(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE oauth_session_delivery_handles")
            connection.exec_driver_sql(
                "CREATE TABLE oauth_session_delivery_handles "
                "(id VARCHAR(64) NOT NULL PRIMARY KEY)"
            )
            connection.exec_driver_sql(
                "INSERT INTO oauth_session_delivery_handles (id) VALUES ('existing')"
            )
            with self.assertRaises(migration.GoogleOidcMigrationError):
                migration.upgrade(connection)
            count = connection.exec_driver_sql(
                "SELECT COUNT(*) FROM oauth_session_delivery_handles"
            ).scalar_one()
        self.assertEqual(count, 1)

    def test_result_handle_has_exactly_one_consumer(self):
        db = self.Session()
        db.add(Usuario(id=1, email="oauth@test.local", hashed_password=None))
        material = create_oauth_authorization_transaction(
            db,
            provider="google",
            purpose="login",
            clock=lambda: self.now,
        )
        transaction = db.get(OAuthAuthorizationTransaction, material.transaction_id)
        transaction.consumed_at = self.now.replace(tzinfo=None)
        transaction.pkce_verifier = None
        delivery = create_oauth_session_delivery(
            db,
            transaction_id=material.transaction_id,
            outcome=AUTHENTICATION_UNAVAILABLE,
            clock=lambda: self.now,
        )
        db.commit()
        db.close()
        barrier = threading.Barrier(2)

        def consume():
            worker = self.Session()
            try:
                barrier.wait(timeout=5)
                consume_oauth_session_delivery(
                    worker,
                    handle=delivery.handle,
                    allowed_purposes=frozenset({"login"}),
                    clock=lambda: self.now + timedelta(seconds=1),
                )
                worker.commit()
                return True
            except OAuthSessionDeliveryError:
                worker.rollback()
                return False
            finally:
                worker.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: consume(), range(2)))
        self.assertEqual(results.count(True), 1)


if __name__ == "__main__":
    unittest.main()
