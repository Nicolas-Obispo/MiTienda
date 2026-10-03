"""Materializador transaccional de blueprints sinteticos ET100.3.

El modulo no selecciona targets ni abre conexiones. Recibe una ``Session`` ya
validada por el runner, materializa dentro de una unica transaccion externa y
certifica el fingerprint logico antes del commit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, time
import hashlib
import hmac
import json
import secrets
from types import MappingProxyType, SimpleNamespace
from typing import Any, Callable
import uuid

from sqlalchemy import Time, inspect, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.core.security import hash_password, password_hash_is_usable, verificar_password
from app.modules.ai.providers.simulated_provider import SimulatedEmbeddingProvider
from app.modules.ai.services.comercios_embeddings_services import _build_texto_comercio
from app.modules.ai.services.usuarios_embeddings_services import generar_embedding_usuario
from app.modules.incidents.schemas.operational_incidents_schemas import (
    OperationalIncidentAction,
    OperationalIncidentCreate,
)
from app.modules.incidents.services.operational_incidents_services import (
    _fingerprint as incident_fingerprint,
    _validate_action as validate_incident_action,
)
from app.modules.moderation.schemas.contenido_denuncias_schemas import (
    ModerationDecisionCreate,
)
from app.modules.moderation.services.moderation_decisions_services import (
    _fingerprint as moderation_fingerprint,
)
from app.modules.notifications.services.operational_notification_services import (
    enqueue_report_created,
)
from app.modules.users.services.account_action_rate_limit_services import subject_digest
from app.modules.users.services.account_action_token_services import (
    _new_issuance_id,
    digest_token_secret,
    generate_token_secret,
)
from app.modules.users.services.feedgo_session_services import generate_session_id

from .blueprint import LogicalBlueprint, LogicalEntity, compile_blueprint
from .fingerprint import (
    NonDeterministicKind,
    NormalizedNonDeterministicValue,
    OwnerDerivedValue,
    canonicalize_logical_value,
)


class MaterializationError(RuntimeError):
    """El blueprint no puede materializarse sin violar su contrato."""


class InternalTransactionMutationError(MaterializationError):
    """Un owner intento apropiarse de la transaccion externa."""


@dataclass(frozen=True)
class MaterializationResult:
    profile: str
    row_count: int
    fingerprint: str
    reconstructed_fingerprint: str
    physical_ids: Mapping[str, Any]
    dependency_layers: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ReadOnlyCertificationResult:
    profile: str
    row_count: int
    fingerprint: str
    physical_ids: Mapping[str, Any]


class CommitGuardSession:
    """Vista de Session que permite trabajo ORM pero no cerrar la UoW externa."""

    def __init__(self, session: Session):
        self._session = session

    def commit(self) -> None:
        raise InternalTransactionMutationError("synthetic_internal_commit_forbidden")

    def rollback(self) -> None:
        raise InternalTransactionMutationError("synthetic_internal_rollback_forbidden")

    def close(self) -> None:
        raise InternalTransactionMutationError("synthetic_internal_close_forbidden")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


class _CaptureQuery:
    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return None


class _CaptureAddSession:
    """Adaptador focal para reutilizar el owner outbox sin persistir su side effect."""

    def __init__(self):
        self.item = None

    def query(self, *_args, **_kwargs):
        return _CaptureQuery()

    def add(self, item) -> None:
        if self.item is not None:
            raise MaterializationError("synthetic_outbox_owner_added_multiple_rows")
        self.item = item

    def commit(self) -> None:
        raise InternalTransactionMutationError("synthetic_internal_commit_forbidden")


def current_model_registry() -> dict[str, type]:
    """Registro HEAD por nombre fisico de tabla; no ejecuta I/O."""

    import_all_models()
    registry: dict[str, type] = {}
    for mapper in Base.registry.mappers:
        table = mapper.local_table.name
        if table in registry:
            raise MaterializationError(f"synthetic_duplicate_model_table:{table}")
        registry[table] = mapper.class_
    return registry


def _walk_alias_dependencies(value: Any) -> set[str]:
    dependencies: set[str] = set()
    if isinstance(value, OwnerDerivedValue):
        if value.owner in {
            "feedgo.synthetic.materializer.alias_to_database_id",
            "feedgo.synthetic.materializer.materialized_owner_attribute",
        }:
            dependencies.add(str(value.inputs["alias"]))
        for item in value.inputs.values():
            dependencies.update(_walk_alias_dependencies(item))
    elif isinstance(value, Mapping):
        for item in value.values():
            dependencies.update(_walk_alias_dependencies(item))
    elif isinstance(value, (tuple, list)):
        for item in value:
            dependencies.update(_walk_alias_dependencies(item))
    return dependencies


def _dependency_layers(blueprint: LogicalBlueprint) -> tuple[tuple[str, ...], ...]:
    aliases = {entity.alias for entity in blueprint.entities}
    dependencies = {
        entity.alias: _walk_alias_dependencies(entity.attributes)
        for entity in blueprint.entities
    }
    for relation in blueprint.relations:
        if relation.attributes.get("source_field"):
            dependencies[relation.source_alias].add(relation.target_alias)
        if relation.attributes.get("owner_before_source_field"):
            dependencies[relation.source_alias].add(relation.target_alias)

    # El owner de embedding de usuario lee interacciones ya materializadas.
    user_embedding_aliases = {
        entity.alias
        for entity in blueprint.entities
        if any(
            isinstance(value, OwnerDerivedValue)
            and value.owner.endswith("usuarios_embeddings_services.generar_embedding_usuario")
            for value in entity.attributes.values()
        )
    }
    for alias in user_embedding_aliases:
        dependencies[alias].update(aliases - {alias})

    for alias, required in dependencies.items():
        unknown = required - aliases
        if unknown:
            raise MaterializationError(
                f"synthetic_dependency_unknown:{alias}:{','.join(sorted(unknown))}"
            )
        required.discard(alias)

    pending = set(aliases)
    completed: set[str] = set()
    layers: list[tuple[str, ...]] = []
    while pending:
        ready = tuple(sorted(alias for alias in pending if dependencies[alias] <= completed))
        if not ready:
            raise MaterializationError(
                f"synthetic_dependency_cycle:{','.join(sorted(pending))}"
            )
        layers.append(ready)
        completed.update(ready)
        pending.difference_update(ready)
    return tuple(layers)


def validate_materialization_contract(
    blueprint: LogicalBlueprint,
    *,
    model_registry: Mapping[str, type] | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Valida modelos, columnas, relaciones, owners y orden sin tocar una DB."""

    registry = dict(
        current_model_registry() if model_registry is None else model_registry
    )
    entities = {entity.alias: entity for entity in blueprint.entities}
    supported_owners = {
        "feedgo.synthetic.materializer.alias_to_database_id",
        "feedgo.synthetic.materializer.materialized_owner_attribute",
        "app.modules.ai.services.comercios_embeddings_services.upsert_embedding_comercio",
        "app.modules.ai.services.usuarios_embeddings_services.generar_embedding_usuario",
        "app.modules.moderation.services.moderation_decisions_services._fingerprint",
        "app.modules.notifications.services.operational_notification_services.enqueue_report_created",
        "app.modules.incidents.services.operational_incidents_services._fingerprint",
        "app.modules.incidents.services.operational_incidents_services.apply_incident_action",
    }

    def validate_value(value: Any) -> None:
        if isinstance(value, OwnerDerivedValue):
            if value.owner not in supported_owners:
                raise MaterializationError(f"synthetic_owner_unsupported:{value.owner}")
            for nested in value.inputs.values():
                validate_value(nested)
        elif isinstance(value, Mapping):
            for nested in value.values():
                validate_value(nested)
        elif isinstance(value, (tuple, list)):
            for nested in value:
                validate_value(nested)

    for entity in blueprint.entities:
        model = registry.get(entity.entity_type)
        if model is None:
            raise MaterializationError(f"synthetic_model_missing:{entity.entity_type}")
        columns = {column.key for column in inspect(model).columns}
        unknown = set(entity.attributes) - columns
        if unknown:
            raise MaterializationError(
                f"synthetic_columns_unknown:{entity.alias}:{','.join(sorted(unknown))}"
            )
        for value in entity.attributes.values():
            validate_value(value)
        primary_keys = tuple(inspect(model).primary_key)
        if len(primary_keys) != 1:
            raise MaterializationError(f"synthetic_primary_key_unsupported:{entity.entity_type}")

    for relation in blueprint.relations:
        source_model = registry[entities[relation.source_alias].entity_type]
        target_model = registry[entities[relation.target_alias].entity_type]
        source_columns = {column.key for column in inspect(source_model).columns}
        target_columns = {column.key for column in inspect(target_model).columns}
        for key in ("source_field", "owner_before_source_field"):
            field = relation.attributes.get(key)
            if field and field not in source_columns:
                raise MaterializationError(f"synthetic_relation_field_unknown:{relation.alias}:{field}")
        target_field = relation.attributes.get("target_field")
        if target_field and target_field not in target_columns:
            raise MaterializationError(
                f"synthetic_relation_field_unknown:{relation.alias}:{target_field}"
            )
    return _dependency_layers(blueprint)


