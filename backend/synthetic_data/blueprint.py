"""Modelo logico puro para compilar escenarios sinteticos deterministas."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import re
from types import MappingProxyType
from typing import Any, Iterable, Mapping
from uuid import NAMESPACE_URL, UUID, uuid5

from .fingerprint import (
    canonicalize_logical_value,
    freeze_logical_value,
    logical_fingerprint,
)


_LABEL_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_SEED_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class BlueprintContractError(ValueError):
    """La declaracion del blueprint es ambigua o viola sus invariantes."""


def _validate_label(value: str, owner: str) -> str:
    if not isinstance(value, str) or not _LABEL_PATTERN.fullmatch(value):
        raise BlueprintContractError(f"{owner} no cumple el formato de alias logico")
    return value


@dataclass(frozen=True)
class ClockPolicy:
    """Reloj controlado: nunca cae implicitamente en el reloj real."""

    anchor: datetime
    policy: str = "fixed_utc_v1"

    def __post_init__(self) -> None:
        if self.policy != "fixed_utc_v1":
            raise BlueprintContractError("clock_policy no soportada")
        if self.anchor.tzinfo is None or self.anchor.utcoffset() is None:
            raise BlueprintContractError("clock anchor debe incluir timezone")
        normalized = self.anchor.astimezone(timezone.utc)
        if normalized.microsecond:
            raise BlueprintContractError("clock anchor debe tener precision de segundos")
        object.__setattr__(self, "anchor", normalized)

    def at(self, *, seconds: int = 0) -> datetime:
        if not isinstance(seconds, int):
            raise BlueprintContractError("El offset del reloj debe expresarse en segundos")
        return self.anchor + timedelta(seconds=seconds)

    def logical_payload(self) -> Mapping[str, Any]:
        return {
            "policy": self.policy,
            "anchor": self.anchor,
        }


@dataclass(frozen=True)
class BlueprintContext:
    dataset_version: str
    profile: str
    seed: str = field(repr=False)
    clock_policy: ClockPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_version, str) or not _VERSION_PATTERN.fullmatch(
            self.dataset_version
        ):
            raise BlueprintContractError("dataset_version invalida")
        _validate_label(self.profile, "profile")
        if not isinstance(self.seed, str) or not _SEED_PATTERN.fullmatch(self.seed):
            raise BlueprintContractError("seed obligatoria o con formato invalido")
        if not isinstance(self.clock_policy, ClockPolicy):
            raise BlueprintContractError("clock_policy obligatoria")

    @property
    def seed_digest(self) -> str:
        payload = f"feedgo.synthetic.seed.v1\0{self.seed}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @property
    def deterministic_namespace(self) -> UUID:
        scope = ":".join((self.dataset_version, self.profile, self.seed_digest))
        return uuid5(NAMESPACE_URL, f"feedgo.synthetic:{scope}")

    def logical_payload(self) -> Mapping[str, Any]:
        # El seed participa del contrato mediante digest; el valor no se serializa.
        return {
            "dataset_version": self.dataset_version,
            "profile": self.profile,
            "seed_digest": self.seed_digest,
            "clock_policy": self.clock_policy.logical_payload(),
        }


class LogicalIdPolicy(str, Enum):
    NONE = "none"
    DETERMINISTIC_UUID = "deterministic_uuid_v5"


@dataclass(frozen=True)
class LogicalEntity:
    alias: str
    entity_type: str
    attributes: Mapping[str, Any]
    id_policy: LogicalIdPolicy = LogicalIdPolicy.NONE
    logical_id: UUID | None = None
    # Identidad fisica observada tras materializar: nunca es identidad logica.
    database_id: int | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        _validate_label(self.alias, "entity alias")
        _validate_label(self.entity_type, "entity_type")
        if not isinstance(self.id_policy, LogicalIdPolicy):
            raise BlueprintContractError("id_policy no soportada")
        if self.id_policy is LogicalIdPolicy.NONE and self.logical_id is not None:
            raise BlueprintContractError("logical_id requiere una politica determinista")
        if self.id_policy is LogicalIdPolicy.DETERMINISTIC_UUID and self.logical_id is None:
            raise BlueprintContractError("Falta logical_id determinista")
        if self.database_id is not None and (
            not isinstance(self.database_id, int) or self.database_id <= 0
        ):
            raise BlueprintContractError("database_id debe ser un entero positivo")
        frozen = freeze_logical_value(self.attributes)
        canonicalize_logical_value(frozen)
        object.__setattr__(self, "attributes", frozen)

    def logical_payload(self) -> Mapping[str, Any]:
        return {
            "alias": self.alias,
            "entity_type": self.entity_type,
            "id_policy": self.id_policy.value,
            "logical_id": self.logical_id,
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class LogicalRelation:
    alias: str
    relation_type: str
    source_alias: str
    target_alias: str
    attributes: Mapping[str, Any]

    def __post_init__(self) -> None:
        _validate_label(self.alias, "relation alias")
        _validate_label(self.relation_type, "relation_type")
        _validate_label(self.source_alias, "source_alias")
        _validate_label(self.target_alias, "target_alias")
        frozen = freeze_logical_value(self.attributes)
        canonicalize_logical_value(frozen)
        object.__setattr__(self, "attributes", frozen)

    def logical_payload(self) -> Mapping[str, Any]:
        return {
            "alias": self.alias,
            "relation_type": self.relation_type,
            "source_alias": self.source_alias,
            "target_alias": self.target_alias,
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class LogicalBlueprint:
    context: BlueprintContext
    entities: tuple[LogicalEntity, ...]
    relations: tuple[LogicalRelation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.context, BlueprintContext):
            raise BlueprintContractError("context obligatorio")
        entities = tuple(sorted(self.entities, key=lambda item: item.alias))
        relations = tuple(sorted(self.relations, key=lambda item: item.alias))
        all_aliases = [item.alias for item in (*entities, *relations)]
        if len(all_aliases) != len(set(all_aliases)):
            raise BlueprintContractError("Los aliases logicos deben ser globalmente unicos")
        entity_aliases = {entity.alias for entity in entities}
        for relation in relations:
            if (
                relation.source_alias not in entity_aliases
                or relation.target_alias not in entity_aliases
            ):
                raise BlueprintContractError(
                    f"Relacion {relation.alias} referencia aliases inexistentes"
                )
        object.__setattr__(self, "entities", entities)
        object.__setattr__(self, "relations", relations)

    def logical_payload(self) -> Mapping[str, Any]:
        return {
            "contract": "feedgo.synthetic.blueprint.v1",
            "context": self.context.logical_payload(),
            "entities": tuple(entity.logical_payload() for entity in self.entities),
            "relations": tuple(relation.logical_payload() for relation in self.relations),
        }

    @property
    def fingerprint(self) -> str:
        return logical_fingerprint(self.logical_payload())

    def entity(self, alias: str) -> LogicalEntity:
        for entity in self.entities:
            if entity.alias == alias:
                return entity
        raise KeyError(alias)

    def with_database_ids(self, database_ids: Mapping[str, int]) -> "LogicalBlueprint":
        known = {entity.alias for entity in self.entities}
        unknown = set(database_ids) - known
        if unknown:
            raise BlueprintContractError(
                f"Aliases sin entidad para database_id: {sorted(unknown)}"
            )
        entities = tuple(
            replace(entity, database_id=database_ids.get(entity.alias, entity.database_id))
            for entity in self.entities
        )
        return replace(self, entities=entities)


class BlueprintBuilder:
    """Compilador declarativo sin I/O, perfiles ni efectos de materializacion."""

    def __init__(self, context: BlueprintContext):
        self.context = context
        self._entities: dict[str, LogicalEntity] = {}
        self._relations: dict[str, LogicalRelation] = {}

    def add_entity(
        self,
        *,
        alias: str,
        entity_type: str,
        attributes: Mapping[str, Any],
        id_policy: LogicalIdPolicy = LogicalIdPolicy.NONE,
        database_id: int | None = None,
    ) -> "BlueprintBuilder":
        if alias in self._entities or alias in self._relations:
            raise BlueprintContractError(f"Alias logico duplicado: {alias}")
        logical_id = None
        if id_policy is LogicalIdPolicy.DETERMINISTIC_UUID:
            logical_id = uuid5(
                self.context.deterministic_namespace,
                f"entity:{entity_type}:{alias}",
            )
        entity = LogicalEntity(
            alias=alias,
            entity_type=entity_type,
            attributes=attributes,
            id_policy=id_policy,
            logical_id=logical_id,
            database_id=database_id,
        )
        self._entities[alias] = entity
        return self

    def add_relation(
        self,
        *,
        alias: str,
        relation_type: str,
        source_alias: str,
        target_alias: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> "BlueprintBuilder":
        if alias in self._entities or alias in self._relations:
            raise BlueprintContractError(f"Alias logico duplicado: {alias}")
        relation = LogicalRelation(
            alias=alias,
            relation_type=relation_type,
            source_alias=source_alias,
            target_alias=target_alias,
            attributes=attributes or MappingProxyType({}),
        )
        self._relations[alias] = relation
        return self

    def build(self) -> LogicalBlueprint:
        aliases = set(self._entities)
        for relation in self._relations.values():
            if relation.source_alias not in aliases or relation.target_alias not in aliases:
                raise BlueprintContractError(
                    f"Relacion {relation.alias} referencia aliases inexistentes"
                )
        return LogicalBlueprint(
            context=self.context,
            entities=tuple(self._entities[key] for key in sorted(self._entities)),
            relations=tuple(self._relations[key] for key in sorted(self._relations)),
        )


def compile_blueprint(
    context: BlueprintContext,
    entities: Iterable[LogicalEntity],
    relations: Iterable[LogicalRelation] = (),
) -> LogicalBlueprint:
    """Compila objetos ya declarados aplicando orden e invariantes globales."""

    entity_list = tuple(entities)
    relation_list = tuple(relations)
    all_aliases = [item.alias for item in (*entity_list, *relation_list)]
    if len(all_aliases) != len(set(all_aliases)):
        raise BlueprintContractError("Los aliases logicos deben ser globalmente unicos")
    entity_aliases = {entity.alias for entity in entity_list}
    for relation in relation_list:
        if (
            relation.source_alias not in entity_aliases
            or relation.target_alias not in entity_aliases
        ):
            raise BlueprintContractError(
                f"Relacion {relation.alias} referencia aliases inexistentes"
            )
    return LogicalBlueprint(
        context=context,
        entities=tuple(sorted(entity_list, key=lambda item: item.alias)),
        relations=tuple(sorted(relation_list, key=lambda item: item.alias)),
    )
