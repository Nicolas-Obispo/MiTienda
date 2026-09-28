import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.modules.users.models.identity_models import AccountActionRateLimit
from app.modules.users.routes.usuarios_routers import router
from app.modules.users.services.account_action_rate_limit_services import PASSWORD_LOGIN
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


@unittest.skipUnless(
    os.environ.get("FEEDGO_STAGE97_TEST_DATABASE_URL"),
    "requiere FEEDGO_STAGE97_TEST_DATABASE_URL aislada",
)
class PasswordLoginHttpMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global TEST_SESSION
        cls.engine, TEST_SESSION = isolated_mysql_test_engine()
        cls.Session = TEST_SESSION

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.patches = [
            patch(
                "app.modules.users.services.account_action_rate_limit_services."
                "settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
                "password-login-http-mysql-secret",
            ),
            patch(
                "app.modules.users.services.account_action_rate_limit_services._utcnow",
                return_value=datetime(2026, 9, 25, 12, 0, 0),
            ),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()

    def test_requests_http_concurrentes_respetan_limite_persistente(self):
        count = 10
        barrier = threading.Barrier(count)

        def login(_index):
            barrier.wait(timeout=15)
            return client.post(
                "/usuarios/login",
                json={
                    "email": "synthetic-concurrent@example.com",
                    "password": "DefinitelyWrong1",
                },
                headers={
                    "X-Forwarded-For": f"203.0.113.{_index + 1}",
                    "Forwarded": f"for=198.51.100.{_index + 1}",
                },
            )

        with ThreadPoolExecutor(max_workers=count) as executor:
            responses = list(executor.map(login, range(count)))

        self.assertEqual(sum(item.status_code == 401 for item in responses), 5)
        self.assertEqual(sum(item.status_code == 429 for item in responses), 5)
        self.assertEqual(
            {item.headers.get("cache-control") for item in responses},
            {"no-store"},
        )
        with self.Session() as db:
            rows = list(
                db.scalars(
                    select(AccountActionRateLimit).where(
                        AccountActionRateLimit.action == PASSWORD_LOGIN
                    )
                )
            )
        self.assertEqual(len(rows), 2)
        self.assertEqual({row.attempt_count for row in rows}, {5})


if __name__ == "__main__":
    unittest.main()
