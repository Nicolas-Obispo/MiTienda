import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import (
    ExternalIdentity,
    FeedGoSession,
    OAuthAuthorizationTransaction,
    OAuthSessionDeliveryHandle,
    PasswordCredential,
)
from app.modules.users.models.usuarios_documentos_aceptaciones_models import (
    UsuarioDocumentoAceptacion,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.documentos_aceptacion_services import (
    digest_documentos_obligatorios_registro,
)
from app.modules.users.services.google_identity_services import process_google_identity
from app.modules.users.services.google_oidc_services import GoogleOidcIdentity
from app.modules.users.services.oauth_authorization_transaction_services import (
    ClaimedOAuthAuthorizationTransaction,
)
from app.modules.users.services.oauth_session_delivery_services import (
    AUTHENTICATION_UNAVAILABLE,
    OAuthSessionDeliveryError,
    consume_oauth_session_delivery,
)


import_all_models()


class GoogleIdentityLoginSignupTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.now = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.engine.dispose()

    def claim(self, db, purpose="signup", transaction_id="tx"):
        db.add(
            OAuthAuthorizationTransaction(
                id=transaction_id,
                provider="google",
                purpose=purpose,
                state_digest=("1" if purpose == "signup" else "2") * 64,
                nonce_digest=("3" if purpose == "signup" else "4") * 64,
                pkce_verifier=None,
                pkce_challenge="challenge",
                legal_document_set_digest=(
                    digest_documentos_obligatorios_registro()
                    if purpose == "signup"
                    else None
                ),
                legal_accepted_at=self.now if purpose == "signup" else None,
                created_at=self.now,
                expires_at=self.now + timedelta(minutes=10),
                consumed_at=self.now,
            )
        )
        db.flush()
        return ClaimedOAuthAuthorizationTransaction(
            transaction_id=transaction_id,
            purpose=purpose,
            nonce_digest="3" * 64,
            pkce_verifier="verifier",
            return_to="/perfil",
            legal_document_set_digest=(
                digest_documentos_obligatorios_registro()
                if purpose == "signup"
                else None
            ),
            legal_accepted_at=self.now if purpose == "signup" else None,
        )

    def identity(self, subject="subject", email="new@example.com"):
        return GoogleOidcIdentity(
            subject=subject,
            email=email,
            email_verified=True,
        )

    def process(self, db, claim, identity):
        return process_google_identity(
            db,
            claim=claim,
            identity=identity,
            session_ttl=timedelta(hours=1),
            result_ttl=timedelta(minutes=2),
            clock=lambda: self.now,
        )

    def test_signup_creates_google_only_user_legal_identity_and_feedgo_session(self):
        db = self.Session()
        result = self.process(db, self.claim(db), self.identity())
        db.commit()
        usuario = db.query(Usuario).one()
        self.assertIsNone(usuario.hashed_password)
        self.assertIsNone(db.get(PasswordCredential, usuario.id))
        self.assertEqual(usuario.email_verified_at, self.now.replace(tzinfo=None))
        self.assertEqual(usuario.email_verification_source, "google_oidc")
        self.assertIsNone(usuario.fecha_nacimiento)
        self.assertIsNone(usuario.telefono_e164)
        self.assertIsNone(usuario.provincia)
        self.assertIsNone(usuario.ciudad)
        self.assertEqual(db.query(UsuarioDocumentoAceptacion).count(), 2)
        external = db.query(ExternalIdentity).one()
        self.assertEqual((external.provider, external.provider_subject), ("google", "subject"))
        session = db.query(FeedGoSession).one()
        self.assertEqual(session.authentication_method, "google")
        self.assertEqual(session.external_identity_id, external.id)
        delivery = consume_oauth_session_delivery(
            db,
            handle=result.delivery.handle,
            allowed_purposes=frozenset({"signup"}),
            clock=lambda: self.now,
        )
        self.assertEqual(delivery.usuario_id, usuario.id)
        db.close()

    def test_signup_requires_legal_acceptance_timestamp(self):
        db = self.Session()
        claim = self.claim(db)
        claim = ClaimedOAuthAuthorizationTransaction(
            transaction_id=claim.transaction_id,
            purpose=claim.purpose,
            nonce_digest=claim.nonce_digest,
            pkce_verifier=claim.pkce_verifier,
            return_to=claim.return_to,
            legal_document_set_digest=claim.legal_document_set_digest,
            legal_accepted_at=None,
        )
        with self.assertRaisesRegex(RuntimeError, "google_signup_legal_acceptance_invalid"):
            self.process(db, claim, self.identity())
        db.rollback()
        self.assertEqual(db.query(Usuario).count(), 0)
        db.close()

    def test_existing_subject_login_uses_subject_not_email_and_issues_new_session(self):
        db = self.Session()
        user = Usuario(
            email="owner@example.com",
            email_canonical="owner@example.com",
            hashed_password=None,
        )
        db.add(user)
        db.flush()
        external = ExternalIdentity(
            usuario_id=user.id,
            provider="google",
            provider_subject="stable-subject",
            provider_email_snapshot="old@example.com",
            provider_email_verified_snapshot=True,
        )
        db.add(external)
        db.commit()
        claim = self.claim(db, purpose="login", transaction_id="login-tx")
        result = self.process(
            db,
            claim,
            self.identity(subject="stable-subject", email="changed@example.com"),
        )
        db.commit()
        self.assertTrue(result.authenticated)
        self.assertEqual(db.query(Usuario).count(), 1)
        self.assertEqual(db.query(FeedGoSession).one().authentication_method, "google")
        self.assertEqual(external.provider_email_snapshot, "changed@example.com")
        db.close()

    def test_unknown_login_and_signup_email_collision_have_same_safe_outcome(self):
        db = self.Session()
        db.add(
            Usuario(
                email="existing@example.com",
                email_canonical="existing@example.com",
                hashed_password="legacy",
            )
        )
        db.commit()
        login = self.process(
            db,
            self.claim(db, purpose="login", transaction_id="unknown-login"),
            self.identity(subject="unknown", email="nobody@example.com"),
        )
        db.commit()
        signup = self.process(
            db,
            self.claim(db, transaction_id="collision-signup"),
            self.identity(subject="new-subject", email="EXISTING@example.com"),
        )
        db.commit()
        self.assertFalse(login.authenticated)
        self.assertFalse(signup.authenticated)
        outcomes = [row.outcome for row in db.query(OAuthSessionDeliveryHandle).all()]
        self.assertEqual(outcomes, [AUTHENTICATION_UNAVAILABLE] * 2)
        self.assertEqual(db.query(Usuario).count(), 1)
        self.assertEqual(db.query(ExternalIdentity).count(), 0)
        db.close()

    def test_signup_also_detects_legacy_email_without_canonical_backfill(self):
        db = self.Session()
        db.add(
            Usuario(
                email="Legacy@Example.com",
                email_canonical=None,
                hashed_password="legacy",
            )
        )
        db.commit()
        result = self.process(
            db,
            self.claim(db, transaction_id="legacy-collision"),
            self.identity(subject="new-subject", email="legacy@example.com"),
        )
        db.commit()
        self.assertFalse(result.authenticated)
        self.assertEqual(db.query(Usuario).count(), 1)
        self.assertEqual(db.query(ExternalIdentity).count(), 0)
        db.close()

    def test_signup_existing_subject_does_not_turn_into_login(self):
        db = self.Session()
        user = Usuario(email="user@example.com", email_canonical="user@example.com")
        db.add(user)
        db.flush()
        db.add(
            ExternalIdentity(
                usuario_id=user.id,
                provider="google",
                provider_subject="known",
            )
        )
        db.commit()
        result = self.process(
            db,
            self.claim(db, transaction_id="existing-subject"),
            self.identity(subject="known", email="user@example.com"),
        )
        db.commit()
        self.assertFalse(result.authenticated)
        self.assertEqual(db.query(FeedGoSession).count(), 0)
        db.close()

    def test_delivery_is_digest_only_one_use_expiring_and_contains_no_provider_tokens(self):
        db = self.Session()
        result = self.process(db, self.claim(db), self.identity())
        db.commit()
        row = db.query(OAuthSessionDeliveryHandle).one()
        self.assertNotEqual(row.handle_digest, result.delivery.handle)
        self.assertFalse(
            {"access_token", "refresh_token", "id_token", "provider_payload", "jwt"}
            & set(OAuthSessionDeliveryHandle.__table__.columns)
        )
        consume_oauth_session_delivery(
            db,
            handle=result.delivery.handle,
            allowed_purposes=frozenset({"signup"}),
            clock=lambda: self.now,
        )
        db.commit()
        with self.assertRaises(OAuthSessionDeliveryError):
            consume_oauth_session_delivery(
                db,
                handle=result.delivery.handle,
                allowed_purposes=frozenset({"signup"}),
                clock=lambda: self.now,
            )
        db.rollback()
        db.close()

    def test_delivery_expiry_is_rejected_and_invalidated(self):
        db = self.Session()
        result = self.process(db, self.claim(db), self.identity())
        db.commit()
        with self.assertRaises(OAuthSessionDeliveryError):
            consume_oauth_session_delivery(
                db,
                handle=result.delivery.handle,
                allowed_purposes=frozenset({"signup"}),
                clock=lambda: self.now + timedelta(minutes=2),
            )
        db.commit()
        row = db.query(OAuthSessionDeliveryHandle).one()
        self.assertEqual(row.invalidation_reason, "expired")
        db.close()

    def test_delivery_ttl_over_two_minutes_is_rejected(self):
        db = self.Session()
        claim = self.claim(db)
        with self.assertRaisesRegex(OAuthSessionDeliveryError, "invalid_result_ttl"):
            process_google_identity(
                db,
                claim=claim,
                identity=self.identity(),
                session_ttl=timedelta(hours=1),
                result_ttl=timedelta(seconds=121),
                clock=lambda: self.now,
            )
        db.rollback()
        db.close()

    def test_constraints_remain_final_authority_for_duplicate_subject(self):
        db = self.Session()
        first = Usuario(email="one@example.com", email_canonical="one@example.com")
        second = Usuario(email="two@example.com", email_canonical="two@example.com")
        db.add_all([first, second])
        db.flush()
        db.add_all(
            [
                ExternalIdentity(usuario_id=first.id, provider="google", provider_subject="same"),
                ExternalIdentity(usuario_id=second.id, provider="google", provider_subject="same"),
            ]
        )
        with self.assertRaises(IntegrityError):
            db.commit()
        db.rollback()
        db.close()


if __name__ == "__main__":
    unittest.main()
