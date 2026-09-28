"""Preflight read-only para el retiro controlado de credenciales legacy.

Este modulo clasifica material de credenciales ya persistido. No corrige,
crea, actualiza ni expone hashes, y su resultado agregado esta pensado para
bloquear cualquier backfill posterior cuando la poblacion no sea segura.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.security import password_hash_is_usable
from app.modules.users.models.identity_models import PasswordCredential
from app.modules.users.models.usuarios_models import Usuario


PREFLIGHT_PASS = "PASS"
PREFLIGHT_BLOCK = "BLOCK"


class LegacyPasswordPreflightBlocked(RuntimeError):
    """Una migracion posterior no puede continuar con este resultado."""


@dataclass(frozen=True)
class LegacyPasswordPreflightReport:
    status: str
    total_users: int
    total_password_accounts: int
    without_password: int
    credential_only: int
    dual_equivalent: int
    legacy_only: int
    divergent: int
    invalid: int
    missing_email_canonical: int
    classification_complete: bool
    blockers: tuple[str, ...]
    without_password_missing_email_canonical: int = 0
    credential_only_missing_email_canonical: int = 0
    dual_equivalent_missing_email_canonical: int = 0
    legacy_only_missing_email_canonical: int = 0
    divergent_missing_email_canonical: int = 0
    invalid_missing_email_canonical: int = 0
    legacy_only_with_email_canonical: int = 0

    def safe_summary(self) -> dict[str, object]:
        """Devuelve exclusivamente conteos y codigos operativos seguros."""

        return {
            "status": self.status,
            "total_users": self.total_users,
            "total_password_accounts": self.total_password_accounts,
            "without_password": self.without_password,
            "credential_only": self.credential_only,
            "dual_equivalent": self.dual_equivalent,
            "legacy_only": self.legacy_only,
            "divergent": self.divergent,
            "invalid": self.invalid,
            "missing_email_canonical": self.missing_email_canonical,
            "without_password_missing_email_canonical": (
                self.without_password_missing_email_canonical
            ),
            "credential_only_missing_email_canonical": (
                self.credential_only_missing_email_canonical
            ),
            "dual_equivalent_missing_email_canonical": (
                self.dual_equivalent_missing_email_canonical
            ),
            "legacy_only_missing_email_canonical": (
                self.legacy_only_missing_email_canonical
            ),
            "divergent_missing_email_canonical": (
                self.divergent_missing_email_canonical
            ),
            "invalid_missing_email_canonical": (
                self.invalid_missing_email_canonical
            ),
            "legacy_only_with_email_canonical": (
                self.legacy_only_with_email_canonical
            ),
            "classification_complete": self.classification_complete,
            "blockers": list(self.blockers),
        }


def _blocked_read_report() -> LegacyPasswordPreflightReport:
    return LegacyPasswordPreflightReport(
        status=PREFLIGHT_BLOCK,
        total_users=0,
        total_password_accounts=0,
        without_password=0,
        credential_only=0,
        dual_equivalent=0,
        legacy_only=0,
        divergent=0,
        invalid=0,
        missing_email_canonical=0,
        classification_complete=False,
        blockers=("preflight_read_error",),
    )


def _credential_is_usable(
    *, credential_present: bool, password_hash: str | None, hash_version: str | None
) -> bool:
    return bool(
        credential_present
        and hash_version == "bcrypt"
        and password_hash_is_usable(password_hash)
    )


def preflight_legacy_password_credentials(db: Session) -> LegacyPasswordPreflightReport:
    """Clasifica la poblacion sin escribir ni devolver material sensible."""

    try:
        rows = (
            db.query(
                Usuario.email_canonical,
                Usuario.hashed_password,
                PasswordCredential.usuario_id,
                PasswordCredential.password_hash,
                PasswordCredential.hash_version,
            )
            .outerjoin(
                PasswordCredential,
                PasswordCredential.usuario_id == Usuario.id,
            )
            .all()
        )
    except Exception:
        return _blocked_read_report()

    counts = {
        "without_password": 0,
        "credential_only": 0,
        "dual_equivalent": 0,
        "legacy_only": 0,
        "divergent": 0,
        "invalid": 0,
        "missing_email_canonical": 0,
        "without_password_missing_email_canonical": 0,
        "credential_only_missing_email_canonical": 0,
        "dual_equivalent_missing_email_canonical": 0,
        "legacy_only_missing_email_canonical": 0,
        "divergent_missing_email_canonical": 0,
        "invalid_missing_email_canonical": 0,
    }

    for canonical, legacy_hash, credential_user_id, credential_hash, hash_version in rows:
        if canonical is None:
            counts["missing_email_canonical"] += 1

        credential_present = credential_user_id is not None
        legacy_present = legacy_hash is not None
        credential_usable = _credential_is_usable(
            credential_present=credential_present,
            password_hash=credential_hash,
            hash_version=hash_version,
        )
        legacy_usable = password_hash_is_usable(legacy_hash) if legacy_present else False

        if not credential_present and not legacy_present:
            category = "without_password"
        elif (credential_present and not credential_usable) or (
            legacy_present and not legacy_usable
        ):
            category = "invalid"
        elif credential_present and not legacy_present:
            category = "credential_only"
        elif not credential_present and legacy_present:
            category = "legacy_only"
        elif credential_hash == legacy_hash:
            category = "dual_equivalent"
        else:
            category = "divergent"

        counts[category] += 1
        if canonical is None:
            counts[f"{category}_missing_email_canonical"] += 1

    classified = sum(
        counts[name]
        for name in (
            "without_password",
            "credential_only",
            "dual_equivalent",
            "legacy_only",
            "divergent",
            "invalid",
        )
    )
    blockers: list[str] = []
    if classified != len(rows):
        blockers.append("credential_classification_incomplete")
    if counts["divergent"]:
        blockers.append("credential_hash_divergence")
    if counts["invalid"]:
        blockers.append("invalid_password_credential_state")
    if counts["missing_email_canonical"]:
        blockers.append("email_canonical_incomplete")

    return LegacyPasswordPreflightReport(
        status=PREFLIGHT_BLOCK if blockers else PREFLIGHT_PASS,
        total_users=len(rows),
        total_password_accounts=len(rows) - counts["without_password"],
        without_password=counts["without_password"],
        credential_only=counts["credential_only"],
        dual_equivalent=counts["dual_equivalent"],
        legacy_only=counts["legacy_only"],
        divergent=counts["divergent"],
        invalid=counts["invalid"],
        missing_email_canonical=counts["missing_email_canonical"],
        classification_complete=classified == len(rows),
        blockers=tuple(blockers),
        without_password_missing_email_canonical=counts[
            "without_password_missing_email_canonical"
        ],
        credential_only_missing_email_canonical=counts[
            "credential_only_missing_email_canonical"
        ],
        dual_equivalent_missing_email_canonical=counts[
            "dual_equivalent_missing_email_canonical"
        ],
        legacy_only_missing_email_canonical=counts[
            "legacy_only_missing_email_canonical"
        ],
        divergent_missing_email_canonical=counts[
            "divergent_missing_email_canonical"
        ],
        invalid_missing_email_canonical=counts[
            "invalid_missing_email_canonical"
        ],
        legacy_only_with_email_canonical=(
            counts["legacy_only"] - counts["legacy_only_missing_email_canonical"]
        ),
    )


def require_legacy_password_preflight_pass(
    report: LegacyPasswordPreflightReport,
) -> None:
    """Fail-closed para la futura L2, sin revelar datos de credenciales."""

    if report.status != PREFLIGHT_PASS:
        raise LegacyPasswordPreflightBlocked("legacy_password_preflight_blocked")
