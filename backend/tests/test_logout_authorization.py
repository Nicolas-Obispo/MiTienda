import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.users.models.tokens_models import TokenRevocado
from app.modules.users.routes.usuarios_routers import router as usuarios_router


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(usuarios_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class LogoutAuthorizationTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides = {get_db: override_get_db}

    def tearDown(self):
        app.dependency_overrides = {get_db: override_get_db}
        Base.metadata.drop_all(bind=engine)

    def test_logout_sin_token_devuelve_401(self):
        response = client.post("/usuarios/logout")

        self.assertEqual(response.status_code, 401)

    def test_logout_con_token_invalido_devuelve_401_y_no_revoca(self):
        response = client.post(
            "/usuarios/logout",
            headers={"Authorization": "Bearer token-invalido"},
        )

        self.assertEqual(response.status_code, 401)

        db = TestingSessionLocal()
        tokens_revocados = db.query(TokenRevocado).count()
        db.close()

        self.assertEqual(tokens_revocados, 0)


if __name__ == "__main__":
    unittest.main()
