"""Contratos HTTP del enforcement comercial de publicaciones e historias."""

from datetime import UTC, date, datetime, timedelta
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import obtener_usuario_actual
from app.core.database import Base, get_db
from app.core.error_handlers import register_exception_handlers
from app.core.model_registry import import_all_models
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.posts.routes.publicaciones_routers import router as publicaciones_router
from app.modules.products.models.rubros_models import Rubro
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.stories.models.historias_models import Historia
from app.modules.stories.routes.historias_routers import router as historias_router
from app.modules.users.models.usuarios_documentos_aceptaciones_models import (
    UsuarioDocumentoAceptacion,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.documentos_aceptacion_services import (
    CANAL_REGISTRO_WEB,
    DOCUMENTOS_OBLIGATORIOS_REGISTRO,
    ESTADO_ACEPTADO,
    METODO_CHECKBOX_EXPLICITO,
)


import_all_models()
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
SessionLocal = sessionmaker(bind=engine)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
register_exception_handlers(app)
app.include_router(publicaciones_router)
app.include_router(historias_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


class ContentCommercialCapabilityEnforcementTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        self.db = SessionLocal()
        self._sequence = 0
        self.db.add(Rubro(id=1, nombre="Servicios", activo=True))
        self.db.commit()

    def tearDown(self):
        app.dependency_overrides = {get_db: override_get_db}
        self.db.close()
        Base.metadata.drop_all(engine)

    def _usuario(self, *, ready: bool, **overrides) -> Usuario:
        self._sequence += 1
        values = {
            "email": f"content{self._sequence}@example.com",
            "email_canonical": f"content{self._sequence}@example.com",
            "hashed_password": "hash",
            "modo_activo": "usuario",
            "onboarding_completo": False,
            "provincia": "Buenos Aires" if ready else None,
            "ciudad": "La Plata" if ready else None,
            "fecha_nacimiento": date(1990, 1, 1) if ready else None,
            "email_verified_at": datetime.now(UTC) if ready else None,
            "telefono_e164": f"+549112345678{self._sequence}" if ready else None,
            "telefono_verified_at": datetime.now(UTC) if ready else None,
            "telefono_verification_source": "phone_otp" if ready else None,
        }
        values.update(overrides)
        usuario = Usuario(**values)
        self.db.add(usuario)
        self.db.flush()
        if ready:
            for document in DOCUMENTOS_OBLIGATORIOS_REGISTRO:
                self.db.add(
                    UsuarioDocumentoAceptacion(
                        usuario_id=usuario.id,
                        documento_tipo=document.tipo,
                        documento_version=document.version,
                        documento_referencia=document.referencia,
                        canal=CANAL_REGISTRO_WEB,
                        metodo=METODO_CHECKBOX_EXPLICITO,
                        estado=ESTADO_ACEPTADO,
                    )
                )
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def _as_current_user(self, usuario: Usuario) -> None:
        app.dependency_overrides[obtener_usuario_actual] = lambda: usuario

    def _comercio(self, usuario: Usuario) -> Comercio:
        comercio = Comercio(
            usuario_id=usuario.id,
            nombre="Espacio de contenido",
            descripcion="Descripcion",
            portada_url="/uploads/portada.jpg",
            rubro_id=1,
            provincia="Buenos Aires",
            ciudad="La Plata",
            direccion="Calle 12 345",
            latitud=-34.9214,
            longitud=-57.9544,
            activo=True,
        )
        self.db.add(comercio)
        self.db.commit()
        self.db.refresh(comercio)
        return comercio

    def _publicacion(self, comercio: Comercio) -> Publicacion:
        publicacion = Publicacion(
            comercio_id=comercio.id,
            titulo="Publicacion existente",
            descripcion="Descripcion",
            is_activa=True,
        )
        self.db.add(publicacion)
        self.db.commit()
        self.db.refresh(publicacion)
        return publicacion

    def _historia(self, comercio: Comercio) -> Historia:
        historia = Historia(
            comercio_id=comercio.id,
            media_url="/uploads/historia.jpg",
            expira_en=datetime.now(UTC) + timedelta(hours=24),
            is_activa=True,
        )
        self.db.add(historia)
        self.db.commit()
        self.db.refresh(historia)
        return historia

    @staticmethod
    def _assert_capability_denied(response):
        assert response.status_code == 403
        assert response.json() == {
            "detail": "No autorizado",
            "code": "commercial_capability_required",
        }
        assert "telefono" not in response.text.lower()
        assert "email" not in response.text.lower()
        assert "perfil" not in response.text.lower()

    @staticmethod
    def _publicacion_payload() -> dict:
        return {"titulo": "Nueva publicacion", "descripcion": "Descripcion"}

    @staticmethod
    def _historia_payload() -> dict:
        return {
            "media_url": "/uploads/nueva-historia.jpg",
            "expira_en": (datetime.now(UTC) + timedelta(hours=24)).isoformat(),
        }

    def test_flag_off_preserves_content_mutations(self):
        owner = self._usuario(ready=False, modo_activo="usuario")
        comercio = self._comercio(owner)
        publicacion = self._publicacion(comercio)
        historia = self._historia(comercio)
        self._as_current_user(owner)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            False,
        ):
            self.assertEqual(
                client.post(
                    f"/publicaciones/comercios/{comercio.id}",
                    json=self._publicacion_payload(),
                ).status_code,
                201,
            )
            self.assertEqual(
                client.post(
                    f"/historias/comercios/{comercio.id}", json=self._historia_payload()
                ).status_code,
                201,
            )
            self.assertEqual(client.delete(f"/publicaciones/{publicacion.id}").status_code, 204)
            self.assertEqual(client.delete(f"/historias/{historia.id}").status_code, 204)

    def test_flag_on_allows_ready_owner_for_create_and_delete(self):
        owner = self._usuario(ready=True, modo_activo="usuario", onboarding_completo=False)
        comercio = self._comercio(owner)
        publicacion = self._publicacion(comercio)
        historia = self._historia(comercio)
        self._as_current_user(owner)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            self.assertEqual(
                client.post(
                    f"/publicaciones/comercios/{comercio.id}",
                    json=self._publicacion_payload(),
                ).status_code,
                201,
            )
            self.assertEqual(
                client.post(
                    f"/historias/comercios/{comercio.id}", json=self._historia_payload()
                ).status_code,
                201,
            )
            self.assertEqual(client.delete(f"/publicaciones/{publicacion.id}").status_code, 204)
            self.assertEqual(client.delete(f"/historias/{historia.id}").status_code, 204)

    def test_flag_on_denies_all_documented_capability_blockers(self):
        blockers = (
            {"provincia": None},
            {"email_verified_at": None},
            {
                "telefono_e164": None,
                "telefono_verified_at": None,
                "telefono_verification_source": None,
            },
            {"fecha_nacimiento": date(2010, 1, 1)},
        )
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            unverified_phone = self._usuario(
                ready=True,
                email="content-unverified-phone@example.com",
                telefono_verified_at=None,
                telefono_verification_source=None,
            )
            unverified_comercio = self._comercio(unverified_phone)
            self._as_current_user(unverified_phone)
            self.assertEqual(
                client.post(
                    f"/publicaciones/comercios/{unverified_comercio.id}",
                    json=self._publicacion_payload(),
                ).status_code,
                201,
            )
            for overrides in blockers:
                owner = self._usuario(ready=True, **overrides)
                comercio = self._comercio(owner)
                self._as_current_user(owner)
                self._assert_capability_denied(
                    client.post(
                        f"/publicaciones/comercios/{comercio.id}",
                        json=self._publicacion_payload(),
                    )
                )

            legal_missing = self._usuario(
                ready=False,
                provincia="Buenos Aires",
                ciudad="La Plata",
                fecha_nacimiento=date(1990, 1, 1),
                email_verified_at=datetime.now(UTC),
                telefono_e164="+5491123456789",
                telefono_verified_at=datetime.now(UTC),
                telefono_verification_source="phone_otp",
            )
            comercio = self._comercio(legal_missing)
            self._as_current_user(legal_missing)
            self._assert_capability_denied(
                client.post(
                    f"/historias/comercios/{comercio.id}", json=self._historia_payload()
                )
            )

    def test_ownership_and_not_found_precede_capability(self):
        owner = self._usuario(ready=False)
        foreign = self._usuario(ready=False)
        comercio = self._comercio(owner)
        publicacion = self._publicacion(comercio)
        historia = self._historia(comercio)
        self._as_current_user(foreign)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            for response in (
                client.post(
                    f"/publicaciones/comercios/{comercio.id}",
                    json=self._publicacion_payload(),
                ),
                client.post(
                    f"/historias/comercios/{comercio.id}", json=self._historia_payload()
                ),
                client.delete(f"/publicaciones/{publicacion.id}"),
                client.delete(f"/historias/{historia.id}"),
            ):
                self.assertEqual(response.status_code, 403)
                self.assertNotEqual(
                    response.json().get("code"), "commercial_capability_required"
                )
            self.assertEqual(
                client.delete("/publicaciones/999999").status_code,
                404,
            )
            self.assertEqual(client.delete("/historias/999999").status_code, 404)

    def test_personal_story_interactions_do_not_use_commercial_capability(self):
        owner = self._usuario(ready=True)
        visitor = self._usuario(ready=False)
        comercio = self._comercio(owner)
        historia = self._historia(comercio)
        self._as_current_user(visitor)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            self.assertEqual(
                client.post(f"/historias/{historia.id}/vistas").status_code,
                201,
            )
            self.assertEqual(
                client.post(f"/historias/{historia.id}/likes").status_code,
                200,
            )


if __name__ == "__main__":
    unittest.main()
