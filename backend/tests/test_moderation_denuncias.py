import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

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
from app.modules.moderation.models.contenido_denuncias_models import (
    ContenidoDenuncia,
)
from app.modules.moderation.constants import (
    ESTADO_DENUNCIA_RECIBIDA,
    MOTIVO_CONTENIDO_INAPROPIADO,
    MOTIVO_SPAM,
    RECURSO_TIPO_COMERCIO,
    RECURSO_TIPO_HISTORIA,
    RECURSO_TIPO_PUBLICACION,
)
from app.modules.moderation.routes.contenido_denuncias_routers import (
    router as moderation_router,
)
from app.modules.moderation.schemas.contenido_denuncias_schemas import (
    ContenidoDenunciaCreate,
)
from app.modules.moderation.services.contenido_denuncias_services import (
    crear_denuncia_contenido,
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
app.include_router(moderation_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class ModerationDenunciasTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides = {get_db: override_get_db}

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
            titulo="Publicacion",
            descripcion="Descripcion",
            is_activa=is_activa,
        )
        db.add(publicacion)
        db.commit()
        db.refresh(publicacion)
        return publicacion

    def _crear_historia(
        self,
        db,
        *,
        historia_id: int = 30,
        comercio_id: int = 10,
        is_activa: bool = True,
    ) -> Historia:
        historia = Historia(
            id=historia_id,
            comercio_id=comercio_id,
            media_url="/uploads/historia.jpg",
            expira_en=datetime.utcnow() + timedelta(days=1),
            is_activa=is_activa,
        )
        db.add(historia)
        db.commit()
        db.refresh(historia)
        return historia

    def _payload(
        self,
        *,
        recurso_tipo: str = RECURSO_TIPO_COMERCIO,
        recurso_id: int = 10,
        motivo: str = MOTIVO_SPAM,
    ) -> dict:
        return {
            "recurso_tipo": recurso_tipo,
            "recurso_id": recurso_id,
            "motivo": motivo,
            "detalle": "Detalle opcional",
        }

    def test_denuncia_sin_token_devuelve_401(self):
        response = client.post("/moderacion/denuncias", json=self._payload())

        self.assertEqual(response.status_code, 401)

    def test_recurso_tipo_invalido_devuelve_422(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(recurso_tipo="usuario"),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 422)

    def test_motivo_invalido_devuelve_422(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(motivo="motivo_libre"),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 422)

    def test_comercio_valido_crea_denuncia(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["recurso_tipo"], RECURSO_TIPO_COMERCIO)

    def test_publicacion_activa_crea_denuncia(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(
                recurso_tipo=RECURSO_TIPO_PUBLICACION,
                recurso_id=20,
            ),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["recurso_tipo"], RECURSO_TIPO_PUBLICACION)

    def test_historia_activa_crea_denuncia(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_historia(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(
                recurso_tipo=RECURSO_TIPO_HISTORIA,
                recurso_id=30,
            ),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["recurso_tipo"], RECURSO_TIPO_HISTORIA)

    def test_recurso_inexistente_devuelve_404(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(recurso_id=999),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)

    def test_publicacion_inactiva_no_es_denunciable(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db, is_activa=False)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(
                recurso_tipo=RECURSO_TIPO_PUBLICACION,
                recurso_id=20,
            ),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)

    def test_historia_inactiva_no_es_denunciable(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_historia(db, is_activa=False)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(
                recurso_tipo=RECURSO_TIPO_HISTORIA,
                recurso_id=30,
            ),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)

    def test_comercio_inactivo_no_es_denunciable(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db, activo=False)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 404)

    def test_duplicado_exacto_es_idempotente(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        db.close()

        primera = client.post(
            "/moderacion/denuncias",
            json=self._payload(),
            headers=self._auth_headers(),
        )
        segunda = client.post(
            "/moderacion/denuncias",
            json=self._payload(),
            headers=self._auth_headers(),
        )

        self.assertEqual(primera.status_code, 201)
        self.assertEqual(segunda.status_code, 200)
        self.assertEqual(primera.json()["id"], segunda.json()["id"])
        db = TestingSessionLocal()
        total = db.query(ContenidoDenuncia).count()
        db.close()
        self.assertEqual(total, 1)

    def test_motivos_diferentes_pueden_coexistir(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        db.close()

        client.post(
            "/moderacion/denuncias",
            json=self._payload(motivo=MOTIVO_SPAM),
            headers=self._auth_headers(),
        )
        client.post(
            "/moderacion/denuncias",
            json=self._payload(motivo=MOTIVO_CONTENIDO_INAPROPIADO),
            headers=self._auth_headers(),
        )

        db = TestingSessionLocal()
        total = db.query(ContenidoDenuncia).count()
        db.close()
        self.assertEqual(total, 2)

    def test_usuarios_diferentes_pueden_denunciar_mismo_recurso(self):
        db = TestingSessionLocal()
        self._crear_usuario(db, usuario_id=1)
        self._crear_usuario(db, usuario_id=2)
        self._crear_comercio(db)
        db.close()

        client.post(
            "/moderacion/denuncias",
            json=self._payload(),
            headers=self._auth_headers(1),
        )
        client.post(
            "/moderacion/denuncias",
            json=self._payload(),
            headers=self._auth_headers(2),
        )

        db = TestingSessionLocal()
        total = db.query(ContenidoDenuncia).count()
        db.close()
        self.assertEqual(total, 2)

    def test_estado_se_genera_como_recibida(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.json()["estado"], ESTADO_DENUNCIA_RECIBIDA)

    def test_timestamp_se_genera_en_backend(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(),
            headers=self._auth_headers(),
        )

        self.assertIsNotNone(response.json()["creado_en"])

    def test_usuario_id_del_payload_es_ignorado(self):
        db = TestingSessionLocal()
        self._crear_usuario(db, usuario_id=1)
        self._crear_usuario(db, usuario_id=999)
        self._crear_comercio(db)
        db.close()

        payload = self._payload()
        payload["usuario_id"] = 999
        response = client.post(
            "/moderacion/denuncias",
            json=payload,
            headers=self._auth_headers(1),
        )

        self.assertEqual(response.status_code, 201)
        db = TestingSessionLocal()
        denuncia = db.query(ContenidoDenuncia).first()
        db.close()
        self.assertEqual(denuncia.usuario_id, 1)

    def test_respuesta_no_expone_usuario_id(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(),
            headers=self._auth_headers(),
        )

        self.assertNotIn("usuario_id", response.json())

    def test_denuncia_no_cambia_estado_del_recurso(self):
        db = TestingSessionLocal()
        self._crear_usuario(db)
        self._crear_comercio(db)
        self._crear_publicacion(db)
        db.close()

        response = client.post(
            "/moderacion/denuncias",
            json=self._payload(
                recurso_tipo=RECURSO_TIPO_PUBLICACION,
                recurso_id=20,
            ),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 201)
        db = TestingSessionLocal()
        publicacion = db.query(Publicacion).filter(Publicacion.id == 20).first()
        db.close()
        self.assertTrue(publicacion.is_activa)

    def test_rollback_ante_error_de_persistencia(self):
        db = TestingSessionLocal()
        usuario = self._crear_usuario(db)
        self._crear_comercio(db)
        payload = ContenidoDenunciaCreate(**self._payload())

        with patch.object(db, "commit", side_effect=RuntimeError("fallo")):
            with self.assertRaises(RuntimeError):
                crear_denuncia_contenido(db=db, payload=payload, usuario=usuario)

        self.assertEqual(db.query(ContenidoDenuncia).count(), 0)
        db.close()

    def test_tabla_restricciones_e_indices_declarados(self):
        tabla = ContenidoDenuncia.__table__
        unique_names = {c.name for c in tabla.constraints}
        index_names = {i.name for i in tabla.indexes}
        fk_columns = {
            fk.parent.name
            for constraint in tabla.constraints
            for fk in getattr(constraint, "elements", [])
        }

        self.assertIn(
            "uq_contenido_denuncias_usuario_recurso_motivo",
            unique_names,
        )
        self.assertIn("ix_contenido_denuncias_recurso", index_names)
        self.assertIn("ix_contenido_denuncias_usuario_id", index_names)
        self.assertIn("usuario_id", fk_columns)


if __name__ == "__main__":
    unittest.main()
