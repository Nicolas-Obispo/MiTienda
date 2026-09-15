from contextlib import ExitStack
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.error_handlers import register_exception_handlers
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import (
    AccountActionRateLimit,
    ExternalIdentity,
    OAuthAuthorizationTransaction,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes import google_identity_routers
from app.modules.users.services.google_oidc_services import (
    GoogleOidcError,
    GoogleOidcIdentity,
)


import_all_models()


class FakeGoogleOidcOwner:
    identity = GoogleOidcIdentity(
        subject="new-google-subject",
        email="new-google@example.com",
        email_verified=True,
    )
    exchanges = []
    authorization_error = None
    exchange_error = None

    async def create_authorization_url(self, material):
        if type(self).authorization_error is not None:
            raise type(self).authorization_error
        return (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"state={material.state}&nonce={material.nonce}"
            f"&code_challenge={material.pkce_challenge}"
            "&code_challenge_method=S256&scope=openid%20email"
        )

    async def exchange_and_validate(self, **kwargs):
        type(self).exchanges.append(kwargs)
        if type(self).exchange_error is not None:
            raise type(self).exchange_error
        return type(self).identity


class GoogleIdentityHttpFlowTests(unittest.TestCase):
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
        app.include_router(google_identity_routers.router)
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app, raise_server_exceptions=False)

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        FakeGoogleOidcOwner.exchanges = []
        FakeGoogleOidcOwner.authorization_error = None
        FakeGoogleOidcOwner.exchange_error = None
        FakeGoogleOidcOwner.identity = GoogleOidcIdentity(
            subject="new-google-subject",
            email="new-google@example.com",
            email_verified=True,
        )
        values = {
            "GOOGLE_IDENTITY_ENABLED": True,
            "GOOGLE_OIDC_CLIENT_ID": "feedgo-client",
            "GOOGLE_OIDC_CLIENT_SECRET": "test-secret",
            "GOOGLE_OIDC_REDIRECT_URI": "https://api.feedgo.test/usuarios/google/callback",
            "GOOGLE_OIDC_PUBLIC_BASE_URL": "https://feedgo.test",
            "GOOGLE_OIDC_FRONTEND_RESULT_PATH": "/auth/google/resultado",
            "ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET": "google-rate-limit-test-secret",
        }
        self.patches = ExitStack()
        for name, value in values.items():
            self.patches.enter_context(patch.object(settings, name, value))
        self.patches.enter_context(
            patch.object(
                google_identity_routers,
                "build_google_oidc_owner",
                side_effect=FakeGoogleOidcOwner,
            )
        )

    def tearDown(self):
        self.patches.close()

    def _start(self, purpose, **extra):
        payload = {"purpose": purpose, "return_to": "/perfil?tab=cuenta"} | extra
        response = self.client.post("/usuarios/google/authorization", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        state = parse_qs(urlsplit(response.json()["authorization_url"]).query)["state"][0]
        return response, state

    def _callback_handle(self, state):
        callback = self.client.get(
            "/usuarios/google/callback",
            params={"state": state, "code": "authorization-code"},
            follow_redirects=False,
        )
        self.assertEqual(callback.status_code, 303, callback.text)
        location = callback.headers["location"]
        self.assertNotIn("token=", location)
        self.assertNotIn("jwt", location.lower())
        return callback, parse_qs(urlsplit(location).query)["handle"][0]

    def test_signup_callback_and_one_use_exchange_deliver_feedgo_jwt_outside_url(self):
        started, state = self._start(
            "signup", acepta_terminos=True, acepta_privacidad=True
        )
        self.assertEqual(started.headers["cache-control"], "private, no-store")
        callback, handle = self._callback_handle(state)
        self.assertEqual(callback.headers["cache-control"], "private, no-store")
        exchanged = self.client.post("/usuarios/google/session", json={"handle": handle})
        self.assertEqual(exchanged.status_code, 200, exchanged.text)
        self.assertEqual(exchanged.json()["status"], "authenticated")
        self.assertTrue(exchanged.json()["token"])
        self.assertEqual(exchanged.headers["cache-control"], "private, no-store")
        replay = self.client.post("/usuarios/google/session", json={"handle": handle})
        self.assertEqual(replay.status_code, 400)
        self.assertEqual(replay.json()["code"], "google_session_result_invalid")
        db = self.Session()
        user = db.query(Usuario).one()
        self.assertIsNone(user.hashed_password)
        self.assertEqual(db.query(ExternalIdentity).one().provider_subject, "new-google-subject")
        db.close()

    def test_callback_transaction_replay_is_rejected_before_second_exchange(self):
        _, state = self._start("signup", acepta_terminos=True, acepta_privacidad=True)
        self._callback_handle(state)
        replay = self.client.get(
            "/usuarios/google/callback",
            params={"state": state, "code": "second-code"},
            follow_redirects=False,
        )
        self.assertEqual(replay.status_code, 400)
        self.assertEqual(len(FakeGoogleOidcOwner.exchanges), 1)

    def test_failed_exchange_still_consumes_transaction_and_clears_verifier(self):
        _, state = self._start("login")
        FakeGoogleOidcOwner.exchange_error = GoogleOidcError(
            "google_oidc_provider_unavailable"
        )
        callback = self.client.get(
            "/usuarios/google/callback",
            params={"state": state, "code": "authorization-code"},
            follow_redirects=False,
        )
        self.assertEqual(callback.status_code, 400)
        db = self.Session()
        transaction = db.query(OAuthAuthorizationTransaction).one()
        self.assertIsNotNone(transaction.consumed_at)
        self.assertIsNone(transaction.pkce_verifier)
        db.close()
        replay = self.client.get(
            "/usuarios/google/callback",
            params={"state": state, "code": "second-code"},
            follow_redirects=False,
        )
        self.assertEqual(replay.status_code, 400)
        self.assertEqual(len(FakeGoogleOidcOwner.exchanges), 1)

    def test_unknown_login_does_not_create_user_and_uses_generic_result(self):
        _, state = self._start("login")
        _, handle = self._callback_handle(state)
        result = self.client.post("/usuarios/google/session", json={"handle": handle})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["status"], "action_required")
        db = self.Session()
        self.assertEqual(db.query(Usuario).count(), 0)
        db.close()

    def test_signup_requires_explicit_legal_acceptance_before_transaction(self):
        response = self.client.post(
            "/usuarios/google/authorization",
            json={"purpose": "signup", "acepta_terminos": True},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "google_signup_legal_acceptance_required")
        db = self.Session()
        self.assertEqual(db.query(Usuario).count(), 0)
        db.close()

    def test_email_collision_does_not_auto_link_or_authenticate_existing_user(self):
        db = self.Session()
        db.add(
            Usuario(
                email="existing@example.com",
                email_canonical="existing@example.com",
                hashed_password="legacy-hash",
            )
        )
        db.commit()
        db.close()
        FakeGoogleOidcOwner.identity = GoogleOidcIdentity(
            subject="different-subject",
            email="EXISTING@example.com",
            email_verified=True,
        )
        _, state = self._start("signup", acepta_terminos=True, acepta_privacidad=True)
        _, handle = self._callback_handle(state)
        result = self.client.post("/usuarios/google/session", json={"handle": handle})
        self.assertEqual(result.json()["status"], "action_required")
        db = self.Session()
        self.assertEqual(db.query(Usuario).count(), 1)
        self.assertEqual(db.query(ExternalIdentity).count(), 0)
        db.close()

    def test_unrelated_integrity_error_is_not_mapped_to_account_collision(self):
        _, state = self._start(
            "signup", acepta_terminos=True, acepta_privacidad=True
        )
        database_error = IntegrityError("statement", {}, RuntimeError("db failure"))
        with patch.object(
            google_identity_routers,
            "process_google_identity",
            side_effect=database_error,
        ):
            callback = self.client.get(
                "/usuarios/google/callback",
                params={"state": state, "code": "authorization-code"},
                follow_redirects=False,
            )
        self.assertEqual(callback.status_code, 500)
        self.assertEqual(callback.json(), {"detail": "Error interno del servidor"})
        self.assertEqual(callback.headers["cache-control"], "private, no-store")

    def test_validation_errors_on_google_endpoints_are_no_store(self):
        response = self.client.post("/usuarios/google/authorization", json={})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.headers["cache-control"], "private, no-store")

    def test_disabled_google_identity_fails_closed(self):
        with patch.object(settings, "GOOGLE_IDENTITY_ENABLED", False):
            response = self.client.post(
                "/usuarios/google/authorization",
                json={"purpose": "login"},
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "google_identity_unavailable")
        self.assertEqual(response.headers["cache-control"], "private, no-store")

    def test_public_authorization_rate_limit_is_ten_per_client_hour(self):
        for _ in range(10):
            response = self.client.post(
                "/usuarios/google/authorization",
                json={"purpose": "login"},
            )
            self.assertEqual(response.status_code, 200)
        limited = self.client.post(
            "/usuarios/google/authorization",
            json={"purpose": "login"},
        )
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(limited.json()["code"], "google_oauth_rate_limited")
        self.assertEqual(limited.headers["cache-control"], "private, no-store")
        db = self.Session()
        buckets = db.query(AccountActionRateLimit).all()
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0].action, "google_oauth")
        self.assertEqual(len(buckets[0].subject_digest), 64)
        self.assertNotIn("testclient", buckets[0].subject_digest)
        db.close()

    def test_provider_failure_does_not_rollback_public_rate_limit(self):
        FakeGoogleOidcOwner.authorization_error = GoogleOidcError(
            "google_oidc_provider_unavailable"
        )
        for _ in range(10):
            response = self.client.post(
                "/usuarios/google/authorization",
                json={"purpose": "login"},
            )
            self.assertEqual(response.status_code, 503)
        limited = self.client.post(
            "/usuarios/google/authorization",
            json={"purpose": "login"},
        )
        self.assertEqual(limited.status_code, 429)
        db = self.Session()
        bucket = db.query(AccountActionRateLimit).one()
        self.assertEqual(bucket.attempt_count, 10)
        db.close()


if __name__ == "__main__":
    unittest.main()
