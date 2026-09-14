import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.core.security import hash_password
from app.modules.users.models.identity_models import FeedGoSession, PasswordCredential
from app.modules.users.models.tokens_models import TokenRevocado
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes.usuarios_routers import router


import_all_models()
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class DualJwtFeedGoSessionValidationTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        self.rate_secret_patch = patch(
            "app.modules.users.services.account_action_rate_limit_services.settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
            "dual-jwt-test-rate-secret",
        )
        self.rate_secret_patch.start()
        db = SessionLocal()
        for user_id in (1, 2):
            password_hash = hash_password("Password1")
            db.add(Usuario(
                id=user_id,
                email=f"user{user_id}@example.com",
                email_canonical=f"user{user_id}@example.com",
                hashed_password=password_hash,
            ))
            db.add(PasswordCredential(
                usuario_id=user_id, password_hash=password_hash, hash_version="bcrypt"
            ))
        db.commit(); db.close()

    def tearDown(self):
        self.rate_secret_patch.stop()
        Base.metadata.drop_all(engine)

    def login(self, user_id=1):
        response = client.post(
            "/usuarios/login",
            json={"email": f"user{user_id}@example.com", "password": "Password1"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["token"]

    def claims(self, token):
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    def encode(self, claims):
        return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def me(self, token):
        return client.get("/usuarios/me", headers={"Authorization": f"Bearer {token}"})

    def assert_rejected(self, token):
        response = self.me(token)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Token inválido o expirado"})

    def test_versioned_and_legacy_tokens_are_both_valid(self):
        versioned = self.login()
        legacy = crear_token_jwt({"sub": "1", "legacy_context": "preserved"})
        self.assertEqual(self.me(versioned).status_code, 200)
        self.assertEqual(self.me(legacy).status_code, 200)

    def test_incomplete_new_and_hybrid_contracts_cannot_downgrade(self):
        claims = self.claims(self.login())
        without_sid = dict(claims); without_sid.pop("sid")
        hybrid = self.claims(crear_token_jwt({"sub": "1"})); hybrid["sid"] = "attempt"
        extended = dict(claims); extended["perfil_completo"] = True
        self.assert_rejected(self.encode(without_sid))
        self.assert_rejected(self.encode(hybrid))
        self.assert_rejected(self.encode(extended))

    def test_missing_or_foreign_sid_is_rejected(self):
        claims = self.claims(self.login(1))
        missing = dict(claims); missing["sid"] = "missing"
        foreign_token = self.login(2)
        foreign_sid = self.claims(foreign_token)["sid"]
        foreign = dict(claims); foreign["sid"] = foreign_sid
        self.assert_rejected(self.encode(missing))
        self.assert_rejected(self.encode(foreign))

    def test_revoked_and_expired_sessions_are_rejected(self):
        revoked_token = self.login()
        revoked_claims = self.claims(revoked_token)
        db = SessionLocal()
        revoked = db.get(FeedGoSession, revoked_claims["sid"])
        revoked.revoked_at = datetime.utcnow(); db.commit(); db.close()
        self.assert_rejected(revoked_token)

        expired_token = self.login()
        expired_claims = self.claims(expired_token)
        db = SessionLocal(); expired = db.get(FeedGoSession, expired_claims["sid"])
        expired.issued_at = datetime.utcnow() - timedelta(hours=2)
        expired.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.commit(); db.close()
        self.assert_rejected(expired_token)

    def test_issuer_audience_version_and_timestamps_are_strict(self):
        claims = self.claims(self.login())
        mutations = []
        for key, value in (
            ("issuer", "other"),
            ("audience", "other"),
            ("version", settings.JWT_CONTRACT_VERSION + 1),
            ("iat", claims["iat"] + 1),
            ("exp", claims["exp"] - 1),
        ):
            changed = dict(claims); changed[key] = value; mutations.append(changed)
        for changed in mutations:
            self.assert_rejected(self.encode(changed))

    def test_replay_works_only_while_session_is_active(self):
        token = self.login()
        self.assertEqual(self.me(token).status_code, 200)
        self.assertEqual(self.me(token).status_code, 200)
        claims = self.claims(token)
        db = SessionLocal(); db.get(FeedGoSession, claims["sid"]).revoked_at = datetime.utcnow(); db.commit(); db.close()
        self.assert_rejected(token)

    def test_legacy_blacklist_does_not_own_versioned_token_after_transition(self):
        token = self.login(); claims = self.claims(token)
        db = SessionLocal()
        db.add(TokenRevocado(
            token=token,
            usuario_id=1,
            expira_en=datetime.utcfromtimestamp(claims["exp"]),
        ))
        db.commit(); db.close()
        self.assertEqual(self.me(token).status_code, 200)

    def test_current_logout_revokes_versioned_session_without_blacklisting_bearer(self):
        token = self.login(); claims = self.claims(token)
        logout = client.post(
            "/usuarios/logout", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(self.me(token).status_code, 401)
        db = SessionLocal()
        self.assertIsNotNone(db.get(FeedGoSession, claims["sid"]).revoked_at)
        self.assertIsNone(db.query(TokenRevocado).filter_by(token=token).first())
        db.close()

    def test_versioned_logout_is_idempotent(self):
        token = self.login()
        headers = {"Authorization": f"Bearer {token}"}
        self.assertEqual(client.post("/usuarios/logout", headers=headers).status_code, 200)
        self.assertEqual(client.post("/usuarios/logout", headers=headers).status_code, 200)
        db = SessionLocal()
        self.assertEqual(db.query(TokenRevocado).filter_by(token=token).count(), 0)
        self.assertEqual(db.query(FeedGoSession).filter(FeedGoSession.revoked_at.is_not(None)).count(), 1)
        db.close()

    def test_legacy_logout_and_replay_keep_blacklist_contract(self):
        token = crear_token_jwt({"sub": "1"})
        headers = {"Authorization": f"Bearer {token}"}
        self.assertEqual(client.post("/usuarios/logout", headers=headers).status_code, 200)
        self.assertEqual(self.me(token).status_code, 401)
        db = SessionLocal()
        self.assertIsNotNone(db.query(TokenRevocado).filter_by(token=token).first())
        db.close()

    def test_logout_one_versioned_session_does_not_revoke_another(self):
        first = self.login(); second = self.login()
        self.assertEqual(client.post(
            "/usuarios/logout", headers={"Authorization": f"Bearer {first}"}
        ).status_code, 200)
        self.assertEqual(self.me(first).status_code, 401)
        self.assertEqual(self.me(second).status_code, 200)

    def test_multiple_sessions_are_independent(self):
        first = self.login(); second = self.login()
        first_claims = self.claims(first)
        db = SessionLocal(); db.get(FeedGoSession, first_claims["sid"]).revoked_at = datetime.utcnow(); db.commit(); db.close()
        self.assert_rejected(first)
        self.assertEqual(self.me(second).status_code, 200)

    def test_versioned_password_change_keeps_current_and_revokes_other_sessions(self):
        current = self.login(); other = self.login()
        response = client.patch(
            "/usuarios/me/password",
            headers={"Authorization": f"Bearer {current}"},
            json={"current_password": "Password1", "new_password": "Password2"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.me(current).status_code, 200)
        self.assert_rejected(other)
        second_change = client.patch(
            "/usuarios/me/password",
            headers={"Authorization": f"Bearer {current}"},
            json={"current_password": "Password2", "new_password": "Password3"},
        )
        self.assertEqual(second_change.status_code, 200)
        self.assertEqual(self.me(current).status_code, 200)
        db = SessionLocal()
        sessions = db.query(FeedGoSession).all()
        self.assertEqual(sum(item.revoked_at is None for item in sessions), 1)
        self.assertIsNone(db.get(FeedGoSession, self.claims(current)["sid"]).revoked_at)
        self.assertEqual(db.get(Usuario, 1).hashed_password, db.get(PasswordCredential, 1).password_hash)
        db.close()

    def test_legacy_password_change_revokes_feedgo_sessions_without_creating_one(self):
        first = self.login(); second = self.login()
        legacy = crear_token_jwt({"sub": "1"})
        response = client.patch(
            "/usuarios/me/password",
            headers={"Authorization": f"Bearer {legacy}"},
            json={"current_password": "Password1", "new_password": "Password2"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.me(legacy).status_code, 200)
        self.assert_rejected(first); self.assert_rejected(second)
        db = SessionLocal()
        self.assertEqual(db.query(FeedGoSession).count(), 2)
        self.assertEqual(db.query(FeedGoSession).filter(FeedGoSession.revoked_at.is_(None)).count(), 0)
        db.close()


if __name__ == "__main__":
    unittest.main()