class _Resolver:
    def __init__(
        self,
        *,
        session: CommitGuardSession,
        blueprint: LogicalBlueprint,
        fixture_secret: str,
        instances: dict[str, Any],
        physical_ids: dict[str, Any],
    ):
        if not fixture_secret:
            raise MaterializationError("synthetic_fixture_secret_required")
        self.session = session
        self.blueprint = blueprint
        self.fixture_secret = fixture_secret
        self.instances = instances
        self.physical_ids = physical_ids
        self.provider = SimulatedEmbeddingProvider(dim=128)
        self._crypto_cache: dict[tuple[str, str], Any] = {}

    def prepare_crypto(self, entity: LogicalEntity) -> None:
        for field, value in entity.attributes.items():
            if not isinstance(value, NormalizedNonDeterministicValue):
                continue
            owner = value.invariants.get("owner")
            fmt = value.invariants.get("format")
            if value.kind is NonDeterministicKind.BCRYPT_HASH:
                generated = hash_password(self.fixture_secret)
            elif fmt == "token_urlsafe_32" and owner.endswith("feedgo_session_services.generate_session_id"):
                generated = generate_session_id()
            elif fmt == "token_urlsafe_32":
                generated = secrets.token_urlsafe(32)
            elif fmt == "uuid4_hex":
                generated = _new_issuance_id()
            elif value.kind is NonDeterministicKind.OWNER_GENERATED_IDENTIFIER:
                generated = f"INC-{uuid.uuid4().hex.upper()}"
            elif value.kind is NonDeterministicKind.TOKEN_DIGEST and owner.endswith(
                "account_action_token_services.digest_token_secret"
            ):
                generated = digest_token_secret(generate_token_secret())
            elif value.kind is NonDeterministicKind.TOKEN_DIGEST and owner.endswith(
                "account_action_rate_limit_services.subject_digest"
            ):
                action = str(entity.attributes["action"])
                generated = subject_digest(
                    action=action,
                    scope="synthetic_fixture",
                    subject=f"alias:{entity.alias}",
                    secret=self.fixture_secret,
                )
            elif value.kind is NonDeterministicKind.TOKEN_DIGEST and owner.endswith(
                "phone_verification_services.digest_code"
            ):
                generated = None  # Requiere issuance_id y FK ya resueltos.
            else:
                raise MaterializationError(
                    f"synthetic_nondeterministic_owner_unsupported:{owner}:{field}"
                )
            self._crypto_cache[(entity.alias, field)] = generated

    def resolve(self, value: Any, *, entity: LogicalEntity, field: str, attrs: Mapping[str, Any]) -> Any:
        if isinstance(value, NormalizedNonDeterministicValue):
            generated = self._crypto_cache[(entity.alias, field)]
            if generated is None:
                issuance = self._crypto_cache[(entity.alias, "issuance_id")]
                usuario_id = attrs.get("usuario_id")
                phone = attrs.get("phone_e164_snapshot")
                if not issuance or not usuario_id or not phone:
                    raise MaterializationError(f"synthetic_phone_digest_context_missing:{entity.alias}")
                code = f"{secrets.randbelow(1_000_000):06d}"
                payload = f"feedgo-phone-otp:v1:{issuance}:{usuario_id}:{phone}:{code}".encode()
                generated = hmac.new(
                    self.fixture_secret.encode("utf-8"), payload, hashlib.sha256
                ).hexdigest()
                self._crypto_cache[(entity.alias, field)] = generated
            return generated
        if isinstance(value, OwnerDerivedValue):
            inputs = {
                key: self.resolve(nested, entity=entity, field=field, attrs=attrs)
                for key, nested in value.inputs.items()
            }
            return self._resolve_owner(value.owner, inputs, attrs=attrs)
        if isinstance(value, Mapping):
            return {
                key: self.resolve(nested, entity=entity, field=field, attrs=attrs)
                for key, nested in value.items()
            }
        if isinstance(value, tuple):
            return [self.resolve(item, entity=entity, field=field, attrs=attrs) for item in value]
        return value

    def _resolve_owner(
        self, owner: str, inputs: dict[str, Any], *, attrs: Mapping[str, Any]
    ) -> Any:
        if owner == "feedgo.synthetic.materializer.alias_to_database_id":
            return self.physical_ids[inputs["alias"]]
        if owner == "feedgo.synthetic.materializer.materialized_owner_attribute":
            return getattr(self.instances[inputs["alias"]], inputs["attribute"])
        if owner.endswith("comercios_embeddings_services.upsert_embedding_comercio"):
            commerce = self.instances[inputs["commerce_alias"]]
            vector = self.provider.embed_text(_build_texto_comercio(commerce))
            if len(vector) != inputs["dimensions"]:
                raise MaterializationError("synthetic_embedding_dimension_mismatch")
            return json.dumps(vector)
        if owner.endswith("usuarios_embeddings_services.generar_embedding_usuario"):
            vector = generar_embedding_usuario(
                self.session, self.physical_ids[inputs["user_alias"]]
            )
            if vector is None or len(vector) != inputs["dimensions"]:
                raise MaterializationError("synthetic_user_embedding_unavailable")
            return json.dumps(vector)
        if owner.endswith("moderation_decisions_services._fingerprint"):
            payload = ModerationDecisionCreate(**inputs["payload"])
            return moderation_fingerprint(inputs["denuncia_id"], payload)
        if owner.endswith("operational_notification_services.enqueue_report_created"):
            report = SimpleNamespace(
                id=inputs["report_id"],
                recurso_tipo=inputs["resource_type"],
                recurso_id=inputs["resource_id"],
                motivo=inputs["reason_code"],
            )
            capture = _CaptureAddSession()
            enqueue_report_created(db=capture, report=report)
            if capture.item is None:
                raise MaterializationError("synthetic_outbox_owner_did_not_build")
            return getattr(capture.item, inputs["output"])
        if owner.endswith("operational_incidents_services._fingerprint"):
            operation = inputs.pop("operation")
            payload_data = inputs.pop("payload")
            if operation == "create_incident":
                payload = OperationalIncidentCreate(**payload_data)
                return incident_fingerprint(payload.model_dump())
            if operation == "apply_incident_action":
                payload = OperationalIncidentAction(**payload_data)
                return incident_fingerprint(
                    {"public_id": inputs["public_id"], **payload.model_dump()}
                )
            raise MaterializationError(f"synthetic_incident_operation_unsupported:{operation}")
        if owner.endswith("operational_incidents_services.apply_incident_action"):
            if inputs.get("output") != "safe_details_json":
                raise MaterializationError("synthetic_incident_output_unsupported")
            payload = OperationalIncidentAction(**inputs["payload"])
            persisted = self.instances[inputs["incident_alias"]]
            state_at_event = SimpleNamespace(
                status=attrs.get("status_before"),
                severity=attrs.get("severity_before") or persisted.severity,
                owner_usuario_id=persisted.owner_usuario_id,
                residual_risk_level=persisted.residual_risk_level,
                residual_risk_owner_usuario_id=persisted.residual_risk_owner_usuario_id,
                residual_risk_review_at=persisted.residual_risk_review_at,
            )
            _new_status, details = validate_incident_action(
                state_at_event, payload, self.session
            )
            return json.dumps(details, default=str, sort_keys=True) if details else None
        raise MaterializationError(f"synthetic_owner_unsupported:{owner}")


