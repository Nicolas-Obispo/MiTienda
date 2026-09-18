from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt, crear_token_jwt_versionado
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.error_handlers import register_exception_handlers
from app.core.security import hash_password
from app.modules.users.models.identity_models import (
    ExternalIdentity,
    FeedGoSession,
    PasswordCredential,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes.usuarios_routers import router as usuarios_router
from app.modules.users.services.feedgo_session_services import create_feedgo_session


class AuthenticationMethodsHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(bind=cls.engine)

        def override_get_db():
            db = cls.Session()
            try:
                yield db
            finally:
                db.close()

        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(usuarios_router)
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app, raise_server_exceptions=False)

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.rate_secret = patch(
            "app.modules.users.services.account_action_rate_limit_services.settings."
            "ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
            "authentication-method-test-rate-secret",
        )
        self.rate_secret.start()

    def tearDown(self):
        self.rate_secret.stop()

    def google_user_token(self, *, age=0, with_password=False):
        db = self.Session()
        user = Usuario(
            id=1,
            email="google@example.com",
            email_canonical="google@example.com",
            hashed_password=None,
        )
        db.add(user)
        db.flush()
        identity = ExternalIdentity(
            usuario_id=1,
            provider="google",
            provider_subject="google-subject",
            provider_email_snapshot="google@example.com",
            provider_email_verified_snapshot=True,
            linked_at=self.now,
        )
        db.add(identity)
        db.flush()
        session = create_feedgo_session(
            db,
            usuario_id=1,
            authentication_method="google",
            external_identity_id=identity.id,
            clock=lambda: self.now - timedelta(seconds=age),
            ttl=timedelta(hours=2),
            sid_factory=lambda: "google-session",
        )
        if with_password:
            password_hash = hash_password("Password1")
            db.add(
                PasswordCredential(
                    usuario_id=1,
                    password_hash=password_hash,
                    hash_version="bcrypt",
                )
            )
            user.hashed_password = password_hash
        db.commit()
        token = crear_token_jwt_versionado(
            usuario_id=1,
            sid=session.id,
            issued_at=session.issued_at,
            expires_at=session.expires_at,
        )
        db.close()
        return token

    @staticmethod
    def headers(token):
        return {"Authorization": f"Bearer {token}"}

    def test_google_only_adds_password_and_me_derives_two_methods(self):
        token = self.google_user_token()
        response = self.client.post(
            "/usuarios/me/authentication-methods/password",
            headers=self.headers(token),
            json={"confirm": True, "new_password": "Password1"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"status": "password_added"})
        self.assertEqual(response.headers["cache-control"], "private, no-store")
        me = self.client.get("/usuarios/me", headers=self.headers(token))
        self.assertEqual(me.status_code, 200, me.text)
        methods = me.json()["authentication_methods"]
        self.assertEqual(
            methods,
            {
                "has_password": True,
                "google_linked": True,
                "usable_methods": ["password", "google"],
                "can_unlink_google": True,
            },
        )
        serialized = str(methods).lower()
        self.assertNotIn("subject", serialized)
        self.assertNotIn("token", serialized)
        db = self.Session()
        self.assertEqual(
            db.get(Usuario, 1).hashed_password,
            db.get(PasswordCredential, 1).password_hash,
        )
        self.assertIsNone(db.get(FeedGoSession, "google-session").revoked_at)
        db.close()

    def test_password_reauthentication_rotates_sid_and_rejects_old_token(self):
        token = self.google_user_token(with_password=True)
        response = self.client.post(
            "/usuarios/me/reauthentication/password",
            headers=self.headers(token),
            json={"current_password": "Password1"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["cache-control"], "private, no-store")
        replacement = response.json()["token"]
        self.assertNotEqual(replacement, token)
        self.assertEqual(self.client.get("/usuarios/me", headers=self.headers(token)).status_code, 401)
        self.assertEqual(self.client.get("/usuarios/me", headers=self.headers(replacement)).status_code, 200)
        db = self.Session()
        current = (
            db.query(FeedGoSession)
            .filter(FeedGoSession.usuario_id == 1, FeedGoSession.revoked_at.is_(None))
            .one()
        )
        self.assertEqual(current.authentication_method, "password")
        self.assertIsNone(current.external_identity_id)
        self.assertEqual(current.contract_version, 1)
        self.assertEqual(current.issued_at.microsecond, 0)
        self.assertEqual(
            current.expires_at - current.issued_at,
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        db.close()

    def test_password_reauthentication_requires_real_usable_password(self):
        token = self.google_user_token(with_password=True)
        rejected = self.client.post(
            "/usuarios/me/reauthentication/password",
            headers=self.headers(token),
            json={"current_password": "incorrecta"},
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(rejected.json()["code"], "reauthentication_invalid")
        self.assertEqual(rejected.headers["cache-control"], "private, no-store")

    def test_password_reauthentication_failures_persist_and_rate_limit(self):
        token = self.google_user_token(with_password=True)
        for _ in range(5):
            rejected = self.client.post(
                "/usuarios/me/reauthentication/password",
                headers=self.headers(token),
                json={"current_password": "incorrecta"},
            )
            self.assertEqual(rejected.status_code, 400)
        limited = self.client.post(
            "/usuarios/me/reauthentication/password",
            headers=self.headers(token),
            json={"current_password": "Password1"},
        )
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(limited.json()["code"], "reauthentication_rate_limited")

    def test_add_password_requires_confirmation_recent_sid_and_no_duplicate(self):
        stale = self.google_user_token(age=601)
        rejected = self.client.post(
            "/usuarios/me/authentication-methods/password",
            headers=self.headers(stale),
            json={"confirm": True, "new_password": "Password1"},
        )
        self.assertEqual(rejected.status_code, 403)
        self.assertEqual(rejected.json()["code"], "recent_reauthentication_required")
        self.assertEqual(rejected.headers["cache-control"], "private, no-store")

        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        current = self.google_user_token(with_password=True)
        duplicate = self.client.post(
            "/usuarios/me/authentication-methods/password",
            headers=self.headers(current),
            json={"confirm": True, "new_password": "Password2"},
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(
            duplicate.json()["code"],
            "authentication_method_already_exists",
        )
        missing_confirmation = self.client.post(
            "/usuarios/me/authentication-methods/password",
            headers=self.headers(current),
            json={"confirm": False, "new_password": "Password2"},
        )
        self.assertEqual(missing_confirmation.status_code, 422)
        self.assertEqual(
            missing_confirmation.headers["cache-control"],
            "private, no-store",
        )

    def test_legacy_jwt_cannot_satisfy_recent_reauthentication(self):
        self.google_user_token()
        legacy = crear_token_jwt({"sub": "1"})
        response = self.client.post(
            "/usuarios/me/authentication-methods/password",
            headers=self.headers(legacy),
            json={"confirm": True, "new_password": "Password1"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "recent_reauthentication_required")

    def test_google_only_cannot_unlink_last_method(self):
        token = self.google_user_token()
        response = self.client.request(
            "DELETE",
            "/usuarios/me/authentication-methods/google",
            headers=self.headers(token),
            json={"confirm": True},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["code"],
            "cannot_remove_last_authentication_method",
        )

    def test_unlink_revokes_current_google_session_but_keeps_password_session(self):
        token = self.google_user_token(with_password=True)
        db = self.Session()
        password_session = create_feedgo_session(
            db,
            usuario_id=1,
            authentication_method="password",
            clock=lambda: self.now,
            ttl=timedelta(hours=2),
            sid_factory=lambda: "password-session",
        )
        password_session_id = password_session.id
        db.commit()
        db.close()
        response = self.client.request(
            "DELETE",
            "/usuarios/me/authentication-methods/google",
            headers=self.headers(token),
            json={"confirm": True},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"status": "google_unlinked"})
        self.assertEqual(
            self.client.get("/usuarios/me", headers=self.headers(token)).status_code,
            401,
        )
        db = self.Session()
        self.assertIsNotNone(db.get(FeedGoSession, "google-session").revoked_at)
        self.assertIsNone(db.get(FeedGoSession, password_session_id).revoked_at)
        self.assertEqual(db.query(ExternalIdentity).count(), 0)
        db.close()


if __name__ == "__main__":
    unittest.main()
