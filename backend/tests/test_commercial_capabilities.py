from datetime import date, datetime, timezone
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.services.commercial_capabilities_services import (
    derive_commercial_readiness,
)
from app.modules.users.services.documentos_aceptacion_services import (
    CANAL_REGISTRO_WEB,
    DOCUMENTOS_OBLIGATORIOS_REGISTRO,
    ESTADO_ACEPTADO,
    METODO_CHECKBOX_EXPLICITO,
)
from app.modules.users.models.usuarios_documentos_aceptaciones_models import (
    UsuarioDocumentoAceptacion,
)


import_all_models()
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
SessionLocal = sessionmaker(bind=engine)


class CommercialCapabilitiesTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(engine)

    def _usuario(self, **overrides) -> Usuario:
        values = {
            "email": "commercial@example.com",
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
        usuario = Usuario(**values)
        self.db.add(usuario)
        self.db.flush()
        return usuario

    def _aceptar_legal(self, usuario: Usuario) -> None:
        for documento in DOCUMENTOS_OBLIGATORIOS_REGISTRO:
            self.db.add(
                UsuarioDocumentoAceptacion(
                    usuario_id=usuario.id,
                    documento_tipo=documento.tipo,
                    documento_version=documento.version,
                    canal=CANAL_REGISTRO_WEB,
                    metodo=METODO_CHECKBOX_EXPLICITO,
                    estado=ESTADO_ACEPTADO,
                    documento_referencia=documento.referencia,
                )
            )
        self.db.flush()

    def test_all_capabilities_require_every_gate(self):
        usuario = self._usuario()
        self._aceptar_legal(usuario)
        result = derive_commercial_readiness(self.db, usuario, today=date(2026, 9, 6))
        self.assertTrue(result.capabilities.puede_crear_espacio)
        self.assertTrue(result.capabilities.puede_administrar_espacios)
        self.assertTrue(result.capabilities.puede_publicar_en_espacios)
        self.assertEqual(result.pendientes_comerciales, ())

    def test_profile_and_legal_pending_are_deterministic(self):
        usuario = self._usuario(
            provincia=" ",
            telefono_verified_at=None,
            telefono_verification_source=None,
        )
        result = derive_commercial_readiness(self.db, usuario, today=date(2026, 9, 6))
        self.assertEqual(
            result.pendientes_comerciales,
            ("perfil_incompleto", "aceptaciones_legales_pendientes"),
        )
        self.assertFalse(result.capabilities.puede_crear_espacio)

    def test_null_minor_exactly_18_and_adult(self):
        cases = (
            (None, "+5491123456781", False, ("perfil_incompleto", "mayoria_edad_requerida")),
            (date(2009, 9, 6), "+5491123456782", False, ("mayoria_edad_requerida",)),
            (date(2008, 9, 6), "+5491123456783", True, ()),
            (date(1990, 1, 1), "+5491123456784", True, ()),
        )
        for index, (birth_date, phone, allowed, pending) in enumerate(cases, start=1):
            usuario = self._usuario(
                email=f"age-{index}@example.com",
                fecha_nacimiento=birth_date,
                telefono_e164=phone,
            )
            self._aceptar_legal(usuario)
            result = derive_commercial_readiness(
                self.db, usuario, today=date(2026, 9, 6)
            )
            self.assertEqual(result.capabilities.puede_crear_espacio, allowed)
            self.assertEqual(result.pendientes_comerciales, pending)

    def test_email_verification_remains_a_profile_blocker_without_phone(self):
        usuario = self._usuario(
            email_verified_at=None,
            telefono_e164=None,
            telefono_verified_at=None,
            telefono_verification_source=None,
        )
        self._aceptar_legal(usuario)
        result = derive_commercial_readiness(self.db, usuario, today=date(2026, 9, 6))
        self.assertEqual(result.pendientes_comerciales, ("perfil_incompleto",))
        self.assertEqual(
            result.profile_status.campos_perfil_faltantes,
            ("telefono", "email_verificado"),
        )

    def test_capabilities_allow_valid_unverified_phone(self):
        usuario = self._usuario(telefono_verified_at=None, telefono_verification_source=None)
        self._aceptar_legal(usuario)
        result = derive_commercial_readiness(self.db, usuario, today=date(2026, 9, 6))
        self.assertTrue(result.profile_status.perfil_completo)
        self.assertTrue(result.capabilities.puede_crear_espacio)
        self.assertTrue(result.capabilities.puede_administrar_espacios)
        self.assertTrue(result.capabilities.puede_publicar_en_espacios)

    def test_capabilities_require_phone_value(self):
        usuario = self._usuario(email="without-phone@example.com", telefono_e164=None, telefono_verified_at=None, telefono_verification_source=None)
        self._aceptar_legal(usuario)
        result = derive_commercial_readiness(self.db, usuario, today=date(2026, 9, 6))
        self.assertFalse(result.profile_status.perfil_completo)
        self.assertFalse(result.capabilities.puede_crear_espacio)
        self.assertEqual(result.pendientes_comerciales, ("perfil_incompleto",))

    def test_minor_has_structurally_complete_profile_but_no_capability(self):
        usuario = self._usuario(
            email="minor-without-phone@example.com",
            fecha_nacimiento=date(2009, 9, 6),
            telefono_verified_at=None,
            telefono_verification_source=None,
        )
        self._aceptar_legal(usuario)
        result = derive_commercial_readiness(self.db, usuario, today=date(2026, 9, 6))
        self.assertTrue(result.profile_status.perfil_completo)
        self.assertFalse(result.capabilities.puede_crear_espacio)
        self.assertEqual(result.pendientes_comerciales, ("mayoria_edad_requerida",))

    def test_legacy_presentation_fields_do_not_grant_or_remove_capability(self):
        first = self._usuario(
            email="first@example.com", telefono_e164="+5491123456785",
            onboarding_completo=True, modo_activo="publicador",
        )
        second = self._usuario(
            email="second@example.com", telefono_e164="+5491123456786",
            onboarding_completo=False, modo_activo="usuario",
        )
        self._aceptar_legal(first)
        self._aceptar_legal(second)
        first_result = derive_commercial_readiness(self.db, first, today=date(2026, 9, 6))
        second_result = derive_commercial_readiness(self.db, second, today=date(2026, 9, 6))
        self.assertEqual(first_result.capabilities, second_result.capabilities)

    def test_derived_fields_are_not_persisted_or_jwt_model_fields(self):
        columns = set(Usuario.__table__.columns.keys())
        self.assertNotIn("perfil_completo", columns)
        self.assertNotIn("pendientes_comerciales", columns)
        self.assertNotIn("capabilities", columns)
        self.assertNotIn("edad", columns)


if __name__ == "__main__":
    unittest.main()
