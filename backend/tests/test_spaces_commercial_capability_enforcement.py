"""Contratos HTTP del enforcement comercial en mutaciones de Spaces."""

from datetime import UTC, date, datetime
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.database import Base, get_db
from app.core.error_handlers import register_exception_handlers
from app.core.model_registry import import_all_models
from app.modules.availability.routes.horarios_atencion_routers import (
    router as horarios_router,
)
from app.modules.feedgo_agenda.routes.feedgo_agenda_routers import (
    router as agenda_router,
)
from app.modules.products.models.rubros_models import Rubro
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.spaces.routes.comercios_routers import router as comercios_router
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
app.include_router(comercios_router)
app.include_router(horarios_router)
app.include_router(agenda_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


def _payload_comercio() -> dict:
    return {
        "nombre": "Espacio comercial",
        "descripcion": "Descripcion",
        "portada_url": "/uploads/portada.jpg",
        "rubro_id": 1,
        "provincia": "Buenos Aires",
        "ciudad": "La Plata",
        "direccion": "Calle 12 345",
        "latitud": -34.9214,
        "longitud": -57.9544,
    }


class SpacesCommercialCapabilityEnforcementTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        self.db = SessionLocal()
        self._user_sequence = 0
        self.db.add(Rubro(id=1, nombre="Servicios", activo=True))
        self.db.commit()
        self._embedding = patch(
            "app.modules.spaces.services.comercios_services.upsert_embedding_comercio"
        )
        self._assignments = patch(
            "app.modules.spaces.services.comercios_services.sincronizar_assignments_comercio_desde_rubros"
        )
        self._specialties = patch(
            "app.modules.spaces.services.comercios_services.sincronizar_especialidades_comercio"
        )
        self._embedding.start()
        self._assignments.start()
        self._specialties.start()

    def tearDown(self):
        self._specialties.stop()
        self._assignments.stop()
        self._embedding.stop()
        self.db.close()
        Base.metadata.drop_all(engine)

    def _usuario(self, *, ready: bool, **overrides) -> Usuario:
        suffix = overrides.pop("suffix", "")
        self._user_sequence += 1
        unique = f"{suffix}{self._user_sequence}"
        values = {
            "email": f"space{unique}@example.com",
            "email_canonical": f"space{unique}@example.com",
            "hashed_password": "hash",
            "modo_activo": "usuario",
            "onboarding_completo": False,
            "provincia": "Buenos Aires" if ready else None,
            "ciudad": "La Plata" if ready else None,
            "fecha_nacimiento": date(1990, 1, 1) if ready else None,
            "email_verified_at": datetime.now(UTC) if ready else None,
            "telefono_e164": f"+549112345678{self._user_sequence}" if ready else None,
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

    @staticmethod
    def _headers(usuario: Usuario) -> dict[str, str]:
        return {"Authorization": f"Bearer {crear_token_jwt({'sub': str(usuario.id)})}"}

    def _comercio(self, usuario: Usuario, *, activo: bool = True) -> Comercio:
        comercio = Comercio(
            usuario_id=usuario.id,
            nombre="Espacio existente",
            descripcion="Descripcion",
            portada_url="/uploads/portada.jpg",
            rubro_id=1,
            provincia="Buenos Aires",
            ciudad="La Plata",
            direccion="Calle 12 345",
            latitud=-34.9214,
            longitud=-57.9544,
            activo=activo,
        )
        self.db.add(comercio)
        self.db.commit()
        self.db.refresh(comercio)
        return comercio

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

    def test_flag_off_preserves_space_mutations_and_mode_is_not_an_authorization_gate(self):
        usuario = self._usuario(ready=False, modo_activo="usuario")
        headers = self._headers(usuario)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            False,
        ):
            created = client.post("/comercios", json=_payload_comercio(), headers=headers)
            self.assertEqual(created.status_code, 201)
            comercio_id = created.json()["id"]

            self.assertEqual(
                client.put(
                    f"/comercios/{comercio_id}",
                    json={"nombre": "Espacio actualizado"},
                    headers=headers,
                ).status_code,
                200,
            )
            self.assertEqual(
                client.put(
                    f"/comercios/{comercio_id}/horarios",
                    json={"franjas": []},
                    headers=headers,
                ).status_code,
                200,
            )
            self.assertEqual(
                client.post(
                    f"/feedgo-agenda/comercios/{comercio_id}/contexto",
                    headers=headers,
                ).status_code,
                200,
            )
            self.assertEqual(
                client.delete(f"/comercios/{comercio_id}", headers=headers).status_code,
                200,
            )
            self.assertEqual(
                client.post(
                    f"/comercios/{comercio_id}/reactivar", headers=headers
                ).status_code,
                200,
            )

    def test_flag_on_allows_ready_user_and_denies_each_missing_readiness_gate(self):
        ready = self._usuario(ready=True, modo_activo="usuario", onboarding_completo=False)
        headers_ready = self._headers(ready)
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
            self.assertEqual(
                client.post("/comercios", json=_payload_comercio(), headers=headers_ready).status_code,
                201,
            )
            unverified_phone = self._usuario(
                ready=True,
                suffix="unverified-phone",
                telefono_verified_at=None,
                telefono_verification_source=None,
            )
            self.assertEqual(
                client.post(
                    "/comercios",
                    json=_payload_comercio(),
                    headers=self._headers(unverified_phone),
                ).status_code,
                201,
            )
            for index, overrides in enumerate(blockers):
                usuario = self._usuario(ready=True, suffix=str(index), **overrides)
                response = client.post(
                    "/comercios", json=_payload_comercio(), headers=self._headers(usuario)
                )
                self._assert_capability_denied(response)

            legal_missing = self._usuario(ready=False, suffix="legal", provincia="Buenos Aires", ciudad="La Plata", fecha_nacimiento=date(1990, 1, 1), email_verified_at=datetime.now(UTC), telefono_e164="+5491198765432", telefono_verified_at=datetime.now(UTC), telefono_verification_source="phone_otp")
            self._assert_capability_denied(
                client.post("/comercios", json=_payload_comercio(), headers=self._headers(legal_missing))
            )

    def test_existing_space_keeps_not_found_and_ownership_before_capability(self):
        owner_incomplete = self._usuario(ready=False, suffix="owner")
        foreign_incomplete = self._usuario(ready=False, suffix="foreign")
        comercio = self._comercio(owner_incomplete)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            self._assert_capability_denied(
                client.put(
                    f"/comercios/{comercio.id}",
                    json={"nombre": "No permitido"},
                    headers=self._headers(owner_incomplete),
                )
            )
            foreign = client.put(
                f"/comercios/{comercio.id}",
                json={"nombre": "Ajeno"},
                headers=self._headers(foreign_incomplete),
            )
            self.assertEqual(foreign.status_code, 403)
            self.assertNotEqual(
                foreign.json().get("code"), "commercial_capability_required"
            )
            self.assertEqual(
                client.put(
                    "/comercios/999999",
                    json={"nombre": "Inexistente"},
                    headers=self._headers(owner_incomplete),
                ).status_code,
                404,
            )

    def test_flag_on_allows_owner_across_all_space_mutations(self):
        usuario = self._usuario(ready=True, suffix="ready")
        comercio = self._comercio(usuario)
        headers = self._headers(usuario)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            self.assertEqual(
                client.put(
                    f"/comercios/{comercio.id}",
                    json={"nombre": "Espacio administrado"},
                    headers=headers,
                ).status_code,
                200,
            )
            self.assertEqual(
                client.put(
                    f"/comercios/{comercio.id}/horarios",
                    json={"franjas": []},
                    headers=headers,
                ).status_code,
                200,
            )
            self.assertEqual(
                client.post(
                    f"/feedgo-agenda/comercios/{comercio.id}/contexto", headers=headers
                ).status_code,
                200,
            )
            created = client.post(
                f"/feedgo-agenda/comercios/{comercio.id}/elementos",
                json={"tipo": "tarea", "titulo": "Tarea administrada"},
                headers=headers,
            )
            self.assertEqual(created.status_code, 200)
            element = created.json()["elemento"]
            updated = client.patch(
                f"/feedgo-agenda/comercios/{comercio.id}/elementos/{element['id']}",
                json={"version_esperada": element["version"], "titulo": "Tarea editada"},
                headers=headers,
            )
            self.assertEqual(updated.status_code, 200)
            self.assertEqual(
                client.patch(
                    f"/feedgo-agenda/comercios/{comercio.id}/elementos/{element['id']}/estado",
                    json={
                        "version_esperada": updated.json()["elemento"]["version"],
                        "estado": "completado",
                    },
                    headers=headers,
                ).status_code,
                200,
            )
            self.assertEqual(
                client.delete(f"/comercios/{comercio.id}", headers=headers).status_code,
                200,
            )
            self.assertEqual(
                client.post(
                    f"/comercios/{comercio.id}/reactivar", headers=headers
                ).status_code,
                200,
            )

    def test_all_existing_space_mutations_use_the_admin_capability(self):
        usuario = self._usuario(ready=False, suffix="admin")
        comercio = self._comercio(usuario)
        headers = self._headers(usuario)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            False,
        ):
            context = client.post(
                f"/feedgo-agenda/comercios/{comercio.id}/contexto", headers=headers
            )
            self.assertEqual(context.status_code, 200)
        with patch(
            "app.modules.users.services.commercial_capabilities_services.settings.COMMERCIAL_CAPABILITIES_ENFORCEMENT_ENABLED",
            True,
        ):
            self.assertEqual(
                client.get(
                    f"/feedgo-agenda/comercios/{comercio.id}/contexto", headers=headers
                ).status_code,
                200,
            )
            self.assertEqual(
                client.get(
                    f"/feedgo-agenda/comercios/{comercio.id}/elementos", headers=headers
                ).status_code,
                200,
            )
            requests = (
                lambda: client.delete(f"/comercios/{comercio.id}", headers=headers),
                lambda: client.post(f"/comercios/{comercio.id}/reactivar", headers=headers),
                lambda: client.put(
                    f"/comercios/{comercio.id}/horarios", json={"franjas": []}, headers=headers
                ),
                lambda: client.post(
                    f"/feedgo-agenda/comercios/{comercio.id}/contexto", headers=headers
                ),
                lambda: client.post(
                    f"/feedgo-agenda/comercios/{comercio.id}/elementos",
                    json={"tipo": "tarea", "titulo": "Tarea privada"},
                    headers=headers,
                ),
                lambda: client.patch(
                    f"/feedgo-agenda/comercios/{comercio.id}/elementos/999999",
                    json={"version_esperada": 1, "titulo": "Cambio"},
                    headers=headers,
                ),
                lambda: client.patch(
                    f"/feedgo-agenda/comercios/{comercio.id}/elementos/999999/estado",
                    json={"version_esperada": 1, "estado": "completado"},
                    headers=headers,
                ),
            )
            for request in requests:
                self._assert_capability_denied(request())


if __name__ == "__main__":
    unittest.main()
