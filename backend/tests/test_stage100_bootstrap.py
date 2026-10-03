"""Contratos fail-closed del bootstrap técnico aislado de ET100.3."""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from sqlalchemy.engine import make_url
from sqlalchemy.dialects.mysql.pymysql import MySQLDialect_pymysql

from synthetic_data.bootstrap import (
    CREATE_DATABASE_SQL,
    EXPECTED_CREATE_INDEX_COUNT,
    EXPECTED_CREATE_TABLE_COUNT,
    EXPECTED_DDL_COUNT,
    EXPECTED_TABLE_COUNT,
    Stage100BootstrapError,
    _normalize_sql,
    _read_only_connection,
    _server_engine,
    canonicalize_ddl_statements,
    classify_existing_schema,
    fingerprint_ddl_statements,
    render_head_ddl_plan,
)
from synthetic_data.ddl_lifecycle import CLIENT_READ_TIMEOUT_SECONDS
from synthetic_data.target_guard import (
    EXPECTED_DATABASE,
    Stage100TargetConfiguration,
    Stage100TargetGuardError,
    validate_pre_schema_connection,
)


ROOT = Path(__file__).resolve().parents[2]


def _initialized_mysql_dialect():
    dialect = MySQLDialect_pymysql()
    dialect.server_version_info = (8, 0, 44)
    dialect.is_mariadb = False
    return dialect


