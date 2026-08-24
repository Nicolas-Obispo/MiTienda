import unittest
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.modules.administration.capabilities import MODERATION_DECISIONS_WRITE, MODERATION_REPORTS_READ
from app.modules.administration.services.administrative_authorization_services import record_administrative_capability_change
from app.modules.moderation.constants import ESTADO_DENUNCIA_RECIBIDA, MOTIVO_SPAM, RECURSO_TIPO_COMERCIO
from app.modules.moderation.models.contenido_denuncias_models import ContenidoDenuncia
from app.modules.moderation.models.moderation_decisions_models import ModerationDecision
from app.modules.moderation.routes.contenido_denuncias_routers import router
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
    try: yield db
    finally: db.close()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = get_test_db
client = TestClient(app)


class ModerationDecisionsTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        db = Session()
        db.add_all([
            Usuario(id=1, email="operator@test.local", hashed_password="x", modo_activo="usuario", onboarding_completo=True),
            Usuario(id=2, email="reporter@test.local", hashed_password="x", modo_activo="usuario", onboarding_completo=True),
            Usuario(id=3, email="owner@test.local", hashed_password="x", modo_activo="publicador", onboarding_completo=True),
            Rubro(id=1, nombre="Rubro", activo=True),
        ])
        db.flush()
        db.add(Comercio(id=10, usuario_id=3, nombre="C", portada_url="/x", rubro_id=1, provincia="P", ciudad="C", activo=True))
        db.add(ContenidoDenuncia(id=20, usuario_id=2, recurso_tipo=RECURSO_TIPO_COMERCIO, recurso_id=10, motivo=MOTIVO_SPAM, estado=ESTADO_DENUNCIA_RECIBIDA))
        db.commit()
        for capability in (MODERATION_REPORTS_READ, MODERATION_DECISIONS_WRITE):
            record_administrative_capability_change(db, usuario_id=1, capability=capability, action="grant", source="test", reason="97.3")
        db.close()

    def tearDown(self): Base.metadata.drop_all(engine)
    def headers(self, user=1): return {"Authorization": f"Bearer {crear_token_jwt({'sub': str(user)})}"}
    def payload(self, action="ocultar_recurso", key="decision-key-1", report_version=1, resource_revision=0, reverse=None):
        key = f"decision-{key}" if len(key) < 8 else key
        value = {"accion": action, "motivo_codigo": "incumplimiento_confirmado" if action == "ocultar_recurso" else "correccion_operativa", "fundamento": "Fundamento", "evidencia_resumen": "Evidencia", "expected_denuncia_version": report_version, "idempotency_key": key}
        if action != "resolver_sin_accion": value["expected_resource_revision"] = resource_revision
        if reverse is not None: value["reverses_decision_id"] = reverse
        return value
    def post(self, payload, report=20, headers=None): return client.post(f"/moderacion/denuncias/{report}/decisiones", json=payload, headers=self.headers() if headers is None else headers)
    def hide(self):
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_01_hide_increments_revision(self):
        self.hide(); db=Session(); self.assertEqual(db.get(Comercio,10).moderation_revision,1); db.close()
    def test_02_hide_records_causal_decision(self):
        decision=self.hide(); db=Session(); self.assertEqual(db.get(Comercio,10).moderation_hidden_by_decision_id,decision["id"]); db.close()
    def test_03_second_report_cannot_hide_hidden_resource(self):
        self.hide(); db=Session(); db.add(ContenidoDenuncia(id=21,usuario_id=2,recurso_tipo=RECURSO_TIPO_COMERCIO,recurso_id=10,motivo="otro",estado=ESTADO_DENUNCIA_RECIBIDA)); db.commit(); db.close(); self.assertEqual(self.post(self.payload(key="second",resource_revision=1),report=21).status_code,409)
    def test_04_failed_attempt_creates_no_decision(self):
        self.hide(); self.post(self.payload(key="failed",resource_revision=1)); db=Session(); self.assertEqual(db.query(ModerationDecision).count(),1); db.close()
    def test_05_restore_requires_reference(self):
        self.hide(); self.assertEqual(self.post(self.payload("restaurar_recurso",key="restore",report_version=2,resource_revision=1)).status_code,422)
    def test_06_only_applied_hide_can_restore(self):
        no_action=self.post(self.payload("resolver_sin_accion",key="none")); self.assertEqual(no_action.status_code,201); self.assertEqual(self.post(self.payload("restaurar_recurso",key="restore",report_version=2,resource_revision=0,reverse=no_action.json()["id"])).status_code,409)
    def test_07_no_change_never_grants_restore(self): self.test_06_only_applied_hide_can_restore()
    def test_08_restore_requires_same_report_and_resource(self):
        hidden=self.hide(); db=Session(); db.add(ContenidoDenuncia(id=21,usuario_id=2,recurso_tipo=RECURSO_TIPO_COMERCIO,recurso_id=10,motivo="otro",estado="resuelta")); db.commit(); db.close(); self.assertEqual(self.post(self.payload("restaurar_recurso",key="restore",report_version=1,resource_revision=1,reverse=hidden["id"]),report=21).status_code,409)
    def test_09_restore_requires_current_cause(self):
        hidden=self.hide(); db=Session(); resource=db.get(Comercio,10); resource.moderation_hidden_by_decision_id=None; db.commit(); db.close(); self.assertEqual(self.post(self.payload("restaurar_recurso",key="restore",report_version=2,resource_revision=1,reverse=hidden["id"])).status_code,409)
    def test_10_stale_resource_revision_conflicts(self):
        hidden=self.hide(); self.assertEqual(self.post(self.payload("restaurar_recurso",key="restore",report_version=2,resource_revision=0,reverse=hidden["id"])).status_code,409)
    def test_11_later_hide_cannot_be_undone_by_old_restore(self):
        first=self.hide(); restored=self.post(self.payload("restaurar_recurso",key="restore",report_version=2,resource_revision=1,reverse=first["id"])); self.assertEqual(restored.status_code,201); db=Session(); db.add(ContenidoDenuncia(id=21,usuario_id=2,recurso_tipo=RECURSO_TIPO_COMERCIO,recurso_id=10,motivo="otro",estado=ESTADO_DENUNCIA_RECIBIDA)); db.commit(); db.close(); second=self.post(self.payload(key="second",resource_revision=2),report=21); self.assertEqual(second.status_code,201); self.assertEqual(self.post(self.payload("restaurar_recurso",key="late",report_version=3,resource_revision=3,reverse=first["id"])).status_code,409)
    def test_12_two_hides_same_versions_one_conflicts(self):
        self.assertEqual(self.post(self.payload(key="one")).status_code,201); self.assertEqual(self.post(self.payload(key="two")).status_code,409)
    def test_13_hide_restore_are_serialized_by_versions(self):
        hidden=self.hide(); self.assertEqual(self.post(self.payload("restaurar_recurso",key="restore",report_version=2,resource_revision=1,reverse=hidden["id"])).status_code,201); self.assertEqual(self.post(self.payload(key="stale-hide",report_version=1,resource_revision=0)).status_code,409)
    def test_14_two_restores_only_one_applies(self):
        hidden=self.hide(); self.assertEqual(self.post(self.payload("restaurar_recurso",key="r1",report_version=2,resource_revision=1,reverse=hidden["id"])).status_code,201); self.assertEqual(self.post(self.payload("restaurar_recurso",key="r2",report_version=2,resource_revision=1,reverse=hidden["id"])).status_code,409)
    def test_15_exact_retry_returns_original(self):
        payload=self.payload(); first=self.post(payload); second=self.post(payload); self.assertEqual(first.json()["id"],second.json()["id"])
    def test_16_same_key_different_payload_conflicts(self):
        self.hide(); changed=self.payload(); changed["fundamento"]="Otro"; self.assertEqual(self.post(changed).status_code,409)
    def test_17_retry_after_other_decision_does_not_repeat_effect(self):
        payload=self.payload(); first=self.post(payload); restore=self.post(self.payload("restaurar_recurso",key="restore",report_version=2,resource_revision=1,reverse=first.json()["id"])); self.assertEqual(restore.status_code,201); retry=self.post(payload); self.assertEqual(retry.json()["id"],first.json()["id"]); db=Session(); self.assertEqual(db.get(Comercio,10).moderation_revision,2); db.close()
    def test_18_restore_does_not_change_owner_lifecycle(self):
        hidden=self.hide(); db=Session(); resource=db.get(Comercio,10); resource.activo=False; db.commit(); db.close(); self.post(self.payload("restaurar_recurso",key="restore",report_version=2,resource_revision=1,reverse=hidden["id"])); db=Session(); self.assertFalse(db.get(Comercio,10).activo); db.close()
    def test_19_restored_owner_inactive_remains_publicly_unavailable(self):
        self.test_18_restore_does_not_change_owner_lifecycle(); response=client.get("/moderacion/denuncias/20",headers=self.headers()); self.assertFalse(response.json()["recurso_actual"]["disponible"])
    def test_20_conflict_rolls_back_report_and_resource(self):
        response=self.post(self.payload(resource_revision=9)); self.assertEqual(response.status_code,409); db=Session(); self.assertEqual(db.get(ContenidoDenuncia,20).version,1); self.assertFalse(db.get(Comercio,10).moderation_hidden); self.assertEqual(db.query(ModerationDecision).count(),0); db.close()

    def test_authorization_and_reporter_privacy(self):
        self.assertEqual(self.post(self.payload(),headers={}).status_code,401)
        self.assertEqual(self.post(self.payload(),headers=self.headers(2)).status_code,403)
        decision=self.hide(); self.assertNotIn("usuario",decision); self.assertNotIn("email",decision)

    def test_owner_services_hide_posts_and_stories_without_changing_lifecycle(self):
        db = Session()
        db.add(Publicacion(id=30, comercio_id=10, titulo="P", is_activa=True))
        db.add(Historia(id=40, comercio_id=10, media_url="/h.jpg", expira_en=datetime(2030, 1, 1), is_activa=True))
        db.add_all([
            ContenidoDenuncia(id=31, usuario_id=2, recurso_tipo="publicacion", recurso_id=30, motivo=MOTIVO_SPAM, estado=ESTADO_DENUNCIA_RECIBIDA),
            ContenidoDenuncia(id=41, usuario_id=2, recurso_tipo="historia", recurso_id=40, motivo=MOTIVO_SPAM, estado=ESTADO_DENUNCIA_RECIBIDA),
        ])
        db.commit(); db.close()
        self.assertEqual(self.post(self.payload(key="post-hide"), report=31).status_code, 201)
        self.assertEqual(self.post(self.payload(key="story-hide"), report=41).status_code, 201)
        db = Session()
        post, story = db.get(Publicacion, 30), db.get(Historia, 40)
        self.assertTrue(post.moderation_hidden); self.assertTrue(post.is_activa)
        self.assertTrue(story.moderation_hidden); self.assertTrue(story.is_activa)
        db.close()

    def test_evidence_reference_accepts_only_opaque_values(self):
        payload = self.payload(action="resolver_sin_accion", key="opaque-evidence")
        payload["evidencia_referencia"] = "moderation-evidence:case_20.v1"
        response = self.post(payload)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["evidencia_referencia"], "moderation-evidence:case_20.v1")

    def test_invalid_evidence_references_return_422_without_persistence(self):
        invalid_references = (
            "https://internal/evidence/20",
            "C:\\private\\evidence.json",
            "../private/evidence.json",
            "Bearer-secret-value",
            "api_key=private",
            '{"payload":"raw"}',
        )
        for index, reference in enumerate(invalid_references):
            with self.subTest(reference=reference):
                payload = self.payload(action="resolver_sin_accion", key=f"invalid-evidence-{index}")
                payload["evidencia_referencia"] = reference
                response = self.post(payload)
                self.assertEqual(response.status_code, 422, response.text)

        db = Session()
        self.assertEqual(db.query(ModerationDecision).count(), 0)
        report = db.get(ContenidoDenuncia, 20)
        resource = db.get(Comercio, 10)
        self.assertEqual(report.estado, ESTADO_DENUNCIA_RECIBIDA)
        self.assertEqual(report.version, 1)
        self.assertFalse(resource.moderation_hidden)
        self.assertEqual(resource.moderation_revision, 0)
        db.close()


if __name__ == "__main__": unittest.main()
