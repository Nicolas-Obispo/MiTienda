from datetime import date, datetime, timezone
import unittest

from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.profile_status_services import (
    business_date,
    calculate_age,
    derive_profile_status,
)


class ProfileStatusTests(unittest.TestCase):
    def _usuario(self, **overrides) -> Usuario:
        values = {
            "email": "profile@example.com",
            "hashed_password": "hash",
            "modo_activo": "usuario",
            "onboarding_completo": False,
            "provincia": "Buenos Aires",
            "ciudad": "La Plata",
            "fecha_nacimiento": date(2000, 9, 6),
            "email_verified_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "telefono_e164": "+5491123456789",
            "telefono_verified_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "telefono_verification_source": "phone_otp",
        }
        values.update(overrides)
        return Usuario(**values)

    def test_age_null_future_and_calendar_boundaries(self):
        self.assertIsNone(calculate_age(None, today=date(2026, 9, 6)))
        with self.assertRaises(ValueError):
            calculate_age(date(2026, 9, 7), today=date(2026, 9, 6))
        self.assertEqual(calculate_age(date(2000, 9, 6), today=date(2026, 9, 6)), 26)
        self.assertEqual(calculate_age(date(2000, 9, 7), today=date(2026, 9, 6)), 25)
        self.assertEqual(calculate_age(date(2000, 9, 5), today=date(2026, 9, 6)), 26)

    def test_leap_day(self):
        self.assertEqual(calculate_age(date(2000, 2, 29), today=date(2025, 2, 28)), 24)
        self.assertEqual(calculate_age(date(2000, 2, 29), today=date(2025, 3, 1)), 25)

    def test_business_timezone_and_injected_clock(self):
        utc = datetime(2026, 9, 7, 2, 30, tzinfo=timezone.utc)
        self.assertEqual(business_date(now=utc), date(2026, 9, 6))
        with self.assertRaises(ValueError):
            business_date(now=datetime(2026, 9, 6, 12, 0))

    def test_complete_profile_ignores_legacy_onboarding(self):
        result = derive_profile_status(self._usuario(onboarding_completo=False), today=date(2026, 9, 6))
        self.assertTrue(result.perfil_completo)
        self.assertEqual(result.campos_perfil_faltantes, ())

    def test_missing_fields_are_deterministic(self):
        result = derive_profile_status(
            self._usuario(
                provincia=" ", ciudad="", fecha_nacimiento=None,
                email_verified_at=None, telefono_e164=None,
                telefono_verified_at=None, telefono_verification_source=None,
            ),
            today=date(2026, 9, 6),
        )
        self.assertFalse(result.perfil_completo)
        self.assertEqual(
            result.campos_perfil_faltantes,
            ("provincia", "ciudad", "fecha_nacimiento", "telefono", "email_verificado"),
        )

    def test_phone_is_required_but_verification_is_not(self):
        missing = derive_profile_status(self._usuario(telefono_e164=None, telefono_verified_at=None, telefono_verification_source=None), today=date(2026, 9, 6))
        self.assertFalse(missing.perfil_completo)
        self.assertEqual(missing.campos_perfil_faltantes, ("telefono",))
        unverified = derive_profile_status(self._usuario(telefono_verified_at=None, telefono_verification_source=None), today=date(2026, 9, 6))
        self.assertTrue(unverified.perfil_completo)
        self.assertEqual(unverified.campos_perfil_faltantes, ())

    def test_future_birth_date_is_missing(self):
        result = derive_profile_status(
            self._usuario(fecha_nacimiento=date(2026, 9, 7)), today=date(2026, 9, 6)
        )
        self.assertEqual(result.campos_perfil_faltantes, ("fecha_nacimiento",))


if __name__ == "__main__":
    unittest.main()
