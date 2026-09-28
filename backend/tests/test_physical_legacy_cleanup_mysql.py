import os
import unittest

from sqlalchemy import create_engine, inspect

import migrate_drop_legacy_hashed_password as hash_cleanup
import migrate_drop_tokens_revocados as token_cleanup


class PhysicalLegacyCleanupMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database_url = os.environ.get("FEEDGO_STAGE97_TEST_DATABASE_URL")
        if not database_url:
            raise unittest.SkipTest("FEEDGO_STAGE97_TEST_DATABASE_URL no configurada")
        cls.engine = create_engine(database_url)
        url = cls.engine.url
        if (
            url.drivername != "mysql+pymysql"
            or url.host != "localhost"
            or url.database != "mitienda_stage97_test"
        ):
            raise RuntimeError("physical_cleanup_mysql_target_invalid")
        with cls.engine.connect() as connection:
            if connection.exec_driver_sql("SELECT DATABASE()").scalar_one() != "mitienda_stage97_test":
                raise RuntimeError("physical_cleanup_mysql_database_mismatch")

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self._drop_fixture()
        self._restore_legacy_fixture()

    def tearDown(self):
        self._drop_fixture()

    def _drop_fixture(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS=0")
            for table in ("tokens_revocados", "feedgo_sessions", "password_credentials", "usuarios"):
                connection.exec_driver_sql(f"DROP TABLE IF EXISTS {table}")
            connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS=1")

    def _restore_legacy_fixture(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE usuarios (id INTEGER PRIMARY KEY, email VARCHAR(255) NOT NULL, "
                "email_canonical VARCHAR(255) NOT NULL, hashed_password VARCHAR(255) NOT NULL) ENGINE=InnoDB"
            )
            connection.exec_driver_sql(
                "CREATE TABLE password_credentials (usuario_id INTEGER PRIMARY KEY, "
                "password_hash VARCHAR(255) NOT NULL, hash_version VARCHAR(32) NOT NULL, "
                "CONSTRAINT fk_pc_user FOREIGN KEY(usuario_id) REFERENCES usuarios(id)) ENGINE=InnoDB"
            )
            connection.exec_driver_sql(
                "CREATE TABLE feedgo_sessions (id VARCHAR(64) PRIMARY KEY, usuario_id INTEGER NOT NULL, "
                "CONSTRAINT fk_session_user FOREIGN KEY(usuario_id) REFERENCES usuarios(id)) ENGINE=InnoDB"
            )
            connection.exec_driver_sql(
                "CREATE TABLE tokens_revocados (id INTEGER PRIMARY KEY, token VARCHAR(512) NOT NULL UNIQUE, "
                "usuario_id INTEGER NOT NULL, fecha_revocado DATETIME NOT NULL, expira_en DATETIME NULL, "
                "CONSTRAINT fk_token_user FOREIGN KEY(usuario_id) REFERENCES usuarios(id)) ENGINE=InnoDB"
            )
            connection.exec_driver_sql(
                "INSERT INTO usuarios VALUES (1, 'test@example.com', 'test@example.com', 'legacy-hash')"
            )
            connection.exec_driver_sql(
                "INSERT INTO password_credentials VALUES (1, 'legacy-hash', 'bcrypt')"
            )
            connection.exec_driver_sql("INSERT INTO feedgo_sessions VALUES ('sid-1', 1)")
            connection.exec_driver_sql(
                "INSERT INTO tokens_revocados VALUES (1, 'legacy-token', 1, UTC_TIMESTAMP(), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 HOUR))"
            )

    def test_mysql_schema_matrix_idempotence_and_full_fixture_restore(self):
        first_a = token_cleanup.apply_cleanup(token_cleanup.APPLY_ACTION, target_engine=self.engine)
        first_b = hash_cleanup.apply_cleanup(hash_cleanup.APPLY_ACTION, target_engine=self.engine)
        self.assertEqual((first_a.dropped, first_b.dropped), (1, 1))
        with self.engine.connect() as connection:
            inspector = inspect(connection)
            self.assertNotIn("tokens_revocados", inspector.get_table_names())
            self.assertNotIn("hashed_password", {c["name"] for c in inspector.get_columns("usuarios")})
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM usuarios").scalar_one(), 1)
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM password_credentials").scalar_one(), 1)
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM feedgo_sessions").scalar_one(), 1)

        self.assertEqual(token_cleanup.apply_cleanup(token_cleanup.APPLY_ACTION, target_engine=self.engine).dropped, 0)
        self.assertEqual(hash_cleanup.apply_cleanup(hash_cleanup.APPLY_ACTION, target_engine=self.engine).dropped, 0)

        self._drop_fixture()
        self._restore_legacy_fixture()
        with self.engine.connect() as connection:
            inspector = inspect(connection)
            self.assertIn("tokens_revocados", inspector.get_table_names())
            self.assertIn("hashed_password", {c["name"] for c in inspector.get_columns("usuarios")})
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM tokens_revocados").scalar_one(), 1)
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM usuarios").scalar_one(), 1)
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM password_credentials").scalar_one(), 1)
            self.assertEqual(connection.exec_driver_sql("SELECT COUNT(*) FROM feedgo_sessions").scalar_one(), 1)
            self.assertEqual(
                connection.exec_driver_sql(
                    "SELECT COUNT(*) FROM usuarios u "
                    "JOIN password_credentials pc ON pc.usuario_id = u.id "
                    "WHERE u.hashed_password = pc.password_hash"
                ).scalar_one(),
                1,
            )


if __name__ == "__main__":
    unittest.main()