def _same_logical_value(expected: Any, actual: Any) -> bool:
    if isinstance(expected, datetime) and isinstance(actual, datetime):
        if expected.tzinfo is not None and actual.tzinfo is None:
            actual = actual.replace(tzinfo=expected.tzinfo)
    elif isinstance(actual, datetime):
        return False
    if isinstance(expected, str) and isinstance(actual, time):
        actual = actual.isoformat()
    elif isinstance(actual, time):
        return False
    return canonicalize_logical_value(expected) == canonicalize_logical_value(actual)


def _coerce_for_column(model: type, field: str, value: Any) -> Any:
    """Adapta representaciones logicas estables al tipo fisico del owner ORM."""

    column = inspect(model).columns[field]
    if isinstance(column.type, Time) and isinstance(value, str):
        try:
            return time.fromisoformat(value)
        except ValueError as exc:
            raise MaterializationError(
                f"synthetic_time_contract_invalid:{model.__tablename__}:{field}"
            ) from exc
    return value


def _validate_opaque(
    descriptor: NormalizedNonDeterministicValue,
    actual: Any,
    *,
    fixture_secret: str,
) -> None:
    if descriptor.kind is NonDeterministicKind.BCRYPT_HASH:
        if not password_hash_is_usable(actual) or not verificar_password(fixture_secret, actual):
            raise MaterializationError("synthetic_bcrypt_invariant_failed")
        return
    if descriptor.kind in {NonDeterministicKind.TOKEN_DIGEST}:
        if not isinstance(actual, str) or len(actual) != 64:
            raise MaterializationError("synthetic_digest_invariant_failed")
        return
    if descriptor.kind is NonDeterministicKind.CRYPTOGRAPHIC_NONCE:
        if not isinstance(actual, str) or len(actual) < 32:
            raise MaterializationError("synthetic_nonce_invariant_failed")
        return
    if descriptor.kind is NonDeterministicKind.OWNER_GENERATED_IDENTIFIER:
        if not isinstance(actual, str) or not actual.startswith("INC-") or len(actual) != 36:
            raise MaterializationError("synthetic_owner_identifier_invariant_failed")
        return
    raise MaterializationError(f"synthetic_opaque_kind_unsupported:{descriptor.kind.value}")


