import unittest

from sqlalchemy import create_engine, inspect

from app.core.database import Base
from migrate_administrative_capabilities import TABLE_NAME, upgrade


class AdministrativeCapabilitiesMigrationTests(unittest.TestCase):
    def test_foreign_key_metadata_is_registered_in_isolated_migration(self):
        table = Base.metadata.tables[TABLE_NAME]
        targets = {
            foreign_key.target_fullname
            for foreign_key in table.foreign_keys
        }
        self.assertEqual(targets, {"usuarios.id"})

    def test_upgrade_is_additive_and_idempotent(self):
        engine = create_engine("sqlite://")

        with engine.begin() as connection:
            self.assertEqual(upgrade(connection), "created")
            self.assertEqual(upgrade(connection), "already_exists")

        self.assertIn(TABLE_NAME, inspect(engine).get_table_names())
        columns = {
            column["name"] for column in inspect(engine).get_columns(TABLE_NAME)
        }
        self.assertEqual(
            columns,
            {
                "id",
                "usuario_id",
                "capability",
                "action",
                "actor_usuario_id",
                "source",
                "reason",
                "created_at",
            },
        )
        Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    unittest.main()
