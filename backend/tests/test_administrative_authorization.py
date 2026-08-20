import unittest

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.database import Base, get_db
from app.core.database_backup import CRITICAL_TABLES
from app.core.model_registry import import_all_models
from app.modules.administration.capabilities import (
    ADMINISTRATIVE_CAPABILITIES,
    MODERATION_DECISIONS_WRITE,
    MODERATION_REPORTS_READ,
    OPERATIONS_INCIDENTS_MANAGE,
    OPERATIONS_STATUS_READ,
)
from app.modules.administration.dependencies import (
    require_administrative_capability,
)
from app.modules.administration.models.administrative_capability_events_models import (
    AdministrativeCapabilityEvent,
)
from app.modules.administration.routes.administration_routers import (
    router as administration_router,
)
from app.modules.administration.services.administrative_authorization_services import (
    BOOTSTRAP_SOURCE,
    record_administrative_capability_change,
)
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
app.include_router(administration_router)


@app.get("/administration-test/moderation")
def protected_moderation_contract(
    usuario=Depends(
        require_administrative_capability(MODERATION_REPORTS_READ)
    ),
):
    return {"usuario_id": usuario.id}


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class AdministrativeAuthorizationTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides = {get_db: override_get_db}

    def tearDown(self):
        app.dependency_overrides = {get_db: override_get_db}
        Base.metadata.drop_all(bind=engine)

    def _create_user(
        self,
        *,
        usuario_id: int = 1,
        modo_activo: str = "usuario",
    ):
        db = TestingSessionLocal()
        db.add(
            Usuario(
                id=usuario_id,
                email=f"usuario-{usuario_id}@example.com",
                hashed_password="hash",
                modo_activo=modo_activo,
                onboarding_completo=True,
            )
        )
        db.commit()
        db.close()

    def _headers(self, usuario_id: int = 1, **extra_claims):
        token = crear_token_jwt({"sub": str(usuario_id), **extra_claims})
        return {"Authorization": f"Bearer {token}"}

    def _change(self, capability: str, action: str, *, usuario_id: int = 1):
        db = TestingSessionLocal()
        event, changed = record_administrative_capability_change(
            db,
            usuario_id=usuario_id,
            capability=capability,
            action=action,
            source=BOOTSTRAP_SOURCE,
            reason="Bootstrap controlado de test",
        )
        db.close()
        return event, changed

    def test_initial_catalog_contains_exactly_four_capabilities(self):
        self.assertEqual(
            ADMINISTRATIVE_CAPABILITIES,
            {
                MODERATION_REPORTS_READ,
                MODERATION_DECISIONS_WRITE,
                OPERATIONS_STATUS_READ,
                OPERATIONS_INCIDENTS_MANAGE,
            },
        )

    def test_administrative_events_are_part_of_critical_backups(self):
        self.assertIn("administrative_capability_events", CRITICAL_TABLES)

    def test_capabilities_endpoint_requires_authentication(self):
        response = client.get("/administracion/me/capacidades")
        self.assertEqual(response.status_code, 401)

    def test_common_user_receives_empty_capabilities(self):
        self._create_user()
        response = client.get(
            "/administracion/me/capacidades",
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"es_operador": False, "capacidades": []},
        )

    def test_authorized_operator_receives_active_capability(self):
        self._create_user()
        self._change(MODERATION_REPORTS_READ, "grant")
        response = client.get(
            "/administracion/me/capacidades",
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "es_operador": True,
                "capacidades": [MODERATION_REPORTS_READ],
            },
        )

    def test_guard_returns_401_for_anonymous_user(self):
        response = client.get("/administration-test/moderation")
        self.assertEqual(response.status_code, 401)

    def test_guard_returns_403_for_common_user(self):
        self._create_user()
        response = client.get(
            "/administration-test/moderation",
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_publicador_mode_does_not_grant_administrative_access(self):
        self._create_user(modo_activo="publicador")
        response = client.get(
            "/administration-test/moderation",
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_unrelated_capability_does_not_grant_access(self):
        self._create_user()
        self._change(OPERATIONS_STATUS_READ, "grant")
        response = client.get(
            "/administration-test/moderation",
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 403)

    def test_required_capability_grants_access(self):
        self._create_user()
        self._change(MODERATION_REPORTS_READ, "grant")
        response = client.get(
            "/administration-test/moderation",
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"usuario_id": 1})

    def test_capability_claim_in_jwt_is_ignored(self):
        self._create_user()
        response = client.get(
            "/administration-test/moderation",
            headers=self._headers(capabilities=[MODERATION_REPORTS_READ]),
        )
        self.assertEqual(response.status_code, 403)

    def test_revocation_applies_without_reissuing_token(self):
        self._create_user()
        headers = self._headers()
        self._change(MODERATION_REPORTS_READ, "grant")
        self.assertEqual(
            client.get(
                "/administration-test/moderation",
                headers=headers,
            ).status_code,
            200,
        )
        self._change(MODERATION_REPORTS_READ, "revoke")
        self.assertEqual(
            client.get(
                "/administration-test/moderation",
                headers=headers,
            ).status_code,
            403,
        )

    def test_bootstrap_events_are_audited_and_idempotent(self):
        self._create_user()
        first, first_changed = self._change(MODERATION_REPORTS_READ, "grant")
        second, second_changed = self._change(MODERATION_REPORTS_READ, "grant")
        revoked, revoke_changed = self._change(
            MODERATION_REPORTS_READ,
            "revoke",
        )

        self.assertTrue(first_changed)
        self.assertFalse(second_changed)
        self.assertEqual(first.id, second.id)
        self.assertTrue(revoke_changed)
        self.assertNotEqual(first.id, revoked.id)

        db = TestingSessionLocal()
        events = db.query(AdministrativeCapabilityEvent).order_by(
            AdministrativeCapabilityEvent.id
        ).all()
        self.assertEqual([event.action for event in events], ["grant", "revoke"])
        self.assertTrue(all(event.source == BOOTSTRAP_SOURCE for event in events))
        self.assertTrue(all(event.reason for event in events))
        db.close()


if __name__ == "__main__":
    unittest.main()
