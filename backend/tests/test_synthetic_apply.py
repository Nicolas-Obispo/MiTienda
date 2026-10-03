"""Guardas del comando canónico ``synthetic-apply`` sin acceso a MySQL."""

from __future__ import annotations

from datetime import timezone
from pathlib import Path
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from synthetic_data.apply import (
    SyntheticApplyError,
    SyntheticMaterializerConfiguration,
    apply_synthetic_dataset,
    load_materializer_configuration,
    parse_clock,
    require_fixture_secret,
)


ROOT = Path(__file__).resolve().parents[2]


def _environment() -> dict[str, str]:
    return {
        "FEEDGO_STAGE100_MATERIALIZER_DATABASE_URL": (
            "mysql+pymysql://feedgo_stage100_materializer:materializer-secret@"
            "localhost/mitienda_stage100_test"
        ),
        "FEEDGO_STAGE100_MATERIALIZER_USER": "feedgo_stage100_materializer",
        "FEEDGO_STAGE100_RESET_DATABASE_URL": (
            "mysql+pymysql://feedgo_stage100_reset:reset-secret@"
            "localhost/mitienda_stage100_test"
        ),
        "FEEDGO_STAGE100_RESET_USER": "feedgo_stage100_reset",
        "FEEDGO_STAGE100_CONTROL_DATABASE_URL": (
            "mysql+pymysql://feedgo_stage100_control:control-secret@localhost/"
        ),
        "FEEDGO_STAGE100_CONTROL_USER": "feedgo_stage100_control",
        "FEEDGO_STAGE100_FIXTURE_SECRET": "fixture-secret-local-only-0123456789abcdef",
    }


def _configuration() -> SyntheticMaterializerConfiguration:
    environment = _environment()
    return SyntheticMaterializerConfiguration(
        materializer_url=make_url(
            environment["FEEDGO_STAGE100_MATERIALIZER_DATABASE_URL"]
        ),
        materializer_username=environment["FEEDGO_STAGE100_MATERIALIZER_USER"],
    )


