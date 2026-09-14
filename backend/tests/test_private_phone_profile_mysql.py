import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.database import Base
from app.core.model_registry import import_all_models
import migrate_private_phone_profile as migration
from tests.mysql_stage97_test_support import isolated_mysql_test_engine

import_all_models()


class PrivatePhoneProfileMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session = isolated_mysql_test_engine()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE usuarios ("
                "id INT PRIMARY KEY, email VARCHAR(255) NOT NULL UNIQUE, "
                "hashed_password VARCHAR(255) NOT NULL, "
                "onboarding_completo BOOLEAN NOT NULL DEFAULT 0)"
            )
            connection.exec_driver_sql(
                "INSERT INTO usuarios (id, email, hashed_password) VALUES "
                "(1, 'one@example.com', 'hash'), (2, 'two@example.com', 'hash')"
            )

    def test_migracion_mysql_limpia_idempotente_y_con_constraints(self):
        with self.engine.begin() as connection:
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertIn(migration.PHONE_UNIQUE, first["changes"])
        self.assertIn(migration.VERIFICATION_PAIR_CHECK, first["changes"])
        self.assertEqual(second["changes"], [])

        inspector = inspect(self.engine)
        unique_names = {
            item.get("name") for item in inspector.get_unique_constraints("usuarios")
        }
        index_names = {item.get("name") for item in inspector.get_indexes("usuarios")}
        self.assertIn(migration.PHONE_UNIQUE, unique_names | index_names)
        check_names = {
            item.get("name") for item in inspector.get_check_constraints("usuarios")
        }
        self.assertIn(migration.VERIFICATION_PAIR_CHECK, check_names)

        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "UPDATE usuarios SET telefono_e164 = NULL WHERE id IN (1, 2)"
            )
            with self.assertRaises(SQLAlchemyError):
                connection.exec_driver_sql(
                    "UPDATE usuarios SET telefono_verified_at = NOW() WHERE id = 1"
                )

    def test_unique_global_resuelve_carrera_y_admite_multiples_null(self):
        with self.engine.begin() as connection:
            migration.upgrade(connection)

        barrier = threading.Barrier(2)

        def assign(usuario_id):
            db = self.Session()
            try:
                barrier.wait(timeout=5)
                db.execute(
                    text("UPDATE usuarios SET telefono_e164 = :phone WHERE id = :id"),
                    {"phone": "+5491123456789", "id": usuario_id},
                )
                db.commit()
                return "ok"
            except IntegrityError:
                db.rollback()
                return "conflict"
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(assign, (1, 2)))
        self.assertEqual(sorted(results), ["conflict", "ok"])

    def test_migracion_mysql_reanuda_estado_parcial(self):
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE usuarios ADD COLUMN telefono_e164 VARCHAR(16) NULL"
            )
            first = migration.upgrade(connection)
            second = migration.upgrade(connection)
        self.assertIn("usuarios.telefono_verified_at", first["changes"])
        self.assertIn("usuarios.telefono_verification_source", first["changes"])
        self.assertEqual(second["changes"], [])


if __name__ == "__main__":
    unittest.main()
