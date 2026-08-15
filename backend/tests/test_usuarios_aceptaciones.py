import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
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
from app.modules.users.models.usuarios_documentos_aceptaciones_models import (
    UsuarioDocumentoAceptacion,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes.usuarios_routers import router as usuarios_router
from app.modules.users.schemas.usuarios_schemas import UsuarioCreate
from app.modules.users.services.documentos_aceptacion_services import (
    CANAL_REGISTRO_WEB,
    DOCUMENTO_POLITICA_PRIVACIDAD,
    DOCUMENTO_TERMINOS_CONDICIONES,
    DOCUMENTO_VERSION_INICIAL,
    ESTADO_ACEPTADO,
    METODO_CHECKBOX_EXPLICITO,
)
from app.modules.users.services.usuarios_services import crear_usuario


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


class UsuariosAceptacionesTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides = {get_db: override_get_db}

    def tearDown(self):
        app.dependency_overrides = {get_db: override_get_db}
        Base.metadata.drop_all(bind=engine)

    def _payload_valido(self, email: str = "nuevo@example.com") -> dict:
        return {
            "email": email,
            "password": "password-segura",
            "acepta_terminos": True,
            "acepta_privacidad": True,
        }

    def _registrar_usuario_valido(self, email: str = "nuevo@example.com"):
        return client.post(
            "/usuarios/registrar",
            json=self._payload_valido(email=email),
        )

    def _auth_headers(self, usuario_id: int = 1) -> dict:
        token = crear_token_jwt({"sub": str(usuario_id)})
        return {"Authorization": f"Bearer {token}"}

    def test_documentos_publicos_comparten_version_con_evidencia_backend(self):
        response = client.get("/usuarios/documentos-vigentes")

        self.assertEqual(response.status_code, 200)
        by_type = {item["tipo"]: item for item in response.json()}
        self.assertEqual(
            by_type[DOCUMENTO_TERMINOS_CONDICIONES],
            {
                "tipo": DOCUMENTO_TERMINOS_CONDICIONES,
                "version": DOCUMENTO_VERSION_INICIAL,
                "referencia": f"{DOCUMENTO_TERMINOS_CONDICIONES}:{DOCUMENTO_VERSION_INICIAL}",
                "url": "/terminos-y-condiciones",
            },
        )
        self.assertEqual(
            by_type[DOCUMENTO_POLITICA_PRIVACIDAD]["version"],
            DOCUMENTO_VERSION_INICIAL,
        )

    def test_registro_sin_aceptacion_terminos_devuelve_422(self):
        payload = self._payload_valido()
        payload.pop("acepta_terminos")

        response = client.post("/usuarios/registrar", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_registro_con_terminos_false_devuelve_422(self):
        payload = self._payload_valido()
        payload["acepta_terminos"] = False

        response = client.post("/usuarios/registrar", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_registro_sin_aceptacion_privacidad_devuelve_422(self):
        payload = self._payload_valido()
        payload.pop("acepta_privacidad")

        response = client.post("/usuarios/registrar", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_registro_con_privacidad_false_devuelve_422(self):
        payload = self._payload_valido()
        payload["acepta_privacidad"] = False

        response = client.post("/usuarios/registrar", json=payload)

        self.assertEqual(response.status_code, 422)

    def test_registro_valido_persiste_dos_evidencias_separadas(self):
        response = self._registrar_usuario_valido()

        self.assertEqual(response.status_code, 200)
        db = TestingSessionLocal()
        evidencias = (
            db.query(UsuarioDocumentoAceptacion)
            .filter(UsuarioDocumentoAceptacion.usuario_id == response.json()["id"])
            .order_by(UsuarioDocumentoAceptacion.documento_tipo)
            .all()
        )
        db.close()

        self.assertEqual(len(evidencias), 2)
        tipos = {e.documento_tipo for e in evidencias}
        self.assertEqual(
            tipos,
            {DOCUMENTO_TERMINOS_CONDICIONES, DOCUMENTO_POLITICA_PRIVACIDAD},
        )

    def test_evidencias_registran_metadatos_controlados_por_backend(self):
        response = self._registrar_usuario_valido()

        self.assertEqual(response.status_code, 200)
        db = TestingSessionLocal()
        evidencias = db.query(UsuarioDocumentoAceptacion).all()
        db.close()

        self.assertEqual(len(evidencias), 2)
        for evidencia in evidencias:
            self.assertEqual(evidencia.documento_version, DOCUMENTO_VERSION_INICIAL)
            self.assertEqual(evidencia.estado, ESTADO_ACEPTADO)
            self.assertEqual(evidencia.canal, CANAL_REGISTRO_WEB)
            self.assertEqual(evidencia.metodo, METODO_CHECKBOX_EXPLICITO)
            self.assertIsNotNone(evidencia.aceptado_en)
            self.assertEqual(
                evidencia.documento_referencia,
                f"{evidencia.documento_tipo}:{evidencia.documento_version}",
            )

    def test_crear_usuario_revierte_si_falla_evidencia(self):
        db = TestingSessionLocal()
        payload = UsuarioCreate(**self._payload_valido())

        with patch(
            "app.modules.users.services.documentos_aceptacion_services"
            ".crear_evidencias_aceptacion_registro",
            side_effect=RuntimeError("fallo controlado"),
        ):
            with self.assertRaises(RuntimeError):
                crear_usuario(db, payload)

        self.assertEqual(db.query(Usuario).count(), 0)
        self.assertEqual(db.query(UsuarioDocumentoAceptacion).count(), 0)
        db.close()

    def test_usuario_duplicado_mantiene_conflicto_actual(self):
        self._registrar_usuario_valido(email="duplicado@example.com")

        response = self._registrar_usuario_valido(email="duplicado@example.com")

        self.assertEqual(response.status_code, 409)

    def test_login_continua_funcionando(self):
        self._registrar_usuario_valido(email="login@example.com")

        response = client.post(
            "/usuarios/login",
            json={
                "email": "login@example.com",
                "password": "password-segura",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())

    def test_usuarios_me_mantiene_contrato_privado_sin_evidencias(self):
        self._registrar_usuario_valido()

        response = client.get("/usuarios/me", headers=self._auth_headers())

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("email", data)
        self.assertNotIn("documentos_aceptaciones", data)

    def test_usuario_publico_mantiene_contrato_publico_sin_evidencias(self):
        self._registrar_usuario_valido()

        response = client.get("/usuarios/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": 1})

    def test_unicidad_usuario_documento_version(self):
        response = self._registrar_usuario_valido()
        usuario_id = response.json()["id"]

        db = TestingSessionLocal()
        duplicada = UsuarioDocumentoAceptacion(
            usuario_id=usuario_id,
            documento_tipo=DOCUMENTO_TERMINOS_CONDICIONES,
            documento_version=DOCUMENTO_VERSION_INICIAL,
            canal=CANAL_REGISTRO_WEB,
            metodo=METODO_CHECKBOX_EXPLICITO,
            estado=ESTADO_ACEPTADO,
            documento_referencia=(
                f"{DOCUMENTO_TERMINOS_CONDICIONES}:{DOCUMENTO_VERSION_INICIAL}"
            ),
        )
        db.add(duplicada)

        with self.assertRaises(IntegrityError):
            db.commit()

        db.rollback()
        db.close()


if __name__ == "__main__":
    unittest.main()
