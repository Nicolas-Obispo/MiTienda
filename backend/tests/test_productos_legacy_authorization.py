import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import obtener_usuario_actual
from app.core.database import Base, get_db
from app.modules.products.routes.productos_routers import router as productos_router
from app.modules.users.models.usuarios_models import Usuario


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
app.include_router(productos_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class ProductosLegacyAuthorizationTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides = {get_db: override_get_db}

    def tearDown(self):
        app.dependency_overrides = {get_db: override_get_db}
        Base.metadata.drop_all(bind=engine)

    def _usuario(self, usuario_id: int) -> Usuario:
        return Usuario(
            id=usuario_id,
            email=f"usuario{usuario_id}@example.com",
            hashed_password="hash",
            modo_activo="publicador",
            onboarding_completo=True,
        )

    def _autenticar_como(self, usuario_id: int):
        app.dependency_overrides[obtener_usuario_actual] = (
            lambda: self._usuario(usuario_id)
        )

    def test_crear_producto_legacy_autenticado_devuelve_403(self):
        self._autenticar_como(1)

        response = client.post(
            "/productos/crear",
            json={
                "nombre": "Producto legacy",
                "descripcion": "No habilitado",
                "precio": 10.0,
                "stock": 1,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_actualizar_producto_legacy_autenticado_devuelve_403(self):
        self._autenticar_como(1)

        response = client.put(
            "/productos/1",
            json={"nombre": "Producto editado"},
        )

        self.assertEqual(response.status_code, 403)

    def test_eliminar_producto_legacy_autenticado_devuelve_403(self):
        self._autenticar_como(1)

        response = client.delete("/productos/1")

        self.assertEqual(response.status_code, 403)

    def test_crear_producto_legacy_sin_token_devuelve_401(self):
        response = client.post(
            "/productos/crear",
            json={
                "nombre": "Producto legacy",
                "descripcion": "No habilitado",
                "precio": 10.0,
                "stock": 1,
            },
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
