"""Apply transaccional y fail-closed de datasets sinteticos ET100.3."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import argparse
import json
import os
from typing import Mapping

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base
from app.core.model_registry import import_all_models
from check_database_schema import check_schema

from .blueprint import BlueprintContractError, ClockPolicy
from .bootstrap import (
    EXPECTED_TABLE_COUNT,
    _assert_no_unexpected_objects,
    _certify_identity,
    _database_metadata,
    _table_counts,
    _unexpected_objects,
    _validate_database_metadata,
)
from .materializer import (
    CommitGuardSession,
    MaterializationError,
    materialize_blueprint,
)
from .scenarios import FUNCTIONAL_PROFILE, SMOKE_PROFILE, compile_scenario
from .target_guard import (
    CredentialRole,
    EXPECTED_DATABASE,
    Stage100TargetGuardError,
    validate_configured_target,
)


FIXTURE_SECRET_ENV = "FEEDGO_STAGE100_FIXTURE_SECRET"
SUPPORTED_CLOCK_POLICY = "fixed_utc_v1"
MATERIALIZABLE_PROFILES = frozenset({SMOKE_PROFILE, FUNCTIONAL_PROFILE})


class SyntheticApplyError(RuntimeError):
    """El apply no puede continuar o su estado final no pudo certificarse."""


@dataclass(frozen=True)
class SyntheticApplyEvidence:
    status: str
    target: str
    profile: str
    dataset_version: str
    rows: int
    fingerprint: str
    reconstructed_fingerprint: str
    schema_head: bool
    transaction_preflight: str
    precommit_certification: str


@dataclass(frozen=True)
class SyntheticMaterializerConfiguration:
    materializer_url: URL
    materializer_username: str


def load_materializer_configuration(
    environment: Mapping[str, str],
) -> SyntheticMaterializerConfiguration:
    username = environment.get("FEEDGO_STAGE100_MATERIALIZER_USER", "")
    url = validate_configured_target(
        environment.get("FEEDGO_STAGE100_MATERIALIZER_DATABASE_URL", ""),
        role=CredentialRole.MATERIALIZER,
        expected_username=username,
    )
    return SyntheticMaterializerConfiguration(
        materializer_url=url,
        materializer_username=username,
    )


def parse_clock(*, policy: str, anchor: str) -> ClockPolicy:
    if policy != SUPPORTED_CLOCK_POLICY:
        raise SyntheticApplyError("synthetic_clock_policy_invalid")
    if not anchor or not anchor.endswith("Z"):
        raise SyntheticApplyError("synthetic_clock_anchor_invalid")
    try:
        parsed = datetime.fromisoformat(anchor[:-1] + "+00:00")
    except ValueError as exc:
        raise SyntheticApplyError("synthetic_clock_anchor_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise SyntheticApplyError("synthetic_clock_anchor_invalid")
    try:
        return ClockPolicy(anchor=parsed, policy=policy)
    except BlueprintContractError as exc:
        raise SyntheticApplyError("synthetic_clock_anchor_invalid") from exc


def require_fixture_secret(environment: Mapping[str, str]) -> str:
    secret = environment.get(FIXTURE_SECRET_ENV, "")
    runtime_secrets = {
        value
        for value in (
            settings.SECRET_KEY,
            settings.RESEND_API_KEY,
            settings.IDENTITY_RESEND_API_KEY,
            settings.ACCOUNT_ACTION_RATE_LIMIT_HMAC_SECRET,
            settings.PHONE_VERIFICATION_HMAC_SECRET,
            settings.GOOGLE_OIDC_CLIENT_SECRET,
        )
        if value
    }
    if secret in runtime_secrets:
        raise SyntheticApplyError("synthetic_fixture_secret_reuses_runtime_secret")
    if len(secret) < 32:
        raise SyntheticApplyError("synthetic_fixture_secret_missing_or_weak")
    return secret


def _expected_counts(blueprint) -> dict[str, int]:
    return dict(Counter(entity.entity_type for entity in blueprint.entities))


def _certify_empty_head_schema(connection, *, config) -> None:
    _certify_identity(
        connection,
        config=config.materializer_url,
        role=CredentialRole.MATERIALIZER,
        username=config.materializer_username,
    )
    _validate_database_metadata(_database_metadata(connection))
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    expected_tables = set(Base.metadata.tables)
    if (
        len(tables) != EXPECTED_TABLE_COUNT
        or tables != expected_tables
        or len(expected_tables) != EXPECTED_TABLE_COUNT
    ):
        raise SyntheticApplyError("synthetic_schema_table_set_mismatch")
    _assert_no_unexpected_objects(_unexpected_objects(connection, inspector))
    schema = check_schema(inspector=inspector, metadata=Base.metadata)
    if not schema.ok:
        raise SyntheticApplyError("synthetic_schema_head_mismatch")
    counts = _table_counts(connection, tables)
    if set(counts) != expected_tables or any(counts.values()):
        raise SyntheticApplyError("synthetic_database_not_empty")


def _certify_post_apply(connection, *, config, blueprint) -> None:
    _certify_identity(
        connection,
        config=config.materializer_url,
        role=CredentialRole.MATERIALIZER,
        username=config.materializer_username,
    )
    _validate_database_metadata(_database_metadata(connection))
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    expected_tables = set(Base.metadata.tables)
    if tables != expected_tables or len(tables) != EXPECTED_TABLE_COUNT:
        raise SyntheticApplyError("synthetic_postcheck_table_set_mismatch")
    _assert_no_unexpected_objects(_unexpected_objects(connection, inspector))
    if not check_schema(inspector=inspector, metadata=Base.metadata).ok:
        raise SyntheticApplyError("synthetic_postcheck_schema_mismatch")
    counts = _table_counts(connection, tables)
    expected_counts = _expected_counts(blueprint)
    for table in expected_tables:
        if counts[table] != expected_counts.get(table, 0):
            raise SyntheticApplyError(f"synthetic_postcheck_count_mismatch:{table}")


def apply_synthetic_dataset(
    *,
    profile: str,
    seed: str,
    dataset_version: str,
    clock_policy: str,
    clock_anchor: str,
    environment: Mapping[str, str] | None = None,
) -> SyntheticApplyEvidence:
    """Ejecuta el primer apply sobre un schema HEAD necesariamente vacio."""

    environment = os.environ if environment is None else environment
    if profile not in MATERIALIZABLE_PROFILES:
        raise SyntheticApplyError("synthetic_profile_not_allowed")
    if not seed or not dataset_version or not clock_policy or not clock_anchor:
        raise SyntheticApplyError("synthetic_explicit_contract_required")
    fixture_secret = require_fixture_secret(environment)
    clock = parse_clock(policy=clock_policy, anchor=clock_anchor)
    config = load_materializer_configuration(environment)
    if (
        config.materializer_username != "feedgo_stage100_materializer"
        or config.materializer_url.username != "feedgo_stage100_materializer"
        or config.materializer_url.database != EXPECTED_DATABASE
    ):
        raise SyntheticApplyError("synthetic_materializer_identity_invalid")

    import_all_models()
    blueprint = compile_scenario(
        dataset_version=dataset_version,
        profile=profile,
        seed=seed,
        clock_policy=clock,
    )
    expected_rows = {"smoke": 20, "functional": 93}[profile]
    if len(blueprint.entities) != expected_rows:
        raise SyntheticApplyError("synthetic_profile_cardinality_mismatch")

    engine = create_engine(config.materializer_url, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            def transaction_preflight(guarded: CommitGuardSession) -> None:
                _certify_empty_head_schema(guarded.connection(), config=config)

            def transaction_precommit(guarded: CommitGuardSession) -> None:
                _certify_post_apply(
                    guarded.connection(), config=config, blueprint=blueprint
                )

            result = materialize_blueprint(
                session,
                blueprint,
                fixture_secret=fixture_secret,
                transaction_preflight=transaction_preflight,
                transaction_precommit=transaction_precommit,
            )
        if (
            result.row_count != expected_rows
            or result.fingerprint != blueprint.fingerprint
            or result.reconstructed_fingerprint != blueprint.fingerprint
        ):
            raise SyntheticApplyError("synthetic_materializer_evidence_mismatch")

    finally:
        engine.dispose()

    return SyntheticApplyEvidence(
        status="PASS",
        target=EXPECTED_DATABASE,
        profile=profile,
        dataset_version=dataset_version,
        rows=expected_rows,
        fingerprint=result.fingerprint,
        reconstructed_fingerprint=result.reconstructed_fingerprint,
        schema_head=True,
        transaction_preflight="PASS",
        precommit_certification="PASS",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, choices=sorted(MATERIALIZABLE_PROFILES))
    parser.add_argument("--seed", required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--clock-policy", required=True)
    parser.add_argument("--clock-anchor", required=True)
    args = parser.parse_args()
    try:
        evidence = apply_synthetic_dataset(
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
    ) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(asdict(evidence), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