def _reconstruct_blueprint(
    blueprint: LogicalBlueprint,
    *,
    instances: Mapping[str, Any],
    expected_values: Mapping[str, Mapping[str, Any]],
    physical_ids: Mapping[str, Any],
    fixture_secret: str,
) -> LogicalBlueprint:
    relation_owned_fields: dict[str, set[str]] = {}
    for relation in blueprint.relations:
        for key in ("source_field", "owner_before_source_field"):
            field = relation.attributes.get(key)
            if field:
                relation_owned_fields.setdefault(relation.source_alias, set()).add(field)
        target_field = relation.attributes.get("target_field")
        if target_field:
            relation_owned_fields.setdefault(relation.target_alias, set()).add(target_field)
    reconstructed: list[LogicalEntity] = []
    for entity in blueprint.entities:
        instance = instances[entity.alias]
        attributes: dict[str, Any] = {}
        for field, logical_value in entity.attributes.items():
            actual = getattr(instance, field)
            if field in relation_owned_fields.get(entity.alias, set()):
                # La relacion es la representacion logica del FK final. El valor
                # fisico se valida debajo y nunca entra al fingerprint.
                attributes[field] = logical_value
            elif isinstance(logical_value, NormalizedNonDeterministicValue):
                _validate_opaque(logical_value, actual, fixture_secret=fixture_secret)
                attributes[field] = logical_value
            elif isinstance(logical_value, OwnerDerivedValue):
                # El valor ya fue producido por el owner y asignado; conservar el
                # descriptor restaura la semantica, no el ID/valor fisico.
                if not _same_logical_value(expected_values[entity.alias][field], actual):
                    raise MaterializationError(
                        f"synthetic_owner_value_mismatch:{entity.alias}:{field}"
                    )
                attributes[field] = logical_value
            else:
                if not _same_logical_value(logical_value, actual):
                    raise MaterializationError(
                        f"synthetic_reconstruction_mismatch:{entity.alias}:{field}"
                    )
                attributes[field] = logical_value
        reconstructed.append(
            LogicalEntity(
                alias=entity.alias,
                entity_type=entity.entity_type,
                attributes=attributes,
                id_policy=entity.id_policy,
                logical_id=entity.logical_id,
            )
        )
    for relation in blueprint.relations:
        source = instances[relation.source_alias]
        target = instances[relation.target_alias]
        for key in ("source_field", "owner_before_source_field"):
            field = relation.attributes.get(key)
            if field and str(getattr(source, field)) != str(physical_ids[relation.target_alias]):
                raise MaterializationError(
                    f"synthetic_relation_reconstruction_mismatch:{relation.alias}:{field}"
                )
        target_field = relation.attributes.get("target_field")
        if target_field and str(getattr(target, target_field)) != str(
            physical_ids[relation.source_alias]
        ):
            raise MaterializationError(
                f"synthetic_relation_reconstruction_mismatch:{relation.alias}:{target_field}"
            )
    return compile_blueprint(blueprint.context, reconstructed, blueprint.relations)


