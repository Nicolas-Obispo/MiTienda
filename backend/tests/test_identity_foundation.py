import unittest

from sqlalchemy import create_engine, inspect

import migrate_identity_foundation as migration
from app.modules.users.services.email_normalization import (
    InvalidEmailError,
    canonicalize_email,
)


class EmailCanonicalizationTests(unittest.TestCase):
    def test_normaliza_espacios_dominio_y_casing(self):
        self.assertEqual(
            canonicalize_email("  Persona@Example.COM  "),
            "persona@example.com",
        )

    def test_no_aplica_reglas_particulares_de_google(self):
        self.assertNotEqual(
            canonicalize_email("persona.alias+feedgo@gmail.com"),
            canonicalize_email("personaalias@gmail.com"),
        )

    def test_rechaza_email_invalido(self):
        with self.assertRaises(InvalidEmailError):
            canonicalize_email("no-es-email")


class IdentityFoundationMigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                """
                CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    hashed_password VARCHAR(255) NOT NULL
                )
                """
            )
            connection.exec_driver_sql(
                """
                INSERT INTO usuarios (id, email, hashed_password)
                VALUES
                    (1, 'Persona@Example.COM', '$2b$legacy-one'),
                    (2, 'otra@example.com', '$2b$legacy-two')
                """
            )

    def test_upgrade_es_aditivo_idempotente_y_copia_hash_exacto(self):
        with self.engine.begin() as connection:
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)

            self.assertEqual(first["preflight"]["colisiones"], 0)
            self.assertEqual(first["backfill"]["emails"], 2)
            self.assertEqual(first["backfill"]["password_credentials"], 2)
            self.assertEqual(second["changes"], [])
            self.assertEqual(second["backfill"]["emails"], 0)
            self.assertEqual(second["backfill"]["password_credentials"], 0)

            users = connection.exec_driver_sql(
                "SELECT id, email, hashed_password, email_canonical, "
                "email_verified_at, fecha_nacimiento FROM usuarios ORDER BY id"
            ).all()
            self.assertEqual(
                [tuple(row) for row in users],
                [
                    (
                        1,
                        "Persona@Example.COM",
                        "$2b$legacy-one",
                        "persona@example.com",
                        None,
                        None,
                    ),
                    (
                        2,
                        "otra@example.com",
                        "$2b$legacy-two",
                        "otra@example.com",
                        None,
                        None,
                    ),
                ],
            )
            credentials = connection.exec_driver_sql(
                "SELECT usuario_id, password_hash FROM password_credentials "
                "ORDER BY usuario_id"
            ).all()
            self.assertEqual(
                [tuple(row) for row in credentials],
                [(1, "$2b$legacy-one"), (2, "$2b$legacy-two")],
            )

        inspector = inspect(self.engine)
        self.assertTrue(set(migration.NEW_TABLES) <= set(inspector.get_table_names()))
        self.assertTrue(
            set(migration.USER_COLUMN_DDL)
            <= {column["name"] for column in inspector.get_columns("usuarios")}
        )
        indexes = {index["name"]: index for index in inspector.get_indexes("usuarios")}
        self.assertTrue(indexes[migration.EMAIL_CANONICAL_INDEX]["unique"])
        with self.engine.connect() as connection:
            self.assertEqual(
                connection.exec_driver_sql("SELECT COUNT(*) FROM external_identities").scalar_one(),
                0,
            )
            self.assertEqual(
                connection.exec_driver_sql("SELECT COUNT(*) FROM feedgo_sessions").scalar_one(),
                0,
            )

    def test_colision_detiene_antes_de_expandir(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO usuarios (id, email, hashed_password) "
                "VALUES (3, 'persona@example.com', '$2b$other')"
            )
            with self.assertRaises(migration.IdentityMigrationPreflightError):
                migration.upgrade(connection)
            columns = {
                column["name"]
                for column in inspect(connection).get_columns("usuarios")
            }
            self.assertNotIn("email_canonical", columns)
            self.assertNotIn("password_credentials", inspect(connection).get_table_names())

    def test_hash_parcial_divergente_bloquea_reintento(self):
        with self.engine.begin() as connection:
            migration.upgrade(connection)
            connection.exec_driver_sql(
                "UPDATE password_credentials SET password_hash = 'divergente' "
                "WHERE usuario_id = 1"
            )
            with self.assertRaises(migration.IdentityMigrationPreflightError):
                migration.upgrade(connection)

    def test_detecta_y_repara_alta_transitoria_posterior_al_backfill(self):
        with self.engine.begin() as connection:
            migration.upgrade(connection)
            connection.exec_driver_sql(
                "INSERT INTO usuarios (id, email, hashed_password) "
                "VALUES (3, 'Nueva@Example.com', '$2b$legacy-three')"
            )

            audit = migration.preflight(connection)
            self.assertEqual(audit["email_canonical_pendientes_ids"], [3])
            self.assertEqual(audit["password_credentials_pendientes_ids"], [3])

            repaired = migration.upgrade(connection)
            repeated = migration.upgrade(connection)

            self.assertEqual(repaired["backfill"]["emails"], 1)
            self.assertEqual(repaired["backfill"]["password_credentials"], 1)
            self.assertEqual(repeated["backfill"]["emails"], 0)
            self.assertEqual(repeated["backfill"]["password_credentials"], 0)
            row = connection.exec_driver_sql(
                "SELECT u.email_canonical, u.hashed_password, p.password_hash "
                "FROM usuarios u JOIN password_credentials p "
                "ON p.usuario_id = u.id WHERE u.id = 3"
            ).one()
            self.assertEqual(
                tuple(row),
                ("nueva@example.com", "$2b$legacy-three", "$2b$legacy-three"),
            )


if __name__ == "__main__":
    unittest.main()
