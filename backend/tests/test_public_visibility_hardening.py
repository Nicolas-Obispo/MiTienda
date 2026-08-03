from datetime import datetime, timedelta, timezone
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
from app.modules.posts.routes.feed_publicaciones_routers import (
    router as feed_publicaciones_router,
)
from app.modules.posts.routes.publicaciones_routers import router as publicaciones_router
from app.modules.posts.routes.ranking_publicaciones_routers import (
    router as ranking_publicaciones_router,
)
from app.modules.products.models.rubros_models import Rubro
from app.modules.products.models.secciones_models import Seccion
from app.modules.search.services.candidate_engine.candidate_sources import (
    PublicacionCandidateSource,
)
from app.modules.search.services.candidate_engine.candidate_types import (
    CandidateGenerationContext,
)
from app.modules.social.models.likes_publicaciones_models import LikePublicacion
from app.modules.social.models.publicaciones_guardadas_models import PublicacionGuardada
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.stories.models.historias_likes_models import HistoriaLike
from app.modules.stories.models.historias_models import Historia
from app.modules.stories.models.historias_vistas_models import HistoriaVista
from app.modules.stories.routes.historias_routers import router as historias_router
from app.modules.users.models.tokens_models import TokenRevocado
from app.modules.users.models.usuarios_documentos_aceptaciones_models import (
    UsuarioDocumentoAceptacion,
)
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
app.include_router(publicaciones_router)
app.include_router(feed_publicaciones_router)
app.include_router(ranking_publicaciones_router)
app.include_router(historias_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class PublicVisibilityHardeningTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides = {get_db: override_get_db}
        db = TestingSessionLocal()
        db.add(Rubro(id=1, nombre="Gastronomia", activo=True))
        db.commit()
        db.close()

    def tearDown(self):
        app.dependency_overrides = {get_db: override_get_db}
        Base.metadata.drop_all(bind=engine)

    def _auth_headers(self, usuario_id: int = 1) -> dict:
        token = crear_token_jwt({"sub": str(usuario_id)})
        return {"Authorization": f"Bearer {token}"}

    def _crear_usuario(self, db, usuario_id: int = 1) -> Usuario:
        usuario = Usuario(
            id=usuario_id,
            email=f"usuario{usuario_id}@example.com",
            hashed_password="hash",
            modo_activo="usuario",
            onboarding_completo=True,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario

    def _crear_comercio(
        self,
        db,
        *,
        comercio_id: int,
        usuario_id: int = 1,
        activo: bool = True,
    ) -> Comercio:
        comercio = Comercio(
            id=comercio_id,
            usuario_id=usuario_id,
            nombre=f"Comercio {comercio_id}",
            descripcion="Descripcion",
            portada_url="/uploads/portada.jpg",
            rubro_id=1,
            provincia="Buenos Aires",
            ciudad="La Plata",
            activo=activo,
        )
        db.add(comercio)
        db.commit()
        db.refresh(comercio)
        return comercio

    def _crear_publicacion(
        self,
        db,
        *,
        publicacion_id: int,
        comercio_id: int,
        activa: bool = True,
        titulo: str = "Pizza destacada",
        views_count: int = 0,
    ) -> Publicacion:
        publicacion = Publicacion(
            id=publicacion_id,
            comercio_id=comercio_id,
            titulo=titulo,
            descripcion="Descripcion pizza",
            is_activa=activa,
            views_count=views_count,
        )
        db.add(publicacion)
        db.commit()
        db.refresh(publicacion)
        return publicacion

    def _crear_historia(
        self,
        db,
        *,
        historia_id: int,
        comercio_id: int,
        activa: bool = True,
    ) -> Historia:
        historia = Historia(
            id=historia_id,
            comercio_id=comercio_id,
            media_url="/uploads/historia.jpg",
            expira_en=datetime.now(timezone.utc) + timedelta(hours=24),
            is_activa=activa,
        )
        db.add(historia)
        db.commit()
        db.refresh(historia)
        return historia

    def test_listado_global_excluye_publicaciones_de_comercio_inactivo(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, activo=True)
        self._crear_comercio(db, comercio_id=11, activo=False)
        self._crear_publicacion(db, publicacion_id=20, comercio_id=10)
        self._crear_publicacion(db, publicacion_id=21, comercio_id=11)
        db.close()

        response = client.get("/publicaciones/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [20])

    def test_publicaciones_por_comercio_inexistente_devuelve_404(self):
        response = client.get("/publicaciones/comercios/999")

        self.assertEqual(response.status_code, 404)

    def test_publicaciones_por_comercio_inactivo_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, activo=False)
        self._crear_publicacion(db, publicacion_id=20, comercio_id=10)
        db.close()

        response = client.get("/publicaciones/comercios/10")

        self.assertEqual(response.status_code, 404)

    def test_detalle_publicacion_de_comercio_inactivo_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, activo=False)
        self._crear_publicacion(db, publicacion_id=20, comercio_id=10)
        db.close()

        response = client.get("/publicaciones/20")

        self.assertEqual(response.status_code, 404)

    def test_detalle_no_incrementa_vistas_si_recurso_no_es_visible(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, activo=False)
        self._crear_publicacion(
            db,
            publicacion_id=20,
            comercio_id=10,
            views_count=5,
        )
        db.close()

        response = client.get("/publicaciones/20")

        self.assertEqual(response.status_code, 404)
        db = TestingSessionLocal()
        publicacion = db.query(Publicacion).filter(Publicacion.id == 20).first()
        db.close()
        self.assertEqual(publicacion.views_count, 5)

    def test_feed_excluye_publicaciones_de_comercio_inactivo(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db, comercio_id=10, activo=True)
        self._crear_comercio(db, comercio_id=11, activo=False)
        self._crear_publicacion(db, publicacion_id=20, comercio_id=10)
        self._crear_publicacion(db, publicacion_id=21, comercio_id=11)
        db.close()

        response = client.get(
            "/feed/publicaciones",
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [20])

    def test_ranking_excluye_publicaciones_de_comercio_inactivo(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, activo=True)
        self._crear_comercio(db, comercio_id=11, activo=False)
        self._crear_publicacion(db, publicacion_id=20, comercio_id=10)
        self._crear_publicacion(db, publicacion_id=21, comercio_id=11)
        db.close()

        response = client.get("/ranking/publicaciones")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [20])

    def test_historias_por_comercio_inexistente_devuelve_404(self):
        response = client.get("/historias/comercios/999")

        self.assertEqual(response.status_code, 404)

    def test_historias_por_comercio_inactivo_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, activo=False)
        self._crear_historia(db, historia_id=30, comercio_id=10)
        db.close()

        response = client.get("/historias/comercios/10")

        self.assertEqual(response.status_code, 404)

    def test_like_historia_inexistente_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        db.close()

        response = client.post("/historias/999/likes", headers=self._auth_headers())

        self.assertEqual(response.status_code, 404)

    def test_like_historia_inactiva_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db, comercio_id=10, activo=True)
        self._crear_historia(db, historia_id=30, comercio_id=10, activa=False)
        db.close()

        response = client.post("/historias/30/likes", headers=self._auth_headers())

        self.assertEqual(response.status_code, 404)

    def test_like_historia_de_comercio_inactivo_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db, comercio_id=10, activo=False)
        self._crear_historia(db, historia_id=30, comercio_id=10, activa=True)
        db.close()

        response = client.post("/historias/30/likes", headers=self._auth_headers())

        self.assertEqual(response.status_code, 404)

    def test_barra_historias_conserva_filtrado_de_comercio_activo(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, activo=True)
        self._crear_comercio(db, comercio_id=11, activo=False)
        self._crear_historia(db, historia_id=30, comercio_id=10)
        self._crear_historia(db, historia_id=31, comercio_id=11)
        db.close()

        response = client.get("/historias/bar")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["comercioId"] for item in response.json()],
            [10],
        )

    def test_busqueda_no_genera_candidatos_desde_publicaciones_de_comercio_inactivo(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, activo=True)
        self._crear_comercio(db, comercio_id=11, activo=False)
        self._crear_publicacion(
            db,
            publicacion_id=20,
            comercio_id=10,
            titulo="Pizza visible",
        )
        self._crear_publicacion(
            db,
            publicacion_id=21,
            comercio_id=11,
            titulo="Pizza oculta",
        )

        source = PublicacionCandidateSource()
        context = CandidateGenerationContext(
            query_original="pizza",
            query_normalizada="pizza",
            limit_por_fuente=10,
        )

        candidates = source.generate(context, db)
        db.close()

        self.assertEqual([candidate.comercio_id for candidate in candidates], [10])


if __name__ == "__main__":
    unittest.main()
