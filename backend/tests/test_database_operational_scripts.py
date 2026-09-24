import importlib
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, patch

from sqlalchemy import Boolean, CheckConstraint, Column, Float, Integer, MetaData, String, Table, text
from sqlalchemy.dialects.mysql import DOUBLE, TINYINT, VARCHAR

from app.core.database import Base


class _FakeColumns:
    def __init__(self, names):
        self._names = names

    def keys(self):
        return self._names

    def __iter__(self):
        return iter(_FakeColumn(name) for name in self._names)


class _FakeColumn:
    def __init__(self, name):
        self.name = name


class _FakeTable:
    def __init__(self, columns, foreign_keys=None, indexes=None, uniques=None):
        self.columns = _FakeColumns(columns)
        self.primary_key = SimpleNamespace(columns=[])
        self.foreign_key_constraints = set(foreign_keys or [])
        self.indexes = set(indexes or [])
        self.constraints = set(uniques or [])


class _FakeMetadata:
    def __init__(self, tables, table_options=None):
        table_options = table_options or {}
        self.tables = {
            table_name: _FakeTable(columns, **table_options.get(table_name, {}))
            for table_name, columns in tables.items()
        }


class _FakeReferredTable:
    def __init__(self, name):
        self.name = name


class _FakeForeignKeyElement:
    def __init__(self, column_name):
        self.column = _FakeColumn(column_name)


class _FakeForeignKeyConstraint:
    def __init__(self, constrained_columns, referred_table, referred_columns):
        self.columns = [_FakeColumn(name) for name in constrained_columns]
        self.referred_table = _FakeReferredTable(referred_table)
        self.elements = [_FakeForeignKeyElement(name) for name in referred_columns]


class _FakeIndex:
    def __init__(self, columns, unique=False):
        self.columns = [_FakeColumn(name) for name in columns]
        self.unique = unique


class UniqueConstraint:
    def __init__(self, columns):
        self.columns = [_FakeColumn(name) for name in columns]


class _FakeInspector:
    def __init__(self, tables, foreign_keys=None, indexes=None, uniques=None, checks=None):
        self._tables = tables
        self._foreign_keys = foreign_keys or {}
        self._indexes = indexes or {}
        self._uniques = uniques or {}
        self._checks = checks or {}
        self.create_all = Mock()
        self.drop_all = Mock()

    def get_table_names(self):
        return list(self._tables.keys())

    def get_columns(self, table_name):
        return [
            column if isinstance(column, dict) else {"name": column}
            for column in self._tables[table_name]
        ]

    def get_foreign_keys(self, table_name):
        return self._foreign_keys.get(table_name, [])

    def get_indexes(self, table_name):
        return self._indexes.get(table_name, [])

    def get_unique_constraints(self, table_name):
        return self._uniques.get(table_name, [])

    def get_check_constraints(self, table_name):
        return self._checks.get(table_name, [])

    def get_pk_constraint(self, table_name):
        return {"constrained_columns": []}


class _FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


class _FakeConnection:
    def __init__(self, scalar_values):
        self._scalar_values = list(scalar_values)
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execution_options(self, **_kwargs):
        return self

    def execute(self, statement, *_args, **_kwargs):
        self.statements.append(str(statement))
        if self._scalar_values:
            return _FakeScalarResult(self._scalar_values.pop(0))
        return _FakeScalarResult(0)


class _FakeSchemaEngine:
    def __init__(self, connection):
        self._connection = connection
        self.dialect = SimpleNamespace(name="mysql")
        self.url = SimpleNamespace(host="localhost", database="mitienda")

    def connect(self):
        return self._connection


def _local_engine():
    return SimpleNamespace(
        dialect=SimpleNamespace(name="mysql"),
        url=SimpleNamespace(host="localhost", database="mitienda"),
    )


