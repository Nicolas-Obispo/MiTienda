import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, inspect

import migrate_operational_incidents as migration


class OperationalIncidentsMigrationTests(unittest.TestCase):
    def test_upgrade_is_idempotent(self):
        engine = create_engine("sqlite://")
        with patch.object(migration, "engine", engine):
            with engine.begin() as connection:
                first = migration.upgrade(connection)
                second = migration.upgrade(connection)
        self.assertEqual(first, ["operational_incidents", "operational_incident_events"])
        self.assertEqual(second, [])
        self.assertTrue(set(migration.TABLES).issubset(inspect(engine).get_table_names()))


if __name__ == "__main__": unittest.main()
