import unittest

from sqlalchemy import create_engine, inspect, text

from app.core.database import Base
from app.core.model_registry import import_all_models
from migrate_moderation_reports_inbox_index import INDEX_NAME, upgrade

import_all_models()


class ModerationInboxIndexMigrationTests(unittest.TestCase):
    def test_upgrade_is_additive_and_idempotent(self):
        engine = create_engine("sqlite://")
        table = Base.metadata.tables["contenido_denuncias"]
        table.create(bind=engine, checkfirst=True)
        with engine.begin() as connection:
            connection.execute(text(f"DROP INDEX {INDEX_NAME}"))
            self.assertEqual(upgrade(connection), "created")
            self.assertEqual(upgrade(connection), "already_exists")

        indexes = {index["name"]: index for index in inspect(engine).get_indexes(table.name)}
        self.assertEqual(
            indexes[INDEX_NAME]["column_names"],
            ["estado", "creado_en", "id"],
        )
        table.drop(bind=engine)


if __name__ == "__main__":
    unittest.main()
