from datetime import datetime, timedelta, timezone
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.security import hash_password
from app.modules.users.models.identity_models import (
    AccountActionRateLimit,
    ExternalIdentity,
    FeedGoSession,
    PasswordCredential,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.authentication_method_services import (
    AuthenticationMethodError,
    add_password_credential,
    derive_authentication_methods,
    link_google_identity,
    require_recent_reauthentication,
    unlink_google_identity,
)
from app.modules.users.services.account_action_rate_limit_services import (
    record_authentication_method_management,
)
from app.modules.users.services.feedgo_session_services import create_feedgo_session
from app.modules.users.services.google_oidc_services import GoogleOidcIdentity
from app.modules.users.services.oauth_authorization_transaction_services import (
    ClaimedOAuthAuthorizationTransaction,
)


class AuthenticationMethodServicesTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.now = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
        with self.Session.begin() as db:
            db.add_all(
                [
                    Usuario(
                        id=1,
                        email="one@example.com",
                        email_canonical="one@example.com",
                        hashed_password=None,
                    ),
                    Usuario(
                        id=2,
                        email="two@example.com",
                        email_canonical="two@example.com",
                        hashed_password=None,
                    ),
                ]
            )

    def tearDown(self):
        self.engine.dispose()

    def password_session(self, db, user_id=1, sid="password-session", age=0):
        return create_feedgo_session(
            db,
            usuario_id=user_id,
            authentication_method="password",
            clock=lambda: self.now - timedelta(seconds=age),
            ttl=timedelta(hours=2),
            sid_factory=lambda: sid,
        )

    def google_identity(self, db, user_id=1, subject="subject"):
        identity = ExternalIdentity(
            usuario_id=user_id,
            provider="google",
            provider_subject=subject,
            provider_email_snapshot=f"user{user_id}@example.com",
            provider_email_verified_snapshot=True,
            linked_at=self.now,
        )
        db.add(identity)
        db.flush()
        return identity

    def google_session(self, db, identity, sid="google-session", age=0):
        return create_feedgo_session(
            db,
            usuario_id=identity.usuario_id,
            authentication_method="google",
            external_identity_id=identity.id,
            clock=lambda: self.now - timedelta(seconds=age),
            ttl=timedelta(hours=2),
            sid_factory=lambda: sid,
        )

    def link_claim(self, sid="password-session", user_id=1):
        return ClaimedOAuthAuthorizationTransaction(
            transaction_id="link-transaction",
            purpose="link",
            nonce_digest="1" * 64,
            pkce_verifier="verifier",
            return_to="/perfil",
            legal_document_set_digest=None,
            legal_accepted_at=None,
            usuario_id=user_id,
            feedgo_session_id=sid,
        )

    def test_recent_reauthentication_uses_session_issued_at_exactly(self):
        db = self.Session()
        self.password_session(db, sid="boundary", age=600)
        self.password_session(db, sid="stale", age=601)
        db.commit()
        self.assertEqual(
            require_recent_reauthentication(
                db,
                usuario_id=1,
                feedgo_session_id="boundary",
                clock=lambda: self.now,
            ).id,
            "boundary",
        )
        with self.assertRaisesRegex(
            AuthenticationMethodError,
            "recent_reauthentication_required",
        ):
            require_recent_reauthentication(
                db,
                usuario_id=1,
                feedgo_session_id="stale",
                clock=lambda: self.now,
            )
        db.rollback()
        db.close()

    def test_link_uses_subject_and_explicit_session_not_email_ownership(self):
        db = self.Session()
        self.password_session(db)
        db.commit()
        linked = link_google_identity(
            db,
            claim=self.link_claim(),
            identity=GoogleOidcIdentity(
                subject="stable-subject",
                email="two@example.com",
                email_verified=True,
            ),
            clock=lambda: self.now,
        )
        db.commit()
        self.assertEqual(linked.usuario_id, 1)
        self.assertEqual(linked.provider_subject, "stable-subject")
        self.assertEqual(db.get(Usuario, 1).email, "one@example.com")
        self.assertEqual(db.get(Usuario, 2).email, "two@example.com")
        db.close()

    def test_link_rejects_subject_owned_by_another_user_and_second_google(self):
        db = self.Session()
        self.password_session(db)
        self.google_identity(db, user_id=2, subject="foreign-subject")
        db.commit()
        with self.assertRaisesRegex(AuthenticationMethodError, "google_link_unavailable"):
            link_google_identity(
                db,
                claim=self.link_claim(),
                identity=GoogleOidcIdentity(
                    subject="foreign-subject",
                    email="one@example.com",
                    email_verified=True,
                ),
                clock=lambda: self.now,
            )
        db.rollback()
        self.google_identity(db, user_id=1, subject="first-subject")
        db.commit()
        with self.assertRaisesRegex(AuthenticationMethodError, "google_link_unavailable"):
            link_google_identity(
                db,
                claim=self.link_claim(),
                identity=GoogleOidcIdentity(
                    subject="second-subject",
                    email="one@example.com",
                    email_verified=True,
                ),
                clock=lambda: self.now,
            )
        db.rollback()
        db.close()

    def test_link_fails_if_correlated_session_was_revoked(self):
        db = self.Session()
        session = self.password_session(db)
        db.commit()
        session.revoked_at = self.now.replace(tzinfo=None)
        db.commit()
        with self.assertRaisesRegex(
            AuthenticationMethodError,
            "recent_reauthentication_required",
        ):
            link_google_identity(
                db,
                claim=self.link_claim(),
                identity=GoogleOidcIdentity(
                    subject="subject",
                    email="one@example.com",
                    email_verified=True,
                ),
                clock=lambda: self.now,
            )
        db.rollback()
        db.close()

    def test_google_only_adds_password_with_policy_and_keeps_google_session(self):
        db = self.Session()
        identity = self.google_identity(db)
        session = self.google_session(db, identity)
        db.commit()
        credential = add_password_credential(
            db,
            usuario_id=1,
            feedgo_session_id=session.id,
            new_password="Password1",
            clock=lambda: self.now,
        )
        db.commit()
        self.assertEqual(db.get(Usuario, 1).hashed_password, credential.password_hash)
        self.assertIsNotNone(db.get(ExternalIdentity, identity.id))
        self.assertIsNone(db.get(FeedGoSession, session.id).revoked_at)
        methods = derive_authentication_methods(db, usuario_id=1)
        self.assertEqual(methods.usable_methods, ("password", "google"))
        self.assertTrue(methods.can_unlink_google)
        db.close()

    def test_add_password_rejects_duplicate_and_policy_is_not_duplicated(self):
        db = self.Session()
        identity = self.google_identity(db)
        session = self.google_session(db, identity)
        existing_hash = hash_password("Password1")
        db.add(
            PasswordCredential(
                usuario_id=1,
                password_hash=existing_hash,
                hash_version="bcrypt",
            )
        )
        db.commit()
        with self.assertRaisesRegex(
            AuthenticationMethodError,
            "authentication_method_already_exists",
        ):
            add_password_credential(
                db,
                usuario_id=1,
                feedgo_session_id=session.id,
                new_password="Password2",
                clock=lambda: self.now,
            )
        with self.assertRaises(ValueError):
            add_password_credential(
                db,
                usuario_id=1,
                feedgo_session_id=session.id,
                new_password="weak",
                clock=lambda: self.now,
            )
        db.rollback()
        self.assertEqual(db.get(PasswordCredential, 1).password_hash, existing_hash)
        db.close()

    def test_unlink_revokes_only_google_sessions_and_can_revoke_current(self):
        db = self.Session()
        password_hash = hash_password("Password1")
        db.add(
            PasswordCredential(
                usuario_id=1,
                password_hash=password_hash,
                hash_version="bcrypt",
            )
        )
        db.get(Usuario, 1).hashed_password = password_hash
        identity = self.google_identity(db)
        current = self.google_session(db, identity, sid="google-current")
        other = self.google_session(db, identity, sid="google-other")
        password_session = self.password_session(db, sid="password-current")
        db.commit()
        revoked = unlink_google_identity(
            db,
            usuario_id=1,
            feedgo_session_id=current.id,
            clock=lambda: self.now,
        )
        db.commit()
        self.assertEqual(revoked, 2)
        self.assertIsNotNone(db.get(FeedGoSession, current.id).revoked_at)
        self.assertIsNotNone(db.get(FeedGoSession, other.id).revoked_at)
        self.assertIsNone(db.get(FeedGoSession, password_session.id).revoked_at)
        self.assertEqual(db.query(ExternalIdentity).count(), 0)
        db.close()

    def test_google_only_cannot_unlink_last_method(self):
        db = self.Session()
        identity = self.google_identity(db)
        current = self.google_session(db, identity)
        db.commit()
        with self.assertRaisesRegex(
            AuthenticationMethodError,
            "cannot_remove_last_authentication_method",
        ):
            unlink_google_identity(
                db,
                usuario_id=1,
                feedgo_session_id=current.id,
                clock=lambda: self.now,
            )
        db.rollback()
        self.assertIsNotNone(db.get(ExternalIdentity, identity.id))
        self.assertIsNone(db.get(FeedGoSession, current.id).revoked_at)
        db.close()

    def test_legacy_hash_is_not_a_usable_password_method(self):
        db = self.Session()
        db.get(Usuario, 1).hashed_password = hash_password("Password1")
        self.google_identity(db)
        db.commit()
        methods = derive_authentication_methods(db, usuario_id=1)
        self.assertFalse(methods.has_password)
        self.assertEqual(methods.usable_methods, ("google",))
        self.assertFalse(methods.can_unlink_google)
        db.close()

    def test_corrupt_password_credential_cannot_authorize_google_unlink(self):
        db = self.Session()
        identity = self.google_identity(db)
        current = self.google_session(db, identity)
        db.add(
            PasswordCredential(
                usuario_id=1,
                password_hash="$2b$12$not-a-valid-bcrypt-hash",
                hash_version="bcrypt",
            )
        )
        db.commit()
        methods = derive_authentication_methods(db, usuario_id=1)
        self.assertFalse(methods.has_password)
        self.assertFalse(methods.can_unlink_google)
        with self.assertRaisesRegex(
            AuthenticationMethodError,
            "cannot_remove_last_authentication_method",
        ):
            unlink_google_identity(
                db,
                usuario_id=1,
                feedgo_session_id=current.id,
                clock=lambda: self.now,
            )
        db.rollback()
        self.assertIsNotNone(db.get(ExternalIdentity, identity.id))
        self.assertIsNone(db.get(FeedGoSession, current.id).revoked_at)
        db.close()

    def test_authentication_method_rate_limit_is_ten_per_user_hour(self):
        db = self.Session()
        decisions = [
            record_authentication_method_management(
                db,
                usuario_id=1,
                limit_per_hour=10,
                now=self.now.replace(tzinfo=None),
                secret="authentication-method-rate-secret",
            )
            for _ in range(11)
        ]
        db.commit()
        self.assertEqual(sum(decision.allowed for decision in decisions), 10)
        self.assertFalse(decisions[-1].allowed)
        row = db.query(AccountActionRateLimit).one()
        self.assertNotIn("user:1", row.subject_digest)
        self.assertEqual(len(row.subject_digest), 64)
        db.close()


if __name__ == "__main__":
    unittest.main()
