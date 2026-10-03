"""Contratos fail-closed del reset tecnico ET100.3, sin acceso a MySQL."""

from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from sqlalchemy.engine import make_url

from synthetic_data.bootstrap import DdlPlan
from synthetic_data.ddl_lifecycle import (
    DdlLifecycleError,
    DdlLifecycleEvidence,
    DdlLifecycleState,
)
from synthetic_data.reset import (
    DROP_DATABASE_SQL,
    EXPECTED_DDL_PLAN_SHA256,
    EXPECTED_SMOKE_FINGERPRINT,
    POSTCONDITION,
    SYNTHETIC_RESET_GATE,
    SyntheticResetError,
    _expected_smoke_blueprint,
    reset_synthetic_lab,
)
from synthetic_data.target_guard import Stage100TargetConfiguration


ROOT = Path(__file__).resolve().parents[2]


def _environment() -> dict[str, str]:
    return {
        SYNTHETIC_RESET_GATE: "apply",
        "FEEDGO_STAGE100_FIXTURE_SECRET": "fixture-secret-local-only-0123456789abcdef",
    }


def _config() -> Stage100TargetConfiguration:
    return Stage100TargetConfiguration(
        materializer_url=make_url(
            "mysql+pymysql://feedgo_stage100_materializer:secret@localhost/"
            "mitienda_stage100_test"
        ),
        reset_url=make_url(
            "mysql+pymysql://feedgo_stage100_reset:secret@localhost/"
            "mitienda_stage100_test"
        ),
        materializer_username="feedgo_stage100_materializer",
        reset_username="feedgo_stage100_reset",
        control_url=make_url(
            "mysql+pymysql://feedgo_stage100_control:secret@localhost/"
        ),
        control_username="feedgo_stage100_control",
    )


def _plan() -> DdlPlan:
    statements = tuple(
        [f"CREATE TABLE t{i}" for i in range(39)]
        + [f"CREATE INDEX i{i}" for i in range(115)]
    )
    return DdlPlan(
        statements=statements,
        create_tables=39,
        create_indexes=115,
        sha256=EXPECTED_DDL_PLAN_SHA256,
    )


def _completed(count: int) -> DdlLifecycleEvidence:
    return DdlLifecycleEvidence(
        state=DdlLifecycleState.COMPLETED,
        connection_id=100 + count,
        dispatched=count,
        completed=count,
        current_statement=None,
        cancellation_confirmed=False,
    )