def materialize_blueprint(
    session: Session,
    blueprint: LogicalBlueprint,
    *,
    fixture_secret: str,
    model_registry: Mapping[str, type] | None = None,
    transaction_preflight: Callable[[CommitGuardSession], None] | None = None,
    transaction_precommit: Callable[[CommitGuardSession], None] | None = None,
) -> MaterializationResult:
    """Materializa y certifica un blueprint con exactamente una UoW externa."""

    if session.in_transaction():
        raise MaterializationError("synthetic_session_must_be_transaction_clean")
    registry = dict(
        current_model_registry() if model_registry is None else model_registry
    )
    layers = validate_materialization_contract(blueprint, model_registry=registry)
    entities = {entity.alias: entity for entity in blueprint.entities}
    instances: dict[str, Any] = {}
    physical_ids: dict[str, Any] = {}
    expected_values: dict[str, dict[str, Any]] = {}
    guarded = CommitGuardSession(session)
    resolver = _Resolver(
        session=guarded,
        blueprint=blueprint,
        fixture_secret=fixture_secret,
        instances=instances,
        physical_ids=physical_ids,
    )
    relations_by_source: dict[str, list[Any]] = {}
    for relation in blueprint.relations:
        relations_by_source.setdefault(relation.source_alias, []).append(relation)

    with session.begin():
        if transaction_preflight is not None:
            transaction_preflight(guarded)
        for layer in layers:
            for alias in layer:
                entity = entities[alias]
                resolver.prepare_crypto(entity)
                relation_values: dict[str, Any] = {}
                for relation in relations_by_source.get(alias, ()):
                    target_id = physical_ids[relation.target_alias]
                    for key in ("source_field", "owner_before_source_field"):
                        field = relation.attributes.get(key)
                        if field:
                            relation_values[field] = target_id
                attrs: dict[str, Any] = dict(relation_values)
                for field, value in entity.attributes.items():
                    resolved = resolver.resolve(value, entity=entity, field=field, attrs=attrs)
                    if field in relation_values and str(resolved) != str(relation_values[field]):
                        raise MaterializationError(
                            f"synthetic_relation_value_mismatch:{alias}:{field}"
                        )
                    attrs[field] = _coerce_for_column(
                        registry[entity.entity_type], field, resolved
                    )
                instance = registry[entity.entity_type](**attrs)
                instances[alias] = instance
                expected_values[alias] = attrs
                session.add(instance)
            session.flush()
            for alias in layer:
                model = registry[entities[alias].entity_type]
                pk_name = inspect(model).primary_key[0].key
                pk_value = getattr(instances[alias], pk_name)
                if pk_value is None:
                    raise MaterializationError(f"synthetic_primary_key_missing:{alias}")
                physical_ids[alias] = pk_value

        for relation in blueprint.relations:
            target_field = relation.attributes.get("target_field")
            if target_field:
                target_alias = relation.target_alias
                target_instance = instances[target_alias]
                setattr(
                    target_instance,
                    target_field,
                    physical_ids[relation.source_alias],
                )
                target_entity = entities[target_alias]
                target_model = registry[target_entity.entity_type]
                for column in inspect(target_model).columns:
                    if column.onupdate is not None and column.key in expected_values[target_alias]:
                        setattr(
                            target_instance,
                            column.key,
                            expected_values[target_alias][column.key],
                        )
                        flag_modified(target_instance, column.key)
        session.flush()

        # La certificacion precommit debe observar la representacion que el
        # motor realmente conservara (por ejemplo, el round-trip de MySQL
        # FLOAT), no los valores asignados que aun retiene el identity map.
        session.expire_all()

        reconstructed = _reconstruct_blueprint(
            blueprint,
            instances=instances,
            expected_values=expected_values,
            physical_ids=physical_ids,
            fixture_secret=fixture_secret,
        )
        if reconstructed.fingerprint != blueprint.fingerprint:
            raise MaterializationError("synthetic_fingerprint_mismatch_before_commit")
        if transaction_precommit is not None:
            transaction_precommit(guarded)

    return MaterializationResult(
        profile=blueprint.context.profile,
        row_count=len(instances),
        fingerprint=blueprint.fingerprint,
        reconstructed_fingerprint=reconstructed.fingerprint,
        physical_ids=MappingProxyType(dict(physical_ids)),
        dependency_layers=layers,
    )


