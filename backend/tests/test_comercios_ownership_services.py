import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
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
from app.modules.spaces.services.comercios_ownership_services import (
    ComercioNoEncontradoError,
    ComercioUsuarioNoPropietarioError,
    obtener_comercio_propio_o_error,
)
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


class ComerciosOwnershipServicesTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)

    def tearDown(self):
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

    def test_devuelve_comercio_si_es_propio(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, usuario_id=1)

        comercio = obtener_comercio_propio_o_error(
            db,
            comercio_id=10,
            usuario_autenticado=self._usuario(1),
        )

        db.close()
        self.assertEqual(comercio.id, 10)

    def test_comercio_inexistente_lanza_error_de_dominio(self):
        db = TestingSessionLocal()

        with self.assertRaises(ComercioNoEncontradoError):
            obtener_comercio_propio_o_error(
                db,
                comercio_id=999,
                usuario_autenticado=self._usuario(1),
            )

        db.close()

    def test_comercio_ajeno_lanza_error_de_dominio(self):
        db = TestingSessionLocal()
        self._crear_comercio(db, comercio_id=10, usuario_id=1)

        with self.assertRaises(ComercioUsuarioNoPropietarioError):
            obtener_comercio_propio_o_error(
                db,
                comercio_id=10,
                usuario_autenticado=self._usuario(2),
            )

        db.close()


if __name__ == "__main__":
    unittest.main()