class _Result:
    def __init__(self, *, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows or []

    def scalar_one(self):
        return self._scalar

    def all(self):
        return self._rows


class _PreSchemaConnection:
    def __init__(self, *, selected=None, username="feedgo_stage100_reset"):
        self.selected = selected
        self.username = username

    def exec_driver_sql(self, statement):
        if statement == "SELECT DATABASE()":
            return _Result(scalar=self.selected)
        if statement == "SELECT CURRENT_USER()":
            return _Result(scalar=f"{self.username}@localhost")
        if statement == "SHOW GRANTS":
            return _Result(
                rows=[
                    (f"GRANT USAGE ON *.* TO `{self.username}`@`localhost`",),
                    (
                        "GRANT CREATE, DROP, ALTER, INDEX, REFERENCES ON "
                        f"`{EXPECTED_DATABASE}`.* TO `{self.username}`@`localhost`",
                    ),
                ]
            )
        raise AssertionError(statement)


class Stage100BootstrapContracts(unittest.TestCase):
    def test_read_only_connection_rolls_back_and_closes(self):
        class Connection:
            def __init__(self):
                self.rolled_back = False
                self.closed = False

            def in_transaction(self):
                return True

            def rollback(self):
                self.rolled_back = True

            def close(self):
                self.closed = True

        class Engine:
            def __init__(self):
                self.connection = Connection()

            def connect(self):
                return self.connection

        engine = Engine()
        with _read_only_connection(engine) as connection:
            self.assertIs(connection, engine.connection)
        self.assertTrue(engine.connection.rolled_back)
        self.assertTrue(engine.connection.closed)

    def test_server_engine_preserves_transport_and_identity_without_database(self):
        reset_url = make_url(
            "mysql+pymysql://feedgo_stage100_reset:secret@localhost:3307/"
            + EXPECTED_DATABASE
        )
        config = Stage100TargetConfiguration(
            materializer_url=make_url(
                "mysql+pymysql://feedgo_stage100_materializer:other@localhost/"
                + EXPECTED_DATABASE
            ),
            reset_url=reset_url,
            materializer_username="feedgo_stage100_materializer",
            reset_username="feedgo_stage100_reset",
            control_url=make_url(
                "mysql+pymysql://feedgo_stage100_control:control@localhost/"
            ),
            control_username="feedgo_stage100_control",
        )

        engine = _server_engine(config)
        try:
            self.assertEqual(engine.url.drivername, reset_url.drivername)
            self.assertEqual(engine.url.username, reset_url.username)
            self.assertEqual(engine.url.password, reset_url.password)
            self.assertEqual(engine.url.host, reset_url.host)
            self.assertEqual(engine.url.port, reset_url.port)
            self.assertIsNone(engine.url.database)
            self.assertEqual(engine.url.query, reset_url.query)
        finally:
            engine.dispose()

    def test_ddl_engine_has_client_timeout_above_server_lock_timeout(self):
        reset_url = make_url(
            "mysql+pymysql://feedgo_stage100_reset:secret@localhost/"
            + EXPECTED_DATABASE
        )
        config = Stage100TargetConfiguration(
            materializer_url=reset_url.set(
                username="feedgo_stage100_materializer", password="other"
            ),
            reset_url=reset_url,
            materializer_username="feedgo_stage100_materializer",
            reset_username="feedgo_stage100_reset",
            control_url=make_url(
                "mysql+pymysql://feedgo_stage100_control:control@localhost/"
            ),
            control_username="feedgo_stage100_control",
        )
        with patch("synthetic_data.bootstrap.create_engine") as create:
            _server_engine(config, ddl=True)
        self.assertEqual(
            create.call_args.kwargs["connect_args"]["read_timeout"],
            CLIENT_READ_TIMEOUT_SECONDS,
        )

    def test_pre_schema_requires_null_database_exact_identity_and_reset_grants(self):
        url = make_url(
            "mysql+pymysql://feedgo_stage100_reset:secret@localhost/"
            + EXPECTED_DATABASE
        )
        result = validate_pre_schema_connection(
            _PreSchemaConnection(),
            configured_url=url,
            expected_username="feedgo_stage100_reset",
        )
        self.assertEqual(result.database, EXPECTED_DATABASE)

        for connection in (
            _PreSchemaConnection(selected=EXPECTED_DATABASE),
            _PreSchemaConnection(username="wrong"),
        ):
            with self.assertRaises(Stage100TargetGuardError):
                validate_pre_schema_connection(
                    connection,
                    configured_url=url,
                    expected_username="feedgo_stage100_reset",
                )

    def test_head_plan_is_exact_and_create_only(self):
        plan = render_head_ddl_plan(_initialized_mysql_dialect())
        self.assertEqual(EXPECTED_TABLE_COUNT, 39)
        self.assertEqual(plan.create_tables, EXPECTED_CREATE_TABLE_COUNT)
        self.assertEqual(plan.create_indexes, EXPECTED_CREATE_INDEX_COUNT)
        self.assertEqual(len(plan.statements), EXPECTED_DDL_COUNT)
        self.assertEqual(len(plan.sha256), 64)
        self.assertTrue(
            all(
                statement.upper().startswith(
                    ("CREATE TABLE ", "CREATE INDEX ", "CREATE UNIQUE INDEX ")
                )
                for statement in plan.statements
            )
        )
        self.assertFalse(any(" DROP " in f" {statement.upper()} " for statement in plan.statements))
        self.assertFalse(
            any(
                statement.upper().startswith(("INSERT ", "UPDATE ", "DELETE ", "REPLACE "))
                for statement in plan.statements
            )
        )

    def test_fingerprint_canonicalizes_only_evidence_and_preserves_multiplicity(self):
        operational = (
            "CREATE INDEX ix_b ON sample (b)",
            "CREATE TABLE sample (id INTEGER)",
            "CREATE INDEX ix_a ON sample (a)",
            "CREATE INDEX ix_a ON sample (a)",
        )
        canonical = canonicalize_ddl_statements(operational)

        self.assertEqual(canonical, tuple(sorted(operational)))
        self.assertEqual(canonical.count("CREATE INDEX ix_a ON sample (a)"), 2)
        self.assertNotEqual(operational, canonical)
        self.assertEqual(
            fingerprint_ddl_statements(operational),
            fingerprint_ddl_statements(reversed(operational)),
        )

    def test_fingerprint_changes_for_added_removed_or_modified_statement(self):
        baseline = (
            "CREATE TABLE sample (id INTEGER)",
            "CREATE INDEX ix_sample_id ON sample (id)",
        )
        variants = (
            baseline + ("CREATE INDEX ix_sample_other ON sample (other)",),
            baseline[:-1],
            (baseline[0], "CREATE UNIQUE INDEX ix_sample_id ON sample (id)"),
        )
        baseline_hash = fingerprint_ddl_statements(baseline)
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertNotEqual(baseline_hash, fingerprint_ddl_statements(variant))

    def test_head_fingerprint_is_stable_across_processes(self):
        command = (
            "from sqlalchemy.dialects.mysql.pymysql import MySQLDialect_pymysql; "
            "from synthetic_data.bootstrap import render_head_ddl_plan; "
            "d=MySQLDialect_pymysql(); d.server_version_info=(8,0,44); "
            "d.is_mariadb=False; print(render_head_ddl_plan(d).sha256)"
        )
        hashes = []
        for seed in ("random", "0", "1", "7"):
            environment = os.environ.copy()
            environment["PYTHONHASHSEED"] = seed
            completed = subprocess.run(
                [sys.executable, "-c", command],
                cwd=ROOT / "backend",
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            hashes.append(completed.stdout.strip())
        self.assertEqual(len(set(hashes)), 1)

    def test_database_statement_is_constant_and_exact(self):
        self.assertEqual(
            CREATE_DATABASE_SQL,
            "CREATE DATABASE `mitienda_stage100_test` CHARACTER SET utf8mb4 "
            "COLLATE utf8mb4_unicode_ci",
        )
        self.assertEqual(_normalize_sql(CREATE_DATABASE_SQL + ";"), CREATE_DATABASE_SQL)

    def test_state_machine_accepts_only_empty_or_exact_empty(self):
        no_objects = {"views": [], "triggers": [], "routines": [], "events": []}
        self.assertEqual(
            classify_existing_schema(
                tables=set(), schema_ok=None, counts={}, unexpected_objects=no_objects
            ),
            "empty",
        )
        self.assertEqual(
            classify_existing_schema(
                tables={"usuarios"},
                schema_ok=True,
                counts={"usuarios": 0},
                unexpected_objects=no_objects,
            ),
            "exact_empty",
        )
        invalid_states = (
            ({"usuarios"}, False, {"usuarios": 0}, no_objects),
            ({"usuarios"}, True, {"usuarios": 1}, no_objects),
            (set(), None, {}, {**no_objects, "views": ["unexpected"]}),
        )
        for tables, schema_ok, counts, objects in invalid_states:
            with self.subTest(tables=tables, counts=counts), self.assertRaises(
                Stage100BootstrapError
            ):
                classify_existing_schema(
                    tables=tables,
                    schema_ok=schema_ok,
                    counts=counts,
                    unexpected_objects=objects,
                )

    def test_bootstrap_has_no_schema_removal_or_data_mutation_path(self):
        source = (ROOT / "backend" / "synthetic_data" / "bootstrap.py").read_text(
            encoding="utf-8"
        )
        forbidden = (
            "metadata.drop_all",
            "DROP" + " DATABASE",
            "TRUNCATE" + " TABLE",
            "DELETE" + " FROM",
            "INSERT" + " INTO",
        )
        for marker in forbidden:
            self.assertNotIn(marker, source)

        runner = (ROOT / "tools" / "feedgo.py").read_text(encoding="utf-8")
        self.assertIn('"stage100-bootstrap"', runner)
        self.assertIn('"stage100-bootstrap-preflight"', runner)
        self.assertIn('"synthetic_data.bootstrap"', runner)


if __name__ == "__main__":
    unittest.main()
