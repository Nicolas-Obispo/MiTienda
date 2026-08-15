import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.database import Base, get_db
from app.modules.ai.models.comercios_embeddings_models import ComercioEmbedding
from app.modules.analytics.models.comercios_metricas_sociales_models import (
    ComercioMetricasSociales,
)
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.products.models.rubros_models import Rubro
from app.modules.products.models.secciones_models import Seccion
from app.modules.social.models.likes_publicaciones_models import LikePublicacion
from app.modules.social.models.publicaciones_guardadas_models import (
    PublicacionGuardada,
)
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.stories.models.historias_likes_models import HistoriaLike
from app.modules.stories.models.historias_models import Historia
from app.modules.stories.models.historias_vistas_models import HistoriaVista
from app.modules.users.models.tokens_models import TokenRevocado
from app.modules.users.models.usuarios_models import Usuario
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


class UsuariosContractsTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides = {get_db: override_get_db}

    def tearDown(self):
        app.dependency_overrides = {get_db: override_get_db}
        Base.metadata.drop_all(bind=engine)

    def _crear_usuario(
        self,
        *,
        usuario_id: int = 1,
        email: str = "usuario@example.com",
    ) -> Usuario:
        db = TestingSessionLocal()
        usuario = Usuario(
            id=usuario_id,
            email=email,
            hashed_password="hash",
            avatar_url="/uploads/avatar.jpg",
            color_fondo="#112233",
            modo_activo="publicador",
            onboarding_completo=True,
            provincia="Buenos Aires",
            ciudad="La Plata",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        db.close()
        return usuario

    def _auth_headers(self, usuario_id: int = 1) -> dict:
        token = crear_token_jwt({"sub": str(usuario_id)})
        return {"Authorization": f"Bearer {token}"}

    def test_obtener_mi_perfil_sin_token_devuelve_401(self):
        response = client.get("/usuarios/me")

        self.assertEqual(response.status_code, 401)

    def test_obtener_mi_perfil_autenticado_devuelve_contrato_privado(self):
        self._crear_usuario()

        response = client.get(
            "/usuarios/me",
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["email"], "usuario@example.com")
        self.assertIn("avatar_url", data)
        self.assertIn("color_fondo", data)
        self.assertIn("modo_activo", data)
        self.assertIn("onboarding_completo", data)
        self.assertIn("provincia", data)
        self.assertIn("ciudad", data)

    def test_actualizar_mi_perfil_usa_el_handler_correcto_y_persiste(self):
        self._crear_usuario()
        payload = {
            "provincia": "Santa Fe",
            "ciudad": "Rafaela",
        }

        response = client.patch(
            "/usuarios/me",
            json=payload,
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["provincia"], payload["provincia"])
        self.assertEqual(data["ciudad"], payload["ciudad"])
        self.assertEqual(data["color_fondo"], "#112233")

        db = TestingSessionLocal()
        usuario = db.get(Usuario, 1)
        self.assertEqual(usuario.provincia, payload["provincia"])
        self.assertEqual(usuario.ciudad, payload["ciudad"])
        self.assertEqual(usuario.color_fondo, "#112233")
        db.close()

    def test_obtener_usuario_publico_existente_devuelve_solo_id(self):
        self._crear_usuario()

        response = client.get("/usuarios/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": 1})

    def test_obtener_usuario_publico_no_expone_campos_privados(self):
        self._crear_usuario()

        response = client.get("/usuarios/1")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn("email", data)
        self.assertNotIn("avatar_url", data)
        self.assertNotIn("color_fondo", data)
        self.assertNotIn("modo_activo", data)
        self.assertNotIn("onboarding_completo", data)
        self.assertNotIn("provincia", data)
        self.assertNotIn("ciudad", data)

    def test_obtener_usuario_publico_inexistente_devuelve_404(self):
        response = client.get("/usuarios/999")

        self.assertEqual(response.status_code, 404)

    def test_registrar_usuario_conserva_contrato_privado_actual(self):
        response = client.post(
            "/usuarios/registrar",
            json={
                "email": "nuevo@example.com",
                "password": "password-segura",
                "acepta_terminos": True,
                "acepta_privacidad": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["email"], "nuevo@example.com")
        self.assertIn("avatar_url", data)
        self.assertIn("color_fondo", data)
        self.assertIn("modo_activo", data)
        self.assertIn("onboarding_completo", data)
        self.assertIn("provincia", data)
        self.assertIn("ciudad", data)


if __name__ == "__main__":
    unittest.main()
