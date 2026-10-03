"""Contratos de privacidad, medios y validacion read-only ET100.3."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import unittest

from synthetic_data.blueprint import ClockPolicy
from synthetic_data.media_recipes import (
    SyntheticMediaContractError,
    compile_media_recipe,
    media_manifest_sha256,
    media_recipes_for_blueprint,
)
from synthetic_data.scenarios import compile_representative, compile_scenario
from synthetic_data.validation import (
    SyntheticValidationError,
    _assert_read_only_sql,
    validate_no_contamination,
    validate_synthetic_profile,
)


ARGS = {
    "dataset_version": "et100.3-v1",
    "seed": "approved-profile-seed-001",
    "clock_policy": ClockPolicy(
        anchor=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    ),
}
CLI_ARGS = {
    "dataset_version": "et100.3-v1",
    "seed": "approved-profile-seed-001",
    "clock_policy": "fixed_utc_v1",
    "clock_anchor": "2026-01-15T12:00:00Z",
}


def _replace_attribute(blueprint, alias: str, field: str, value):
    entities = tuple(
        replace(item, attributes={**item.attributes, field: value})
        if item.alias == alias
        else item
        for item in blueprint.entities
    )
    return replace(blueprint, entities=entities)


class SyntheticPrivacyAndMediaTests(unittest.TestCase):
    def test_all_profiles_pass_privacy_and_media_contracts(self):
        expected = {"smoke": (20, 3), "functional": (93, 11), "representative": (129, 18)}
        for profile, (rows, recipes) in expected.items():
            with self.subTest(profile=profile):
                evidence = validate_synthetic_profile(
                    source="blueprint", profile=profile, environment={}, **CLI_ARGS
                )
                self.assertEqual(evidence.status, "PASS")
                self.assertEqual(evidence.rows, rows)
                self.assertEqual(evidence.media_recipes, recipes)
                self.assertEqual(len(evidence.media_manifest_sha256), 64)
                self.assertIsNone(evidence.target)
                self.assertIsNone(evidence.schema_head)

    def test_media_recipes_are_versioned_deterministic_and_synthetic(self):
        blueprint = compile_representative(**ARGS)
        first = media_recipes_for_blueprint(blueprint)
        second = media_recipes_for_blueprint(blueprint)
        self.assertEqual(first, second)
        self.assertEqual(media_manifest_sha256(first), media_manifest_sha256(second))
        self.assertEqual(len(first), 18)
        for recipe in first:
            self.assertEqual(recipe.recipe_version, "synthetic-media-recipe-v1")
            self.assertEqual(len(recipe.recipe_sha256), 64)
            self.assertEqual(
                recipe.parameters["synthetic_marker"], "FEEDGO_SYNTHETIC_ET100_3"
            )
            self.assertTrue(recipe.renderer.startswith("feedgo.synthetic."))

    def test_media_reference_allowlist_rejects_paths_and_near_matches(self):
        for value in (
            "synthetic-media://commerce/primary/../../backend/uploads/file.jpg",
            "synthetic-media://commerce/primary/cover-v2",
            "synthetic-media://Commerce/primary/cover-v1",
            "synthetic-media://commerce/primary/cover-v1?source=uploads",
            "/uploads/real.jpg",
        ):
            with self.subTest(value=value), self.assertRaises(SyntheticMediaContractError):
                compile_media_recipe(value)

    def test_contamination_canaries_fail_closed(self):
        baseline = compile_scenario(profile="smoke", **ARGS)
        canaries = (
            ("user.owner", "email", "ordinary.person@company.test", {}, "email"),
            ("user.owner", "telefono_e164", "+5491123456789", {}, "phone"),
            ("commerce.primary", "portada_url", "backend/uploads/real.jpg", {}, "path"),
            ("commerce.primary", "portada_url", "https://cdn.example.com/real.jpg", {}, "external_url"),
            ("commerce.primary", "descripcion", "sk_live_NOT_A_REAL_CANARY", {}, "secret_pattern"),
            ("credential.owner", "password_hash", "plain-secret-canary", {}, "secret_field"),
            (
                "commerce.primary",
                "descripcion",
                "local-runtime-secret-canary",
                {"SECRET_KEY": "local-runtime-secret-canary"},
                "runtime_secret",
            ),
        )
        for alias, field, value, environment, error in canaries:
            with self.subTest(error=error), self.assertRaisesRegex(
                SyntheticValidationError, error
            ):
                validate_no_contamination(
                    _replace_attribute(baseline, alias, field, value),
                    environment=environment,
                )

    def test_approved_synthetic_canaries_pass(self):
        validate_no_contamination(compile_representative(**ARGS), environment={})
        recipe = compile_media_recipe("synthetic-media://commerce/primary/cover-v1")
        self.assertEqual(recipe.kind, "cover")

    def test_sql_guard_allows_reads_and_blocks_every_mutation_class(self):
        for statement in ("SELECT 1", "SHOW TABLES", "DESCRIBE usuarios"):
            _assert_read_only_sql(statement)
        for statement in (
            "INSERT INTO usuarios VALUES (1)",
            "UPDATE usuarios SET email = 'x'",
            "DELETE FROM usuarios",
            "CREATE TABLE x (id INT)",
            "ALTER TABLE usuarios ADD COLUMN x INT",
            "DROP TABLE usuarios",
            "TRUNCATE TABLE usuarios",
            "SET @x = 1",
            "SELECT * FROM usuarios FOR UPDATE",
            "SELECT email INTO OUTFILE '/tmp/leak' FROM usuarios",
            "SELECT GET_LOCK('x', 10)",
            "EXPLAIN SELECT 1",
        ):
            with self.subTest(statement=statement), self.assertRaisesRegex(
                SyntheticValidationError, "write_statement_blocked"
            ):
                _assert_read_only_sql(statement)

    def test_representative_mysql_validation_remains_deferred(self):
        with self.assertRaisesRegex(
            SyntheticValidationError, "profile_not_materializable"
        ):
            validate_synthetic_profile(
                source="mysql",
                profile="representative",
                environment={},
                **CLI_ARGS,
            )


if __name__ == "__main__":
    unittest.main()
