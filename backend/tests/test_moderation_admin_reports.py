import unittest
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.modules.administration.capabilities import (
    MODERATION_REPORTS_READ,
    OPERATIONS_STATUS_READ,
)
from app.modules.administration.services.administrative_authorization_services import (
    record_administrative_capability_change,
)
from app.modules.moderation.constants import (
    ESTADO_DENUNCIA_RECIBIDA,
    MOTIVO_OTRO,
    MOTIVO_SPAM,
    RECURSO_TIPO_COMERCIO,
    RECURSO_TIPO_HISTORIA,
)
from app.modules.moderation.models.contenido_denuncias_models import (
    ContenidoDenuncia,
)
from app.modules.moderation.routes.contenido_denuncias_routers import (
    router as moderation_router,
)
from app.modules.products.models.rubros_models import Rubro
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.stories.models.historias_models import Historia
from app.modules.users.models.usuarios_models import Usuario

import_all_models()

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


class ModerationAdminReportsTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides = {get_db: override_get_db}

    def tearDown(self):
        app.dependency_overrides = {get_db: override_get_db}
        Base.metadata.drop_all(bind=engine)

    def _create_user(self, usuario_id: int, modo_activo: str = "usuario"):
        db = TestingSessionLocal()
        db.add(
            Usuario(
                id=usuario_id,
                email=f"private-{usuario_id}@example.com",
                hashed_password="hash",
                modo_activo=modo_activo,
                onboarding_completo=True,
                provincia="Privada",
                ciudad="Privada",
            )
        )
        db.commit()
        db.close()

    def _headers(self, usuario_id: int):
        token = crear_token_jwt({"sub": str(usuario_id)})
        return {"Authorization": f"Bearer {token}"}

    def _change_capability(self, usuario_id: int, capability: str, action: str):
        db = TestingSessionLocal()
        record_administrative_capability_change(
            db,
            usuario_id=usuario_id,
            capability=capability,
            action=action,
            source="test",
            reason="Contrato 97.2",
        )
        db.close()

    def _create_commerce(self, comercio_id: int = 10, activo: bool = True):
        db = TestingSessionLocal()
        if db.get(Rubro, 1) is None:
            db.add(Rubro(id=1, nombre="Rubro", activo=True))
            db.flush()
        db.add(
            Comercio(
                id=comercio_id,
                usuario_id=1,
                nombre="Comercio",
                descripcion="Contenido actual",
                portada_url="/uploads/portada.jpg",
                rubro_id=1,
                provincia="Buenos Aires",
                ciudad="La Plata",
                activo=activo,
            )
        )
        db.commit()
        db.close()

    def _create_story(self, historia_id: int = 30, activa: bool = True):
        db = TestingSessionLocal()
        db.add(
            Historia(
                id=historia_id,
                comercio_id=10,
                media_url="/uploads/historia.jpg",
                expira_en=datetime(2030, 1, 1),
                is_activa=activa,
            )
        )
        db.commit()
        db.close()

    def _create_report(
        self,
        report_id: int,
        *,
        reporter_id: int = 2,
        resource_type: str = RECURSO_TIPO_COMERCIO,
        resource_id: int = 10,
        reason: str = MOTIVO_SPAM,
        detail: str | None = "Detalle privado",
        created_at: datetime | None = None,
    ):
        db = TestingSessionLocal()
        db.add(
            ContenidoDenuncia(
                id=report_id,
                usuario_id=reporter_id,
                recurso_tipo=resource_type,
                recurso_id=resource_id,
                motivo=reason,
                detalle=detail,
                estado=ESTADO_DENUNCIA_RECIBIDA,
                creado_en=created_at or datetime(2026, 1, 1, 12, 0),
            )
        )
        db.commit()
        db.close()

    def _prepare_operator_and_report(self):
        self._create_user(1)
        self._create_user(2)
        self._create_commerce()
        self._change_capability(1, MODERATION_REPORTS_READ, "grant")
        self._create_report(1)

    def test_anonymous_list_and_detail_return_401(self):
        self.assertEqual(client.get("/moderacion/denuncias").status_code, 401)
        self.assertEqual(client.get("/moderacion/denuncias/1").status_code, 401)

    def test_common_user_and_publicador_return_403(self):
        self._create_user(1, modo_activo="publicador")
        self.assertEqual(
            client.get(
                "/moderacion/denuncias",
                headers=self._headers(1),
            ).status_code,
            403,
        )

    def test_unrelated_capability_returns_403(self):
        self._create_user(1)
        self._change_capability(1, OPERATIONS_STATUS_READ, "grant")
        self.assertEqual(
            client.get(
                "/moderacion/denuncias",
                headers=self._headers(1),
            ).status_code,
            403,
        )

    def test_authorized_list_is_minimized(self):
        self._prepare_operator_and_report()
        response = client.get(
            "/moderacion/denuncias",
            headers=self._headers(1),
        )
        self.assertEqual(response.status_code, 200)
        item = response.json()["items"][0]
        self.assertEqual(item["id"], 1)
        self.assertTrue(item["tiene_detalle"])
        self.assertNotIn("detalle", item)
        self.assertNotIn("usuario_id", item)
        self.assertNotIn("usuario", item)
        self.assertNotIn("email", response.text)
        self.assertNotIn("private-", response.text)

    def test_authorized_detail_is_minimized_and_has_live_availability(self):
        self._prepare_operator_and_report()
        response = client.get(
            "/moderacion/denuncias/1",
            headers=self._headers(1),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["detalle"], "Detalle privado")
        self.assertTrue(data["recurso_actual"]["disponible"])
        self.assertEqual(data["recurso_actual"]["ruta_publica"], "/comercios/10")
        self.assertFalse(data["recurso_actual"]["moderation_hidden"])
        self.assertEqual(data["recurso_actual"]["moderation_revision"], 0)
        self.assertNotIn("usuario_id", data)
        self.assertNotIn("usuario", data)
        self.assertNotIn("email", response.text)

    def test_missing_or_inactive_resource_does_not_hide_report(self):
        self._prepare_operator_and_report()
        db = TestingSessionLocal()
        db.get(Comercio, 10).activo = False
        db.commit()
        db.close()
        response = client.get(
            "/moderacion/denuncias/1",
            headers=self._headers(1),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["recurso_actual"]["disponible"])
        self.assertIsNone(response.json()["recurso_actual"]["ruta_publica"])

    def test_story_never_invents_public_detail_route(self):
        self._create_user(1)
        self._create_user(2)
        self._create_commerce()
        self._create_story()
        self._change_capability(1, MODERATION_REPORTS_READ, "grant")
        self._create_report(
            1,
            resource_type=RECURSO_TIPO_HISTORIA,
            resource_id=30,
        )
        data = client.get(
            "/moderacion/denuncias/1",
            headers=self._headers(1),
        ).json()
        self.assertTrue(data["recurso_actual"]["disponible"])
        self.assertIsNone(data["recurso_actual"]["ruta_publica"])

    def test_filters_are_controlled(self):
        self._prepare_operator_and_report()
        valid = client.get(
            "/moderacion/denuncias",
            params={
                "estado": ESTADO_DENUNCIA_RECIBIDA,
                "recurso_tipo": RECURSO_TIPO_COMERCIO,
                "recurso_id": 10,
                "motivo": MOTIVO_SPAM,
            },
            headers=self._headers(1),
        )
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(len(valid.json()["items"]), 1)

        for params in (
            {"estado": "desconocida"},
            {"recurso_tipo": "usuario"},
            {"motivo": "libre"},
            {"recurso_id": 10},
            {"desde": "2026-02-01", "hasta": "2026-01-01"},
        ):
            response = client.get(
                "/moderacion/denuncias",
                params=params,
                headers=self._headers(1),
            )
            self.assertEqual(response.status_code, 422, params)

    def test_invalid_cursor_and_limit_return_422(self):
        self._create_user(1)
        self._change_capability(1, MODERATION_REPORTS_READ, "grant")
        self.assertEqual(
            client.get(
                "/moderacion/denuncias",
                params={"cursor": "not-a-cursor"},
                headers=self._headers(1),
            ).status_code,
            422,
        )
        self.assertEqual(
            client.get(
                "/moderacion/denuncias",
                params={"limit": 51},
                headers=self._headers(1),
            ).status_code,
            422,
        )

    def test_keyset_is_stable_when_new_report_arrives(self):
        self._create_user(1)
        self._create_user(2)
        self._change_capability(1, MODERATION_REPORTS_READ, "grant")
        base = datetime(2026, 1, 1, 12, 0)
        self._create_report(1, resource_id=11, created_at=base)
        self._create_report(
            2,
            resource_id=12,
            created_at=base + timedelta(minutes=1),
            reason=MOTIVO_OTRO,
        )
        self._create_report(
            3,
            resource_id=13,
            created_at=base + timedelta(minutes=2),
        )

        first = client.get(
            "/moderacion/denuncias",
            params={"limit": 2},
            headers=self._headers(1),
        ).json()
        self.assertEqual([item["id"] for item in first["items"]], [3, 2])
        self.assertTrue(first["has_more"])

        self._create_report(
            4,
            resource_id=14,
            created_at=base + timedelta(minutes=3),
        )
        second = client.get(
            "/moderacion/denuncias",
            params={"limit": 2, "cursor": first["next_cursor"]},
            headers=self._headers(1),
        ).json()
        self.assertEqual([item["id"] for item in second["items"]], [1])
        self.assertFalse(second["has_more"])

    def test_same_timestamp_uses_id_as_tiebreaker(self):
        self._create_user(1)
        self._create_user(2)
        self._change_capability(1, MODERATION_REPORTS_READ, "grant")
        timestamp = datetime(2026, 1, 1, 12, 0)
        self._create_report(1, created_at=timestamp)
        self._create_report(2, created_at=timestamp, reason=MOTIVO_OTRO)
        response = client.get(
            "/moderacion/denuncias",
            headers=self._headers(1),
        )
        self.assertEqual(
            [item["id"] for item in response.json()["items"]],
            [2, 1],
        )

    def test_empty_and_filtered_empty_are_successful(self):
        self._create_user(1)
        self._change_capability(1, MODERATION_REPORTS_READ, "grant")
        empty = client.get(
            "/moderacion/denuncias",
            headers=self._headers(1),
        )
        self.assertEqual(
            empty.json(),
            {"items": [], "next_cursor": None, "has_more": False},
        )

    def test_missing_detail_returns_404(self):
        self._create_user(1)
        self._change_capability(1, MODERATION_REPORTS_READ, "grant")
        self.assertEqual(
            client.get(
                "/moderacion/denuncias/999",
                headers=self._headers(1),
            ).status_code,
            404,
        )

    def test_revocation_blocks_next_read_without_new_token(self):
        self._create_user(1)
        headers = self._headers(1)
        self._change_capability(1, MODERATION_REPORTS_READ, "grant")
        self.assertEqual(
            client.get("/moderacion/denuncias", headers=headers).status_code,
            200,
        )
        self._change_capability(1, MODERATION_REPORTS_READ, "revoke")
        self.assertEqual(
            client.get("/moderacion/denuncias", headers=headers).status_code,
            403,
        )


if __name__ == "__main__":
    unittest.main()
