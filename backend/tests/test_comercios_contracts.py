import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.database import Base, get_db
from app.modules.analytics.models.comercios_metricas_sociales_models import (
    ComercioMetricasSociales,
)
from app.modules.ai.models.comercios_embeddings_models import ComercioEmbedding
from app.modules.availability.models.horarios_atencion_models import (
    ComercioHorarioAtencion,
)
from app.modules.discovery.models.taxonomy_models import (
    TaxonomyAssignment,
    TaxonomyNode,
)
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.products.models.rubros_models import Rubro
from app.modules.products.models.secciones_models import Seccion
from app.modules.social.models.likes_publicaciones_models import LikePublicacion
from app.modules.social.models.publicaciones_guardadas_models import (
    PublicacionGuardada,
)
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.spaces.routes.comercios_routers import router as comercios_router
from app.modules.stories.models.historias_likes_models import HistoriaLike
from app.modules.stories.models.historias_models import Historia
from app.modules.stories.models.historias_vistas_models import HistoriaVista
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
app.include_router(comercios_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class ComerciosContractsTests(unittest.TestCase):
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

    def _crear_usuario(self, usuario_id: int = 1) -> Usuario:
        db = TestingSessionLocal()
        usuario = self._usuario(usuario_id)
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        db.close()
        return usuario

    def _auth_headers(self, usuario_id: int = 1) -> dict:
        token = crear_token_jwt({"sub": str(usuario_id)})
        return {"Authorization": f"Bearer {token}"}

    def _crear_comercio(
        self,
        *,
        comercio_id: int = 10,
        usuario_id: int = 1,
        mostrar_direccion_publicamente: bool = True,
    ):
        db = TestingSessionLocal()
        comercio = Comercio(
            id=comercio_id,
            usuario_id=usuario_id,
            nombre=f"Comercio {comercio_id}",
            descripcion="Descripcion",
            portada_url="/uploads/portada.jpg",
            rubro_id=1,
            provincia="Buenos Aires",
            ciudad="La Plata",
            direccion="Calle 12 345",
            latitud=-34.9214,
            longitud=-57.9544,
            maps_url="https://maps.example/espacio",
            mostrar_direccion_publicamente=mostrar_direccion_publicamente,
            activo=True,
        )
        db.add(comercio)
        db.commit()
        db.refresh(comercio)
        db.close()
        return comercio

    def _assert_no_expone_ubicacion_privada(self, data: dict):
        for campo in (
            "direccion",
            "latitud",
            "longitud",
            "maps_url",
            "distancia_km",
        ):
            self.assertNotIn(campo, data)
        self.assertEqual(data["ciudad"], "La Plata")

    def test_obtener_comercio_publico_no_expone_usuario_id(self):
        self._crear_comercio(comercio_id=10, usuario_id=1)

        response = client.get("/comercios/10")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], 10)
        self.assertNotIn("usuario_id", data)
        self.assertFalse(data["es_propietario"])

    def test_obtener_comercio_publico_autenticado_como_dueno_informa_estado_sin_usuario_id(self):
        self._crear_usuario(usuario_id=1)
        self._crear_comercio(comercio_id=10, usuario_id=1)

        response = client.get("/comercios/10", headers=self._auth_headers(1))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn("usuario_id", data)
        self.assertTrue(data["es_propietario"])

    def test_listar_comercios_publicos_no_expone_usuario_id(self):
        self._crear_comercio(comercio_id=10, usuario_id=1)

        response = client.get("/comercios")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertNotIn("usuario_id", data[0])
        self.assertIn("es_propietario", data[0])

    def test_mis_comercios_privado_mantiene_usuario_id(self):
        self._crear_usuario(usuario_id=1)
        self._crear_comercio(comercio_id=10, usuario_id=1)

        response = client.get("/comercios/mis", headers=self._auth_headers(1))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["usuario_id"], 1)
        self.assertEqual(data[0]["id"], 10)

    def test_detalle_publico_oculta_ubicacion_privada(self):
        self._crear_comercio(
            comercio_id=10,
            mostrar_direccion_publicamente=False,
        )

        response = client.get("/comercios/10")

        self.assertEqual(response.status_code, 200)
        self._assert_no_expone_ubicacion_privada(response.json())

    def test_lista_publica_oculta_ubicacion_privada(self):
        self._crear_comercio(
            comercio_id=10,
            mostrar_direccion_publicamente=False,
        )

        response = client.get("/comercios")

        self.assertEqual(response.status_code, 200)
        self._assert_no_expone_ubicacion_privada(response.json()[0])

    def test_explorar_oculta_ubicacion_y_distancia_privadas(self):
        self._crear_comercio(
            comercio_id=10,
            mostrar_direccion_publicamente=False,
        )

        response = client.get(
            "/comercios/activos",
            params={"lat": -34.91, "lng": -57.95},
        )

        self.assertEqual(response.status_code, 200)
        self._assert_no_expone_ubicacion_privada(response.json()[0])

    def test_owner_recibe_ubicacion_privada_completa_en_mis_comercios(self):
        self._crear_usuario(usuario_id=1)
        self._crear_comercio(
            comercio_id=10,
            usuario_id=1,
            mostrar_direccion_publicamente=False,
        )

        response = client.get("/comercios/mis", headers=self._auth_headers(1))

        self.assertEqual(response.status_code, 200)
        data = response.json()[0]
        self.assertEqual(data["direccion"], "Calle 12 345")
        self.assertEqual(data["latitud"], -34.9214)
        self.assertEqual(data["longitud"], -57.9544)
        self.assertEqual(data["maps_url"], "https://maps.example/espacio")
        self.assertFalse(data["mostrar_direccion_publicamente"])

    def test_espacio_publico_preserva_contrato_geografico(self):
        self._crear_comercio(comercio_id=10)

        response = client.get(
            "/comercios/activos",
            params={"lat": -34.91, "lng": -57.95},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()[0]
        self.assertEqual(data["direccion"], "Calle 12 345")
        self.assertEqual(data["latitud"], -34.9214)
        self.assertEqual(data["longitud"], -57.9544)
        self.assertEqual(data["maps_url"], "https://maps.example/espacio")
        self.assertIsInstance(data["distancia_km"], float)


if __name__ == "__main__":
    unittest.main()
