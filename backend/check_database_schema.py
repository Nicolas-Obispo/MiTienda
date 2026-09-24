"""
check_database_schema.py
------------------------
Verificacion read-only entre Base.metadata y la base fisica configurada.

No crea, modifica ni elimina tablas o datos.
"""

from dataclasses import asdict, dataclass, field
import re

from sqlalchemy import inspect
from sqlalchemy.sql import sqltypes

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
    nullability_differences: dict[str, dict[str, dict[str, bool]]] = field(
        default_factory=dict
    )
    type_differences: dict[str, dict[str, dict[str, str]]] = field(
        default_factory=dict
    )
    default_differences: dict[str, dict[str, dict[str, str | None]]] = field(
        default_factory=dict
    )
    check_differences: dict[str, dict[str, object]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return (
            not self.missing_tables
            and not self.extra_tables
            and not self.column_differences
            and not self.foreign_key_differences
            and not self.index_differences
            and not self.unique_differences
            and not self.nullability_differences
            and not self.type_differences
            and not self.default_differences
            and not self.check_differences
        )


def schema_result_to_dict(result: SchemaCheckResult) -> dict[str, object]:
    """Serializa evidencia estable para manifiestos de backup/restore."""

    value = asdict(result)
    value["ok"] = result.ok
    return value


def _column_names(columns: list[dict]) -> set[str]:
    return {column["name"] for column in columns}


def _type_signature(column_type) -> str:
    """Normaliza familias que MySQL introspecta con clases equivalentes."""

    if isinstance(column_type, sqltypes.Boolean) or (
        column_type.__class__.__name__.lower() == "tinyint"
        and getattr(column_type, "display_width", None) == 1
    ):
        return "boolean"
    if isinstance(column_type, sqltypes.Text):
        return "text"
    if isinstance(column_type, sqltypes.String):
        return f"string({getattr(column_type, 'length', None) or '*'})"
    if isinstance(column_type, sqltypes.BigInteger):
        return "bigint"
    if isinstance(column_type, sqltypes.SmallInteger):
        return "smallint"
    if isinstance(column_type, sqltypes.Integer):
        return "integer"
    if isinstance(column_type, sqltypes.Float):
        return "float"
    if isinstance(column_type, sqltypes.Numeric):
        return (
            f"numeric({getattr(column_type, 'precision', None)},"
            f"{getattr(column_type, 'scale', None)})"
        )
    if isinstance(column_type, sqltypes.DateTime):
        return "datetime"
    if isinstance(column_type, sqltypes.Date):
        return "date"
    if isinstance(column_type, sqltypes.Time):
        return "time"
    if isinstance(column_type, sqltypes.JSON):
        return "json"
    if isinstance(column_type, sqltypes.LargeBinary):
        return f"binary({getattr(column_type, 'length', None) or '*'})"
    return column_type.__class__.__name__.lower()


def _strip_wrapping_parentheses(value: str) -> str:
    while value.startswith("(") and value.endswith(")"):
        depth = 0
        wraps_all = True
        for index, character in enumerate(value):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and index != len(value) - 1:
                    wraps_all = False
                    break
        if not wraps_all or depth != 0:
            break
        value = value[1:-1].strip()
    return value


def _normalize_default(value) -> str | None:
    if value is None:
        return None
    value = getattr(value, "arg", value)
    normalized = str(value).strip().lower().replace("`", "")
    normalized = normalized.replace("_utf8mb4", "")
    normalized = _strip_wrapping_parentheses(normalized)
    normalized = re.sub(r"\bnow\(\)", "current_timestamp", normalized)
    normalized = re.sub(r"\bcurrent_timestamp\(\)", "current_timestamp", normalized)
    normalized = re.sub(r"\btrue\b", "1", normalized)
    normalized = re.sub(r"\bfalse\b", "0", normalized)
    if re.fullmatch(r"'[^']*'", normalized):
        normalized = normalized[1:-1]
    return re.sub(r"\s+", " ", normalized).strip()


def _normalize_check(value: object) -> str:
    normalized = str(value).lower().replace("`", "")
    normalized = normalized.replace("_utf8mb4", "")
    normalized = re.sub(r"\s+", "", normalized)
    normalized = normalized.replace("!=", "<>")
    normalized = re.sub(r"\btrue\b", "1", normalized)
    normalized = re.sub(r"\bfalse\b", "0", normalized)
    # MySQL reescribe NOT (a IS NOT NULL AND b IS NOT NULL) mediante De Morgan.
    normalized = re.sub(
        r"not\(([a-z0-9_]+)isnotnulland([a-z0-9_]+)isnotnull\)",
        r"(\1isnullor\2isnull)",
        normalized,
    )
    atomic = re.compile(
        r"\(([a-z0-9_]+(?:isnull|isnotnull|in\([^()]*\)|"
        r"(?:<>|<=|>=|=|<|>)[a-z0-9_'\.\-]+))\)"
    )
    previous = None
    while previous != normalized:
        previous = normalized
        normalized = atomic.sub(r"\1", normalized)
        normalized = _strip_wrapping_parentheses(normalized)
    return normalized


def _metadata_checks(table) -> tuple[dict[str, str], set[str]]:
    checks: dict[str, str] = {}
    ignored: set[str] = set()
    for constraint in getattr(table, "constraints", set()):
        if constraint.__class__.__name__ != "CheckConstraint":
            continue
        name = getattr(constraint, "name", None)
        if not name:
            continue
        expression = str(getattr(constraint, "sqltext", ""))
        # SQLAlchemy Enum(native_enum=False) usa placeholders internos que no
        # pueden compararse literalmente con la expresion introspectada.
        if "__[POSTCOMPILE" in expression:
            ignored.add(name)
            continue
        checks[name] = _normalize_check(expression)
    return checks, ignored


def _physical_checks(inspector, table_name: str, ignored: set[str]) -> dict[str, str]:
    return {
        item["name"]: _normalize_check(item.get("sqltext", ""))
        for item in inspector.get_check_constraints(table_name)
        if item.get("name") and item["name"] not in ignored
    }


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
    nullability_differences: dict[str, dict[str, dict[str, bool]]] = {}
    type_differences: dict[str, dict[str, dict[str, str]]] = {}
    default_differences: dict[str, dict[str, dict[str, str | None]]] = {}
    check_differences: dict[str, dict[str, object]] = {}
    for table_name in sorted(common_tables):
        table = metadata.tables[table_name]
        metadata_columns_by_name = {column.name: column for column in table.columns}
        physical_columns_by_name = {
            column["name"]: column for column in inspector.get_columns(table_name)
        }
        metadata_columns = set(table.columns.keys())
        physical_columns = set(physical_columns_by_name)
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

        for column_name in sorted(metadata_columns & physical_columns):
            metadata_column = metadata_columns_by_name[column_name]
            physical_column = physical_columns_by_name[column_name]

            if "nullable" in physical_column and (
                bool(metadata_column.nullable) != bool(physical_column["nullable"])
            ):
                nullability_differences.setdefault(table_name, {})[column_name] = {
                    "metadata": bool(metadata_column.nullable),
                    "physical": bool(physical_column["nullable"]),
                }

            if "type" in physical_column:
                metadata_type = _type_signature(metadata_column.type)
                physical_type = _type_signature(physical_column["type"])
                if metadata_type != physical_type:
                    type_differences.setdefault(table_name, {})[column_name] = {
                        "metadata": metadata_type,
                        "physical": physical_type,
                    }

            if "default" in physical_column:
                metadata_default = _normalize_default(metadata_column.server_default)
                physical_default = _normalize_default(physical_column.get("default"))
                if metadata_default != physical_default:
                    default_differences.setdefault(table_name, {})[column_name] = {
                        "metadata": metadata_default,
                        "physical": physical_default,
                    }

        metadata_checks, ignored_checks = _metadata_checks(table)
        physical_checks = _physical_checks(inspector, table_name, ignored_checks)
        missing_checks = sorted(set(metadata_checks) - set(physical_checks))
        extra_checks = sorted(set(physical_checks) - set(metadata_checks))
        changed_checks = {
            name: {
                "metadata": metadata_checks[name],
                "physical": physical_checks[name],
            }
            for name in sorted(set(metadata_checks) & set(physical_checks))
            if metadata_checks[name] != physical_checks[name]
        }
        if missing_checks or extra_checks or changed_checks:
            check_differences[table_name] = {
                "missing_checks": missing_checks,
                "extra_checks": extra_checks,
                "changed_checks": changed_checks,
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
        nullability_differences=nullability_differences,
        type_differences=type_differences,
        default_differences=default_differences,
        check_differences=check_differences,
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
    if result.nullability_differences:
        print("Diferencias de nullability:")
        for table_name, diff in result.nullability_differences.items():
            print(f"- {table_name}: {diff}")
    else:
        print("Diferencias de nullability: ninguna")
    if result.type_differences:
        print("Diferencias de tipos/longitudes:")
        for table_name, diff in result.type_differences.items():
            print(f"- {table_name}: {diff}")
    else:
        print("Diferencias de tipos/longitudes: ninguna")
    if result.default_differences:
        print("Diferencias de server defaults:")
        for table_name, diff in result.default_differences.items():
            print(f"- {table_name}: {diff}")
    else:
        print("Diferencias de server defaults: ninguna")
    if result.check_differences:
        print("Diferencias de check constraints:")
        for table_name, diff in result.check_differences.items():
            print(f"- {table_name}: {diff}")
    else:
        print("Diferencias de check constraints: ninguna")


def main() -> int:
    result = check_schema()
    print_result(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
