import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from app.core.auth import _utc_epoch_seconds
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.core.security import hash_password
from app.modules.users.models.identity_models import FeedGoSession, PasswordCredential
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes.usuarios_routers import router
from app.modules.users.services.feedgo_session_services import create_feedgo_session
from app.modules.users.services.account_action_token_services import (
    PASSWORD_RESET,
    issue_account_action_token,
)
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


import_all_models()
TEST_SESSION = None


def override_get_db():
    db = TEST_SESSION()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class FeedGoSessionLifecycleMySQLE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global TEST_SESSION
        cls.engine, TEST_SESSION = isolated_mysql_test_engine()
        cls.Session = TEST_SESSION
        Base.metadata.drop_all(cls.engine)
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        self.rate_patch = patch(
            "app.modules.users.services.account_action_rate_limit_services.settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
            "mysql-lifecycle-rate-secret",
        )
        self.rate_patch.start()
        password_hash = hash_password("Password1")
        db = self.Session()
        db.add(Usuario(
            id=900001,
            email="session-e2e@example.com",
            email_canonical="session-e2e@example.com",
            hashed_password=password_hash,
        ))
        db.commit()
        db.add(PasswordCredential(
            usuario_id=900001,
            password_hash=password_hash,
            hash_version="bcrypt",
        ))
        db.commit(); db.close()

    def tearDown(self):
        self.rate_patch.stop()
        db = self.Session()
        db.query(Usuario).filter(Usuario.id == 900001).delete()
        db.commit(); db.close()

    def login(self, password):
        response = client.post(
            "/usuarios/login",
            json={"email": "session-e2e@example.com", "password": password},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["token"]

    def headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def assert_valid(self, token):
        response = client.get("/usuarios/me", headers=self.headers(token))
        self.assertEqual(response.status_code, 200, response.text)

    def assert_invalid(self, token):
        self.assertEqual(client.get("/usuarios/me", headers=self.headers(token)).status_code, 401)

    def test_complete_session_and_password_lifecycle(self):
        token_a = self.login("Password1")
        token_b = self.login("Password1")
        self.assert_valid(token_a); self.assert_valid(token_b)

        self.assertEqual(client.post("/usuarios/logout", headers=self.headers(token_a)).status_code, 200)
        self.assert_invalid(token_a); self.assert_valid(token_b)

        changed = client.patch(
            "/usuarios/me/password",
            headers=self.headers(token_b),
            json={"current_password": "Password1", "new_password": "Password2"},
        )
        self.assertEqual(changed.status_code, 200)
        self.assert_valid(token_b); self.assert_invalid(token_a)

        db = self.Session()
        issued = issue_account_action_token(
            db=db, usuario_id=900001, purpose=PASSWORD_RESET
        )
        db.close()
        reset = client.post(
            "/usuarios/password/restablecer",
            json={"token": issued.secret, "new_password": "Password3"},
        )
        self.assertEqual(reset.status_code, 200)
        self.assertNotIn("token", reset.json())
        self.assert_invalid(token_b)
        db = self.Session()
        self.assertEqual(
            db.query(FeedGoSession).filter(
                FeedGoSession.usuario_id == 900001,
                FeedGoSession.revoked_at.is_(None),
            ).count(),
            0,
        )
        db.close()

        token_c = self.login("Password3")
        self.assert_valid(token_c)
        self.assertNotEqual(token_c, token_a)
        self.assertNotEqual(token_c, token_b)

    def test_datetime_zero_round_trip_and_immediate_relogin_are_exact(self):
        base = datetime.now(timezone.utc).replace(microsecond=0)
        fractions = (0, 499999, 500000, 999999)
        moments = iter(
            base.replace(microsecond=microsecond)
            for microsecond in fractions
            for _ in range(2)
        )
        real_create = create_feedgo_session

        def create_with_forced_clock(db, **kwargs):
            instant = next(moments)
            return real_create(db, clock=lambda: instant, **kwargs)

        with patch(
            "app.modules.users.routes.usuarios_routers.create_feedgo_session",
            side_effect=create_with_forced_clock,
        ):
            for _ in fractions:
                token_a = self.login("Password1")
                self.assert_valid(token_a)
                self.assertEqual(
                    client.post(
                        "/usuarios/logout", headers=self.headers(token_a)
                    ).status_code,
                    200,
                )

                token_b = self.login("Password1")
                claims = jwt.decode(
                    token_b,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                db = self.Session()
                try:
                    persisted = db.get(FeedGoSession, claims["sid"])
                    self.assertEqual(persisted.issued_at.microsecond, 0)
                    self.assertEqual(persisted.expires_at.microsecond, 0)
                    self.assertEqual(
                        claims["iat"], _utc_epoch_seconds(persisted.issued_at)
                    )
                    self.assertEqual(
                        claims["exp"], _utc_epoch_seconds(persisted.expires_at)
                    )
                finally:
                    db.close()
                self.assert_valid(token_b)


if __name__ == "__main__":
    unittest.main()
