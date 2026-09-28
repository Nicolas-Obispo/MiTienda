import unittest

from pydantic import ValidationError

from app.modules.users.schemas.usuarios_schemas import (
    AddPasswordCredentialRequest,
    AuthenticatedPasswordChangeRequest,
    PasswordReauthenticationRequest,
    PasswordResetRequest,
    UsuarioCreate,
    UsuarioLogin,
)
from app.modules.users.services.password_policy import validate_new_password


def _new_password_payloads(password: str):
    return (
        lambda: UsuarioCreate(
            email="person@example.com",
            password=password,
            acepta_terminos=True,
            acepta_privacidad=True,
        ),
        lambda: PasswordResetRequest(token="token", new_password=password),
        lambda: AuthenticatedPasswordChangeRequest(
            current_password="legacy",
            new_password=password,
        ),
        lambda: AddPasswordCredentialRequest(confirm=True, new_password=password),
    )


class PasswordPolicyB1ContractTests(unittest.TestCase):
    def test_all_new_password_flows_share_exact_valid_boundaries(self):
        valid_passwords = (
            "Aa1" + "x" * 69,
            "Áa١" + "x" * 67,
        )
        for password in valid_passwords:
            self.assertEqual(validate_new_password(password), password)
            for build in _new_password_payloads(password):
                build()

    def test_all_new_password_flows_share_exact_rejections(self):
        invalid_passwords = (
            "Short1",
            "password1",
            "PASSWORD1",
            "Password",
            "Pass\u2003word1",
            "Aa1" + "x" * 70,
            "Áa١" + "x" * 68,
        )
        for password in invalid_passwords:
            with self.assertRaises(ValueError):
                validate_new_password(password)
            for build in _new_password_payloads(password):
                with self.assertRaises(ValidationError):
                    build()

    def test_login_and_reauthentication_keep_existing_legacy_passwords_outside_policy(self):
        self.assertEqual(
            UsuarioLogin(email="person@example.com", password="legacy").password,
            "legacy",
        )
        self.assertEqual(
            PasswordReauthenticationRequest(current_password="legacy").current_password,
            "legacy",
        )


if __name__ == "__main__":
    unittest.main()
