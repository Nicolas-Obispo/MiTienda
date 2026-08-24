import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import inspect

import migrate_operational_notification_outbox as outbox_migration
from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.administration.capabilities import OPERATIONS_INCIDENTS_MANAGE
from app.modules.administration.services.administrative_authorization_services import record_administrative_capability_change
from app.modules.incidents.models.operational_incidents_models import OperationalIncident, OperationalIncidentEvent
from app.modules.incidents.schemas.operational_incidents_schemas import OperationalIncidentAction, OperationalIncidentCreate
from app.modules.incidents.services.operational_incidents_services import IncidentConflictError, apply_incident_action, create_incident
from app.modules.communications.services.operational_email_services import claim_due_operational_emails
from app.modules.moderation.constants import ESTADO_DENUNCIA_RECIBIDA, MOTIVO_SPAM, RECURSO_TIPO_COMERCIO
from app.modules.moderation.models.contenido_denuncias_models import ContenidoDenuncia
from app.modules.moderation.models.moderation_decisions_models import ModerationDecision
from app.modules.moderation.schemas.contenido_denuncias_schemas import ModerationDecisionCreate
from app.modules.moderation.services.moderation_decisions_services import ModerationDecisionConflictError, create_moderation_decision
from app.modules.notifications.models.operational_notification_outbox_models import OperationalNotificationOutbox
from app.modules.notifications.services.operational_notification_services import enqueue_report_created
from app.modules.products.models.rubros_models import Rubro
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.users.models.usuarios_models import Usuario
from tests.mysql_stage97_test_support import isolated_mysql_test_engine


import_all_models()


