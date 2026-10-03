"""Canonicalizacion pura para fingerprints logicos de datasets sinteticos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID


FINGERPRINT_CONTRACT = "feedgo.synthetic.logical-blueprint.v1"


class FingerprintContractError(ValueError):
    """El valor no puede representarse sin ambiguedad en el contrato logico."""


class NonDeterministicKind(str, Enum):
    """Clases criptograficas admitidas para normalizacion explicita."""

    BCRYPT_HASH = "bcrypt_hash"
    TOKEN_DIGEST = "token_digest"
    SALT = "salt"
    CRYPTOGRAPHIC_NONCE = "cryptographic_nonce"
    CIPHERTEXT = "ciphertext"
    OWNER_GENERATED_IDENTIFIER = "owner_generated_identifier"


@dataclass(frozen=True)
class OwnerDerivedValue:
    """Valor que el materializador debe obtener invocando al owner indicado.

    El descriptor conserva en el fingerprint logico el contrato y sus entradas
    semanticas, pero no adelanta IDs autoincrementales ni duplica el algoritmo
    productivo que calculara el valor fisico.
    """

    owner: str
    inputs: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.owner or not isinstance(self.owner, str):
            raise FingerprintContractError("Owner derivado obligatorio")
        if not self.inputs:
            raise FingerprintContractError("Un valor derivado requiere entradas logicas")
        frozen = freeze_logical_value(self.inputs)
        object.__setattr__(self, "inputs", frozen)
        canonicalize_logical_value(frozen)


def freeze_logical_value(value: Any) -> Any:
    """Copia y congela estructuras logicas para evitar mutaciones posteriores."""

    if isinstance(value, (NormalizedNonDeterministicValue, OwnerDerivedValue)):
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise FingerprintContractError("Las claves logicas deben ser strings")
            frozen[key] = freeze_logical_value(item)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(freeze_logical_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        raise FingerprintContractError("Los sets no tienen orden logico estable")
    return value


@dataclass(frozen=True)
class NormalizedNonDeterministicValue:
    """Valor opaco cuyo fingerprint conserva invariantes, nunca el material secreto.

    ``opaque_value`` puede contener el resultado aleatorio real generado por un owner
    criptografico. Queda deliberadamente fuera de igualdad, repr y fingerprint. La
    normalizacion sólo es valida para una categoria enumerada y con invariantes
    funcionales explicitos.
    """

    kind: NonDeterministicKind
    invariants: Mapping[str, Any]
    opaque_value: Any = field(repr=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, NonDeterministicKind):
            raise FingerprintContractError("La categoria no determinista no esta permitida")
        if not self.invariants:
            raise FingerprintContractError(
                "Un valor no determinista requiere invariantes funcionales"
            )
        frozen = freeze_logical_value(self.invariants)
        object.__setattr__(self, "invariants", frozen)
        # Valida ahora para fallar al construir el blueprint, no al certificarlo.
        canonicalize_logical_value(frozen)


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise FingerprintContractError("Los datetime logicos deben incluir timezone")
    normalized = value.astimezone(timezone.utc)
    return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical_float(value: float) -> str:
    if not math.isfinite(value):
        raise FingerprintContractError("NaN e infinito no son valores logicos validos")
    if value == 0:
        return "0"
    return format(value, ".17g")


def canonicalize_logical_value(value: Any) -> Any:
    """Convierte un valor permitido a una representacion JSON canonica y tipada."""

    if isinstance(value, NormalizedNonDeterministicValue):
        return {
            "$normalized_non_deterministic": {
                "kind": value.kind.value,
                "invariants": canonicalize_logical_value(value.invariants),
            }
        }
    if isinstance(value, OwnerDerivedValue):
        return {
            "$owner_derived": {
                "owner": value.owner,
                "inputs": canonicalize_logical_value(value.inputs),
            }
        }
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return {"$float": _canonical_float(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise FingerprintContractError("Decimal no finito no permitido")
        return {"$decimal": str(value.normalize())}
    if isinstance(value, datetime):
        return {"$datetime": _canonical_datetime(value)}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, UUID):
        return {"$uuid": str(value)}
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise FingerprintContractError("Las claves logicas deben ser strings")
        canonical: dict[str, Any] = {}
        for key in sorted(value):
            canonical[key] = canonicalize_logical_value(value[key])
        return canonical
    if isinstance(value, (list, tuple)):
        return [canonicalize_logical_value(item) for item in value]
    raise FingerprintContractError(
        f"Tipo no soportado por el fingerprint logico: {type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    canonical = canonicalize_logical_value(value)
    return json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def logical_fingerprint(value: Any) -> str:
    payload = canonical_json(value).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(FINGERPRINT_CONTRACT.encode("ascii"))
    digest.update(b"\0")
    digest.update(payload)
    return digest.hexdigest()
