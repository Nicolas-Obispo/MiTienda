import unittest

from app.core.database import Base
from app.core.model_registry import import_all_models
from migrate_password_login_rate_limit import (
    DESIRED_ACTIONS,
    GOOGLE_ACTIONS,
    PHONE_ACTIONS,
    _actions_from_check,
)


import_all_models()


class PasswordLoginRateLimitMigrationContractTests(unittest.TestCase):
    def test_estados_fisicos_conocidos(self):
        self.assertLess(PHONE_ACTIONS, GOOGLE_ACTIONS)
        self.assertLess(GOOGLE_ACTIONS, DESIRED_ACTIONS)
        self.assertEqual(DESIRED_ACTIONS - GOOGLE_ACTIONS, {"password_login"})

    def test_normaliza_expresion_mysql(self):
        expression = (
            "`action` in (_utf8mb4'email_verification',_utf8mb4'password_reset',"
            "_utf8mb4'current_password',_utf8mb4'phone_verification',"
            "_utf8mb4'google_oauth')"
        )
        self.assertEqual(_actions_from_check(expression), GOOGLE_ACTIONS)

    def test_metadata_incluye_accion_e_indice_cleanup(self):
        table = Base.metadata.tables["account_action_rate_limits"]
        check = next(
            constraint
            for constraint in table.constraints
            if constraint.name == "ck_account_action_rate_limits_action"
        )
        self.assertIn("password_login", str(check.sqltext))
        indexes = {index.name: tuple(column.name for column in index.columns) for index in table.indexes}
        self.assertEqual(
            indexes["ix_account_action_rate_limits_action_updated"],
            ("action", "updated_at"),
        )


if __name__ == "__main__":
    unittest.main()
