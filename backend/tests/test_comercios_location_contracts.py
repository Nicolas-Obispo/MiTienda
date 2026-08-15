import math
import unittest
from unittest.mock import patch

from pydantic import ValidationError
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.model_registry import import_all_models
from app.modules.products.models.rubros_models import Rubro
from app.modules.spaces.models.comercios_models import Comercio
from app.modules.spaces.schemas.comercios_schemas import ComercioCreate, ComercioUpdate
from app.modules.spaces.services.comercios_services import (
    actualizar_comercio,
    crear_comercio,
)
from app.modules.users.models.usuarios_models import Usuario
from check_database_schema import check_schema
from migrate_comercios_location_visibility import downgrade, upgrade


def _payload_valido(**overrides):
    payload = {
        "nombre": "Espacio valido",
        "descripcion": "Descripcion",
        "portada_url": "/uploads/portada.jpg",
        "rubro_id": 1,
        "provincia": "Santa Fe",
        "ciudad": "Rafaela",
        "direccion": "Sargento Cabral 159",
        "latitud": -31.2503,
        "longitud": -61.4867,
    }
    payload.update(overrides)
    return payload


class ComercioLocationSchemaTests(unittest.TestCase):
    def test_alta_valida_y_default_publico(self):
        data = ComercioCreate(**_payload_valido())

        self.assertTrue(data.mostrar_direccion_publicamente)
        self.assertEqual(data.direccion, "Sargento Cabral 159")

    def test_alta_sin_ubicacion_es_rechazada(self):
        for campo in ("provincia", "ciudad", "direccion", "latitud", "longitud"):
            payload = _payload_valido()
            payload.pop(campo)
            with self.subTest(campo=campo), self.assertRaises(ValidationError):
                ComercioCreate(**payload)

    def test_coordenadas_parciales_son_rechazadas(self):
        for campo in ("latitud", "longitud"):
            with self.subTest(campo=campo), self.assertRaises(ValidationError):
                ComercioCreate(**_payload_valido(**{campo: None}))

    def test_nan_e_infinito_son_rechazados(self):
        for campo in ("latitud", "longitud"):
            for valor in (math.nan, math.inf, -math.inf):
                with (
                    self.subTest(campo=campo, valor=valor),
                    self.assertRaises(ValidationError),
                ):
                    ComercioCreate(**_payload_valido(**{campo: valor}))

    def test_latitud_fuera_de_rango_es_rechazada(self):
        for valor in (-90.0001, 90.0001):
            with self.subTest(valor=valor), self.assertRaises(ValidationError):
                ComercioCreate(**_payload_valido(latitud=valor))

    def test_longitud_fuera_de_rango_es_rechazada(self):
        for valor in (-180.0001, 180.0001):
            with self.subTest(valor=valor), self.assertRaises(ValidationError):
                ComercioCreate(**_payload_valido(longitud=valor))


class ComercioLocationServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_models()

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.Session()
        self.usuario = Usuario(
            id=1,
            email="owner@example.com",
            hashed_password="hash",
            modo_activo="publicador",
            onboarding_completo=True,
        )
        self.db.add_all(
            [
                self.usuario,
                Rubro(id=1, nombre="Servicios", activo=True),
            ]
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    @patch(
        "app.modules.spaces.services.comercios_services.upsert_embedding_comercio"
    )
    @patch(
        "app.modules.spaces.services.comercios_services.sincronizar_especialidades_comercio"
    )
    @patch(
        "app.modules.spaces.services.comercios_services.sincronizar_assignments_comercio_desde_rubros"
    )
    def test_alta_persiste_ubicacion_y_default_publico(
        self,
        _sincronizar_assignments,
        _sincronizar_especialidades,
        _upsert_embedding,
    ):
        comercio = crear_comercio(
            self.db,
            self.usuario,
            ComercioCreate(**_payload_valido()),
        )

        self.assertEqual(comercio.latitud, -31.2503)
        self.assertEqual(comercio.longitud, -61.4867)
        self.assertTrue(comercio.mostrar_direccion_publicamente)

    @patch(
        "app.modules.spaces.services.comercios_services.upsert_embedding_comercio"
    )
    def test_historico_incompleto_sigue_siendo_administrable(
        self,
        _upsert_embedding,
    ):
        historico = Comercio(
            usuario_id=self.usuario.id,
            nombre="Historico",
            portada_url="/uploads/historico.jpg",
            rubro_id=1,
            provincia="Santa Fe",
            ciudad="Rafaela",
            direccion=None,
            latitud=None,
            longitud=None,
        )
        self.db.add(historico)
        self.db.commit()

        actualizado = actualizar_comercio(
            self.db,
            self.usuario,
            historico,
            ComercioUpdate(nombre="Historico administrado"),
        )

        self.assertEqual(actualizado.nombre, "Historico administrado")
        self.assertIsNone(actualizado.latitud)
        self.assertTrue(actualizado.mostrar_direccion_publicamente)

    def test_historico_no_admite_una_correccion_de_ubicacion_parcial(self):
        historico = Comercio(
            usuario_id=self.usuario.id,
            nombre="Historico",
            portada_url="/uploads/historico.jpg",
            rubro_id=1,
            provincia="Santa Fe",
            ciudad="Rafaela",
        )
        self.db.add(historico)
        self.db.commit()

        with self.assertRaisesRegex(ValueError, "presentes juntas"):
            actualizar_comercio(
                self.db,
                self.usuario,
                historico,
                ComercioUpdate(direccion="Sargento Cabral 159"),
            )


class ComercioLocationMigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE comercios ("
                    "id INTEGER PRIMARY KEY, nombre VARCHAR(255) NOT NULL)"
                )
            )
            connection.execute(
                text("INSERT INTO comercios (id, nombre) VALUES (1, 'Historico')")
            )

    def tearDown(self):
        self.engine.dispose()

    def test_upgrade_preserva_historicos_como_publicos(self):
        with self.engine.begin() as connection:
            self.assertEqual(upgrade(connection), "created")
            valor = connection.execute(
                text(
                    "SELECT mostrar_direccion_publicamente "
                    "FROM comercios WHERE id = 1"
                )
            ).scalar_one()

        self.assertEqual(valor, 1)
        self.assertIn(
            "mostrar_direccion_publicamente",
            {column["name"] for column in inspect(self.engine).get_columns("comercios")},
        )

    def test_upgrade_es_idempotente(self):
        with self.engine.begin() as connection:
            self.assertEqual(upgrade(connection), "created")
            self.assertEqual(upgrade(connection), "already_exists")

    def test_downgrade_elimina_la_columna(self):
        with self.engine.begin() as connection:
            upgrade(connection)
            self.assertEqual(downgrade(connection), "dropped")
            self.assertEqual(downgrade(connection), "already_absent")

        self.assertNotIn(
            "mostrar_direccion_publicamente",
            {column["name"] for column in inspect(self.engine).get_columns("comercios")},
        )


class ComercioLocationMetadataTests(unittest.TestCase):
    def test_metadata_coincide_con_base_fisica_nueva(self):
        import_all_models()
        engine = create_engine("sqlite://")
        try:
            Base.metadata.create_all(bind=engine)
            result = check_schema(inspector=inspect(engine), metadata=Base.metadata)
        finally:
            Base.metadata.drop_all(bind=engine)
            engine.dispose()

        self.assertNotIn("comercios", result.column_differences)
        self.assertNotIn("comercios", result.foreign_key_differences)
        self.assertNotIn("comercios", result.index_differences)
        self.assertNotIn("comercios", result.unique_differences)


if __name__ == "__main__":
    unittest.main()
