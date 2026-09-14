import unittest

from sqlalchemy import create_engine, inspect

import migrate_private_phone_profile as migration
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.phone_normalization import (
    InvalidPhoneError,
    canonicalize_phone,
)


class PhoneNormalizationTests(unittest.TestCase):
    def test_canonicaliza_formato_internacional_e164(self):
        self.assertEqual(
            canonicalize_phone(" +54 9 11 2345-6789 "),
            "+5491123456789",
        )

    def test_canonicaliza_numero_argentino_con_region_default(self):
        self.assertEqual(canonicalize_phone("11 2345-6789"), "+541123456789")

    def test_rechaza_numero_invalido(self):
        with self.assertRaises(InvalidPhoneError):
            canonicalize_phone("123")


class PrivatePhoneMigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE usuarios ("
                "id INTEGER PRIMARY KEY, email VARCHAR(255) NOT NULL UNIQUE, "
                "hashed_password VARCHAR(255) NOT NULL, "
                "onboarding_completo BOOLEAN NOT NULL DEFAULT 0)"
            )
            connection.exec_driver_sql(
                "INSERT INTO usuarios (id, email, hashed_password) VALUES "
                "(1, 'one@example.com', 'hash'), (2, 'two@example.com', 'hash')"
            )

    def test_upgrade_limpio_es_aditivo_sin_backfill_e_idempotente(self):
        with self.engine.begin() as connection:
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
            self.assertEqual(first["backfill"], 0)
            self.assertEqual(second["changes"], [])
            rows = connection.exec_driver_sql(
                "SELECT telefono_e164, telefono_verified_at, "
                "telefono_verification_source FROM usuarios ORDER BY id"
            ).all()
            self.assertEqual([tuple(row) for row in rows], [(None, None, None)] * 2)

        inspector = inspect(self.engine)
        columns = {column["name"] for column in inspector.get_columns("usuarios")}
        self.assertTrue(set(migration.USER_COLUMN_DDL) <= columns)
        indexes = {item["name"]: item for item in inspector.get_indexes("usuarios")}
        self.assertTrue(indexes[migration.PHONE_UNIQUE]["unique"])

    def test_estado_parcial_se_completa_sin_duplicar(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE usuarios ADD COLUMN telefono_e164 VARCHAR(16) NULL"
            )
            result = migration.upgrade(connection)
            repeated = migration.upgrade(connection)
        self.assertIn("usuarios.telefono_verified_at", result["changes"])
        self.assertIn("usuarios.telefono_verification_source", result["changes"])
        self.assertEqual(repeated["changes"], [])

    def test_metadata_declara_unique_y_coherencia_de_verificacion(self):
        constraints = {constraint.name for constraint in Usuario.__table__.constraints}
        self.assertIn(migration.PHONE_UNIQUE, constraints)
        self.assertIn(migration.VERIFICATION_PAIR_CHECK, constraints)


if __name__ == "__main__":
    unittest.main()