def certify_materialized_blueprint_read_only(
    session: Session,
    blueprint: LogicalBlueprint,
    *,
    fixture_secret: str,
    model_registry: Mapping[str, type] | None = None,
) -> ReadOnlyCertificationResult:
    """Reconstruye aliases e invariantes desde ORM sin mutar ni confirmar la DB."""

    registry = dict(
        current_model_registry() if model_registry is None else model_registry
    )
    layers = validate_materialization_contract(blueprint, model_registry=registry)
    entities = {entity.alias: entity for entity in blueprint.entities}
    relations_by_source: dict[str, list[Any]] = {}
    relation_owned_fields: dict[str, set[str]] = {}
    for relation in blueprint.relations:
        relations_by_source.setdefault(relation.source_alias, []).append(relation)
        for key in ("source_field", "owner_before_source_field"):
            field = relation.attributes.get(key)
            if field:
                relation_owned_fields.setdefault(relation.source_alias, set()).add(field)
        target_field = relation.attributes.get("target_field")
        if target_field:
            relation_owned_fields.setdefault(relation.target_alias, set()).add(target_field)

    rows_by_table = {
        table: list(session.scalars(select(model)).all())
        for table, model in registry.items()
    }
    expected_counts: dict[str, int] = {}
    for entity in blueprint.entities:
        expected_counts[entity.entity_type] = expected_counts.get(entity.entity_type, 0) + 1
    for table, rows in rows_by_table.items():
        if len(rows) != expected_counts.get(table, 0):
            raise MaterializationError(f"synthetic_readonly_count_mismatch:{table}")

    instances: dict[str, Any] = {}
    physical_ids: dict[str, Any] = {}
    used_rows: dict[str, set[int]] = {}
    for layer in layers:
        for alias in layer:
            entity = entities[alias]
            model = registry[entity.entity_type]
            candidates = []
            for row in rows_by_table[entity.entity_type]:
                if id(row) in used_rows.setdefault(entity.entity_type, set()):
                    continue
                matches = True
                for field, logical in entity.attributes.items():
                    if field in relation_owned_fields.get(alias, set()) or isinstance(
                        logical, (NormalizedNonDeterministicValue, OwnerDerivedValue)
                    ):
                        continue
                    if not _same_logical_value(logical, getattr(row, field)):
                        matches = False
                        break
                if not matches:
                    continue
                for relation in relations_by_source.get(alias, ()):
                    target_id = physical_ids[relation.target_alias]
                    for key in ("source_field", "owner_before_source_field"):
                        field = relation.attributes.get(key)
                        if field and str(getattr(row, field)) != str(target_id):
                            matches = False
                            break
                    if not matches:
                        break
                if matches:
                    candidates.append(row)
            if len(candidates) != 1:
                raise MaterializationError(
                    f"synthetic_readonly_alias_ambiguous:{alias}:{len(candidates)}"
                )
            instance = candidates[0]
            instances[alias] = instance
            used_rows[entity.entity_type].add(id(instance))
            physical_ids[alias] = getattr(instance, inspect(model).primary_key[0].key)

    resolver = _Resolver(
        session=CommitGuardSession(session),
        blueprint=blueprint,
        fixture_secret=fixture_secret,
        instances=instances,
        physical_ids=physical_ids,
    )
    for entity in blueprint.entities:
        attrs = {
            field: getattr(instances[entity.alias], field)
            for field in inspect(registry[entity.entity_type]).columns.keys()
        }
        for field, logical in entity.attributes.items():
            actual = getattr(instances[entity.alias], field)
            if isinstance(logical, NormalizedNonDeterministicValue):
                _validate_opaque(logical, actual, fixture_secret=fixture_secret)
            elif isinstance(logical, OwnerDerivedValue):
                expected = resolver.resolve(
                    logical, entity=entity, field=field, attrs=attrs
                )
                if not _same_logical_value(expected, actual):
                    raise MaterializationError(
                        f"synthetic_readonly_owner_mismatch:{entity.alias}:{field}"
                    )

    for relation in blueprint.relations:
        target_field = relation.attributes.get("target_field")
        if target_field and str(
            getattr(instances[relation.target_alias], target_field)
        ) != str(physical_ids[relation.source_alias]):
            raise MaterializationError(
                f"synthetic_readonly_relation_mismatch:{relation.alias}:{target_field}"
            )

    return ReadOnlyCertificationResult(
        profile=blueprint.context.profile,
        row_count=len(instances),
        fingerprint=blueprint.fingerprint,
        physical_ids=MappingProxyType(dict(physical_ids)),
    )
