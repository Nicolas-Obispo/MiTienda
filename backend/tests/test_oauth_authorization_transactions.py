import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import migrate_identity_foundation as identity_foundation_migration
import migrate_google_identity_foundation as google_identity_migration
from app.core.config import Settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import (
    ExternalIdentity,
    OAuthAuthorizationTransaction,
    PasswordCredential,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.schemas.usuarios_schemas import UsuarioLogin
from app.modules.users.services.feedgo_session_services import create_feedgo_session
from app.modules.users.services.oauth_authorization_transaction_services import (
    OAuthAuthorizationTransactionError,
    create_oauth_authorization_transaction,
    invalidate_oauth_authorization_transaction,
    invalidate_expired_oauth_authorization_transactions,
    validate_and_consume_oauth_authorization_transaction,
    claim_oauth_authorization_transaction_by_state,
)
from app.modules.users.services.usuarios_services import autenticar_usuario


import_all_models()


class OAuthAuthorizationTransactionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.now = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
        db = self.Session()
        db.add_all(
            [
                Usuario(
                    id=1,
                    email="password@example.com",
                    email_canonical="password@example.com",
                    hashed_password="legacy-hash",
                ),
                Usuario(
                    id=2,
                    email="google-only@example.com",
                    email_canonical="google-only@example.com",
                    hashed_password=None,
                ),
            ]
        )
        db.add(PasswordCredential(usuario_id=1, password_hash="legacy-hash", hash_version="bcrypt"))
        db.commit()
        db.close()

    def tearDown(self):
        self.engine.dispose()

    def create(self, db, **kwargs):
        return create_oauth_authorization_transaction(
            db,
            provider="google",
            purpose="signup",
            clock=lambda: self.now,
            **kwargs,
        )

    def test_google_only_user_is_valid_but_cannot_password_login(self):
        db = self.Session()
        google_only = db.get(Usuario, 2)
        self.assertIsNone(google_only.hashed_password)
        self.assertIsNone(db.get(PasswordCredential, 2))
        self.assertIsNone(
            autenticar_usuario(
                db,
                UsuarioLogin(email="google-only@example.com", password="anything"),
            )
        )
        db.close()

    def test_existing_identity_foundation_migration_tolerates_google_only_users(self):
        db = self.Session()
        with db.begin():
            result = identity_foundation_migration.upgrade(db.connection())
        self.assertEqual(result["backfill"]["password_credentials"], 0)
        self.assertEqual(result["preflight"]["password_credentials_pendientes_ids"], [])
        db.close()

    def test_external_identity_has_one_provider_per_user_and_stable_subject_unique(self):
        db = self.Session()
        db.add(ExternalIdentity(usuario_id=1, provider="google", provider_subject="subject-one"))
        db.commit()
        db.add(ExternalIdentity(usuario_id=1, provider="google", provider_subject="subject-two"))
        with self.assertRaises(IntegrityError):
            db.commit()
        db.rollback()
        db.add(ExternalIdentity(usuario_id=2, provider="google", provider_subject="subject-one"))
        with self.assertRaises(IntegrityError):
            db.commit()
        db.rollback()
        uniques = {
            tuple(item.get("column_names") or [])
            for item in inspect(self.engine).get_unique_constraints("external_identities")
        }
        self.assertIn(("usuario_id", "provider"), uniques)
        self.assertIn(("provider", "provider_subject"), uniques)
        db.close()

    def test_create_persists_only_digests_for_presented_state_and_nonce(self):
        db = self.Session()
        material = self.create(db, return_to="/perfil?tab=security#ignored")
        transaction = db.get(OAuthAuthorizationTransaction, material.transaction_id)
        self.assertNotEqual(transaction.state_digest, material.state)
        self.assertNotEqual(transaction.nonce_digest, material.nonce)
        self.assertEqual(transaction.pkce_challenge, material.pkce_challenge)
        self.assertFalse(hasattr(material, "pkce_verifier"))
        self.assertIsNotNone(transaction.pkce_verifier)
        self.assertEqual(transaction.return_to, "/perfil?tab=security")
        self.assertEqual(transaction.expires_at - transaction.created_at, timedelta(minutes=10))
        columns = set(OAuthAuthorizationTransaction.__table__.columns)
        self.assertFalse(
            {
                "authorization_code",
                "access_token",
                "refresh_token",
                "id_token",
                "provider_payload",
            }
            & columns
        )
        db.rollback()
        db.close()

    def test_model_migration_constraints_and_fail_closed_defaults_match(self):
        table = OAuthAuthorizationTransaction.__table__
        checks = {
            constraint.name
            for constraint in table.constraints
            if constraint.__class__.__name__ == "CheckConstraint"
        }
        uniques = {
            tuple(column.name for column in constraint.columns)
            for constraint in table.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        }
        self.assertEqual(checks, set(google_identity_migration.TRANSACTION_CHECKS))
        self.assertEqual(uniques, set(google_identity_migration.TRANSACTION_UNIQUES.values()))
        self.assertFalse(Settings.model_fields["GOOGLE_IDENTITY_ENABLED"].default)
        self.assertEqual(
            Settings.model_fields["GOOGLE_OAUTH_TRANSACTION_TTL_SECONDS"].default,
            600,
        )

    def test_transaction_is_one_use_and_replay_is_rejected(self):
        db = self.Session()
        material = self.create(db)
        db.commit()
        consumed = validate_and_consume_oauth_authorization_transaction(
            db,
            transaction_id=material.transaction_id,
            state=material.state,
            nonce=material.nonce,
            provider="google",
            purpose="signup",
            clock=lambda: self.now + timedelta(seconds=1),
        )
        self.assertIsNotNone(consumed.consumed_at)
        self.assertIsNone(consumed.pkce_verifier)
        db.commit()
        with self.assertRaises(OAuthAuthorizationTransactionError) as replay:
            validate_and_consume_oauth_authorization_transaction(
                db,
                transaction_id=material.transaction_id,
                state=material.state,
                nonce=material.nonce,
                provider="google",
                purpose="signup",
                clock=lambda: self.now + timedelta(seconds=2),
            )
        self.assertEqual(replay.exception.code, "invalid_transaction")
        db.rollback()
        db.close()

    def test_expiry_invalidates_without_frontend_participation(self):
        db = self.Session()
        material = self.create(db)
        db.commit()
        self.assertEqual(
            invalidate_expired_oauth_authorization_transactions(
                db, clock=lambda: self.now + timedelta(minutes=10)
            ),
            1,
        )
        db.commit()
        transaction = db.get(OAuthAuthorizationTransaction, material.transaction_id)
        self.assertEqual(transaction.invalidation_reason, "expired")
        self.assertIsNone(transaction.pkce_verifier)
        db.close()

    def test_validation_of_expired_transaction_clears_verifier_in_same_uow(self):
        db = self.Session()
        material = self.create(db)
        db.commit()
        with self.assertRaises(OAuthAuthorizationTransactionError):
            validate_and_consume_oauth_authorization_transaction(
                db,
                transaction_id=material.transaction_id,
                state=material.state,
                nonce=material.nonce,
                provider="google",
                purpose="signup",
                clock=lambda: self.now + timedelta(minutes=10),
            )
        db.commit()
        transaction = db.get(OAuthAuthorizationTransaction, material.transaction_id)
        self.assertEqual(transaction.invalidation_reason, "expired")
        self.assertIsNone(transaction.pkce_verifier)
        db.close()

    def test_nonce_is_constant_time_validated_and_explicit_invalidation_clears_verifier(self):
        db = self.Session()
        material = self.create(db)
        db.commit()
        with self.assertRaises(OAuthAuthorizationTransactionError):
            validate_and_consume_oauth_authorization_transaction(
                db,
                transaction_id=material.transaction_id,
                state=material.state,
                nonce="wrong-nonce",
                provider="google",
                purpose="signup",
                clock=lambda: self.now + timedelta(seconds=1),
            )
        self.assertTrue(
            invalidate_oauth_authorization_transaction(
                db,
                transaction_id=material.transaction_id,
                reason="superseded",
                clock=lambda: self.now + timedelta(seconds=2),
            )
        )
        db.commit()
        transaction = db.get(OAuthAuthorizationTransaction, material.transaction_id)
        self.assertIsNone(transaction.pkce_verifier)
        self.assertEqual(transaction.invalidation_reason, "superseded")
        with self.assertRaises(OAuthAuthorizationTransactionError):
            validate_and_consume_oauth_authorization_transaction(
                db,
                transaction_id=material.transaction_id,
                state=material.state,
                nonce=material.nonce,
                provider="google",
                purpose="signup",
                clock=lambda: self.now + timedelta(seconds=3),
            )
        db.close()

    def test_link_requires_matching_user_and_current_feedgo_session(self):
        db = self.Session()
        session = create_feedgo_session(
            db,
            usuario_id=1,
            authentication_method="password",
            clock=lambda: self.now,
        )
        db.commit()
        material = create_oauth_authorization_transaction(
            db,
            provider="google",
            purpose="link",
            usuario_id=1,
            feedgo_session_id=session.id,
            clock=lambda: self.now,
        )
        db.commit()
        with self.assertRaises(OAuthAuthorizationTransactionError):
            validate_and_consume_oauth_authorization_transaction(
                db,
                transaction_id=material.transaction_id,
                state=material.state,
                nonce=material.nonce,
                provider="google",
                purpose="link",
                usuario_id=2,
                feedgo_session_id=session.id,
                clock=lambda: self.now + timedelta(seconds=1),
            )
        transaction = validate_and_consume_oauth_authorization_transaction(
            db,
            transaction_id=material.transaction_id,
            state=material.state,
            nonce=material.nonce,
            provider="google",
            purpose="link",
            usuario_id=1,
            feedgo_session_id=session.id,
            clock=lambda: self.now + timedelta(seconds=1),
        )
        self.assertEqual(transaction.usuario_id, 1)
        db.rollback()
        db.close()

    def test_invalid_return_to_and_invalid_purpose_are_rejected(self):
        db = self.Session()
        with self.assertRaises(OAuthAuthorizationTransactionError):
            self.create(db, return_to="https://attacker.invalid")
        for unsafe in (
            "//attacker.invalid/path",
            "/\\attacker.invalid/path",
            "/%5c%5cattacker.invalid/path",
            "/%252f%252fattacker.invalid/path",
        ):
            with self.assertRaises(OAuthAuthorizationTransactionError):
                self.create(db, return_to=unsafe)
        with self.assertRaises(OAuthAuthorizationTransactionError):
            create_oauth_authorization_transaction(
                db, provider="google", purpose="other", clock=lambda: self.now
            )
        with self.assertRaises(OAuthAuthorizationTransactionError):
            create_oauth_authorization_transaction(
                db,
                provider="google",
                purpose="signup",
                usuario_id=1,
                feedgo_session_id="not-allowed",
                clock=lambda: self.now,
            )
        with self.assertRaises(OAuthAuthorizationTransactionError):
            create_oauth_authorization_transaction(
                db,
                provider="google",
                purpose="login",
                ttl=timedelta(seconds=601),
                clock=lambda: self.now,
            )
        safe = self.create(
            db,
            return_to="/perfil?token=secret&state=secret&tab=security#removed",
        )
        self.assertEqual(
            db.get(OAuthAuthorizationTransaction, safe.transaction_id).return_to,
            "/perfil?tab=security",
        )
        double_encoded = self.create(
            db,
            return_to="/perfil?%2574oken=secret&%256eonce=secret&tab=security",
        )
        self.assertEqual(
            db.get(
                OAuthAuthorizationTransaction,
                double_encoded.transaction_id,
            ).return_to,
            "/perfil?tab=security",
        )
        db.rollback()
        db.close()

    def test_callback_claim_rejects_link_purpose_and_expired_state(self):
        db = self.Session()
        session = create_feedgo_session(
            db,
            usuario_id=1,
            authentication_method="password",
            clock=lambda: self.now,
        )
        link = create_oauth_authorization_transaction(
            db,
            provider="google",
            purpose="link",
            usuario_id=1,
            feedgo_session_id=session.id,
            clock=lambda: self.now,
        )
        expired = self.create(db)
        db.commit()
        with self.assertRaises(OAuthAuthorizationTransactionError):
            claim_oauth_authorization_transaction_by_state(
                db,
                state=link.state,
                provider="google",
                allowed_purposes=frozenset({"login", "signup"}),
                clock=lambda: self.now + timedelta(seconds=1),
            )
        with self.assertRaises(OAuthAuthorizationTransactionError):
            claim_oauth_authorization_transaction_by_state(
                db,
                state=expired.state,
                provider="google",
                allowed_purposes=frozenset({"login", "signup"}),
                clock=lambda: self.now + timedelta(minutes=10),
            )
        db.commit()
        transaction = db.get(OAuthAuthorizationTransaction, expired.transaction_id)
        self.assertEqual(transaction.invalidation_reason, "expired")
        db.close()


if __name__ == "__main__":
    unittest.main()
