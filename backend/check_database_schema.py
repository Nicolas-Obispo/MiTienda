"""
check_database_schema.py
------------------------
Verificacion read-only entre Base.metadata y la base fisica configurada.

No crea, modifica ni elimina tablas o datos.
"""

from dataclasses import dataclass, field

from sqlalchemy import inspect

from app.core.database import Base, engine
from app.core.model_registry import import_all_models


@dataclass(frozen=True)
class SchemaCheckResult:
    metadata_count: int
    physical_count: int
    missing_tables: list[str]
    extra_tables: list[str]
    column_differences: dict[str, dict[str, list[str]]]
    foreign_key_differences: dict[str, dict[str, list[str]]] = field(
        default_factory=dict
    )
    index_differences: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    unique_differences: dict[str, dict[str, list[str]]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return (
            not self.missing_tables
            and not self.extra_tables
            and not self.column_differences
            and not self.foreign_key_differences
            and not self.index_differences
            and not self.unique_differences
        )


def _column_names(columns: list[dict]) -> set[str]:
    return {column["name"] for column in columns}


def _metadata_foreign_keys(table) -> set[str]:
    signatures = set()
    for constraint in getattr(table, "foreign_key_constraints", set()):
        constrained = ",".join(column.name for column in constraint.columns)
        referred_table = getattr(constraint.referred_table, "name", "")
        referred = ",".join(
            element.column.name for element in getattr(constraint, "elements", [])
        )
        signatures.add(f"{constrained}->{referred_table}({referred})")
    return signatures


def _metadata_foreign_key_columns(table) -> set[str]:
    return {
        ",".join(column.name for column in constraint.columns)
        for constraint in getattr(table, "foreign_key_constraints", set())
    }


def _physical_foreign_keys(inspector, table_name: str) -> set[str]:
    signatures = set()
    for fk in inspector.get_foreign_keys(table_name):
        constrained = ",".join(fk.get("constrained_columns") or [])
        referred_table = fk.get("referred_table") or ""
        referred = ",".join(fk.get("referred_columns") or [])
        signatures.add(f"{constrained}->{referred_table}({referred})")
    return signatures


def _physical_foreign_key_columns(inspector, table_name: str) -> set[str]:
    return {
        ",".join(fk.get("constrained_columns") or [])
        for fk in inspector.get_foreign_keys(table_name)
    }


def _metadata_indexes(table) -> set[str]:
    signatures = set()
    primary_key_columns = {
        column.name for column in getattr(getattr(table, "primary_key", None), "columns", [])
    }
    for index in getattr(table, "indexes", set()):
        if getattr(index, "unique", False):
            continue
        index_columns = [column.name for column in index.columns]
        if set(index_columns) == primary_key_columns:
            continue
        columns = ",".join(index_columns)
        signatures.add(f"index:{columns}")
    return signatures


def _physical_indexes(
    inspector,
    table_name: str,
    metadata_index_signatures: set[str] | None = None,
) -> set[str]:
    signatures = set()
    metadata_index_signatures = metadata_index_signatures or set()
    primary_key = inspector.get_pk_constraint(table_name) or {}
    primary_key_columns = set(primary_key.get("constrained_columns") or [])
    physical_fk_columns = _physical_foreign_key_columns(inspector, table_name)
    for index in inspector.get_indexes(table_name):
        if index.get("unique"):
            continue
        index_columns = index.get("column_names") or []
        if set(index_columns) == primary_key_columns:
            continue
        columns = ",".join(index_columns)
        signature = f"index:{columns}"
        if columns in physical_fk_columns and signature not in metadata_index_signatures:
            continue
        signatures.add(signature)
    return signatures


def _metadata_uniques(table) -> set[str]:
    signatures = set()
    for constraint in getattr(table, "constraints", set()):
        if constraint.__class__.__name__ == "UniqueConstraint":
            columns = ",".join(column.name for column in constraint.columns)
            signatures.add(columns)
    for column in table.columns:
        if getattr(column, "unique", False):
            signatures.add(column.name)
    return signatures


def _physical_uniques(inspector, table_name: str) -> set[str]:
    signatures = set()
    for constraint in inspector.get_unique_constraints(table_name):
        signatures.add(",".join(constraint.get("column_names") or []))
    return signatures


def _diff_signatures(metadata_values: set[str], physical_values: set[str]):
    missing = sorted(metadata_values - physical_values)
    extra = sorted(physical_values - metadata_values)
    return missing, extra


def check_schema(inspector=None, metadata=None) -> SchemaCheckResult:
    import_all_models()

    metadata = metadata or Base.metadata
    inspector = inspector or inspect(engine)

    metadata_tables = set(metadata.tables.keys())
    physical_tables = set(inspector.get_table_names())
    common_tables = metadata_tables & physical_tables

    column_differences: dict[str, dict[str, list[str]]] = {}
    foreign_key_differences: dict[str, dict[str, list[str]]] = {}
    index_differences: dict[str, dict[str, list[str]]] = {}
    unique_differences: dict[str, dict[str, list[str]]] = {}
    for table_name in sorted(common_tables):
        table = metadata.tables[table_name]
        metadata_columns = set(table.columns.keys())
        physical_columns = _column_names(inspector.get_columns(table_name))
        missing_columns = sorted(metadata_columns - physical_columns)
        extra_columns = sorted(physical_columns - metadata_columns)
        if missing_columns or extra_columns:
            column_differences[table_name] = {
                "missing_columns": missing_columns,
                "extra_columns": extra_columns,
            }

        missing_fks, extra_fks = _diff_signatures(
            _metadata_foreign_keys(table),
            _physical_foreign_keys(inspector, table_name),
        )
        if missing_fks or extra_fks:
            foreign_key_differences[table_name] = {
                "missing_foreign_keys": missing_fks,
                "extra_foreign_keys": extra_fks,
            }

        metadata_indexes = _metadata_indexes(table)
        missing_indexes, extra_indexes = _diff_signatures(
            metadata_indexes,
            _physical_indexes(
                inspector,
                table_name,
                metadata_index_signatures=metadata_indexes,
            ),
        )
        if missing_indexes or extra_indexes:
            index_differences[table_name] = {
                "missing_indexes": missing_indexes,
                "extra_indexes": extra_indexes,
            }

        missing_uniques, extra_uniques = _diff_signatures(
            _metadata_uniques(table),
            _physical_uniques(inspector, table_name),
        )
        if missing_uniques or extra_uniques:
            unique_differences[table_name] = {
                "missing_uniques": missing_uniques,
                "extra_uniques": extra_uniques,
            }

    return SchemaCheckResult(
        metadata_count=len(metadata_tables),
        physical_count=len(physical_tables),
        missing_tables=sorted(metadata_tables - physical_tables),
        extra_tables=sorted(physical_tables - metadata_tables),
        column_differences=column_differences,
        foreign_key_differences=foreign_key_differences,
        index_differences=index_differences,
        unique_differences=unique_differences,
    )


def _safe_database_target() -> str:
    host = engine.url.host or "<sin-host>"
    database = engine.url.database or "<sin-base>"
    return f"{engine.dialect.name}://{host}/{database}"


def print_result(result: SchemaCheckResult) -> None:
    print(f"Destino: {_safe_database_target()}")
    print(f"Tablas metadata: {result.metadata_count}")
    print(f"Tablas fisicas: {result.physical_count}")
    print(
        "Tablas faltantes: "
        + (", ".join(result.missing_tables) if result.missing_tables else "ninguna")
    )
    print(
        "Tablas extra: "
        + (", ".join(result.extra_tables) if result.extra_tables else "ninguna")
    )
    if result.column_differences:
        print("Diferencias de columnas:")
        for table_name, diff in result.column_differences.items():
            print(
                f"- {table_name}: faltantes={diff['missing_columns']}; "
                f"extra={diff['extra_columns']}"
            )
    else:
        print("Diferencias de columnas: ninguna")
    if result.foreign_key_differences:
        print("Diferencias de claves foraneas:")
        for table_name, diff in result.foreign_key_differences.items():
            print(
                f"- {table_name}: faltantes={diff['missing_foreign_keys']}; "
                f"extra={diff['extra_foreign_keys']}"
            )
    else:
        print("Diferencias de claves foraneas: ninguna")
    if result.index_differences:
        print("Diferencias de indices:")
        for table_name, diff in result.index_differences.items():
            print(
                f"- {table_name}: faltantes={diff['missing_indexes']}; "
                f"extra={diff['extra_indexes']}"
            )
    else:
        print("Diferencias de indices: ninguna")
    if result.unique_differences:
        print("Diferencias de restricciones unicas:")
        for table_name, diff in result.unique_differences.items():
            print(
                f"- {table_name}: faltantes={diff['missing_uniques']}; "
                f"extra={diff['extra_uniques']}"
            )
    else:
        print("Diferencias de restricciones unicas: ninguna")


def main() -> int:
    result = check_schema()
    print_result(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