class DatabaseOperationalScriptsTests(unittest.TestCase):
    def test_import_create_tables_no_ejecuta_create_all(self):
        sys.modules.pop("create_tables", None)
        with patch.object(Base.metadata, "create_all") as create_all:
            importlib.import_module("create_tables")

        create_all.assert_not_called()

    def test_create_tables_main_invoca_create_all(self):
        import create_tables

        with patch.object(create_tables, "import_all_models") as import_models:
            with patch.object(create_tables.Base.metadata, "create_all") as create_all:
                with redirect_stdout(io.StringIO()):
                    create_tables.main()

        import_models.assert_called_once_with()
        create_all.assert_called_once_with(bind=create_tables.engine)

    def test_create_tables_main_no_silencia_errores(self):
        import create_tables

        with patch.object(create_tables, "import_all_models"):
            with patch.object(
                create_tables.Base.metadata,
                "create_all",
                side_effect=RuntimeError("fallo"),
            ):
                with self.assertRaises(RuntimeError):
                    with redirect_stdout(io.StringIO()):
                        create_tables.main()

    def test_import_reset_db_no_ejecuta_drop_all(self):
        sys.modules.pop("reset_db", None)
        with patch.object(Base.metadata, "drop_all") as drop_all:
            importlib.import_module("reset_db")

        drop_all.assert_not_called()

    def test_reset_db_sin_confirmacion_explicita_aborta(self):
        import reset_db

        with self.assertRaises(reset_db.ResetDbAbortadoError):
            reset_db.reset_database("NO")

    def test_reset_db_con_destino_no_local_aborta(self):
        import reset_db

        remote_engine = SimpleNamespace(
            dialect=SimpleNamespace(name="mysql"),
            url=SimpleNamespace(host="db.example.com", database="mitienda"),
        )
        with patch.object(reset_db, "engine", remote_engine):
            with self.assertRaises(reset_db.ResetDbAbortadoError):
                reset_db.reset_database(reset_db.CONFIRMACION_DESTRUCTIVA)

    def test_reset_db_con_destino_ambiguo_aborta(self):
        import reset_db

        ambiguous_engine = SimpleNamespace(
            dialect=SimpleNamespace(name="mysql"),
            url=SimpleNamespace(host=None, database=None),
        )
        with patch.object(reset_db, "engine", ambiguous_engine):
            with self.assertRaises(reset_db.ResetDbAbortadoError):
                reset_db.reset_database(reset_db.CONFIRMACION_DESTRUCTIVA)

    def test_reset_db_con_confirmacion_y_destino_local_ejecuta_operaciones(self):
        import reset_db

        fake_engine = _local_engine()
        with patch.object(reset_db, "engine", fake_engine):
            with patch.object(reset_db, "import_all_models") as import_models:
                with patch.object(reset_db.Base.metadata, "drop_all") as drop_all:
                    with patch.object(reset_db.Base.metadata, "create_all") as create_all:
                        with redirect_stdout(io.StringIO()):
                            reset_db.reset_database(reset_db.CONFIRMACION_DESTRUCTIVA)

        import_models.assert_called_once_with()
        drop_all.assert_called_once_with(bind=fake_engine)
        create_all.assert_called_once_with(bind=fake_engine)

    def test_check_database_schema_ok(self):
        import check_database_schema

        metadata = _FakeMetadata({"usuarios": ["id", "email"]})
        inspector = _FakeInspector({"usuarios": ["id", "email"]})

        with patch.object(check_database_schema, "import_all_models") as import_models:
            with redirect_stderr(io.StringIO()):
                result = check_database_schema.check_schema(
                    inspector=inspector,
                    metadata=metadata,
                )

        self.assertTrue(result.ok)
        self.assertEqual(result.metadata_count, 1)
        self.assertEqual(result.physical_count, 1)
        self.assertEqual(result.missing_tables, [])
        self.assertEqual(result.extra_tables, [])
        import_models.assert_called_once_with()
        inspector.create_all.assert_not_called()
        inspector.drop_all.assert_not_called()

    def test_check_database_schema_detecta_tabla_faltante(self):
        import check_database_schema

        metadata = _FakeMetadata({"usuarios": ["id"], "comercios": ["id"]})
        inspector = _FakeInspector({"usuarios": ["id"]})

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(
                inspector=inspector,
                metadata=metadata,
            )

        self.assertFalse(result.ok)
        self.assertEqual(result.missing_tables, ["comercios"])

    def test_check_database_schema_detecta_tabla_extra(self):
        import check_database_schema

        metadata = _FakeMetadata({"usuarios": ["id"]})
        inspector = _FakeInspector({"usuarios": ["id"], "legacy": ["id"]})

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(
                inspector=inspector,
                metadata=metadata,
            )

        self.assertFalse(result.ok)
        self.assertEqual(result.extra_tables, ["legacy"])

    def test_check_database_schema_detecta_columnas(self):
        import check_database_schema

        metadata = _FakeMetadata({"usuarios": ["id", "email"]})
        inspector = _FakeInspector({"usuarios": ["id", "legacy"]})

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(
                inspector=inspector,
                metadata=metadata,
            )

        self.assertFalse(result.ok)
        self.assertEqual(
            result.column_differences["usuarios"]["missing_columns"],
            ["email"],
        )
        self.assertEqual(
            result.column_differences["usuarios"]["extra_columns"],
            ["legacy"],
        )

    def test_check_database_schema_detecta_fk(self):
        import check_database_schema

        metadata = _FakeMetadata(
            {"publicaciones": ["id", "comercio_id"]},
            table_options={
                "publicaciones": {
                    "foreign_keys": [
                        _FakeForeignKeyConstraint(
                            ["comercio_id"],
                            "comercios",
                            ["id"],
                        )
                    ]
                }
            },
        )
        inspector = _FakeInspector({"publicaciones": ["id", "comercio_id"]})

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(
                inspector=inspector,
                metadata=metadata,
            )

        self.assertFalse(result.ok)
        self.assertEqual(
            result.foreign_key_differences["publicaciones"]["missing_foreign_keys"],
            ["comercio_id->comercios(id)"],
        )

    def test_check_database_schema_no_marca_indice_implicito_de_fk(self):
        import check_database_schema

        metadata = _FakeMetadata(
            {"seguidores": ["id", "comercio_id"]},
            table_options={
                "seguidores": {
                    "foreign_keys": [
                        _FakeForeignKeyConstraint(
                            ["comercio_id"],
                            "comercios",
                            ["id"],
                        )
                    ]
                }
            },
        )
        inspector = _FakeInspector(
            {"seguidores": ["id", "comercio_id"]},
            foreign_keys={
                "seguidores": [
                    {
                        "constrained_columns": ["comercio_id"],
                        "referred_table": "comercios",
                        "referred_columns": ["id"],
                    }
                ]
            },
            indexes={
                "seguidores": [
                    {"column_names": ["comercio_id"], "unique": False}
                ]
            },
        )

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(
                inspector=inspector,
                metadata=metadata,
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.index_differences, {})

    def test_check_database_schema_detecta_indice(self):
        import check_database_schema

        metadata = _FakeMetadata(
            {"publicaciones": ["id", "comercio_id"]},
            table_options={
                "publicaciones": {
                    "indexes": [_FakeIndex(["comercio_id"])]
                }
            },
        )
        inspector = _FakeInspector({"publicaciones": ["id", "comercio_id"]})

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(
                inspector=inspector,
                metadata=metadata,
            )

        self.assertFalse(result.ok)
        self.assertEqual(
            result.index_differences["publicaciones"]["missing_indexes"],
            ["index:comercio_id"],
        )

    def test_check_database_schema_detecta_unique(self):
        import check_database_schema

        metadata = _FakeMetadata(
            {"contenido_denuncias": ["usuario_id", "recurso_tipo", "recurso_id", "motivo"]},
            table_options={
                "contenido_denuncias": {
                    "uniques": [
                        UniqueConstraint(
                            ["usuario_id", "recurso_tipo", "recurso_id", "motivo"]
                        )
                    ]
                }
            },
        )
        inspector = _FakeInspector(
            {"contenido_denuncias": ["usuario_id", "recurso_tipo", "recurso_id", "motivo"]}
        )

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(
                inspector=inspector,
                metadata=metadata,
            )

        self.assertFalse(result.ok)
        self.assertEqual(
            result.unique_differences["contenido_denuncias"]["missing_uniques"],
            ["usuario_id,recurso_tipo,recurso_id,motivo"],
        )

    def _metadata_with_contract_column(
        self,
        *,
        column_type=String(255),
        nullable=False,
        server_default=None,
        check_expression=None,
    ):
        metadata = MetaData()
        constraints = []
        if check_expression is not None:
            constraints.append(
                CheckConstraint(check_expression, name="ck_users_contract")
            )
        Table(
            "users",
            metadata,
            Column("id", Integer, primary_key=True),
            Column(
                "contract",
                column_type,
                nullable=nullable,
                server_default=server_default,
            ),
            *constraints,
        )
        return metadata

    def test_check_database_schema_detecta_nullability(self):
        import check_database_schema

        metadata = self._metadata_with_contract_column(nullable=False)
        inspector = _FakeInspector(
            {"users": [
                {"name": "id", "type": Integer(), "nullable": False, "default": None},
                {"name": "contract", "type": VARCHAR(255), "nullable": True, "default": None},
            ]}
        )

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(inspector=inspector, metadata=metadata)

        self.assertEqual(
            result.nullability_differences["users"]["contract"],
            {"metadata": False, "physical": True},
        )

    def test_check_database_schema_detecta_longitud_varchar(self):
        import check_database_schema

        metadata = self._metadata_with_contract_column(column_type=String(255))
        inspector = _FakeInspector(
            {"users": [
                {"name": "id", "type": Integer(), "nullable": False, "default": None},
                {"name": "contract", "type": VARCHAR(128), "nullable": False, "default": None},
            ]}
        )

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(inspector=inspector, metadata=metadata)

        self.assertEqual(
            result.type_differences["users"]["contract"],
            {"metadata": "string(255)", "physical": "string(128)"},
        )

    def test_check_database_schema_detecta_server_default(self):
        import check_database_schema

        metadata = self._metadata_with_contract_column(server_default=text("'active'"))
        inspector = _FakeInspector(
            {"users": [
                {"name": "id", "type": Integer(), "nullable": False, "default": None},
                {"name": "contract", "type": VARCHAR(255), "nullable": False, "default": "'disabled'"},
            ]}
        )

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(inspector=inspector, metadata=metadata)

        self.assertEqual(
            result.default_differences["users"]["contract"],
            {"metadata": "active", "physical": "disabled"},
        )

    def test_check_database_schema_detecta_check_distinto(self):
        import check_database_schema

        metadata = self._metadata_with_contract_column(
            check_expression="contract IN ('active', 'disabled')"
        )
        inspector = _FakeInspector(
            {"users": [
                {"name": "id", "type": Integer(), "nullable": False, "default": None},
                {"name": "contract", "type": VARCHAR(255), "nullable": False, "default": None},
            ]},
            checks={"users": [{
                "name": "ck_users_contract",
                "sqltext": "(`contract` in (_utf8mb4'active'))",
            }]},
        )

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(inspector=inspector, metadata=metadata)

        self.assertIn("ck_users_contract", result.check_differences["users"]["changed_checks"])

    def test_check_database_schema_normaliza_equivalencias_mysql(self):
        import check_database_schema

        metadata = MetaData()
        Table(
            "users",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("enabled", Boolean, nullable=False, server_default=text("true")),
            Column("score", Float, nullable=False),
            CheckConstraint(
                "NOT (disabled_at IS NOT NULL AND deleted_at IS NOT NULL)",
                name="ck_users_terminal",
            ),
            CheckConstraint(
                "disabled_at IS NULL OR disabled_at IN (1, 2)",
                name="ck_users_reason",
            ),
            Column("disabled_at", Integer),
            Column("deleted_at", Integer),
        )
        inspector = _FakeInspector(
            {"users": [
                {"name": "id", "type": Integer(), "nullable": False, "default": None},
                {"name": "enabled", "type": TINYINT(display_width=1), "nullable": False, "default": "'1'"},
                {"name": "score", "type": DOUBLE(), "nullable": False, "default": None},
                {"name": "disabled_at", "type": Integer(), "nullable": True, "default": None},
                {"name": "deleted_at", "type": Integer(), "nullable": True, "default": None},
            ]},
            checks={"users": [{
                "name": "ck_users_terminal",
                "sqltext": "((`disabled_at` is null) or (`deleted_at` is null))",
            }, {
                "name": "ck_users_reason",
                "sqltext": "((`disabled_at` is null) or (`disabled_at` in (1,2)))",
            }]},
        )

        with patch.object(check_database_schema, "import_all_models"):
            result = check_database_schema.check_schema(inspector=inspector, metadata=metadata)

        self.assertTrue(result.ok, result)

    def test_add_comercios_rubro_fk_import_no_ejecuta_alter(self):
        sys.modules.pop("add_comercios_rubro_fk", None)
        connection = _FakeConnection([0, 0])
        with patch("app.core.database.engine", _FakeSchemaEngine(connection)):
            importlib.import_module("add_comercios_rubro_fk")

        self.assertEqual(connection.statements, [])

    def test_add_comercios_rubro_fk_requiere_confirmacion(self):
        import add_comercios_rubro_fk

        with self.assertRaises(add_comercios_rubro_fk.SchemaAlignmentError):
            add_comercios_rubro_fk.apply_alignment(None)

    def test_add_comercios_rubro_fk_aborta_con_huerfanos(self):
        import add_comercios_rubro_fk

        connection = _FakeConnection([0, 2])
        with patch.object(
            add_comercios_rubro_fk,
            "engine",
            _FakeSchemaEngine(connection),
        ):
            with self.assertRaises(add_comercios_rubro_fk.SchemaAlignmentError):
                add_comercios_rubro_fk.apply_alignment(
                    add_comercios_rubro_fk.APPLY_CONFIRMATION
                )

        self.assertFalse(any("ALTER TABLE comercios" in item for item in connection.statements))

    def test_add_comercios_rubro_fk_idempotente_si_existe(self):
        import add_comercios_rubro_fk

        connection = _FakeConnection([1, 0])
        with patch.object(
            add_comercios_rubro_fk,
            "engine",
            _FakeSchemaEngine(connection),
        ):
            result = add_comercios_rubro_fk.apply_alignment(
                add_comercios_rubro_fk.APPLY_CONFIRMATION
            )

        self.assertEqual(result, "already_exists")
        self.assertFalse(any("ALTER TABLE comercios" in item for item in connection.statements))

    def test_add_comercios_rubro_fk_crea_si_no_existe(self):
        import add_comercios_rubro_fk

        connection = _FakeConnection([0, 0])
        with patch.object(
            add_comercios_rubro_fk,
            "engine",
            _FakeSchemaEngine(connection),
        ):
            result = add_comercios_rubro_fk.apply_alignment(
                add_comercios_rubro_fk.APPLY_CONFIRMATION
            )

        self.assertEqual(result, "created")
        self.assertTrue(any("ALTER TABLE comercios" in item for item in connection.statements))


if __name__ == "__main__":
    unittest.main()
