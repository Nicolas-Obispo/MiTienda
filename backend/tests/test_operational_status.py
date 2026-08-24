import unittest
from datetime import datetime
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.database import Base, get_db
from app.core.health import HealthCheckResult, HealthRegistry
from app.core.model_registry import import_all_models
from app.core.operation_alerts import AlertEvent, local_alert_sink
from app.core.operation_metrics import (
    METRIC_HTTP_RESPONSE_5XX_COUNT,
    METRIC_UPLOAD_ACCEPTED_COUNT,
    METRIC_UPLOAD_REJECTED_COUNT,
    increment_counter,
    local_metrics_sink,
)
from app.modules.administration.capabilities import OPERATIONS_INCIDENTS_MANAGE, OPERATIONS_STATUS_READ
from app.modules.administration.services.administrative_authorization_services import record_administrative_capability_change
from app.modules.operations.routes.health_routers import router as health_router
from app.modules.operations.routes.operational_status_routers import router
from app.modules.products.models.rubros_models import Rubro
from app.modules.posts.models.publicaciones_models import Publicacion
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.stories.models.historias_models import Historia
from app.modules.users.models.usuarios_models import Usuario


import_all_models()
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(router)
app.include_router(health_router)
app.dependency_overrides[get_db] = get_test_db
client = TestClient(app)


def check(component, status="healthy", message="Componente disponible."):
    return HealthCheckResult(component=component, status=status, duration_ms=1.0, message=message)


def test_registry():
    registry = HealthRegistry()
    registry.register_liveness(lambda: check("api"))
    for component, status in (
        ("api", "healthy"), ("database", "healthy"), ("database_schema", "healthy"),
        ("uploads_storage", "healthy"), ("backup_evidence", "healthy"),
        ("restore_evidence", "degraded"),
    ):
        registry.register_readiness(lambda component=component, status=status: check(component, status))
    return registry


class OperationalStatusTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        db = Session()
        db.add_all([
            Usuario(id=1, email="status@test.local", hashed_password="x", modo_activo="usuario", onboarding_completo=True),
            Usuario(id=2, email="common@test.local", hashed_password="x", modo_activo="publicador", onboarding_completo=True),
            Usuario(id=3, email="owner@test.local", hashed_password="x", modo_activo="publicador", onboarding_completo=True),
            Usuario(id=4, email="incident@test.local", hashed_password="x", modo_activo="usuario", onboarding_completo=True),
            Rubro(id=1, nombre="Rubro", activo=True),
        ])
        db.flush()
        db.add(Comercio(id=10, usuario_id=3, nombre="Comercio", portada_url="/uploads/missing-space.jpg", rubro_id=1, provincia="P", ciudad="C", activo=True))
        db.add_all([
            Publicacion(id=20, comercio_id=10, titulo="Publicacion", imagen_url=None, is_activa=True),
            Historia(id=30, comercio_id=10, media_url="/uploads/missing-story.jpg", expira_en=datetime(2030, 1, 1), is_activa=True),
        ])
        db.commit()
        record_administrative_capability_change(db, usuario_id=1, capability=OPERATIONS_STATUS_READ, action="grant", source="test", reason="97.5")
        record_administrative_capability_change(db, usuario_id=4, capability=OPERATIONS_INCIDENTS_MANAGE, action="grant", source="test", reason="97.5")
        db.close()
        local_metrics_sink.clear()
        local_alert_sink.clear()
        self.registry_patch = patch("app.modules.operations.services.operational_status_services.health_registry", test_registry())
        self.registry_patch.start()

    def tearDown(self):
        self.registry_patch.stop()
        local_metrics_sink.clear()
        local_alert_sink.clear()
        Base.metadata.drop_all(engine)

    def headers(self, user=1):
        return {"Authorization": f"Bearer {crear_token_jwt({'sub': str(user)})}"}

    def get_status(self, user=1):
        return client.get("/administracion/operaciones/estado", headers=self.headers(user))

    def inspect(self, resource_type, resource_id, user=1):
        return client.get(f"/administracion/operaciones/recursos/{resource_type}/{resource_id}/integridad", headers=self.headers(user))

    def test_01_anonymous_is_401(self): self.assertEqual(client.get("/administracion/operaciones/estado").status_code, 401)
    def test_02_common_user_is_403(self): self.assertEqual(self.get_status(2).status_code, 403)
    def test_03_other_capability_is_403(self): self.assertEqual(self.get_status(4).status_code, 403)
    def test_04_status_reader_is_200(self): self.assertEqual(self.get_status().status_code, 200)
    def test_05_product_mode_does_not_grant(self): self.assertEqual(self.get_status(2).status_code, 403)
    def test_06_resource_ownership_does_not_grant(self): self.assertEqual(self.inspect("comercio", 10, 3).status_code, 403)

    def test_07_health_contract_is_composed(self):
        body = self.get_status().json()
        self.assertEqual(body["health"]["liveness"], "healthy")
        self.assertEqual(body["health"]["readiness"], "degraded")

    def test_08_backup_is_not_executed(self):
        with patch("app.core.database_backup.run_backup") as operation:
            self.get_status()
            operation.assert_not_called()

    def test_09_restore_is_not_executed(self):
        with patch("app.core.database_restore.restore_backup") as operation:
            self.get_status()
            operation.assert_not_called()

    def test_10_status_does_not_create_files(self):
        with patch("pathlib.Path.write_text") as write, patch("builtins.open") as opening:
            self.get_status()
            write.assert_not_called(); opening.assert_not_called()

    def test_11_status_does_not_change_sinks(self):
        increment_counter(METRIC_UPLOAD_ACCEPTED_COUNT)
        before_metrics = local_metrics_sink.snapshot(); before_alerts = local_alert_sink.snapshot()
        self.get_status()
        self.assertEqual(before_metrics, local_metrics_sink.snapshot()); self.assertEqual(before_alerts, local_alert_sink.snapshot())

    def test_12_response_has_no_paths(self):
        text = self.get_status().text.lower()
        self.assertNotIn("c:\\", text); self.assertNotIn("/users/", text); self.assertNotIn("backup_file", text)

    def test_13_response_has_no_secrets(self):
        text = self.get_status().text.lower()
        for marker in ("authorization", "bearer ", "password", "secret_key", ".env"):
            self.assertNotIn(marker, text)

    def test_14_response_has_no_sql_or_traceback(self):
        text = self.get_status().text.lower()
        self.assertNotIn("select ", text); self.assertNotIn("traceback", text)

    def test_15_only_allowlisted_metric_aggregates_are_returned(self):
        increment_counter(METRIC_UPLOAD_ACCEPTED_COUNT, 2, tags={"media_type": "image"})
        increment_counter("private.metric", 99)
        aggregates = self.get_status().json()["aggregates"]
        self.assertEqual(aggregates, [{"name": METRIC_UPLOAD_ACCEPTED_COUNT, "value": 2.0, "sample_count": 1}])

    def test_16_alerts_are_sanitized(self):
        local_alert_sink.emit(AlertEvent("alert-1", "uploads_rejected_repeated", "warning", "active", "condition", "2026-08-22T00:00:00+00:00", 60, 60, "secret-dedup", {"request_id": "private"}, "Mensaje inyectado"))
        alert = self.get_status().json()["alerts"][0]
        self.assertEqual(set(alert), {"alert_id", "rule_name", "severity", "status", "triggered_at_utc", "message"})

    def test_17_local_volatile_scope_is_explicit(self):
        body = self.get_status().json()
        self.assertEqual(body["scope"], "process_local"); self.assertTrue(body["volatile"]); self.assertFalse(body["historical"]); self.assertFalse(body["global_status"])

    def test_18_missing_resource_is_404(self): self.assertEqual(self.inspect("historia", 999).status_code, 404)
    def test_19_commerce_can_be_inspected(self): self.assertEqual(self.inspect("comercio", 10).json()["resource_type"], "comercio")
    def test_20_post_can_be_inspected(self): self.assertEqual(self.inspect("publicacion", 20).json()["resource_type"], "publicacion")
    def test_21_story_can_be_inspected(self): self.assertEqual(self.inspect("historia", 30).json()["resource_type"], "historia")

    def test_22_present_local_asset(self):
        with patch("pathlib.Path.is_file", return_value=True):
            self.assertEqual(self.inspect("historia", 30).json()["asset"], {"kind": "local_upload", "status": "present"})

    def test_23_missing_local_asset(self):
        body = self.inspect("historia", 30).json()
        self.assertEqual(body["asset"]["status"], "missing"); self.assertEqual(body["issues"][0]["code"], "local_asset_missing")

    def test_24_invalid_local_reference(self):
        db=Session(); db.get(Historia,30).media_url="/uploads/a/b.jpg"; db.commit(); db.close()
        self.assertEqual(self.inspect("historia",30).json()["asset"]["status"],"invalid_reference")

    def test_25_external_url_never_uses_network(self):
        db=Session(); db.get(Historia,30).media_url="https://example.invalid/image.jpg"; db.commit(); db.close()
        with patch("socket.create_connection") as network:
            self.assertEqual(self.inspect("historia",30).json()["asset"],{"kind":"external","status":"not_verified"}); network.assert_not_called()

    def test_26_lifecycle_is_read_without_mutation(self):
        db=Session(); db.get(Publicacion,20).is_activa=False; db.commit(); db.close()
        self.assertEqual(self.inspect("publicacion",20).json()["lifecycle"],"inactive")
        db=Session(); self.assertFalse(db.get(Publicacion,20).is_activa); db.close()

    def test_27_moderation_is_read_without_mutation(self):
        db=Session(); db.get(Comercio,10).moderation_hidden=True; db.commit(); db.close()
        body=self.inspect("comercio",10).json(); self.assertTrue(body["moderation_hidden"]); self.assertFalse(body["publicly_eligible"])

    def test_28_repeated_reads_do_not_mix_resources(self):
        post=self.inspect("publicacion",20).json(); story=self.inspect("historia",30).json()
        self.assertEqual((post["resource_type"],post["resource_id"]),("publicacion",20)); self.assertEqual((story["resource_type"],story["resource_id"]),("historia",30))

    def test_29_reads_issue_no_insert_update_or_delete(self):
        statements=[]
        def observe(_conn, _cursor, statement, _parameters, _context, _many): statements.append(statement.strip().lower())
        event.listen(engine,"before_cursor_execute",observe)
        try: self.get_status(); self.inspect("historia",30)
        finally: event.remove(engine,"before_cursor_execute",observe)
        self.assertFalse(any(item.startswith(("insert ","update ","delete ")) for item in statements), statements)

    def test_30_public_liveness_remains_available(self): self.assertEqual(client.get("/health/live").status_code,200)

    def test_31_unsupported_resource_type_is_422(self): self.assertEqual(self.inspect("usuario",1).status_code,422)
    def test_32_optional_post_asset_is_not_an_issue(self): self.assertEqual(self.inspect("publicacion",20).json()["asset"],{"kind":"none","status":"not_applicable"})
    def test_33_recovery_projection_does_not_claim_freshness(self): self.assertNotIn("fresh", self.get_status().text.lower())
    def test_34_aggregates_drop_tags_and_timestamps(self):
        increment_counter(METRIC_HTTP_RESPONSE_5XX_COUNT,tags={"route":"/private/{id}","status":"500"})
        aggregate=self.get_status().json()["aggregates"][0]; self.assertEqual(set(aggregate),{"name","value","sample_count"})
    def test_35_alerts_are_bounded(self):
        for index in range(25): local_alert_sink.emit(AlertEvent(f"a-{index}","uploads_rejected_repeated","warning","active","condition",f"2026-08-22T00:00:{index:02d}+00:00",60,60,"key",{},"safe"))
        self.assertEqual(len(self.get_status().json()["alerts"]),20)

    def test_36_worker_status_is_sanitized_and_disabled_by_default(self):
        body = self.get_status().json()["operational_email_worker"]
        self.assertEqual(body, {"status": "disabled", "scope": "local_runtime", "volatile": True})


if __name__ == "__main__": unittest.main()
