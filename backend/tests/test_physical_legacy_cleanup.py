import ast
from datetime import datetime, timedelta
from pathlib import Path
import unittest

from sqlalchemy import create_engine, inspect

import migrate_drop_legacy_hashed_password as hash_cleanup
import migrate_drop_tokens_revocados as token_cleanup
from app.core.database_backup import CRITICAL_TABLES
from app.core.model_registry import import_all_models
from app.modules.users.models.usuarios_models import Usuario


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def create_legacy_schema(engine, *, divergent=False, future_token=False):
    legacy = "legacy-hash"
    credential = "other-hash" if divergent else legacy
    expiry = datetime.utcnow() + (timedelta(hours=1) if future_token else -timedelta(hours=1))
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE usuarios (id INTEGER PRIMARY KEY, email VARCHAR(255) NOT NULL, "
            "email_canonical VARCHAR(255) NOT NULL, hashed_password VARCHAR(255) NULL)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE password_credentials (usuario_id INTEGER PRIMARY KEY, "
            "password_hash VARCHAR(255) NOT NULL, hash_version VARCHAR(32) NOT NULL)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE feedgo_sessions (id VARCHAR(64) PRIMARY KEY, usuario_id INTEGER NOT NULL)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE tokens_revocados (id INTEGER PRIMARY KEY, token VARCHAR(512) NOT NULL UNIQUE, "
            "usuario_id INTEGER NOT NULL, fecha_revocado DATETIME NOT NULL, expira_en DATETIME NULL, "
            "FOREIGN KEY(usuario_id) REFERENCES usuarios(id))"
        )
        connection.exec_driver_sql(
            "INSERT INTO usuarios VALUES (1, 'test@example.com', 'test@example.com', ?)",
            (legacy,),
        )
        connection.exec_driver_sql(
            "INSERT INTO password_credentials VALUES (1, ?, 'bcrypt')",
            (credential,),
        )
        connection.exec_driver_sql(
            "INSERT INTO feedgo_sessions VALUES ('sid-1', 1)"
        )
        connection.exec_driver_sql(
            "INSERT INTO tokens_revocados VALUES (1, 'legacy-token', 1, ?, ?)",
            (datetime.utcnow(), expiry),
        )


class PhysicalLegacyCleanupTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        create_legacy_schema(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_schema_matrix_and_idempotence(self):
        with self.engine.begin() as connection:
            legacy = set(inspect(connection).get_table_names())
            self.assertIn("tokens_revocados", legacy)
            self.assertIn("hashed_password", {c["name"] for c in inspect(connection).get_columns("usuarios")})

            first_a = token_cleanup.drop_tokens_revocados(connection)
            self.assertEqual(first_a.dropped, 1)
            self.assertNotIn("tokens_revocados", inspect(connection).get_table_names())
            self.assertIn("hashed_password", {c["name"] for c in inspect(connection).get_columns("usuarios")})

            first_b = hash_cleanup.drop_legacy_hashed_password(connection)
            self.assertEqual(first_b.dropped, 1)
            self.assertNotIn("hashed_password", {c["name"] for c in inspect(connection).get_columns("usuarios")})

            self.assertEqual(token_cleanup.drop_tokens_revocados(connection).dropped, 0)
            self.assertEqual(hash_cleanup.drop_legacy_hashed_password(connection).dropped, 0)
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM usuarios").scalar_one(), 1)
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM password_credentials").scalar_one(), 1)
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM feedgo_sessions").scalar_one(), 1)

    def test_unexpired_token_blocks_drop(self):
        engine = create_engine("sqlite://")
        try:
            create_legacy_schema(engine, future_token=True)
            with engine.begin() as connection:
                plan = token_cleanup.preflight_tokens_revocados_cleanup(connection)
                self.assertEqual(plan.status, "BLOCK")
                self.assertIn("tokens_cleanup_unexpired_rows", plan.blockers)
                with self.assertRaises(token_cleanup.TokensRevocadosCleanupError):
                    token_cleanup.drop_tokens_revocados(connection)
                self.assertIn("tokens_revocados", inspect(connection).get_table_names())
        finally:
            engine.dispose()

    def test_divergent_hash_blocks_drop(self):
        engine = create_engine("sqlite://")
        try:
            create_legacy_schema(engine, divergent=True)
            with engine.begin() as connection:
                plan = hash_cleanup.preflight_hashed_password_cleanup(connection)
                self.assertEqual(plan.status, "BLOCK")
                self.assertEqual(plan.divergent, 1)
                with self.assertRaises(hash_cleanup.HashedPasswordCleanupError):
                    hash_cleanup.drop_legacy_hashed_password(connection)
                self.assertIn("hashed_password", {c["name"] for c in inspect(connection).get_columns("usuarios")})
        finally:
            engine.dispose()

    def test_partial_schemas_fail_closed(self):
        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, email_canonical VARCHAR(255))")
                connection.exec_driver_sql("CREATE TABLE password_credentials (usuario_id INTEGER PRIMARY KEY, password_hash VARCHAR(255))")
                connection.exec_driver_sql("CREATE TABLE feedgo_sessions (id VARCHAR(64) PRIMARY KEY)")
                connection.exec_driver_sql("CREATE TABLE tokens_revocados (id INTEGER PRIMARY KEY)")
                with self.assertRaises(token_cleanup.TokensRevocadosCleanupError):
                    token_cleanup.preflight_tokens_revocados_cleanup(connection)
        finally:
            engine.dispose()

    def test_public_apply_rejects_non_mysql_target(self):
        with self.assertRaises(token_cleanup.TokensRevocadosCleanupError):
            token_cleanup.apply_cleanup(token_cleanup.APPLY_ACTION, target_engine=self.engine)
        with self.assertRaises(hash_cleanup.HashedPasswordCleanupError):
            hash_cleanup.apply_cleanup(hash_cleanup.APPLY_ACTION, target_engine=self.engine)

    def test_current_model_registry_and_backup_have_no_legacy_structures(self):
        import_all_models()
        self.assertNotIn("hashed_password", Usuario.__table__.columns)
        self.assertNotIn("tokens_revocados", CRITICAL_TABLES)
        self.assertNotIn("tokens_revocados", Usuario.metadata.tables)
        self.assertFalse((BACKEND_ROOT / "app/modules/users/models/tokens_models.py").exists())
        self.assertFalse((BACKEND_ROOT / "preflight_legacy_password_credentials.py").exists())
        self.assertFalse((BACKEND_ROOT / "app/modules/users/services/legacy_password_preflight_services.py").exists())

    def test_runtime_sources_do_not_reintroduce_legacy_contracts(self):
        forbidden = {"hashed_password", "TokenRevocado", "tokens_revocados"}
        occurrences = []
        for path in (BACKEND_ROOT / "app").rglob("*.py"):
            if path in {
                BACKEND_ROOT / "app/core/database_backup.py",
                BACKEND_ROOT / "app/core/database_restore.py",
            }:
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            rendered = ast.dump(tree)
            for value in forbidden:
                if value in source or value in rendered:
                    occurrences.append((str(path.relative_to(BACKEND_ROOT)), value))
        self.assertEqual(occurrences, [])

    def test_migrators_contain_only_the_authorized_physical_drops(self):
        token_source = (BACKEND_ROOT / "migrate_drop_tokens_revocados.py").read_text(
            encoding="utf-8"
        )
        hash_source = (
            BACKEND_ROOT / "migrate_drop_legacy_hashed_password.py"
        ).read_text(encoding="utf-8")
        self.assertEqual(token_source.count('exec_driver_sql("DROP TABLE tokens_revocados")'), 1)
        self.assertEqual(
            hash_source.count(
                'exec_driver_sql("ALTER TABLE usuarios DROP COLUMN hashed_password")'
            ),
            1,
        )
        combined = token_source + hash_source
        for forbidden in ("INSERT INTO", "UPDATE usuarios", "DELETE FROM"):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
