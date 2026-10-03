"""Recetas puras y versionadas para medios sinteticos de ET100.3.

Este modulo no lee ni escribe archivos. Una referencia ``synthetic-media://``
se convierte en un contrato reproducible cuyo hash cubre toda la metadata que
un materializador futuro debera respetar.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Iterable, Mapping

from .blueprint import LogicalBlueprint


RECIPE_VERSION = "synthetic-media-recipe-v1"
_URI_PATTERN = re.compile(
    r"^synthetic-media://[a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9_-]*)+"
    r"/(cover-v1|image-v1|video-v1)$"
)


class SyntheticMediaContractError(ValueError):
    """Una referencia de medio no pertenece al contrato sintetico aprobado."""


@dataclass(frozen=True)
class SyntheticMediaRecipe:
    uri: str
    recipe_version: str
    kind: str
    mime_type: str
    renderer: str
    parameters: Mapping[str, Any]
    recipe_sha256: str

    def logical_payload(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "recipe_version": self.recipe_version,
            "kind": self.kind,
            "mime_type": self.mime_type,
            "renderer": self.renderer,
            "parameters": dict(self.parameters),
        }


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _recipe_payload(uri: str) -> dict[str, Any]:
    match = _URI_PATTERN.fullmatch(uri)
    if match is None or ".." in uri or "\\" in uri or "?" in uri or "#" in uri:
        raise SyntheticMediaContractError("synthetic_media_uri_not_allowlisted")
    variant = match.group(1)
    digest = hashlib.sha256(uri.encode("utf-8")).hexdigest()
    palette = (f"#{digest[0:6]}", f"#{digest[6:12]}", f"#{digest[12:18]}")
    common = {
        "synthetic_marker": "FEEDGO_SYNTHETIC_ET100_3",
        "palette": palette,
        "label_digest": digest[:16],
    }
    if variant == "cover-v1":
        return {
            "kind": "cover",
            "mime_type": "image/svg+xml",
            "renderer": "feedgo.synthetic.svg-placeholder.v1",
            "parameters": {**common, "width": 1280, "height": 720},
        }
    if variant == "image-v1":
        return {
            "kind": "image",
            "mime_type": "image/svg+xml",
            "renderer": "feedgo.synthetic.svg-placeholder.v1",
            "parameters": {**common, "width": 1080, "height": 1080},
        }
    return {
        "kind": "video",
        "mime_type": "video/mp4",
        "renderer": "feedgo.synthetic.video-placeholder.v1",
        "parameters": {
            **common,
            "width": 720,
            "height": 1280,
            "duration_ms": 5000,
            "frames_per_second": 24,
            "audio": False,
        },
    }


def compile_media_recipe(uri: str) -> SyntheticMediaRecipe:
    payload = _recipe_payload(uri)
    unsigned = {
        "uri": uri,
        "recipe_version": RECIPE_VERSION,
        **payload,
    }
    sha256 = hashlib.sha256(_canonical_json(unsigned).encode("utf-8")).hexdigest()
    return SyntheticMediaRecipe(recipe_sha256=sha256, **unsigned)


def _walk_media_references(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        if value.startswith("synthetic-media://"):
            yield value
        return
    if isinstance(value, Mapping):
        for nested in value.values():
            yield from _walk_media_references(nested)
        return
    if isinstance(value, (tuple, list, set, frozenset)):
        for nested in value:
            yield from _walk_media_references(nested)
        return
    inputs = getattr(value, "inputs", None)
    if isinstance(inputs, Mapping):
        yield from _walk_media_references(inputs)


def media_recipes_for_blueprint(
    blueprint: LogicalBlueprint,
) -> tuple[SyntheticMediaRecipe, ...]:
    references: set[str] = set()
    for entity in blueprint.entities:
        references.update(_walk_media_references(entity.attributes))
    return tuple(compile_media_recipe(uri) for uri in sorted(references))


def media_manifest_sha256(recipes: Iterable[SyntheticMediaRecipe]) -> str:
    payload = [recipe.logical_payload() | {"recipe_sha256": recipe.recipe_sha256}
               for recipe in recipes]
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
