"""Contratos focales de los profiles puros smoke y functional de ET100.3."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import unittest

from app.modules.users.services.email_normalization import canonicalize_email
from app.modules.users.services.phone_normalization import canonicalize_phone
from synthetic_data.blueprint import BlueprintContractError, ClockPolicy, LogicalIdPolicy
from synthetic_data.fingerprint import (
    NonDeterministicKind,
    NormalizedNonDeterministicValue,
    OwnerDerivedValue,
    canonical_json,
)
from synthetic_data.scenarios import (
    compile_functional,
    compile_representative,
    compile_scenario,
    compile_smoke,
)


ANCHOR = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
ARGS = {
    "dataset_version": "et100.3-v1",
    "seed": "approved-profile-seed-001",
    "clock_policy": ClockPolicy(anchor=ANCHOR),
}


def _aliases(blueprint):
    return {entity.alias for entity in blueprint.entities}


class SyntheticScenarioTests(unittest.TestCase):
    def test_approved_cardinalities_are_exact(self):
        smoke = compile_smoke(**ARGS)
        functional = compile_functional(**ARGS)

        self.assertEqual(len(smoke.entities), 20)
        self.assertEqual(len(functional.entities), 93)
        self.assertEqual(
            Counter(entity.entity_type for entity in smoke.entities),
            Counter(
                {
                    "usuarios": 1,
                    "password_credentials": 1,
                    "usuarios_documentos_aceptaciones": 2,
                    "feedgo_sessions": 1,
                    "rubros": 1,
                    "taxonomy_nodes": 5,
                    "taxonomy_assignments": 3,
                    "comercios": 1,
                    "comercios_horarios_atencion": 1,
                    "secciones": 1,
                    "publicaciones": 1,
                    "historias": 1,
                    "comercios_embeddings": 1,
                }
            ),
        )
        self.assertEqual(
            Counter(entity.entity_type for entity in functional.entities),
            Counter(
                {
                    "usuarios": 3,
                    "password_credentials": 3,
                    "usuarios_documentos_aceptaciones": 4,
                    "feedgo_sessions": 3,
                    "account_action_tokens": 4,
                    "account_action_rate_limits": 2,
                    "phone_verification_challenges": 3,
                    "administrative_capability_events": 4,
                    "rubros": 2,
                    "taxonomy_nodes": 8,
                    "taxonomy_assignments": 6,
                    "comercios": 3,
                    "comercios_horarios_atencion": 1,
                    "secciones": 2,
                    "publicaciones": 4,
                    "historias": 4,
                    "seguidores": 1,
                    "likes_publicaciones": 1,
                    "publicaciones_guardadas": 1,
                    "historias_vistas": 1,
                    "historias_likes": 1,
                    "comercios_embeddings": 2,
                    "usuarios_embeddings": 1,
                    "contenido_denuncias": 3,
                    "moderation_decisions": 2,
                    "operational_notification_outbox": 3,
                    "comercios_metricas_sociales": 2,
                    "comercios_metricas_snapshots": 2,
                    "agenda_contextos_agendables": 2,
                    "feedgo_agenda_contextos": 2,
                    "agenda_elementos": 3,
                    "operational_incidents": 2,
                    "operational_incident_events": 6,
                    "knowledge_proposals": 2,
                }
            ),
        )

    def test_functional_contains_the_exact_smoke_rows_and_relations(self):
        smoke = compile_smoke(**ARGS)
        functional = compile_functional(**ARGS)
        functional_entities = {item.alias: item for item in functional.entities}
        functional_relations = {item.alias: item for item in functional.relations}

        for entity in smoke.entities:
            self.assertIn(entity.alias, functional_entities)
            self.assertEqual(entity, functional_entities[entity.alias])
        for relation in smoke.relations:
            self.assertIn(relation.alias, functional_relations)
            self.assertEqual(relation, functional_relations[relation.alias])

    def test_representative_contains_functional_and_adds_exactly_36_rows(self):
        functional = compile_functional(**ARGS)
        representative = compile_representative(**ARGS)
        representative_entities = {
            item.alias: item for item in representative.entities
        }
        representative_relations = {
            item.alias: item for item in representative.relations
        }

        self.assertEqual(len(functional.entities), 93)
        self.assertEqual(len(representative.entities), 129)
        self.assertEqual(len(representative.entities) - len(functional.entities), 36)
        for entity in functional.entities:
            self.assertEqual(representative_entities.get(entity.alias), entity)
        for relation in functional.relations:
            self.assertEqual(representative_relations.get(relation.alias), relation)

        delta = Counter(item.entity_type for item in representative.entities) - Counter(
            item.entity_type for item in functional.entities
        )
        self.assertEqual(
            delta,
            Counter(
                {
                    "usuarios": 1,
                    "password_credentials": 1,
                    "usuarios_documentos_aceptaciones": 2,
                    "feedgo_sessions": 1,
                    "usuarios_embeddings": 1,
                    "comercios": 3,
                    "taxonomy_assignments": 3,
                    "comercios_embeddings": 3,
                    "comercios_horarios_atencion": 2,
                    "publicaciones": 4,
                    "historias": 2,
                    "seguidores": 1,
                    "likes_publicaciones": 1,
                    "publicaciones_guardadas": 1,
                    "historias_vistas": 1,
                    "historias_likes": 1,
                    "comercios_metricas_sociales": 1,
                    "comercios_metricas_snapshots": 2,
                    "search_events": 3,
                    "operational_notification_outbox": 1,
                    "knowledge_proposals": 1,
                }
            ),
        )

    def test_expected_aliases_and_representative_states_exist(self):
        smoke = compile_smoke(**ARGS)
        functional = compile_functional(**ARGS)
        self.assertTrue(
            {
                "user.owner",
                "credential.owner",
                "session.owner.active",
                "commerce.primary",
                "post.primary.active",
                "story.primary.active",
                "embedding.commerce.primary",
            }
            <= _aliases(smoke)
        )
        self.assertTrue(
            {
                "user.operator",
                "user.incomplete",
                "session.owner.expired",
                "session.owner.revoked",
                "commerce.inactive",
                "post.primary.hidden",
                "story.primary.expired_active",
                "report.post.received",
                "decision.post.hidden",
                "agenda.element.cancelled",
                "incident.open",
                "incident.reviewed",
                "knowledge.proposal.pending",
                "knowledge.proposal.rejected",
            }
            <= _aliases(functional)
        )

        self.assertTrue(functional.entity("commerce.primary").attributes["activo"])
        self.assertFalse(functional.entity("commerce.inactive").attributes["activo"])
        self.assertTrue(functional.entity("post.primary.hidden").attributes["moderation_hidden"])
        self.assertEqual(functional.entity("agenda.element.completed").attributes["estado"], "completado")
        self.assertEqual(functional.entity("incident.reviewed").attributes["status"], "reviewed")

    def test_taxonomy_and_ownership_invariants_are_explicit(self):
        functional = compile_functional(**ARGS)
        entity_aliases = _aliases(functional)
        relation_aliases = {relation.alias for relation in functional.relations}

        self.assertEqual(
            {entity.attributes["slug"] for entity in functional.entities if entity.entity_type == "taxonomy_nodes"},
            {
                "consumo",
                "gastronomia-categoria",
                "comida-preparada",
                "gastronomia",
                "pizzerias-rotiserias-delivery",
                "servicios",
                "servicios-profesionales",
                "marketing-digital",
            },
        )
        self.assertIn("link.commerce.primary.owner", relation_aliases)
        self.assertIn("link.commerce.secondary.owner", relation_aliases)
        self.assertIn("hierarchy.taxonomy.pizzerias", relation_aliases)
        for relation in functional.relations:
            self.assertIn(relation.source_alias, entity_aliases)
            self.assertIn(relation.target_alias, entity_aliases)

    def test_fingerprints_are_reproducible_and_profile_specific(self):
        smoke_a = compile_smoke(**ARGS)
        smoke_b = compile_smoke(**ARGS)
        functional_a = compile_functional(**ARGS)
        functional_b = compile_functional(**ARGS)
        representative_a = compile_representative(**ARGS)
        representative_b = compile_representative(**ARGS)

        self.assertEqual(smoke_a.fingerprint, smoke_b.fingerprint)
        self.assertEqual(functional_a.fingerprint, functional_b.fingerprint)
        self.assertEqual(representative_a.fingerprint, representative_b.fingerprint)
        self.assertNotEqual(smoke_a.fingerprint, functional_a.fingerprint)
        self.assertNotEqual(functional_a.fingerprint, representative_a.fingerprint)
        self.assertEqual(
            smoke_a.fingerprint,
            "270e49fbb75c5dfb28baa98e4e888370b551cb88ac7707f56afad5e934ddb8cb",
        )
        self.assertEqual(
            functional_a.fingerprint,
            "ce296eaac309698a382e3bc932ec270e0b45336ac563180b7b145064912d2e33",
        )
        self.assertEqual(
            representative_a.fingerprint,
            "6449fff23402a480bdb42dac00adff4f2f549946bf41087bc2f4cda07cc76748",
        )

    def test_blueprint_attributes_belong_to_current_head_models(self):
        from app.core.database import Base
        from app.core.model_registry import import_all_models

        import_all_models()
        representative = compile_representative(**ARGS)
        for entity in representative.entities:
            table = Base.metadata.tables.get(entity.entity_type)
            self.assertIsNotNone(table, entity.entity_type)
            self.assertEqual(
                set(entity.attributes) - set(table.columns.keys()),
                set(),
                entity.alias,
            )

    def test_legal_and_taxonomy_rows_match_their_current_owners(self):
        from app.modules.discovery.services.taxonomy_seed_services import TAXONOMY_NODES_SEED
        from app.modules.users.services.documentos_aceptacion_services import (
            CANAL_REGISTRO_WEB,
            DOCUMENTOS_OBLIGATORIOS_REGISTRO,
            ESTADO_ACEPTADO,
            METODO_CHECKBOX_EXPLICITO,
        )

        functional = compile_functional(**ARGS)
        for suffix, document in zip(
            ("terms", "privacy"), DOCUMENTOS_OBLIGATORIOS_REGISTRO, strict=True
        ):
            row = functional.entity(f"legal.owner.{suffix}").attributes
            self.assertEqual(
                (
                    row["documento_tipo"], row["documento_version"],
                    row["documento_referencia"], row["canal"], row["metodo"], row["estado"],
                ),
                (
                    document.tipo, document.version, document.referencia,
                    CANAL_REGISTRO_WEB, METODO_CHECKBOX_EXPLICITO, ESTADO_ACEPTADO,
                ),
            )

        owner_nodes = {item.slug: item for item in TAXONOMY_NODES_SEED}
        for row in (item for item in functional.entities if item.entity_type == "taxonomy_nodes"):
            owner = owner_nodes[row.attributes["slug"]]
            self.assertEqual(row.attributes["nombre"], owner.nombre)
            self.assertEqual(row.attributes["type"], owner.type)
            self.assertEqual(row.attributes["descripcion"], owner.descripcion)
            self.assertEqual(row.attributes["orden"], owner.orden)
            self.assertEqual(
                canonical_json(row.attributes["metadata_json"]),
                canonical_json(owner.metadata_json),
            )

    def test_embeddings_are_owned_by_current_services_and_simulated_dimension(self):
        from app.modules.ai.providers.simulated_provider import SimulatedEmbeddingProvider

        functional = compile_functional(**ARGS)
        provider = SimulatedEmbeddingProvider()
        self.assertEqual(len(provider.embed_text("feedgo synthetic contract")), 128)
        for alias in (
            "embedding.commerce.primary",
            "embedding.commerce.secondary",
            "embedding.user.operator",
        ):
            vector = functional.entity(alias).attributes["vector"]
            self.assertIsInstance(vector, OwnerDerivedValue)
            self.assertEqual(vector.inputs["provider"], "SimulatedEmbeddingProvider")
            self.assertEqual(vector.inputs["dimensions"], 128)
            self.assertIn("embeddings_services", vector.owner)

    def test_moderation_outbox_and_incident_derived_values_reference_current_owners(self):
        from types import SimpleNamespace

        from app.core.model_registry import import_all_models
        from app.modules.moderation.schemas.contenido_denuncias_schemas import ModerationDecisionCreate
        from app.modules.moderation.services.moderation_decisions_services import (
            _fingerprint as moderation_fingerprint,
        )
        from app.modules.notifications.services.operational_notification_services import (
            REPORT_CREATED,
            enqueue_report_created,
        )
        from app.modules.incidents.schemas.operational_incidents_schemas import (
            OperationalIncidentAction,
            OperationalIncidentCreate,
        )
        from app.modules.incidents.services.operational_incidents_services import (
            _fingerprint as incident_fingerprint,
        )

        functional = compile_functional(**ARGS)
        import_all_models()
        decision = functional.entity("decision.post.hidden").attributes
        self.assertIsInstance(decision["request_fingerprint"], OwnerDerivedValue)
        self.assertEqual(
            decision["request_fingerprint"].owner,
            "app.modules.moderation.services.moderation_decisions_services._fingerprint",
        )
        self.assertIsInstance(decision["request_fingerprint"].inputs["denuncia_id"], OwnerDerivedValue)
        moderation_payload = ModerationDecisionCreate(
            **dict(decision["request_fingerprint"].inputs["payload"])
        )
        self.assertEqual(len(moderation_fingerprint(101, moderation_payload)), 64)
        decision_resource = next(
            relation
            for relation in functional.relations
            if relation.alias == "link.decision.post.hidden.resource"
        )
        self.assertEqual(
            decision_resource.attributes["target_field"],
            "moderation_hidden_by_decision_id",
        )

        for index in range(1, 4):
            outbox = functional.entity(f"outbox.moderation.{index}").attributes
            self.assertEqual(outbox["event_type"], REPORT_CREATED)
            self.assertEqual(outbox["aggregate_type"], "moderation_report")
            for field in ("aggregate_id", "deduplication_key", "payload_json", "payload_fingerprint"):
                self.assertIsInstance(outbox[field], OwnerDerivedValue)
                self.assertTrue(outbox[field].owner.endswith(".enqueue_report_created"))
                self.assertEqual(outbox[field].inputs["output"], field)

        class EmptyQuery:
            def filter(self, *_args):
                return self

            def first(self):
                return None

        class CaptureSession:
            def __init__(self):
                self.added = []

            def query(self, *_args):
                return EmptyQuery()

            def add(self, item):
                self.added.append(item)

        capture = CaptureSession()
        owner_outbox = enqueue_report_created(
            db=capture,
            report=SimpleNamespace(
                id=101, recurso_tipo="publicacion", recurso_id=202, motivo="spam"
            ),
        )
        self.assertIs(owner_outbox, capture.added[0])
        self.assertEqual(owner_outbox.event_type, REPORT_CREATED)
        self.assertEqual(owner_outbox.aggregate_type, "moderation_report")
        self.assertEqual(len(owner_outbox.payload_fingerprint), 64)

        incident = functional.entity("incident.open").attributes
        self.assertIsInstance(incident["public_id"], NormalizedNonDeterministicValue)
        self.assertIs(incident["public_id"].kind, NonDeterministicKind.OWNER_GENERATED_IDENTIFIER)
        self.assertEqual(incident["public_id"].invariants["format"], "INC-{UUID4_HEX_UPPER}")
        self.assertIsInstance(incident["request_fingerprint"], OwnerDerivedValue)
        create_payload = dict(incident["request_fingerprint"].inputs["payload"])
        create_payload["owner_usuario_id"] = 42
        create_schema = OperationalIncidentCreate(**create_payload)
        self.assertEqual(len(incident_fingerprint(create_schema.model_dump())), 64)
        opened = functional.entity("incident.event.open.created").attributes
        self.assertEqual(opened["event_type"], "opened")
        self.assertEqual(opened["idempotency_key"], incident["idempotency_key"])
        self.assertEqual(opened["request_fingerprint"], incident["request_fingerprint"])
        action = functional.entity("incident.event.reviewed.investigating").attributes
        action_payload = OperationalIncidentAction(
            **dict(action["request_fingerprint"].inputs["payload"])
        )
        self.assertEqual(
            len(incident_fingerprint({"public_id": "INC-" + "A" * 32, **action_payload.model_dump()})),
            64,
        )
        resolved = functional.entity("incident.event.reviewed.resolved").attributes
        self.assertIsInstance(resolved["safe_details_json"], OwnerDerivedValue)
        reviewed_owner_relation = next(
            relation
            for relation in functional.relations
            if relation.alias == "link.incident.event.reviewed.reviewed.owner_after"
        )
        self.assertEqual(
            reviewed_owner_relation.attributes["owner_before_source_field"],
            "owner_before_usuario_id",
        )
        self.assertNotIn("synthetic-incident-fingerprint", canonical_json(functional.logical_payload()))

    def test_knowledge_rows_match_candidate_owner(self):
        from app.modules.knowledge.builder.schemas.evidence_schemas import SynonymEvidence
        from app.modules.knowledge.builder.services.proposal_services import proposal_from_evidence

        functional = compile_functional(**ARGS)
        for index, alias in enumerate(
            ("knowledge.proposal.pending", "knowledge.proposal.rejected"), 1
        ):
            row = functional.entity(alias).attributes
            evidence = SynonymEvidence(**row["evidence_json"])
            candidate = proposal_from_evidence(evidence)
            self.assertIsNotNone(candidate)
            self.assertEqual(row["proposal_type"], candidate.proposal_type)
            self.assertEqual(row["query"], candidate.query)
            self.assertEqual(row["term"], candidate.term)
            self.assertEqual(row["target_payload_json"], candidate.target_payload_json)
            self.assertEqual(row["dedupe_key"], candidate.dedupe_key)

    def test_representative_matrix_aliases_relations_and_domains_are_exact(self):
        functional = compile_functional(**ARGS)
        representative = compile_representative(**ARGS)
        functional_aliases = _aliases(functional)
        aliases = _aliases(representative)
        approved_delta_aliases = {
            "assignment.commerce.representative.distant_peer",
            "assignment.commerce.representative.local_peer",
            "assignment.commerce.representative.no_location_secondary_owner",
            "credential.representative.owner_secondary",
            "embedding.commerce.representative.distant_peer",
            "embedding.commerce.representative.local_peer",
            "embedding.commerce.representative.no_location_secondary_owner",
            "embedding.user.representative.owner_secondary",
            "legal.representative.owner_secondary.privacy",
            "legal.representative.owner_secondary.terms",
            "user.representative.owner_secondary",
            "commerce.representative.local_peer",
            "commerce.representative.distant_peer",
            "commerce.representative.no_location_secondary_owner",
            "schedule.representative.local_peer.morning",
            "schedule.representative.local_peer.afternoon",
            "post.representative.local.tie",
            "story.representative.local.linked",
            "social.representative.follow.local",
            "metrics.representative.local_peer",
            "snapshot.representative.local_peer.1",
            "snapshot.representative.local_peer.2",
            "search.representative.keyword",
            "search.representative.semantic_geo",
            "search.representative.no_results",
            "outbox.representative.incident.pending",
            "knowledge.proposal.representative.approved",
            "post.representative.distant.tie",
            "post.representative.local.secondary",
            "post.representative.secondary_owner",
            "session.representative.owner_secondary.active",
            "social.representative.like.post",
            "social.representative.like.story",
            "social.representative.save.post",
            "social.representative.view.story",
            "story.representative.secondary_owner.independent",
        }
        self.assertEqual(aliases - functional_aliases, approved_delta_aliases)
        entity_aliases = _aliases(representative)
        for relation in representative.relations:
            self.assertIn(relation.source_alias, entity_aliases)
            self.assertIn(relation.target_alias, entity_aliases)

        entity_types = {item.entity_type for item in representative.entities}
        self.assertTrue(
            {
                "external_identities",
                "oauth_authorization_transactions",
                "oauth_session_delivery_handles",
                "productos",
            }.isdisjoint(entity_types)
        )
        self.assertEqual(
            sum(item.entity_type == "search_events" for item in representative.entities),
            3,
        )
        for item in representative.entities:
            if item.alias.startswith("embedding."):
                vector = item.attributes["vector"]
                self.assertEqual(vector.inputs["provider"], "SimulatedEmbeddingProvider")
                self.assertEqual(vector.inputs["dimensions"], 128)

        outbox = representative.entity(
            "outbox.representative.incident.pending"
        ).attributes
        for field in (
            "aggregate_id",
            "deduplication_key",
            "payload_json",
            "payload_fingerprint",
        ):
            self.assertIsInstance(outbox[field], OwnerDerivedValue)
            self.assertTrue(outbox[field].owner.endswith(".enqueue_incident_opened"))
            self.assertEqual(outbox[field].inputs["output"], field)

    def test_only_unapproved_future_profiles_remain_deferred(self):
        self.assertEqual(len(compile_scenario(profile="representative", **ARGS).entities), 129)
        for profile in ("capacity", "adversarial"):
            with self.subTest(profile=profile), self.assertRaises(BlueprintContractError):
                compile_scenario(profile=profile, **ARGS)

    def test_profiles_use_no_deterministic_uuid(self):
        for blueprint in (
            compile_smoke(**ARGS),
            compile_functional(**ARGS),
            compile_representative(**ARGS),
        ):
            self.assertTrue(
                all(entity.id_policy is LogicalIdPolicy.NONE for entity in blueprint.entities)
            )
            self.assertTrue(all(entity.logical_id is None for entity in blueprint.entities))

    def test_approved_synthetic_email_and_phone_contract(self):
        from app.modules.users.services.email_verification_services import EMAIL_LINK_SOURCE
        from app.modules.users.services.phone_verification_services import SOURCE as PHONE_OTP_SOURCE

        functional = compile_functional(**ARGS)
        users = [entity for entity in functional.entities if entity.entity_type == "usuarios"]

        self.assertEqual(len(users), 3)
        self.assertTrue(all(entity.attributes["email"].endswith("@example.com") for entity in users))
        self.assertEqual(functional.entity("user.owner").attributes["telefono_e164"], "+12025550123")
        self.assertEqual(
            functional.entity("phone.challenge.active").attributes["phone_e164_snapshot"],
            "+12025550123",
        )
        serialized = canonical_json(functional.logical_payload())
        self.assertNotIn("example.invalid", serialized)
        for user in users:
            email = user.attributes["email"]
            self.assertEqual(canonicalize_email(email), email)
        self.assertEqual(canonicalize_phone("+12025550123"), "+12025550123")
        self.assertEqual(functional.entity("user.owner").attributes["email_verification_source"], EMAIL_LINK_SOURCE)
        self.assertEqual(functional.entity("user.owner").attributes["telefono_verification_source"], PHONE_OTP_SOURCE)

        session_id = functional.entity("session.owner.active").attributes["id"]
        token_digest = functional.entity("token.password_reset.active").attributes["token_digest"]
        rate_digest = functional.entity("rate.password_login.open").attributes["subject_digest"]
        phone_digest = functional.entity("phone.challenge.active").attributes["code_digest"]
        self.assertTrue(session_id.invariants["owner"].endswith(".generate_session_id"))
        self.assertTrue(token_digest.invariants["owner"].endswith(".digest_token_secret"))
        self.assertEqual(rate_digest.invariants["algorithm"], "hmac-sha256")
        self.assertTrue(phone_digest.invariants["owner"].endswith(".digest_code"))

    def test_deferred_domains_and_physical_media_are_absent(self):
        functional = compile_functional(**ARGS)
        entity_types = {entity.entity_type for entity in functional.entities}
        deferred = {
            "external_identities",
            "oauth_authorization_transactions",
            "oauth_session_delivery_handles",
            "search_events",
            "productos",
        }
        self.assertTrue(deferred.isdisjoint(entity_types))
        self.assertTrue(
            all(entity.id_policy is LogicalIdPolicy.NONE for entity in functional.entities)
        )
        serialized = canonical_json(functional.logical_payload())
        self.assertNotIn("backend/uploads", serialized)
        self.assertNotIn("sentence-transformers", serialized)
        self.assertNotIn("google", serialized.casefold())


if __name__ == "__main__":
    unittest.main()
