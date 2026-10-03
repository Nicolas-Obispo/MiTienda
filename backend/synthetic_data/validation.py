"""Certificacion canonica read-only de profiles sinteticos ET100.3."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
import os
import re
from typing import Any, Iterable, Mapping

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.model_registry import import_all_models

from .apply import (
    MATERIALIZABLE_PROFILES,
    SyntheticApplyError,
    _certify_post_apply,
    load_materializer_configuration,
    parse_clock,
    require_fixture_secret,
)
from .blueprint import BlueprintContractError, LogicalBlueprint
from .materializer import MaterializationError, certify_materialized_blueprint_read_only
from .media_recipes import (
    SyntheticMediaContractError,
    media_manifest_sha256,
    media_recipes_for_blueprint,
)
from .scenarios import SUPPORTED_PROFILES, compile_scenario
from .target_guard import EXPECTED_DATABASE, Stage100TargetGuardError


EXPECTED_ROWS = {"smoke": 20, "functional": 93, "representative": 129}
_EMAIL_PATTERN = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_PHONE_PATTERN = re.compile(r"(?<!\w)\+[1-9][0-9]{7,14}(?!\w)")
_WINDOWS_PATH_PATTERN = re.compile(r"(?i)(?:^|\s)[a-z]:[\\/]")
_JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_SECRET_PREFIX_PATTERN = re.compile(
    r"(?i)(?:sk_live_|sk_test_|ghp_|github_pat_|AKIA[0-9A-Z]{12,})"
)
_SENSITIVE_ENVIRONMENT_KEYS = frozenset(
    {
        "SECRET_KEY",
        "RESEND_API_KEY",
        "IDENTITY_RESEND_API_KEY",
        "ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET",
        "PHONE_VERIFICATION_HMAC_SECRET",
        "GOOGLE_OIDC_CLIENT_SECRET",
        "FEEDGO_STAGE100_FIXTURE_SECRET",
    }
)
_SENSITIVE_FIELD_NAMES = frozenset(
    {
        "password_hash",
        "token_digest",
        "subject_digest",
        "code_digest",
        "request_fingerprint",
        "payload_fingerprint",
        "event_fingerprint",
    }
)


class SyntheticValidationError(RuntimeError):
    """La certificacion no puede declarar PASS de forma inequívoca."""


@dataclass(frozen=True)
class SyntheticValidationEvidence:
    status: str
    source: str
    target: str | None
    profile: str
    dataset_version: str
    rows: int
    fingerprint: str
    privacy: str
    media_recipes: int
    media_manifest_sha256: str
    schema_head: bool | None


def _walk_scalars(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str]]:
    if isinstance(value, str):
        yield path, value
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield from _walk_scalars(nested, (*path, str(key)))
        return
    if isinstance(value, (tuple, list, set, frozenset)):
        for index, nested in enumerate(value):
            yield from _walk_scalars(nested, (*path, str(index)))
        return
    inputs = getattr(value, "inputs", None)
    if isinstance(inputs, Mapping):
        yield from _walk_scalars(inputs, (*path, "owner_inputs"))
    invariants = getattr(value, "invariants", None)
    if isinstance(invariants, Mapping):
        yield from _walk_scalars(invariants, (*path, "invariants"))


def _forbidden_secret_values(environment: Mapping[str, str]) -> frozenset[str]:
    return frozenset(
        value
        for key, value in environment.items()
        if (
            key in _SENSITIVE_ENVIRONMENT_KEYS
            or any(marker in key.upper() for marker in ("SECRET", "PASSWORD", "TOKEN", "API_KEY"))
        )
        and isinstance(value, str)
        and len(value) >= 8
    )


def validate_no_contamination(
    blueprint: LogicalBlueprint,
    *,
    environment: Mapping[str, str] | None = None,
) -> None:
    """Falla cerrado ante PII, secretos, URLs, rutas o medios no aprobados."""

    environment = os.environ if environment is None else environment
    forbidden_secrets = _forbidden_secret_values(environment)
    for entity in blueprint.entities:
        for path, value in _walk_scalars(entity.attributes, (entity.alias,)):
            lowered = value.casefold()
            if path and path[-1] in _SENSITIVE_FIELD_NAMES:
                raise SyntheticValidationError("synthetic_contamination_secret_field")
            if value in forbidden_secrets:
                raise SyntheticValidationError("synthetic_contamination_runtime_secret")
            if "-----begin " in lowered or _JWT_PATTERN.search(value) or _SECRET_PREFIX_PATTERN.search(value):
                raise SyntheticValidationError("synthetic_contamination_secret_pattern")
            if (
                "backend/uploads" in lowered
                or "backend\\uploads" in lowered
                or "/uploads" in lowered
                or "\\uploads" in lowered
                or "file://" in lowered
                or lowered.startswith("\\\\")
                or _WINDOWS_PATH_PATTERN.search(value)
            ):
                raise SyntheticValidationError("synthetic_contamination_path")
            if "http://" in lowered or "https://" in lowered:
                raise SyntheticValidationError("synthetic_contamination_external_url")
            for email in _EMAIL_PATTERN.findall(value):
                local, domain = email.rsplit("@", 1)
                if domain.casefold() != "example.com" or "synthetic" not in local.casefold():
                    raise SyntheticValidationError("synthetic_contamination_email")
            for phone in _PHONE_PATTERN.findall(value):
                if phone != "+12025550123":
                    raise SyntheticValidationError("synthetic_contamination_phone")
            if value.startswith("synthetic-media://"):
                # Compilar la receta es la allowlist unica de referencias.
                from .media_recipes import compile_media_recipe

                compile_media_recipe(value)


def _assert_blueprint_contract(blueprint: LogicalBlueprint) -> None:
    expected_rows = EXPECTED_ROWS.get(blueprint.context.profile)
    if expected_rows is None or len(blueprint.entities) != expected_rows:
        raise SyntheticValidationError("synthetic_validation_cardinality_mismatch")
    aliases = {entity.alias for entity in blueprint.entities}
    if len(aliases) != len(blueprint.entities):
        raise SyntheticValidationError("synthetic_validation_alias_duplicate")
    for relation in blueprint.relations:
        if relation.source_alias not in aliases or relation.target_alias not in aliases:
            raise SyntheticValidationError("synthetic_validation_relation_orphan")


def _assert_read_only_sql(statement: str) -> None:
    normalized = " ".join(statement.strip().upper().split())
    first = normalized.split(None, 1)[0] if normalized else ""
    forbidden_select_forms = (
        " INTO OUTFILE",
        " INTO DUMPFILE",
        " FOR UPDATE",
        " LOCK IN SHARE MODE",
        "GET_LOCK(",
        "RELEASE_LOCK(",
    )
    if first not in {"SELECT", "SHOW", "DESCRIBE"} or any(
        marker in normalized for marker in forbidden_select_forms
    ):
        raise SyntheticValidationError("synthetic_validation_write_statement_blocked")


def validate_synthetic_profile(
    *,
    source: str,
    profile: str,
    seed: str,
    dataset_version: str,
    clock_policy: str,
    clock_anchor: str,
    environment: Mapping[str, str] | None = None,
) -> SyntheticValidationEvidence:
    environment = os.environ if environment is None else environment
    if source not in {"blueprint", "mysql"}:
        raise SyntheticValidationError("synthetic_validation_source_invalid")
    if profile not in SUPPORTED_PROFILES:
        raise SyntheticValidationError("synthetic_validation_profile_invalid")
    clock = parse_clock(policy=clock_policy, anchor=clock_anchor)
    blueprint = compile_scenario(
        dataset_version=dataset_version,
        profile=profile,
        seed=seed,
        clock_policy=clock,
    )
    _assert_blueprint_contract(blueprint)
    validate_no_contamination(blueprint, environment=environment)
    recipes = media_recipes_for_blueprint(blueprint)
    manifest_sha256 = media_manifest_sha256(recipes)

    target: str | None = None
    schema_head: bool | None = None
    if source == "mysql":
        if profile not in MATERIALIZABLE_PROFILES:
            raise SyntheticValidationError("synthetic_validation_profile_not_materializable")
        fixture_secret = require_fixture_secret(environment)
        config = load_materializer_configuration(environment)
        if config.materializer_url.database != EXPECTED_DATABASE:
            raise SyntheticValidationError("synthetic_validation_target_invalid")
        import_all_models()
        engine = create_engine(config.materializer_url, pool_pre_ping=True)
        event.listen(
            engine,
            "before_cursor_execute",
            lambda _conn, _cursor, statement, _parameters, _context, _many: (
                _assert_read_only_sql(statement)
            ),
        )
        try:
            with Session(engine, autoflush=False) as session:
                _certify_post_apply(session.connection(), config=config, blueprint=blueprint)
                result = certify_materialized_blueprint_read_only(
                    session,
                    blueprint,
                    fixture_secret=fixture_secret,
                )
                if session.new or session.dirty or session.deleted:
                    raise SyntheticValidationError("synthetic_validation_session_mutated")
                if result.row_count != len(blueprint.entities) or result.fingerprint != blueprint.fingerprint:
                    raise SyntheticValidationError("synthetic_validation_mysql_mismatch")
                session.rollback()
            target = EXPECTED_DATABASE
            schema_head = True
        finally:
            engine.dispose()

    return SyntheticValidationEvidence(
        status="PASS",
        source=source,
        target=target,
        profile=profile,
        dataset_version=dataset_version,
        rows=len(blueprint.entities),
        fingerprint=blueprint.fingerprint,
        privacy="PASS",
        media_recipes=len(recipes),
        media_manifest_sha256=manifest_sha256,
        schema_head=schema_head,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, choices=("blueprint", "mysql"))
    parser.add_argument("--profile", required=True, choices=sorted(SUPPORTED_PROFILES))
    parser.add_argument("--seed", required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--clock-policy", required=True, choices=("fixed_utc_v1",))
    parser.add_argument("--clock-anchor", required=True)
    args = parser.parse_args()
    try:
        evidence = validate_synthetic_profile(
            source=args.source,
            profile=args.profile,
            seed=args.seed,
            dataset_version=args.dataset_version,
            clock_policy=args.clock_policy,
            clock_anchor=args.clock_anchor,
        )
    except (
        BlueprintContractError,
        MaterializationError,
        Stage100TargetGuardError,
        SyntheticApplyError,
        SyntheticMediaContractError,
        SyntheticValidationError,
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(asdict(evidence), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
