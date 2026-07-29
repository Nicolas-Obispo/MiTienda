from datetime import datetime, timedelta, timezone
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import obtener_usuario_actual
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


if __name__ == "__main__":
    unittest.main()