class Stage97MySQLConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session = isolated_mysql_test_engine()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        db = self.Session()
        db.add_all([
            Usuario(id=1, email="operator-stage97@test.local", hashed_password="x", modo_activo="usuario", onboarding_completo=True),
            Usuario(id=2, email="reporter-stage97@test.local", hashed_password="x", modo_activo="usuario", onboarding_completo=True),
            Usuario(id=3, email="owner-stage97@test.local", hashed_password="x", modo_activo="publicador", onboarding_completo=True),
            Rubro(id=1, nombre="Rubro", activo=True),
        ])
        db.flush()
        db.add(Comercio(id=10, usuario_id=3, nombre="Comercio", portada_url="/x", rubro_id=1, provincia="P", ciudad="C", activo=True))
        db.add_all([
            ContenidoDenuncia(id=20, usuario_id=2, recurso_tipo=RECURSO_TIPO_COMERCIO, recurso_id=10, motivo=MOTIVO_SPAM, estado=ESTADO_DENUNCIA_RECIBIDA),
            ContenidoDenuncia(id=21, usuario_id=2, recurso_tipo=RECURSO_TIPO_COMERCIO, recurso_id=10, motivo="otro", estado=ESTADO_DENUNCIA_RECIBIDA),
        ])
        db.commit()
        record_administrative_capability_change(
            db, usuario_id=1, capability=OPERATIONS_INCIDENTS_MANAGE,
            action="grant", source="mysql-concurrency-test", reason="97.6",
        )
        db.close()

    def run_concurrently(self, operations):
        barrier = threading.Barrier(len(operations))

        def run(operation):
            db = self.Session()
            try:
                barrier.wait(timeout=5)
                return ("ok", operation(db))
            except Exception as exc:
                return ("error", exc)
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=len(operations)) as executor:
            return list(executor.map(run, operations))

    @staticmethod
    def decision_payload(key, report_version=1, resource_revision=0):
        return ModerationDecisionCreate(
            accion="ocultar_recurso", motivo_codigo="incumplimiento_confirmado",
            fundamento="Fundamento", evidencia_resumen="Evidencia",
            expected_denuncia_version=report_version,
            expected_resource_revision=resource_revision,
            idempotency_key=key,
        )

    def test_same_report_and_versions_apply_exactly_once(self):
        results = self.run_concurrently([
            lambda db: create_moderation_decision(db=db, denuncia_id=20, operador_usuario_id=1, payload=self.decision_payload("mysql-report-one")),
            lambda db: create_moderation_decision(db=db, denuncia_id=20, operador_usuario_id=1, payload=self.decision_payload("mysql-report-two")),
        ])
        self.assertEqual([kind for kind, _ in results].count("ok"), 1)
        self.assertEqual(sum(isinstance(value, ModerationDecisionConflictError) for kind, value in results if kind == "error"), 1)
        db = self.Session()
        self.assertEqual(db.query(ModerationDecision).count(), 1)
        self.assertEqual(db.get(ContenidoDenuncia, 20).version, 2)
        self.assertEqual(db.get(Comercio, 10).moderation_revision, 1)
        db.close()

    def test_two_reports_cannot_apply_the_same_resource_revision(self):
        results = self.run_concurrently([
            lambda db: create_moderation_decision(db=db, denuncia_id=20, operador_usuario_id=1, payload=self.decision_payload("mysql-resource-one")),
            lambda db: create_moderation_decision(db=db, denuncia_id=21, operador_usuario_id=1, payload=self.decision_payload("mysql-resource-two")),
        ])
        self.assertEqual([kind for kind, _ in results].count("ok"), 1)
        self.assertEqual(sum(isinstance(value, ModerationDecisionConflictError) for kind, value in results if kind == "error"), 1)
        db = self.Session()
        self.assertEqual(db.query(ModerationDecision).count(), 1)
        self.assertEqual(db.get(Comercio, 10).moderation_revision, 1)
        self.assertEqual(sorted((db.get(ContenidoDenuncia, 20).version, db.get(ContenidoDenuncia, 21).version)), [1, 2])
        db.close()

    def test_concurrent_exact_decision_retry_returns_one_decision(self):
        payload = self.decision_payload("mysql-decision-idempotent")
        results = self.run_concurrently([
            lambda db: create_moderation_decision(db=db, denuncia_id=20, operador_usuario_id=1, payload=payload),
            lambda db: create_moderation_decision(db=db, denuncia_id=20, operador_usuario_id=1, payload=payload),
        ])
        self.assertEqual([kind for kind, _ in results], ["ok", "ok"])
        self.assertEqual(len({decision.id for _, decision in results}), 1)
        db = self.Session()
        self.assertEqual(db.query(ModerationDecision).count(), 1)
        self.assertEqual(db.get(Comercio, 10).moderation_revision, 1)
        db.close()

    def create_incident(self):
        db = self.Session()
        incident, _, _ = create_incident(
            db=db, actor_usuario_id=1,
            payload=OperationalIncidentCreate(
                title="Incidente", summary="Resumen seguro", incident_type="availability",
                severity="sev2_high", owner_usuario_id=1,
                idempotency_key="mysql-incident-open",
            ),
        )
        public_id = incident.public_id
        db.close()
        return public_id

    @staticmethod
    def incident_action(key):
        return OperationalIncidentAction(
            action="start_investigation", expected_version=1,
            idempotency_key=key, summary="Investigacion iniciada",
        )

    def test_incident_versions_serialize_concurrent_actions(self):
        public_id = self.create_incident()
        results = self.run_concurrently([
            lambda db: apply_incident_action(db=db, public_id=public_id, actor_usuario_id=1, payload=self.incident_action("mysql-incident-action-one")),
            lambda db: apply_incident_action(db=db, public_id=public_id, actor_usuario_id=1, payload=self.incident_action("mysql-incident-action-two")),
        ])
        self.assertEqual([kind for kind, _ in results].count("ok"), 1)
        self.assertEqual(sum(isinstance(value, IncidentConflictError) for kind, value in results if kind == "error"), 1)
        db = self.Session()
        incident = db.query(OperationalIncident).filter_by(public_id=public_id).one()
        self.assertEqual(incident.version, 2)
        self.assertEqual(db.query(OperationalIncidentEvent).filter_by(incident_id=incident.id).count(), 2)
        db.close()

    def test_concurrent_exact_incident_retry_returns_one_event(self):
        public_id = self.create_incident()
        payload = self.incident_action("mysql-incident-idempotent")
        results = self.run_concurrently([
            lambda db: apply_incident_action(db=db, public_id=public_id, actor_usuario_id=1, payload=payload),
            lambda db: apply_incident_action(db=db, public_id=public_id, actor_usuario_id=1, payload=payload),
        ])
        self.assertEqual([kind for kind, _ in results], ["ok", "ok"])
        self.assertEqual(len({event.id for _, (_, event) in results}), 1)
        db = self.Session()
        incident = db.query(OperationalIncident).filter_by(public_id=public_id).one()
        self.assertEqual(incident.version, 2)
        self.assertEqual(db.query(OperationalIncidentEvent).filter_by(incident_id=incident.id).count(), 2)
        db.close()

    def _enqueue_worker_items(self, count=1):
        db = self.Session()
        ids = []
        for offset in range(count):
            item = enqueue_report_created(
                db=db,
                report=SimpleNamespace(
                    id=100 + offset, recurso_tipo="comercio",
                    recurso_id=10, motivo=f"worker-{offset}",
                ),
            )
            db.flush()
            ids.append(item.id)
        db.commit()
        db.close()
        return ids

    def test_outbox_claim_is_exclusive_with_real_mysql_locking(self):
        ids = self._enqueue_worker_items(1)
        results = self.run_concurrently([
            lambda db: claim_due_operational_emails(db=db, claimed_by="mysql-worker-a", limit=1),
            lambda db: claim_due_operational_emails(db=db, claimed_by="mysql-worker-b", limit=1),
        ])
        self.assertEqual([kind for kind, _ in results], ["ok", "ok"])
        claims = [claim for _, batch in results for claim in batch]
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].outbox_id, ids[0])
        db = self.Session()
        row = db.get(OperationalNotificationOutbox, ids[0])
        self.assertEqual(row.status, "processing")
        self.assertEqual(row.attempt_count, 1)
        db.close()

    def test_skip_locked_distributes_distinct_rows_between_workers(self):
        ids = self._enqueue_worker_items(2)
        results = self.run_concurrently([
            lambda db: claim_due_operational_emails(db=db, claimed_by="mysql-worker-a", limit=1),
            lambda db: claim_due_operational_emails(db=db, claimed_by="mysql-worker-b", limit=1),
        ])
        self.assertEqual([kind for kind, _ in results], ["ok", "ok"])
        claimed_ids = [claim.outbox_id for _, batch in results for claim in batch]
        self.assertEqual(sorted(claimed_ids), sorted(ids))
        self.assertEqual(len(set(claimed_ids)), 2)

    def test_expired_mysql_lease_is_reclaimed_once(self):
        ids = self._enqueue_worker_items(1)
        db = self.Session()
        row = db.get(OperationalNotificationOutbox, ids[0])
        row.status = "processing"
        row.claimed_by = "dead-worker"
        row.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        row.attempt_count = 1
        db.commit()
        db.close()
        results = self.run_concurrently([
            lambda session: claim_due_operational_emails(db=session, claimed_by="recovery-a", limit=1),
            lambda session: claim_due_operational_emails(db=session, claimed_by="recovery-b", limit=1),
        ])
        claims = [claim for _, batch in results for claim in batch]
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0].attempt_count, 2)

    def test_outbox_legacy_schema_migrates_idempotently_on_mysql(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql("DROP TABLE operational_notification_outbox")
            connection.exec_driver_sql("""
                CREATE TABLE operational_notification_outbox (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    event_type VARCHAR(80) NOT NULL,
                    aggregate_type VARCHAR(40) NOT NULL,
                    aggregate_id VARCHAR(80) NOT NULL,
                    deduplication_key VARCHAR(190) NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_fingerprint VARCHAR(64) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    next_attempt_at DATETIME NULL,
                    provider_reference VARCHAR(190) NULL,
                    last_error_code VARCHAR(80) NULL,
                    created_at DATETIME NOT NULL,
                    sent_at DATETIME NULL,
                    CONSTRAINT uq_operational_notification_outbox_dedupe UNIQUE (deduplication_key)
                )
            """)
            first = outbox_migration.upgrade(connection)
            second = outbox_migration.upgrade(connection)
            inspector = inspect(connection)
            columns = {column["name"] for column in inspector.get_columns(outbox_migration.TABLE_NAME)}
            indexes = {index["name"] for index in inspector.get_indexes(outbox_migration.TABLE_NAME)}
        self.assertTrue({
            "lease_expires_at", "claimed_by", "suppressed_at",
            "suppressed_by", "suppression_reason",
            "ix_operational_notification_outbox_dispatch",
        } <= set(first))
        self.assertEqual(second, [])
        self.assertTrue({
            "lease_expires_at", "claimed_by", "suppressed_at",
            "suppressed_by", "suppression_reason",
        } <= columns)
        self.assertIn("ix_operational_notification_outbox_dispatch", indexes)


if __name__ == "__main__":
    unittest.main()
