from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import obtener_usuario_actual, obtener_usuario_actual_opcional
from app.core.database import Base, get_db
from app.modules.analytics.models.comercios_metricas_sociales_models import (
    ComercioMetricasSociales,
)
from app.modules.ai.models.comercios_embeddings_models import ComercioEmbedding
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.products.models.rubros_models import Rubro
from app.modules.products.models.secciones_models import Seccion
from app.modules.social.models.likes_publicaciones_models import LikePublicacion
from app.modules.social.models.publicaciones_guardadas_models import PublicacionGuardada
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.stories.models.historias_likes_models import HistoriaLike
from app.modules.stories.models.historias_models import Historia
from app.modules.stories.models.historias_vistas_models import HistoriaVista
from app.modules.stories.routes.historias_routers import router as historias_router
from app.modules.users.models.tokens_models import TokenRevocado
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
app.include_router(historias_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class HistoriasAuthorizationTests(unittest.TestCase):
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

    def _crear_comercio(self, db, *, comercio_id: int, usuario_id: int) -> Comercio:
        comercio = Comercio(
            id=comercio_id,
            usuario_id=usuario_id,
            nombre=f"Comercio {comercio_id}",
            descripcion="Descripcion",
            portada_url="/uploads/portada.jpg",
            rubro_id=1,
            provincia="Buenos Aires",
            ciudad="La Plata",
        )
        db.add(comercio)
        db.commit()
        db.refresh(comercio)
        return comercio

    def _autenticar_como(self, usuario_id: int):
        app.dependency_overrides[obtener_usuario_actual] = (
            lambda: self._usuario(usuario_id)
        )

    def _autenticar_opcional_como(self, usuario_id: int):
        app.dependency_overrides[obtener_usuario_actual_opcional] = (
            lambda: self._usuario(usuario_id)
        )

    def _crear_historia(
        self,
        db,
        *,
        historia_id: int,
        comercio_id: int,
        media_url: str = "/uploads/historia.jpg",
        publicacion_id=None,
    ) -> Historia:
        historia = Historia(
            id=historia_id,
            comercio_id=comercio_id,
            media_url=media_url,
            publicacion_id=publicacion_id,
            expira_en=datetime.now(timezone.utc) + timedelta(hours=24),
            is_activa=True,
        )
        db.add(historia)
        db.commit()
        db.refresh(historia)
        return historia

    def _historia_payload(self):
        expira_en = datetime.now(timezone.utc) + timedelta(hours=24)
        return {
            "media_url": "/uploads/historia.jpg",
            "expira_en": expira_en.isoformat(),
            "is_activa": True,
        }

    def test_crear_historia_como_dueno(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, usuario_id=1)
        db.close()
        self._autenticar_como(1)

        response = client.post(
            "/historias/comercios/10",
            json=self._historia_payload(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["comercio_id"], 10)

    def test_crear_historia_como_no_dueno_devuelve_403(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, usuario_id=1)
        db.close()
        self._autenticar_como(2)

        response = client.post(
            "/historias/comercios/10",
            json=self._historia_payload(),
        )

        self.assertEqual(response.status_code, 403)

    def test_crear_historia_sin_token_devuelve_401(self):
        response = client.post(
            "/historias/comercios/10",
            json=self._historia_payload(),
        )

        self.assertEqual(response.status_code, 401)

    def test_crear_historia_con_comercio_inexistente_devuelve_404(self):
        self._autenticar_como(1)

        response = client.post(
            "/historias/comercios/999",
            json=self._historia_payload(),
        )

        self.assertEqual(response.status_code, 404)

    def test_listado_informa_administracion_solo_al_propietario(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, usuario_id=1)
        self._crear_historia(db, historia_id=20, comercio_id=10)
        db.close()

        response_publica = client.get("/historias/comercios/10")
        self.assertEqual(response_publica.status_code, 200)
        self.assertFalse(response_publica.json()[0]["puede_administrar"])

        self._autenticar_opcional_como(1)
        response_propietario = client.get("/historias/comercios/10")
        self.assertEqual(response_propietario.status_code, 200)
        self.assertTrue(response_propietario.json()[0]["puede_administrar"])

        self._autenticar_opcional_como(2)
        response_ajena = client.get("/historias/comercios/10")
        self.assertEqual(response_ajena.status_code, 200)
        self.assertFalse(response_ajena.json()[0]["puede_administrar"])

    def test_eliminar_historia_sin_token_devuelve_401(self):
        response = client.delete("/historias/20")
        self.assertEqual(response.status_code, 401)

    def test_eliminar_historia_inexistente_devuelve_404(self):
        self._autenticar_como(1)
        response = client.delete("/historias/999")
        self.assertEqual(response.status_code, 404)

    def test_eliminar_historia_ajena_devuelve_403_y_no_la_modifica(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, usuario_id=1)
        self._crear_historia(db, historia_id=20, comercio_id=10)
        db.close()
        self._autenticar_como(2)

        response = client.delete("/historias/20")

        self.assertEqual(response.status_code, 403)
        db = TestingSessionLocal()
        self.assertTrue(db.get(Historia, 20).is_activa)
        db.close()

    def test_soft_delete_preserva_media_relaciones_y_publicacion(self):
        media_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        media_file.close()
        media_path = Path(media_file.name)

        try:
            db = TestingSessionLocal()
            usuario = self._usuario(1)
            db.add(usuario)
            self._crear_comercio(db, comercio_id=10, usuario_id=1)
            publicacion = Publicacion(
                id=30,
                comercio_id=10,
                titulo="Publicacion relacionada",
                imagen_url="/uploads/publicacion.jpg",
                is_activa=True,
            )
            db.add(publicacion)
            db.commit()
            self._crear_historia(
                db,
                historia_id=20,
                comercio_id=10,
                media_url=str(media_path),
                publicacion_id=30,
            )
            self._crear_historia(db, historia_id=21, comercio_id=10)
            db.add(HistoriaVista(historia_id=20, usuario_id=1))
            db.add(HistoriaLike(historia_id=20, usuario_id=1))
            db.commit()
            db.close()
            self._autenticar_como(1)

            response = client.delete("/historias/20")

            self.assertEqual(response.status_code, 204)
            db = TestingSessionLocal()
            self.assertFalse(db.get(Historia, 20).is_activa)
            self.assertTrue(db.get(Historia, 21).is_activa)
            self.assertIsNotNone(db.get(Publicacion, 30))
            self.assertEqual(
                db.query(HistoriaVista).filter_by(historia_id=20).count(), 1
            )
            self.assertEqual(
                db.query(HistoriaLike).filter_by(historia_id=20).count(), 1
            )
            db.close()
            self.assertTrue(media_path.exists())

            listado = client.get("/historias/comercios/10")
            self.assertEqual([item["id"] for item in listado.json()], [21])
        finally:
            media_path.unlink(missing_ok=True)

    def test_historia_con_asset_faltante_se_desactiva_y_barra_se_recalcula(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, usuario_id=1)
        self._crear_historia(
            db,
            historia_id=20,
            comercio_id=10,
            media_url="/uploads/asset-inexistente.jpg",
        )
        db.close()
        self._autenticar_como(1)

        self.assertEqual(client.get("/historias/bar").json()[0]["cantidad"], 1)
        response = client.delete("/historias/20")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(client.get("/historias/bar").json(), [])


if __name__ == "__main__":
    unittest.main()