class SyntheticApplyContractTests(unittest.TestCase):
    def test_representative_is_not_materializable_during_et1003(self):
        with self.assertRaisesRegex(SyntheticApplyError, "synthetic_profile_not_allowed"):
            apply_synthetic_dataset(
                profile="representative",
                seed="approved-profile-seed-001",
                dataset_version="et100.3-v1",
                clock_policy="fixed_utc_v1",
                clock_anchor="2026-01-15T12:00:00Z",
                environment=_environment(),
            )

    def test_configuration_requires_only_the_exact_materializer_credential(self):
        environment = {
            "FEEDGO_STAGE100_MATERIALIZER_DATABASE_URL": (
                "mysql+pymysql://feedgo_stage100_materializer:secret@localhost/"
                "mitienda_stage100_test"
            ),
            "FEEDGO_STAGE100_MATERIALIZER_USER": "feedgo_stage100_materializer",
        }
        config = load_materializer_configuration(environment)
        self.assertEqual(config.materializer_username, "feedgo_stage100_materializer")
        self.assertEqual(config.materializer_url.database, "mitienda_stage100_test")

    def test_clock_contract_is_explicit_utc_and_second_precision(self):
        clock = parse_clock(
            policy="fixed_utc_v1", anchor="2026-01-15T12:00:00Z"
        )
        self.assertEqual(clock.anchor.tzinfo, timezone.utc)
        for policy, anchor in (
            ("wall_clock", "2026-01-15T12:00:00Z"),
            ("fixed_utc_v1", "2026-01-15T12:00:00"),
            ("fixed_utc_v1", "invalid"),
            ("fixed_utc_v1", "2026-01-15T12:00:00.1Z"),
        ):
            with self.subTest(policy=policy, anchor=anchor):
                with self.assertRaises(SyntheticApplyError):
                    parse_clock(policy=policy, anchor=anchor)

    def test_fixture_secret_is_required_strong_and_distinct_from_runtime(self):
        with self.assertRaisesRegex(SyntheticApplyError, "missing_or_weak"):
            require_fixture_secret({})
        with self.assertRaisesRegex(SyntheticApplyError, "reuses_runtime"):
            require_fixture_secret(
                {"FEEDGO_STAGE100_FIXTURE_SECRET": settings.SECRET_KEY}
            )
        accepted = _environment()["FEEDGO_STAGE100_FIXTURE_SECRET"]
        self.assertEqual(
            require_fixture_secret(_environment()), accepted
        )

    def test_smoke_apply_uses_transaction_preflight_and_certifies_20_rows(self):
        import_all_models()
        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)
        observations: list[bool] = []

        def preflight(connection, *, config):
            self.assertEqual(
                config.materializer_username, "feedgo_stage100_materializer"
            )
            observations.append(connection.in_transaction())

        try:
            with (
                patch("synthetic_data.apply.load_materializer_configuration", return_value=_configuration()),
                patch("synthetic_data.apply.create_engine", return_value=engine),
                patch("synthetic_data.apply._certify_empty_head_schema", side_effect=preflight),
                patch("synthetic_data.apply._certify_post_apply") as postcheck,
            ):
                evidence = apply_synthetic_dataset(
                    profile="smoke",
                    seed="approved-smoke-seed",
                    dataset_version="v1",
                    clock_policy="fixed_utc_v1",
                    clock_anchor="2026-01-15T12:00:00Z",
                    environment=_environment(),
                )
            self.assertEqual(observations, [True])
            self.assertEqual(evidence.status, "PASS")
            self.assertEqual(evidence.target, "mitienda_stage100_test")
            self.assertEqual(evidence.rows, 20)
            self.assertEqual(evidence.fingerprint, evidence.reconstructed_fingerprint)
            postcheck.assert_called_once()
        finally:
            engine.dispose()

    def test_preflight_rejection_prevents_postcheck_and_returns_no_evidence(self):
        import_all_models()
        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with (
                patch("synthetic_data.apply.load_materializer_configuration", return_value=_configuration()),
                patch("synthetic_data.apply.create_engine", return_value=engine),
                patch(
                    "synthetic_data.apply._certify_empty_head_schema",
                    side_effect=SyntheticApplyError("synthetic_database_not_empty"),
                ),
                patch("synthetic_data.apply._certify_post_apply") as postcheck,
            ):
                with self.assertRaisesRegex(SyntheticApplyError, "database_not_empty"):
                    apply_synthetic_dataset(
                        profile="smoke",
                        seed="approved-smoke-seed",
                        dataset_version="v1",
                        clock_policy="fixed_utc_v1",
                        clock_anchor="2026-01-15T12:00:00Z",
                        environment=_environment(),
                    )
            postcheck.assert_not_called()
        finally:
            engine.dispose()

    def test_only_approved_materializer_identity_is_accepted(self):
        config = _configuration()
        invalid = SyntheticMaterializerConfiguration(
            materializer_url=config.materializer_url.set(username="other"),
            materializer_username="other",
        )
        with patch(
            "synthetic_data.apply.load_materializer_configuration", return_value=invalid
        ):
            with self.assertRaisesRegex(SyntheticApplyError, "identity_invalid"):
                apply_synthetic_dataset(
                    profile="smoke",
                    seed="approved-smoke-seed",
                    dataset_version="v1",
                    clock_policy="fixed_utc_v1",
                    clock_anchor="2026-01-15T12:00:00Z",
                    environment=_environment(),
                )

    def test_runner_exposes_only_explicit_synthetic_apply_arguments(self):
        source = (ROOT / "tools" / "feedgo.py").read_text(encoding="utf-8")
        self.assertIn('subparsers.add_parser("synthetic-apply")', source)
        for argument in (
            "--profile",
            "--seed",
            "--dataset-version",
            "--clock-policy",
            "--clock-anchor",
        ):
            self.assertIn(f'add_argument("{argument}", required=True', source)
        self.assertNotIn("--fixture-secret", source)
        self.assertIn('"synthetic_data.apply"', source)


if __name__ == "__main__":
    unittest.main()
