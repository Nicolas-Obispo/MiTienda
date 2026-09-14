import unittest
from datetime import timedelta, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.core.security import hash_password
from app.modules.users.models.identity_models import FeedGoSession, PasswordCredential
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes.usuarios_routers import login_endpoint, router
from app.modules.users.schemas.usuarios_schemas import UsuarioLogin


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


class FeedGoSessionLoginEmissionTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        password_hash = hash_password("Password1")
        db = SessionLocal()
        db.add(Usuario(
            id=1,
            email="user@example.com",
            email_canonical="user@example.com",
            hashed_password=password_hash,
        ))
        db.add(PasswordCredential(
            usuario_id=1, password_hash=password_hash, hash_version="bcrypt"
        ))
        db.commit(); db.close()

    def tearDown(self):
        Base.metadata.drop_all(engine)

    def login(self, email="user@example.com", password="Password1"):
        return client.post("/usuarios/login", json={"email": email, "password": password})

    def decode(self, token):
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    def test_login_creates_one_password_session_and_exact_versioned_claims(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]
        claims = self.decode(token)
        self.assertEqual(
            set(claims),
            {"sub", "sid", "iat", "exp", "issuer", "audience", "version"},
        )
        db = SessionLocal(); sessions = db.query(FeedGoSession).all()
        self.assertEqual(len(sessions), 1)
        session = sessions[0]
        self.assertEqual(claims["sub"], "1")
        self.assertEqual(claims["sid"], session.id)
        self.assertEqual(
            claims["iat"], int(session.issued_at.replace(tzinfo=timezone.utc).timestamp())
        )
        self.assertEqual(
            claims["exp"], int(session.expires_at.replace(tzinfo=timezone.utc).timestamp())
        )
        self.assertEqual(claims["issuer"], settings.JWT_ISSUER)
        self.assertEqual(claims["audience"], settings.JWT_AUDIENCE)
        self.assertEqual(claims["version"], settings.JWT_CONTRACT_VERSION)
        self.assertEqual(session.authentication_method, "password")
        self.assertIsNone(session.external_identity_id)
        self.assertFalse({"jwt", "token", "bearer"} & set(session.__table__.columns))
        db.close()
        me = client.get(
            "/usuarios/me", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(me.status_code, 200)

    def test_ttl_is_governed_by_configuration(self):
        original = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 17
        try:
            response = self.login()
        finally:
            settings.ACCESS_TOKEN_EXPIRE_MINUTES = original
        claims = self.decode(response.json()["token"])
        self.assertEqual(claims["exp"] - claims["iat"], 17 * 60)
        db = SessionLocal(); session = db.query(FeedGoSession).one()
        self.assertEqual(session.expires_at - session.issued_at, timedelta(minutes=17))
        db.close()

    def test_multiple_close_logins_create_distinct_sessions_and_tokens(self):
        first = self.login(); second = self.login()
        self.assertNotEqual(first.json()["token"], second.json()["token"])
        first_claims = self.decode(first.json()["token"])
        second_claims = self.decode(second.json()["token"])
        self.assertNotEqual(first_claims["sid"], second_claims["sid"])
        db = SessionLocal(); self.assertEqual(db.query(FeedGoSession).count(), 2); db.close()

    def test_failed_login_creates_no_session(self):
        response = self.login(password="incorrect")
        self.assertEqual(response.status_code, 401)
        db = SessionLocal(); self.assertEqual(db.query(FeedGoSession).count(), 0); db.close()

    def test_transaction_failure_returns_no_token_and_leaves_no_session(self):
        db = SessionLocal()
        def fail_commit(session):
            raise RuntimeError("forced commit failure")
        event.listen(db, "before_commit", fail_commit)
        with self.assertRaises(RuntimeError):
            login_endpoint(
                UsuarioLogin(email="user@example.com", password="Password1"), db
            )
        event.remove(db, "before_commit", fail_commit)
        db.close()
        verification = SessionLocal()
        self.assertEqual(verification.query(FeedGoSession).count(), 0)
        verification.close()

    def test_registration_does_not_duplicate_session_and_normal_login_creates_it(self):
        response = client.post(
            "/usuarios/registrar",
            json={
                "email": "new@example.com",
                "password": "Password2",
                "acepta_terminos": True,
                "acepta_privacidad": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        db = SessionLocal(); self.assertEqual(db.query(FeedGoSession).count(), 0); db.close()
        self.assertEqual(self.login("new@example.com", "Password2").status_code, 200)
        db = SessionLocal(); self.assertEqual(db.query(FeedGoSession).count(), 1); db.close()

    def test_legacy_fixture_remains_accepted_during_transition(self):
        legacy = crear_token_jwt({"sub": "1"})
        response = client.get(
            "/usuarios/me", headers={"Authorization": f"Bearer {legacy}"}
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
