import unittest
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import crear_token_jwt
from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.core.operation_alerts import local_alert_sink
from app.modules.administration.capabilities import OPERATIONS_INCIDENTS_MANAGE, OPERATIONS_STATUS_READ
from app.modules.administration.services.administrative_authorization_services import record_administrative_capability_change
from app.modules.incidents.models.operational_incidents_models import OperationalIncident, OperationalIncidentEvent
from app.modules.incidents.routes.operational_incidents_routers import router
from app.modules.notifications.models.operational_notification_outbox_models import OperationalNotificationOutbox
from app.modules.users.models.usuarios_models import Usuario

import_all_models()
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    db = Session()
    try: yield db
    finally: db.close()


app = FastAPI(); app.include_router(router); app.dependency_overrides[get_db] = get_test_db
client = TestClient(app)


class OperationalIncidentTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        db = Session()
        db.add_all([
            Usuario(id=1, email="operator@test.local", hashed_password="x", modo_activo="usuario", onboarding_completo=True),
            Usuario(id=2, email="common@test.local", hashed_password="x", modo_activo="publicador", onboarding_completo=True),
            Usuario(id=3, email="operator2@test.local", hashed_password="x", modo_activo="usuario", onboarding_completo=True),
            Usuario(id=4, email="status@test.local", hashed_password="x", modo_activo="usuario", onboarding_completo=True),
        ]); db.commit()
        for user, capability in ((1, OPERATIONS_INCIDENTS_MANAGE), (3, OPERATIONS_INCIDENTS_MANAGE), (4, OPERATIONS_STATUS_READ)):
            record_administrative_capability_change(db, usuario_id=user, capability=capability, action="grant", source="test", reason="97.4")
        db.close(); local_alert_sink.clear()

    def tearDown(self): Base.metadata.drop_all(engine)
    def headers(self, user=1): return {"Authorization": f"Bearer {crear_token_jwt({'sub': str(user)})}"}
    def create_payload(self, key="incident-key-1", severity="sev2_high", owner=1, source=None):
        value = {"title":"API degradada", "summary":"Incidente operativo sanitizado", "incident_type":"availability", "severity":severity, "owner_usuario_id":owner, "idempotency_key":key}
        if source is not None: value["source"] = source
        return value
    def open(self, **kwargs):
        response=client.post("/administracion/incidentes",json=self.create_payload(**kwargs),headers=self.headers()); self.assertIn(response.status_code,(200,201),response.text); return response.json()
    def action(self, public_id, action, version, key, **extra):
        payload={"action":action,"expected_version":version,"idempotency_key":key,"summary":extra.pop("summary","Actualizacion operativa segura"),**extra}
        return client.post(f"/administracion/incidentes/{public_id}/acciones",json=payload,headers=self.headers())
    def investigate(self, public_id, version=1, key="action-investigate"): return self.action(public_id,"start_investigation",version,key)
    def resolved(self, risk="low"):
        opened=self.open(key=f"incident-{risk}-key"); pid=opened["incident"]["public_id"]; self.investigate(pid,key=f"investigate-{risk}")
        resolve=self.action(pid,"resolve",2,f"resolve-{risk}",residual_risk_level=risk,residual_risk_summary="Riesgo evaluado")
        return pid, resolve

    def test_01_anonymous_is_401(self): self.assertEqual(client.get("/administracion/incidentes").status_code,401)
    def test_02_common_user_is_403(self): self.assertEqual(client.get("/administracion/incidentes",headers=self.headers(2)).status_code,403)
    def test_03_authorized_operator_can_access(self): self.assertEqual(client.get("/administracion/incidentes",headers=self.headers()).status_code,200)
    def test_04_status_read_does_not_grant_manage(self): self.assertEqual(client.get("/administracion/incidentes",headers=self.headers(4)).status_code,403)
    def test_05_product_mode_does_not_grant_access(self): self.assertEqual(client.get("/administracion/incidentes",headers=self.headers(2)).status_code,403)
    def test_06_opening_creates_stable_identifier(self):
        data=self.open(); self.assertRegex(data["incident"]["public_id"],r"^INC-[A-F0-9]{32}$")
    def test_07_exact_opening_retry_returns_same_incident(self):
        first=self.open(); second=self.open(); self.assertEqual(first["incident"]["public_id"],second["incident"]["public_id"])
        db=Session(); notices=db.query(OperationalNotificationOutbox).all(); db.close(); self.assertEqual(len(notices),1)
    def test_08_opening_key_with_different_fingerprint_conflicts(self):
        self.open(); response=client.post("/administracion/incidentes",json=self.create_payload(severity="sev1_critical"),headers=self.headers()); self.assertEqual(response.status_code,409)
    def test_09_valid_transition_increments_version(self):
        pid=self.open()["incident"]["public_id"]; response=self.investigate(pid); self.assertEqual(response.status_code,201); self.assertEqual(response.json()["incident"]["version"],2)
    def test_10_invalid_transition_conflicts(self):
        pid=self.open()["incident"]["public_id"]; self.assertEqual(self.action(pid,"resolve",1,"invalid-resolve",residual_risk_level="low",residual_risk_summary="Evaluado").status_code,409)
    def test_11_stale_version_does_not_change_state(self):
        pid=self.open()["incident"]["public_id"]; self.investigate(pid); self.assertEqual(self.action(pid,"record_finding",1,"stale-version").status_code,409); self.assertEqual(client.get(f"/administracion/incidentes/{pid}",headers=self.headers()).json()["version"],2)
    def test_12_timeline_is_append_only(self):
        pid=self.open()["incident"]["public_id"]; self.investigate(pid); events=client.get(f"/administracion/incidentes/{pid}/eventos",headers=self.headers()).json(); self.assertEqual([e["event_type"] for e in events],["opened","start_investigation"]); self.assertIn(client.delete(f"/administracion/incidentes/{pid}/eventos/{events[0]['id']}",headers=self.headers()).status_code,(404,405))
    def test_13_assignment_is_traced(self):
        pid=self.open()["incident"]["public_id"]; response=self.action(pid,"assign_owner",1,"assign-owner",owner_usuario_id=3); self.assertEqual(response.json()["event"]["owner_before_usuario_id"],1); self.assertEqual(response.json()["event"]["owner_after_usuario_id"],3)
    def test_14_new_owner_must_be_authorized(self):
        pid=self.open()["incident"]["public_id"]; self.assertEqual(self.action(pid,"assign_owner",1,"bad-owner",owner_usuario_id=2).status_code,422)
    def test_15_severity_change_requires_reason_and_value(self):
        pid=self.open()["incident"]["public_id"]; self.assertEqual(self.action(pid,"change_severity",1,"severity-missing").status_code,409); self.assertEqual(self.action(pid,"change_severity",1,"severity-ok",severity="sev1_critical",summary="Impacto de seguridad confirmado").status_code,201)
    def test_15a_current_severity_is_rejected_as_controlled_conflict(self):
        pid=self.open(severity="sev3_medium")["incident"]["public_id"]
        response=self.action(pid,"change_severity",1,"same-severity-conflict",severity="sev3_medium",summary="No debe persistirse")
        self.assertEqual(response.status_code,409)
    def test_15aa_rejected_same_severity_does_not_create_event_or_increment_version(self):
        pid=self.open(key="same-severity-no-effect",severity="sev3_medium")["incident"]["public_id"]
        self.assertEqual(self.action(pid,"change_severity",1,"same-severity-no-effect-action",severity="sev3_medium",summary="No debe persistirse").status_code,409)
        detail=client.get(f"/administracion/incidentes/{pid}",headers=self.headers()).json()
        events=client.get(f"/administracion/incidentes/{pid}/eventos",headers=self.headers()).json()
        self.assertEqual(detail["version"],1)
        self.assertEqual(detail["severity"],"sev3_medium")
        self.assertEqual([event["event_type"] for event in events],["opened"])
    def test_15b_low_opening_is_silent_and_escalation_enqueues_once(self):
        opened=self.open(key="low-opening",severity="sev3_medium"); pid=opened["incident"]["public_id"]
        db=Session(); self.assertEqual(db.query(OperationalNotificationOutbox).count(),0); db.close()
        self.assertEqual(self.action(pid,"change_severity",1,"low-escalation",severity="sev2_high",summary="Escalamiento confirmado").status_code,201)
        self.assertEqual(self.action(pid,"change_severity",1,"low-escalation",severity="sev2_high",summary="Escalamiento confirmado").status_code,201)
        db=Session(); notices=db.query(OperationalNotificationOutbox).all(); db.close(); self.assertEqual(len(notices),1); self.assertIn("severity_escalated",notices[0].event_type)
    def test_16_invalid_correlation_id_is_rejected(self):
        source={"evidence_type":"correlation","evidence_reference":"corr-1","correlation_id":"Bearer secret value"}; self.assertEqual(client.post("/administracion/incidentes",json=self.create_payload(source=source),headers=self.headers()).status_code,422)
    def test_17_secret_or_url_evidence_is_rejected(self):
        for reference in ("https://internal/evidence","C:\\secret\\dump.sql","Bearer-token"):
            payload=self.create_payload(key=f"secret-{len(reference)}",source={"evidence_type":"other_reference","evidence_reference":reference})
            self.assertEqual(client.post("/administracion/incidentes",json=payload,headers=self.headers()).status_code,422)
    def test_18_alert_does_not_open_incident_automatically(self):
        before=len(local_alert_sink.snapshot()); self.open(source={"evidence_type":"alert","evidence_reference":"alert-1","alert_id":"alert-1"}); self.assertEqual(len(local_alert_sink.snapshot()),before)
    def test_19_resolve_requires_residual_risk(self):
        pid=self.open()["incident"]["public_id"]; self.investigate(pid); self.assertEqual(self.action(pid,"resolve",2,"resolve-no-risk").status_code,409)
    def test_20_review_requires_post_incident_summary(self):
        pid,resolved=self.resolved(); self.assertEqual(resolved.status_code,201); self.assertEqual(client.post(f"/administracion/incidentes/{pid}/acciones",json={"action":"review","expected_version":3,"idempotency_key":"review-empty","summary":""},headers=self.headers()).status_code,422)
    def test_21_high_and_critical_risk_block_review(self):
        for risk in ("high","critical"):
            pid,resolved=self.resolved(risk); self.assertEqual(resolved.status_code,201); self.assertEqual(self.action(pid,"review",3,f"review-{risk}").status_code,409)
    def test_22_medium_risk_requires_owner_and_review_date(self):
        pid=self.open()["incident"]["public_id"]; self.investigate(pid); missing=self.action(pid,"resolve",2,"medium-missing",residual_risk_level="medium",residual_risk_summary="Pendiente"); self.assertEqual(missing.status_code,409); ok=self.action(pid,"resolve",2,"medium-ok",residual_risk_level="medium",residual_risk_summary="Pendiente",residual_risk_owner_usuario_id=1,residual_risk_review_at=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()); self.assertEqual(ok.status_code,201)
    def test_23_reopening_preserves_prior_timeline(self):
        pid,resolved=self.resolved(); self.assertEqual(resolved.status_code,201); reopened=self.action(pid,"reopen",3,"reopen-key"); self.assertEqual(reopened.status_code,201); events=client.get(f"/administracion/incidentes/{pid}/eventos",headers=self.headers()).json(); self.assertEqual(len(events),4); self.assertEqual(events[-1]["event_type"],"reopen")
    def test_24_legal_assessment_is_traced_without_owner_identity(self):
        pid=self.open()["incident"]["public_id"]; response=self.action(pid,"record_legal_assessment",1,"legal-assessment",legal_assessment_status="required",personal_data_impact="suspected",user_communication_status="pending",authority_communication_status="pending"); self.assertEqual(response.status_code,201); self.assertIsNone(response.json()["incident"]["legal_owner_usuario_id"])
    def test_25_responses_do_not_expose_private_identity_or_raw_details(self):
        data=self.open(); serialized=str(data).lower(); self.assertNotIn("email",serialized); self.assertNotIn("hashed_password",serialized); self.assertNotIn("safe_details_json",serialized)
    def test_26_incident_actions_do_not_mutate_alert_sink(self):
        before=local_alert_sink.snapshot(); pid=self.open()["incident"]["public_id"]; self.investigate(pid); self.assertEqual(local_alert_sink.snapshot(),before)
    def test_27_keyset_pagination_is_stable_under_insert(self):
        self.open(key="incident-page-1"); self.open(key="incident-page-2"); self.open(key="incident-page-3"); page1=client.get("/administracion/incidentes?limit=2",headers=self.headers()).json(); self.open(key="incident-page-new"); page2=client.get(f"/administracion/incidentes?limit=2&cursor={page1['next_cursor']}",headers=self.headers()).json(); first_ids={item["public_id"] for item in page1["items"]}; second_ids={item["public_id"] for item in page2["items"]}; self.assertFalse(first_ids & second_ids)
    def test_28_action_exact_retry_is_idempotent(self):
        pid=self.open()["incident"]["public_id"]; first=self.investigate(pid); second=self.investigate(pid); self.assertEqual(first.json()["event"]["id"],second.json()["event"]["id"]); self.assertEqual(second.json()["incident"]["version"],2)
    def test_29_action_same_key_different_fingerprint_conflicts(self):
        pid=self.open()["incident"]["public_id"]; self.investigate(pid); self.assertEqual(self.action(pid,"record_finding",2,"action-investigate").status_code,409)
    def test_30_same_operator_can_open_resolve_and_review_sev1_with_trace(self):
        opened=self.open(severity="sev1_critical"); pid=opened["incident"]["public_id"]; self.investigate(pid); self.assertEqual(self.action(pid,"resolve",2,"sev1-resolve",residual_risk_level="low",residual_risk_summary="Mitigado").status_code,201); review=self.action(pid,"review",3,"sev1-review",summary="Revision final documentada"); self.assertEqual(review.status_code,201); events=client.get(f"/administracion/incidentes/{pid}/eventos",headers=self.headers()).json(); self.assertEqual({event["actor_usuario_id"] for event in events},{1}); self.assertEqual(events[-1]["status_after"],"reviewed"); self.assertEqual(self.action(pid,"record_finding",4,"after-review").status_code,409)


if __name__ == "__main__": unittest.main()
