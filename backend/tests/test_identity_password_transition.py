import inspect
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.model_registry import import_all_models
from app.core.security import hash_password
from app.modules.users.models.identity_models import (
    AccountActionToken,
    PasswordCredential,
)
from app.modules.users.models.usuarios_documentos_aceptaciones_models import (
    UsuarioDocumentoAceptacion,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes.usuarios_routers import router as usuarios_router
from app.modules.users.schemas.usuarios_schemas import UsuarioCreate
from app.modules.users.services.authenticated_password_services import (
    change_authenticated_password,
)
from app.modules.users.services.authentication_method_services import (
    add_password_credential,
)
from app.modules.users.services.google_identity_services import (
    process_google_identity,
)
from app.modules.users.services.password_recovery_services import (
    reset_password_with_token,
)
from app.modules.users.services.usuarios_services import autenticar_usuario, crear_usuario


import_all_models()

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(usuarios_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def registration_payload(email: str, password: str = "Password1-segura") -> dict:
    return {
        "email": email,
        "password": password,
        "acepta_terminos": True,
        "acepta_privacidad": True,
    }


class IdentityPasswordTransitionTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.rate_secret_patch = patch(
            "app.modules.users.services.account_action_rate_limit_services."
            "settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
            "identity-transition-rate-secret",
        )
        self.rate_secret_patch.start()

    def tearDown(self):
        self.rate_secret_patch.stop()
        Base.metadata.drop_all(bind=engine)

    def test_registro_atomico_usa_canonical_y_un_solo_hash(self):
        with patch(
            "app.modules.users.services.usuarios_services.hash_password",
            return_value="$2b$hash-unico",
        ) as hasher:
            response = client.post(
                "/usuarios/registrar",
                json=registration_payload("  Persona@Example.COM  "),
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {"status": "registration_received"})
        self.assertEqual(response.headers["cache-control"], "no-store")
        db = TestingSessionLocal()
        usuario = db.query(Usuario).one()
        credencial = db.query(PasswordCredential).one()
        evidencias = db.query(UsuarioDocumentoAceptacion).all()
        self.assertEqual(usuario.email_canonical, "persona@example.com")
        self.assertIsNone(usuario.hashed_password)
        self.assertEqual(credencial.password_hash, "$2b$hash-unico")
        self.assertEqual(len(evidencias), 2)
        self.assertEqual(hasher.call_count, 1)
        db.close()

    def test_registro_nuevo_y_duplicado_comparten_contrato_publico(self):
        with patch(
            "app.modules.users.routes.usuarios_routers."
            "send_registration_verification",
        ) as delivery:
            first = client.post(
                "/usuarios/registrar",
                json=registration_payload("Persona@Example.com"),
            )
        self.assertEqual(delivery.call_count, 1)

        db = TestingSessionLocal()
        usuario = db.query(Usuario).one()
        credencial = db.query(PasswordCredential).one()
        original_legacy_hash = usuario.hashed_password
        original_credential_hash = credencial.password_hash
        db.close()

        with (
            patch(
                "app.modules.users.services.usuarios_services.hash_password",
                wraps=hash_password,
            ) as duplicate_hasher,
            patch(
                "app.modules.users.routes.usuarios_routers."
                "send_registration_verification",
            ) as duplicate_delivery,
        ):
            second = client.post(
                "/usuarios/registrar",
                json=registration_payload(
                    "persona@example.COM",
                    "Different2-secure",
                ),
            )

        self.assertEqual(duplicate_hasher.call_count, 1)
        duplicate_delivery.assert_not_called()

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        self.assertEqual(first.json(), {"status": "registration_received"})
        self.assertEqual(second.json(), first.json())
        self.assertEqual(first.headers["cache-control"], "no-store")
        self.assertEqual(second.headers["cache-control"], "no-store")
        db = TestingSessionLocal()
        self.assertEqual(db.query(Usuario).count(), 1)
        self.assertEqual(db.query(PasswordCredential).count(), 1)
        self.assertEqual(db.query(UsuarioDocumentoAceptacion).count(), 2)
        self.assertEqual(db.query(AccountActionToken).count(), 0)
        usuario = db.query(Usuario).one()
        credencial = db.query(PasswordCredential).one()
        self.assertEqual(usuario.hashed_password, original_legacy_hash)
        self.assertEqual(credencial.password_hash, original_credential_hash)
        db.close()

    def test_registro_duplicado_con_password_invalida_conserva_422(self):
        with patch(
            "app.modules.users.routes.usuarios_routers."
            "send_registration_verification",
        ):
            created = client.post(
                "/usuarios/registrar",
                json=registration_payload("existing-policy@example.com"),
            )
        self.assertEqual(created.status_code, 202)

        with patch(
            "app.modules.users.services.usuarios_services.hash_password",
        ) as hasher:
            rejected = client.post(
                "/usuarios/registrar",
                json=registration_payload(
                    "existing-policy@example.com",
                    "weak",
                ),
            )

        self.assertEqual(rejected.status_code, 422)
        hasher.assert_not_called()
        db = TestingSessionLocal()
        self.assertEqual(db.query(Usuario).count(), 1)
        self.assertEqual(db.query(PasswordCredential).count(), 1)
        db.close()

    def test_login_canonical_usa_password_credential_como_owner(self):
        client.post(
            "/usuarios/registrar",
            json=registration_payload("Persona@Example.com"),
        )
        db = TestingSessionLocal()
        usuario = db.query(Usuario).one()
        usuario.hashed_password = hash_password("legacy-divergente")
        db.commit()
        db.close()

        response = client.post(
            "/usuarios/login",
            json={
                "email": "  persona@EXAMPLE.COM ",
                "password": "Password1-segura",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())

    def test_login_no_usa_fallback_legacy_sin_canonical_ni_credential(self):
        db = TestingSessionLocal()
        db.add(
            Usuario(
                email="Legacy@Example.com",
                email_canonical=None,
                hashed_password=hash_password("password-legacy"),
            )
        )
        db.commit()
        db.close()

        response = client.post(
            "/usuarios/login",
            json={
                "email": " legacy@example.COM ",
                "password": "password-legacy",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"detail": "Credenciales inv\u00e1lidas"},
        )

    def test_usuario_canonico_sin_credencial_no_usa_hash_legacy(self):
        db = TestingSessionLocal()
        db.add(
            Usuario(
                email="incompleto@example.com",
                email_canonical="incompleto@example.com",
                hashed_password=hash_password("password-legacy"),
            )
        )
        db.commit()
        db.close()

        response = client.post(
            "/usuarios/login",
            json={
                "email": "incompleto@example.com",
                "password": "password-legacy",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Credenciales inválidas"})

    def test_runtime_password_no_referencia_hashed_password_legacy(self):
        runtime_flows = (
            crear_usuario,
            autenticar_usuario,
            change_authenticated_password,
            reset_password_with_token,
            add_password_credential,
            process_google_identity,
        )
        for flow in runtime_flows:
            self.assertNotIn("hashed_password", inspect.getsource(flow), flow.__name__)

    def test_politica_password_cubre_requisitos_y_limite_bcrypt(self):
        invalid_passwords = [
            "Prue1a",
            "prueba12",
            "PRUEBA12",
            "PruebaAA",
            "Prue ba1",
            "Prueba\t1",
        ]
        for index, password in enumerate(invalid_passwords):
            response = client.post(
                "/usuarios/registrar",
                json=registration_payload(f"invalid-{index}@example.com", password),
            )
            self.assertEqual(response.status_code, 422, password)

        valid = client.post(
            "/usuarios/registrar",
            json=registration_payload("valid@example.com", "Prueba12"),
        )
        boundary = client.post(
            "/usuarios/registrar",
            json=registration_payload("boundary@example.com", "Aa1" + "x" * 69),
        )
        too_long = client.post(
            "/usuarios/registrar",
            json=registration_payload("long@example.com", "Aa1" + "x" * 70),
        )
        unicode_boundary = client.post(
            "/usuarios/registrar",
            json=registration_payload("unicode@example.com", "Áa١" + "x" * 67),
        )
        unicode_too_long = client.post(
            "/usuarios/registrar",
            json=registration_payload("unicode-long@example.com", "Áa١" + "x" * 68),
        )

        self.assertEqual(valid.status_code, 202)
        self.assertEqual(boundary.status_code, 202)
        self.assertEqual(too_long.status_code, 422)
        self.assertEqual(unicode_boundary.status_code, 202)
        self.assertEqual(unicode_too_long.status_code, 422)

    def test_servicio_de_alta_revalida_la_politica_al_omitir_el_schema(self):
        payload = UsuarioCreate.model_construct(
            email="direct@example.com",
            password="weak",
            acepta_terminos=True,
            acepta_privacidad=True,
        )
        db = TestingSessionLocal()
        with self.assertRaises(ValueError):
            crear_usuario(db, payload)
        self.assertEqual(db.query(Usuario).count(), 0)
        db.close()

    def test_disponibilidad_email_es_neutra_y_no_revela_existencia(self):
        available = client.post(
            "/usuarios/email-disponibilidad",
            json={"email": "  Persona@Example.COM  "},
        )
        self.assertEqual(available.status_code, 200)
        self.assertEqual(available.json(), {"status": "check_on_submit"})
        self.assertEqual(available.headers["cache-control"], "no-store")

        client.post(
            "/usuarios/registrar",
            json=registration_payload("persona@example.com"),
        )
        occupied = client.post(
            "/usuarios/email-disponibilidad",
            json={"email": " PERSONA@example.COM "},
        )
        self.assertEqual(occupied.status_code, 200)
        self.assertEqual(occupied.json(), available.json())
        self.assertEqual(occupied.headers["cache-control"], "no-store")

    def test_disponibilidad_conserva_validacion_sintactica_sin_rate_limiter_local(self):
        invalid = client.post(
            "/usuarios/email-disponibilidad",
            json={"email": "no-es-email"},
        )
        self.assertEqual(invalid.status_code, 422)

        neutral = client.post(
            "/usuarios/email-disponibilidad",
            json={"email": "persona@example.com"},
        )
        self.assertEqual(neutral.status_code, 200)
        self.assertEqual(neutral.json(), {"status": "check_on_submit"})

    def test_submit_conserva_constraint_y_contrato_uniforme(self):
        available = client.post(
            "/usuarios/email-disponibilidad",
            json={"email": "race@example.com"},
        )
        first = client.post(
            "/usuarios/registrar",
            json=registration_payload("Race@example.com"),
        )
        raced = client.post(
            "/usuarios/registrar",
            json=registration_payload("race@EXAMPLE.com"),
        )

        self.assertEqual(available.json(), {"status": "check_on_submit"})
        self.assertEqual(first.status_code, 202)
        self.assertEqual(raced.status_code, 202)
        self.assertEqual(first.json(), raced.json())

    def test_altas_canonicas_concurrentes_crean_una_sola_identidad(self):
        with tempfile.TemporaryDirectory() as directory:
            concurrent_engine = create_engine(
                f"sqlite:///{directory}/identity.db",
                connect_args={"check_same_thread": False, "timeout": 10},
            )
            Base.metadata.create_all(bind=concurrent_engine)
            sessions = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=concurrent_engine,
            )
            barrier = threading.Barrier(2)

            def synchronized_hash(_password: str) -> str:
                barrier.wait(timeout=5)
                return "$2b$concurrent-hash"

            def register(email: str):
                db = sessions()
                try:
                    payload = UsuarioCreate(**registration_payload(email))
                    return crear_usuario(db, payload)
                finally:
                    db.close()

            with patch(
                "app.modules.users.services.usuarios_services.hash_password",
                side_effect=synchronized_hash,
            ):
                with ThreadPoolExecutor(max_workers=2) as executor:
                    results = list(
                        executor.map(
                            register,
                            ["Race@Example.com", "race@example.COM"],
                        )
                    )

            db = sessions()
            self.assertEqual(sum(result is not None for result in results), 1)
            self.assertEqual(db.query(Usuario).count(), 1)
            self.assertEqual(db.query(PasswordCredential).count(), 1)
            self.assertEqual(db.query(UsuarioDocumentoAceptacion).count(), 2)
            db.close()
            concurrent_engine.dispose()


if __name__ == "__main__":
    unittest.main()
