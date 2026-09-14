from datetime import date, datetime, timezone
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
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

import_all_models()


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
        self.assertIn("email_verified_at", data)
        self.assertIn("email_verification_source", data)
        self.assertIn("fecha_nacimiento", data)
        self.assertIn("telefono_e164", data)
        self.assertIn("telefono_verified_at", data)
        self.assertIn("telefono_verification_source", data)
        self.assertFalse(data["perfil_completo"])
        self.assertEqual(
            data["campos_perfil_faltantes"],
            ["fecha_nacimiento", "telefono", "email_verificado"],
        )
        self.assertEqual(response.headers["cache-control"], "no-store, private")

    def test_me_deriva_perfil_completo_sin_usar_onboarding(self):
        self._crear_usuario()
        db = TestingSessionLocal()
        usuario = db.get(Usuario, 1)
        usuario.onboarding_completo = False
        usuario.fecha_nacimiento = date(1996, 8, 14)
        usuario.email_verified_at = datetime(2026, 9, 6, tzinfo=timezone.utc)
        usuario.email_verification_source = "email_link"
        usuario.telefono_e164 = "+5491123456789"
        usuario.telefono_verified_at = datetime(2026, 9, 6, tzinfo=timezone.utc)
        usuario.telefono_verification_source = "phone_otp"
        db.commit()
        db.close()

        response = client.get("/usuarios/me", headers=self._auth_headers())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["perfil_completo"])
        self.assertEqual(response.json()["campos_perfil_faltantes"], [])
        self.assertFalse(response.json()["onboarding_completo"])

    def test_estado_verificacion_es_solo_lectura_en_me(self):
        self._crear_usuario()

        response = client.patch(
            "/usuarios/me",
            json={
                "email_verified_at": "2026-09-05T12:00:00Z",
                "email_verification_source": "email_link",
            },
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["email_verified_at"])
        self.assertIsNone(response.json()["email_verification_source"])

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

    def test_patch_me_canonicaliza_telefono_y_expone_datos_privados(self):
        self._crear_usuario()
        response = client.patch(
            "/usuarios/me",
            json={
                "fecha_nacimiento": "1996-08-14",
                "telefono_e164": "+54 9 11 2345-6789",
            },
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store, private")
        self.assertEqual(response.json()["fecha_nacimiento"], "1996-08-14")
        self.assertEqual(response.json()["telefono_e164"], "+5491123456789")
        self.assertIsNone(response.json()["telefono_verified_at"])
        self.assertIsNone(response.json()["telefono_verification_source"])
        db = TestingSessionLocal()
        usuario = db.get(Usuario, 1)
        self.assertEqual(usuario.fecha_nacimiento, date(1996, 8, 14))
        self.assertEqual(usuario.telefono_e164, "+5491123456789")
        self.assertTrue(usuario.onboarding_completo)
        db.close()

    def test_patch_me_no_reemplaza_telefono_verificado(self):
        self._crear_usuario()
        db = TestingSessionLocal()
        usuario = db.get(Usuario, 1)
        usuario.telefono_e164 = "+5491123456789"
        usuario.telefono_verified_at = datetime(2026, 9, 6, tzinfo=timezone.utc)
        usuario.telefono_verification_source = "phone_otp"
        db.commit()
        db.close()

        response = client.patch(
            "/usuarios/me",
            json={"telefono_e164": "+54 9 11 3456-7890"},
            headers=self._auth_headers(),
        )
        self.assertEqual(response.status_code, 400)
        db = TestingSessionLocal()
        usuario = db.get(Usuario, 1)
        self.assertEqual(usuario.telefono_e164, "+5491123456789")
        self.assertEqual(usuario.telefono_verification_source, "phone_otp")
        db.close()

    def test_patch_me_rechaza_telefono_invalido(self):
        self._crear_usuario()
        response = client.patch(
            "/usuarios/me",
            json={"telefono_e164": "123"},
            headers=self._auth_headers(),
        )
        self.assertEqual(response.status_code, 400)

    def test_patch_me_respeta_unicidad_global_de_telefono(self):
        self._crear_usuario(usuario_id=1, email="one@example.com")
        self._crear_usuario(usuario_id=2, email="two@example.com")
        first = client.patch(
            "/usuarios/me",
            json={"telefono_e164": "+54 9 11 2345-6789"},
            headers=self._auth_headers(1),
        )
        second = client.patch(
            "/usuarios/me",
            json={"telefono_e164": "+5491123456789"},
            headers=self._auth_headers(2),
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(second.json()["detail"], "telefono_no_disponible")

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
        self.assertNotIn("fecha_nacimiento", data)
        self.assertNotIn("telefono_e164", data)
        self.assertNotIn("telefono_verified_at", data)
        self.assertNotIn("telefono_verification_source", data)
        self.assertNotIn("perfil_completo", data)
        self.assertNotIn("campos_perfil_faltantes", data)

    def test_obtener_usuario_publico_inexistente_devuelve_404(self):
        response = client.get("/usuarios/999")

        self.assertEqual(response.status_code, 404)

    def test_registrar_usuario_conserva_contrato_privado_actual(self):
        response = client.post(
            "/usuarios/registrar",
            json={
                "email": "nuevo@example.com",
                "password": "Password1-segura",
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
