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
from app.modules.users.models.identity_models import PasswordCredential
from app.modules.users.models.usuarios_documentos_aceptaciones_models import (
    UsuarioDocumentoAceptacion,
)
from app.modules.users.models.usuarios_models import Usuario
from app.modules.users.routes.usuarios_routers import router as usuarios_router
from app.modules.users.schemas.usuarios_schemas import UsuarioCreate
from app.modules.users.services.usuarios_services import crear_usuario
from app.modules.users.services.email_availability import (
    EmailAvailabilityRateLimiter,
    email_availability_rate_limiter,
)


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
        email_availability_rate_limiter.reset()

    def tearDown(self):
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

        self.assertEqual(response.status_code, 200)
        db = TestingSessionLocal()
        usuario = db.query(Usuario).one()
        credencial = db.query(PasswordCredential).one()
        evidencias = db.query(UsuarioDocumentoAceptacion).all()
        self.assertEqual(usuario.email_canonical, "persona@example.com")
        self.assertEqual(usuario.hashed_password, "$2b$hash-unico")
        self.assertEqual(credencial.password_hash, usuario.hashed_password)
        self.assertEqual(len(evidencias), 2)
        self.assertEqual(hasher.call_count, 1)
        db.close()

    def test_duplicado_canonico_conserva_conflicto_generico(self):
        first = client.post(
            "/usuarios/registrar",
            json=registration_payload("Persona@Example.com"),
        )
        second = client.post(
            "/usuarios/registrar",
            json=registration_payload("persona@example.COM"),
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json(), {"detail": "No se pudo completar el registro"})
        db = TestingSessionLocal()
        self.assertEqual(db.query(Usuario).count(), 1)
        self.assertEqual(db.query(PasswordCredential).count(), 1)
        self.assertEqual(db.query(UsuarioDocumentoAceptacion).count(), 2)
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

    def test_login_fallback_se_limita_a_fila_legacy_sin_reparar(self):
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

        self.assertEqual(response.status_code, 200)

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

        self.assertEqual(valid.status_code, 200)
        self.assertEqual(boundary.status_code, 200)
        self.assertEqual(too_long.status_code, 422)

    def test_disponibilidad_email_es_minima_y_canonica(self):
        available = client.post(
            "/usuarios/email-disponibilidad",
            json={"email": "  Persona@Example.COM  "},
        )
        self.assertEqual(available.status_code, 200)
        self.assertEqual(available.json(), {"disponible": True})

        client.post(
            "/usuarios/registrar",
            json=registration_payload("persona@example.com"),
        )
        occupied = client.post(
            "/usuarios/email-disponibilidad",
            json={"email": " PERSONA@example.COM "},
        )
        self.assertEqual(occupied.status_code, 200)
        self.assertEqual(occupied.json(), {"disponible": False})
        self.assertEqual(set(occupied.json()), {"disponible"})

    def test_disponibilidad_rechaza_email_invalido_y_limita_abuso(self):
        invalid = client.post(
            "/usuarios/email-disponibilidad",
            json={"email": "no-es-email"},
        )
        self.assertEqual(invalid.status_code, 422)

        clock = [0.0]
        limiter = EmailAvailabilityRateLimiter(
            limit=2,
            window_seconds=60,
            clock=lambda: clock[0],
        )
        self.assertTrue(limiter.allow("client"))
        self.assertTrue(limiter.allow("client"))
        self.assertFalse(limiter.allow("client"))
        clock[0] = 61.0
        self.assertTrue(limiter.allow("client"))

        with patch.object(email_availability_rate_limiter, "allow", return_value=False):
            limited = client.post(
                "/usuarios/email-disponibilidad",
                json={"email": "persona@example.com"},
            )
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(limited.headers["retry-after"], "60")
        self.assertEqual(
            limited.json(),
            {"detail": "Demasiadas solicitudes. Intenta nuevamente mas tarde."},
        )

    def test_disponibilidad_no_reemplaza_constraint_del_submit(self):
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

        self.assertEqual(available.json(), {"disponible": True})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(raced.status_code, 409)

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