class SyntheticResetContracts(unittest.TestCase):
    def _patches(self, *, phases=None):
        plan = _plan()
        phases = phases or [_completed(1), _completed(1), _completed(154)]
        return (
            patch("synthetic_data.reset.load_target_configuration", return_value=_config()),
            patch("synthetic_data.reset.require_fixture_secret", return_value="x" * 32),
            patch("synthetic_data.reset.import_all_models"),
            patch("synthetic_data.reset._certify_server_and_observer", return_value=plan),
            patch("synthetic_data.reset._certify_current_smoke"),
            patch("synthetic_data.reset._run_ddl_phase", side_effect=phases),
            patch("synthetic_data.reset._certify_database_absent"),
            patch("synthetic_data.reset._certify_database_empty", return_value=plan),
            patch("synthetic_data.reset._certify_head_empty", return_value=(39, True)),
        )

    def test_opt_in_is_required_before_configuration_or_any_phase(self):
        with patch("synthetic_data.reset.load_target_configuration") as load:
            with self.assertRaisesRegex(SyntheticResetError, "opt_in_missing"):
                reset_synthetic_lab(environment={})
        load.assert_not_called()

    def test_three_phases_are_ordered_and_finish_only_at_head_empty(self):
        patches = self._patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as phases, patches[6] as absent, patches[7] as empty, patches[8] as head:
            evidence = reset_synthetic_lab(environment=_environment())

        self.assertEqual(evidence.status, "PASS")
        self.assertEqual(evidence.target, "mitienda_stage100_test")
        self.assertEqual(evidence.previous_fingerprint, EXPECTED_SMOKE_FINGERPRINT)
        self.assertEqual(evidence.postcondition, POSTCONDITION)
        self.assertEqual(evidence.tables, 39)
        self.assertTrue(evidence.all_tables_empty)
        self.assertEqual(phases.call_count, 3)
        self.assertFalse(phases.call_args_list[0].kwargs["selected_database"])
        self.assertEqual(
            phases.call_args_list[0].kwargs["statements"], (DROP_DATABASE_SQL,)
        )
        self.assertFalse(phases.call_args_list[1].kwargs["selected_database"])
        self.assertTrue(phases.call_args_list[2].kwargs["selected_database"])
        self.assertEqual(len(phases.call_args_list[2].kwargs["statements"]), 154)
        absent.assert_called_once()
        empty.assert_called_once()
        head.assert_called_once()

    def test_drop_failure_prevents_create_schema_and_postchecks(self):
        failure = DdlLifecycleError(
            "stage100_ddl_result_unknown",
            DdlLifecycleEvidence(
                state=DdlLifecycleState.UNKNOWN,
                connection_id=559,
                dispatched=1,
                completed=0,
                current_statement=DROP_DATABASE_SQL,
                cancellation_confirmed=True,
            ),
        )
        patches = self._patches(phases=[failure])
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as phases, patches[6] as absent, patches[7] as empty, patches[8] as head:
            with self.assertRaises(DdlLifecycleError):
                reset_synthetic_lab(environment=_environment())
        self.assertEqual(phases.call_count, 1)
        absent.assert_not_called()
        empty.assert_not_called()
        head.assert_not_called()

    def test_create_failure_stops_after_confirmed_absence(self):
        failure = DdlLifecycleError(
            "stage100_ddl_result_unknown",
            DdlLifecycleEvidence(
                state=DdlLifecycleState.UNKNOWN,
                connection_id=560,
                dispatched=1,
                completed=0,
                current_statement="CREATE DATABASE",
                cancellation_confirmed=True,
            ),
        )
        patches = self._patches(phases=[_completed(1), failure])
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as phases, patches[6] as absent, patches[7] as empty, patches[8] as head:
            with self.assertRaises(DdlLifecycleError):
                reset_synthetic_lab(environment=_environment())
        self.assertEqual(phases.call_count, 2)
        absent.assert_called_once()
        empty.assert_not_called()
        head.assert_not_called()

    def test_failed_drop_postcheck_prevents_create_without_retry(self):
        patches = self._patches(phases=[_completed(1)])
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as phases, patch(
            "synthetic_data.reset._certify_database_absent",
            side_effect=SyntheticResetError("drop_postcheck_failed"),
        ), patches[7] as empty, patches[8] as head:
            with self.assertRaisesRegex(SyntheticResetError, "drop_postcheck_failed"):
                reset_synthetic_lab(environment=_environment())
        self.assertEqual(phases.call_count, 1)
        empty.assert_not_called()
        head.assert_not_called()

    def test_schema_failure_never_reports_head_empty_or_retries(self):
        failure = DdlLifecycleError(
            "stage100_ddl_result_unknown",
            DdlLifecycleEvidence(
                state=DdlLifecycleState.UNKNOWN,
                connection_id=561,
                dispatched=12,
                completed=11,
                current_statement="CREATE TABLE partial",
                cancellation_confirmed=True,
            ),
        )
        patches = self._patches(
            phases=[_completed(1), _completed(1), failure]
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5] as phases, patches[6], patches[7], patches[8] as head:
            with self.assertRaises(DdlLifecycleError):
                reset_synthetic_lab(environment=_environment())
        self.assertEqual(phases.call_count, 3)
        head.assert_not_called()

    def test_approved_smoke_contract_is_fixed_and_reproducible(self):
        self.assertEqual(
            _expected_smoke_blueprint().fingerprint,
            EXPECTED_SMOKE_FINGERPRINT,
        )

    def test_runner_exposes_reset_without_dataset_or_target_arguments(self):
        source = (ROOT / "tools" / "feedgo.py").read_text(encoding="utf-8")
        self.assertIn('subparsers.add_parser("synthetic-reset")', source)
        self.assertIn('module="synthetic_data.reset"', source)
        reset_section = source[source.index("def synthetic_reset()") : source.index("def synthetic_apply(")]
        self.assertNotIn("--profile", reset_section)
        self.assertNotIn("--database", reset_section)
        self.assertNotIn("synthetic_data.apply", reset_section)
        reset_source = (
            ROOT / "backend" / "synthetic_data" / "reset.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("apply_synthetic_dataset", reset_source)
        self.assertNotIn("materialize_blueprint", reset_source)


if __name__ == "__main__":
    unittest.main()
