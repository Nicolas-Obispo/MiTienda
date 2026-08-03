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
from app.modules.moderation.constants import (
    MOTIVO_CONTENIDO_INAPROPIADO,
    RECURSO_TIPO_PUBLICACION,
)
from app.modules.moderation.models.contenido_denuncias_models import (
    ContenidoDenuncia,
)
from app.modules.moderation.routes.contenido_denuncias_routers import (
    router as moderation_router,
)
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.products.models.rubros_models import Rubro
from app.modules.products.models.secciones_models import Seccion
from app.modules.social.models.likes_publicaciones_models import LikePublicacion
from app.modules.social.models.publicaciones_guardadas_models import PublicacionGuardada
from app.modules.social.models.seguidores_models import Seguidores
from app.modules.social.routes.likes_publicaciones_routers import (
    router as likes_publicaciones_router,
)
from app.modules.social.routes.publicaciones_guardadas_routers import (
    router as publicaciones_guardadas_router,
)
from app.modules.social.routes.seguidores_routers import router as seguidores_router
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.stories.models.historias_likes_models import HistoriaLike
from app.modules.stories.models.historias_models import Historia
from app.modules.stories.models.historias_vistas_models import HistoriaVista
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
app.include_router(likes_publicaciones_router)
app.include_router(publicaciones_guardadas_router)
app.include_router(seguidores_router)
app.include_router(moderation_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class SocialHardeningTests(unittest.TestCase):
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
        comercio_id: int = 10,
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
        publicacion_id: int = 20,
        comercio_id: int = 10,
        is_activa: bool = True,
    ) -> Publicacion:
        publicacion = Publicacion(
            id=publicacion_id,
            comercio_id=comercio_id,
            titulo="Oferta",
            descripcion="Descripcion",
            is_activa=is_activa,
        )
        db.add(publicacion)
        db.commit()
        db.refresh(publicacion)
        return publicacion

    def test_like_publicacion_valida_crea_like(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db)
        db.close()

        response = client.post("/likes/publicaciones/20", headers=self._auth_headers())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"liked": True})

    def test_like_publicacion_sin_token_devuelve_401(self):
        response = client.post("/likes/publicaciones/20")

        self.assertEqual(response.status_code, 401)

    def test_like_publicacion_inexistente_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        db.close()

        response = client.post("/likes/publicaciones/999", headers=self._auth_headers())

        self.assertEqual(response.status_code, 404)

    def test_like_publicacion_inactiva_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db, is_activa=False)
        db.close()

        response = client.post("/likes/publicaciones/20", headers=self._auth_headers())

        self.assertEqual(response.status_code, 404)

    def test_like_publicacion_de_comercio_inactivo_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db, activo=False)
        self._crear_publicacion(db)
        db.close()

        response = client.post("/likes/publicaciones/20", headers=self._auth_headers())

        self.assertEqual(response.status_code, 404)

    def test_like_publicacion_repetido_togglea(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db)
        db.close()

        first = client.post("/likes/publicaciones/20", headers=self._auth_headers())
        second = client.post("/likes/publicaciones/20", headers=self._auth_headers())

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json(), {"liked": False})

    def test_guardar_publicacion_valida_crea_guardado(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db)
        db.close()

        response = client.post(
            "/publicaciones/guardadas",
            json={"publicacion_id": 20},
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["publicacion_id"], 20)

    def test_guardar_publicacion_duplicada_es_idempotente(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db)
        db.close()

        first = client.post(
            "/publicaciones/guardadas",
            json={"publicacion_id": 20},
            headers=self._auth_headers(),
        )
        second = client.post(
            "/publicaciones/guardadas",
            json={"publicacion_id": 20},
            headers=self._auth_headers(),
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["id"], second.json()["id"])

    def test_guardar_publicacion_inexistente_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        db.close()

        response = client.post(
            "/publicaciones/guardadas",
            json={"publicacion_id": 999},
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)

    def test_guardar_publicacion_inactiva_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db, is_activa=False)
        db.close()

        response = client.post(
            "/publicaciones/guardadas",
            json={"publicacion_id": 20},
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)

    def test_guardar_publicacion_de_comercio_inactivo_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db, activo=False)
        self._crear_publicacion(db)
        db.close()

        response = client.post(
            "/publicaciones/guardadas",
            json={"publicacion_id": 20},
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)

    def test_quitar_guardado_existente_devuelve_204(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db)
        db.add(PublicacionGuardada(usuario_id=1, publicacion_id=20))
        db.commit()
        db.close()

        response = client.delete(
            "/publicaciones/guardadas/20",
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 204)

    def test_quitar_guardado_inexistente_es_idempotente(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        db.close()

        response = client.delete(
            "/publicaciones/guardadas/999",
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 204)

    def test_listar_guardadas_oculta_publicaciones_no_visibles(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db, comercio_id=10, activo=True)
        self._crear_comercio(db, comercio_id=11, activo=False)
        self._crear_publicacion(db, publicacion_id=20, comercio_id=10, is_activa=True)
        self._crear_publicacion(db, publicacion_id=21, comercio_id=10, is_activa=False)
        self._crear_publicacion(db, publicacion_id=22, comercio_id=11, is_activa=True)
        db.add_all(
            [
                PublicacionGuardada(usuario_id=1, publicacion_id=20),
                PublicacionGuardada(usuario_id=1, publicacion_id=21),
                PublicacionGuardada(usuario_id=1, publicacion_id=22),
            ]
        )
        db.commit()
        db.close()

        response = client.get("/publicaciones/guardadas", headers=self._auth_headers())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["publicacion_id"] for item in response.json()],
            [20],
        )

    def test_seguir_comercio_valido_crea_relacion(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        db.close()

        response = client.post("/seguidores/espacios/10", headers=self._auth_headers())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["siguiendo"])
        self.assertEqual(response.json()["seguidores_count"], 1)

    def test_seguir_comercio_duplicado_es_idempotente(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        db.close()

        first = client.post("/seguidores/espacios/10", headers=self._auth_headers())
        second = client.post("/seguidores/espacios/10", headers=self._auth_headers())

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["seguidores_count"], 1)

    def test_seguir_comercio_inexistente_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        db.close()

        response = client.post("/seguidores/espacios/999", headers=self._auth_headers())

        self.assertEqual(response.status_code, 404)

    def test_seguir_comercio_inactivo_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db, activo=False)
        db.close()

        response = client.post("/seguidores/espacios/10", headers=self._auth_headers())

        self.assertEqual(response.status_code, 404)

    def test_dejar_de_seguir_no_existente_es_idempotente(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        db.close()

        response = client.delete("/seguidores/espacios/10", headers=self._auth_headers())

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["siguiendo"])
        self.assertEqual(response.json()["seguidores_count"], 0)

    def test_dejar_de_seguir_comercio_inactivo_con_relacion_existente_elimina_relacion(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        comercio = self._crear_comercio(db, activo=True)
        db.add(Seguidores(usuario_id=1, comercio_id=comercio.id))
        db.commit()
        comercio.activo = False
        db.commit()
        db.close()

        response = client.delete("/seguidores/espacios/10", headers=self._auth_headers())

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["siguiendo"])
        self.assertIsNone(response.json()["seguidores_count"])

        db = TestingSessionLocal()
        relacion = (
            db.query(Seguidores)
            .filter(
                Seguidores.usuario_id == 1,
                Seguidores.comercio_id == 10,
            )
            .first()
        )
        db.close()
        self.assertIsNone(relacion)

        repeated = client.delete("/seguidores/espacios/10", headers=self._auth_headers())

        self.assertEqual(repeated.status_code, 200)
        self.assertFalse(repeated.json()["siguiendo"])
        self.assertIsNone(repeated.json()["seguidores_count"])

    def test_estado_seguimiento_comercio_inexistente_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        db.close()

        response = client.get(
            "/seguidores/espacios/999/estado",
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)

    def test_contador_comercio_inactivo_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, activo=False)
        db.close()

        response = client.get("/seguidores/espacios/10/contador")

        self.assertEqual(response.status_code, 404)

    def test_mis_espacios_seguidos_oculta_comercios_inactivos(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db, comercio_id=10, activo=True)
        self._crear_comercio(db, comercio_id=11, activo=False)
        db.add_all(
            [
                Seguidores(usuario_id=1, comercio_id=10),
                Seguidores(usuario_id=1, comercio_id=11),
            ]
        )
        db.commit()
        db.close()

        response = client.get("/seguidores/mis-espacios", headers=self._auth_headers())

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [10])

    def test_regresion_denuncias_publicacion_valida_sigue_funcionando(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json={
                "recurso_tipo": RECURSO_TIPO_PUBLICACION,
                "recurso_id": 20,
                "motivo": MOTIVO_CONTENIDO_INAPROPIADO,
            },
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 201)


if __name__ == "__main__":
    unittest.main()
