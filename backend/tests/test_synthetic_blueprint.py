"""Contratos focales de determinismo logico para ET100.3."""

from __future__ import annotations

from datetime import datetime, timezone
import unittest

from synthetic_data.blueprint import (
    BlueprintBuilder,
    BlueprintContext,
    BlueprintContractError,
    ClockPolicy,
    LogicalIdPolicy,
)
from synthetic_data.fingerprint import (
    NonDeterministicKind,
    NormalizedNonDeterministicValue,
    canonical_json,
)


ANCHOR = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _context(
    *, seed: str = "fixture-seed-001", version: str = "v1",
    anchor: datetime = ANCHOR,
) -> BlueprintContext:
    return BlueprintContext(
        dataset_version=version,
        profile="contract",
        seed=seed,
        clock_policy=ClockPolicy(anchor=anchor),
    )


def _password_hash(actual: str, *, cost: int = 12) -> NormalizedNonDeterministicValue:
    return NormalizedNonDeterministicValue(
        kind=NonDeterministicKind.BCRYPT_HASH,
        invariants={
            "algorithm": "bcrypt",
            "cost": cost,
            "verifies_fixture_password": True,
        },
        opaque_value=actual,
    )


def _blueprint(
    *,
    context: BlueprintContext | None = None,
    hash_value: str = "bcrypt-output-a",
    display_name: str = "Comercio sintetico",
    reverse_declaration_order: bool = False,
    user_database_id: int | None = None,
):
    context = context or _context()
    builder = BlueprintBuilder(context)
    entities = [
        {
            "alias": "user.owner",
            "entity_type": "user",
            "attributes": {
                "created_at": context.clock_policy.at(seconds=10),
                "password_hash": _password_hash(hash_value),
                "status": "active",
            },
            "id_policy": LogicalIdPolicy.NONE,
            "database_id": user_database_id,
        },
        {
            "alias": "space.primary",
            "entity_type": "space",
            "attributes": {"display_name": display_name, "status": "active"},
            "id_policy": LogicalIdPolicy.DETERMINISTIC_UUID,
        },
    ]
    if reverse_declaration_order:
        entities.reverse()
    for entity in entities:
        builder.add_entity(**entity)
    builder.add_relation(
        alias="ownership.primary",
        relation_type="owns",
        source_alias="user.owner",
        target_alias="space.primary",
        attributes={"role": "owner"},
    )
    return builder.build()


class SyntheticBlueprintContractTests(unittest.TestCase):
    def test_same_input_produces_same_blueprint_and_fingerprint(self):
        first = _blueprint()
        second = _blueprint(reverse_declaration_order=True)

        self.assertEqual(first.logical_payload(), second.logical_payload())
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(
            first.fingerprint,
            "786fdf977ecad5aa0de40c7b424ddc996c983e2e7f8a905363e921e5d881d8e1",
        )

    def test_seed_is_mandatory_and_a_change_changes_id_and_fingerprint(self):
        with self.assertRaises(BlueprintContractError):
            _context(seed="")

        first = _blueprint(context=_context(seed="fixture-seed-001"))
        second = _blueprint(context=_context(seed="fixture-seed-002"))

        self.assertNotEqual(
            first.entity("space.primary").logical_id,
            second.entity("space.primary").logical_id,
        )
        self.assertIsNone(first.entity("user.owner").logical_id)
        self.assertNotIn("fixture-seed-001", canonical_json(first.logical_payload()))
        self.assertNotEqual(first.fingerprint, second.fingerprint)

    def test_dataset_version_change_changes_id_and_fingerprint(self):
        first = _blueprint(context=_context(version="v1"))
        second = _blueprint(context=_context(version="v2"))

        self.assertNotEqual(
            first.entity("space.primary").logical_id,
            second.entity("space.primary").logical_id,
        )
        self.assertNotEqual(first.fingerprint, second.fingerprint)

    def test_clock_is_controlled_reproducible_and_has_no_real_time_fallback(self):
        clock = ClockPolicy(anchor=ANCHOR)
        self.assertEqual(
            clock.at(seconds=90),
            datetime(2026, 1, 15, 12, 1, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(clock.at(seconds=90), clock.at(seconds=90))
        with self.assertRaises(BlueprintContractError):
            ClockPolicy(anchor=datetime(2026, 1, 15, 12, 0, 0))

        shifted = _blueprint(
            context=_context(anchor=datetime(2026, 1, 16, 12, 0, 0, tzinfo=timezone.utc))
        )
        self.assertNotEqual(_blueprint().fingerprint, shifted.fingerprint)

    def test_aliases_are_stable_unique_and_relations_require_existing_aliases(self):
        first = _blueprint()
        second = _blueprint(reverse_declaration_order=True)
        self.assertEqual(
            tuple(entity.alias for entity in first.entities),
            ("space.primary", "user.owner"),
        )
        self.assertEqual(
            tuple(entity.alias for entity in first.entities),
            tuple(entity.alias for entity in second.entities),
        )

        builder = BlueprintBuilder(_context())
        builder.add_entity(alias="user.owner", entity_type="user", attributes={})
        with self.assertRaises(BlueprintContractError):
            builder.add_entity(alias="user.owner", entity_type="user", attributes={})
        builder.add_relation(
            alias="ownership.invalid",
            relation_type="owns",
            source_alias="user.owner",
            target_alias="space.missing",
        )
        with self.assertRaises(BlueprintContractError):
            builder.build()

    def test_autoincrement_database_ids_are_outside_logical_fingerprint(self):
        first = _blueprint(user_database_id=41)
        second = _blueprint(user_database_id=912)

        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertNotIn("database_id", canonical_json(first.logical_payload()))
        enriched = first.with_database_ids({"space.primary": 50})
        self.assertEqual(first.fingerprint, enriched.fingerprint)

    def test_crypto_outputs_are_explicitly_normalized_without_weakening_them(self):
        first = _blueprint(hash_value="bcrypt-output-a")
        second = _blueprint(hash_value="bcrypt-output-b")

        self.assertEqual(first.fingerprint, second.fingerprint)
        serialized = canonical_json(first.logical_payload())
        self.assertNotIn("bcrypt-output-a", serialized)
        self.assertIn("bcrypt_hash", serialized)
        self.assertIn("verifies_fixture_password", serialized)

    def test_functional_changes_are_not_hidden_by_normalization(self):
        baseline = _blueprint()
        renamed = _blueprint(display_name="Otro comercio sintetico")
        changed_crypto_contract = BlueprintBuilder(_context())
        changed_crypto_contract.add_entity(
            alias="user.owner",
            entity_type="user",
            attributes={
                "created_at": _context().clock_policy.at(seconds=10),
                "password_hash": _password_hash("other-output", cost=13),
                "status": "active",
            },
        )
        changed_crypto_contract.add_entity(
            alias="space.primary",
            entity_type="space",
            attributes={"display_name": "Comercio sintetico", "status": "active"},
            id_policy=LogicalIdPolicy.DETERMINISTIC_UUID,
        )
        changed_crypto_contract.add_relation(
            alias="ownership.primary",
            relation_type="owns",
            source_alias="user.owner",
            target_alias="space.primary",
            attributes={"role": "owner"},
        )

        self.assertNotEqual(baseline.fingerprint, renamed.fingerprint)
        self.assertNotEqual(baseline.fingerprint, changed_crypto_contract.build().fingerprint)


if __name__ == "__main__":
    unittest.main()
