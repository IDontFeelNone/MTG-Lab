"""Loading and validation for repository-archived evidence bundles."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from validation import SchemaValidationError, validate_document

from .sources import SourceLoadError, load_source_record

_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_EVIDENCE_ROOT = _PROJECT_ROOT / "data" / "sources"
_DEFAULT_GAMES_ROOT = _PROJECT_ROOT / "data" / "canonical" / "games"


class EvidenceRepositoryError(ValueError):
    """Raised when archived evidence is incomplete, altered, or untraceable."""


@dataclass(frozen=True, slots=True)
class ArchivedEvidence:
    """One verified archived file and its manifest metadata."""

    id: str
    path: Path
    media_type: str
    content: bytes
    provenance: tuple[Mapping[str, Any], ...]
    population_batch: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    """A schema-valid manifest and all of its content-verified artifacts."""

    manifest: Mapping[str, Any]
    artifacts: tuple[ArchivedEvidence, ...]


def evidence_manifest_path(
    game: str, bundle_id: str, *, evidence_root: Path | None = None
) -> Path:
    """Return the canonical manifest path for a stable evidence-bundle identity."""
    _validate_identifier("game", game)
    _validate_identifier("bundle_id", bundle_id)
    root = Path(evidence_root) if evidence_root is not None else _DEFAULT_EVIDENCE_ROOT
    return root / game / bundle_id / "manifest.json"


def load_evidence_bundle(
    game: str,
    bundle_id: str,
    *,
    evidence_root: Path | None = None,
    games_root: Path | None = None,
) -> EvidenceBundle:
    """Load a complete bundle, verifying paths, bytes, sources, and provenance."""
    manifest_path = evidence_manifest_path(game, bundle_id, evidence_root=evidence_root)
    manifest = _load_manifest(manifest_path)
    if manifest["id"] != bundle_id or manifest["game"] != game:
        raise EvidenceRepositoryError("Evidence manifest identifiers do not match its path")

    canonical_games = Path(games_root) if games_root is not None else _DEFAULT_GAMES_ROOT
    known_sources = _load_sources(game, manifest, canonical_games)
    bundle_root = manifest_path.parent.resolve()
    artifacts: list[ArchivedEvidence] = []
    artifact_ids: set[str] = set()
    artifact_paths: set[str] = set()
    referenced_sources: set[str] = set()
    for record in manifest["artifacts"]:
        if record["id"] in artifact_ids:
            raise EvidenceRepositoryError(f"Duplicate evidence artifact id: {record['id']}")
        if record["path"] in artifact_paths:
            raise EvidenceRepositoryError(f"Duplicate evidence artifact path: {record['path']}")
        artifact_ids.add(record["id"])
        artifact_paths.add(record["path"])

        archive_path = bundle_root / record["path"]
        resolved_path = archive_path.resolve()
        if not resolved_path.is_relative_to(bundle_root):
            raise EvidenceRepositoryError(f"Evidence artifact escapes its bundle: {record['path']}")
        try:
            content = resolved_path.read_bytes()
        except OSError as error:
            raise EvidenceRepositoryError(
                f"Cannot read evidence artifact {record['id']}: {archive_path}"
            ) from error
        if len(content) != record["byte_size"]:
            raise EvidenceRepositoryError(f"Evidence artifact size mismatch: {record['id']}")
        if hashlib.sha256(content).hexdigest() != record["sha256"]:
            raise EvidenceRepositoryError(f"Evidence artifact hash mismatch: {record['id']}")

        artifact_sources = {entry["source_id"] for entry in record["provenance"]}
        unknown = artifact_sources - set(known_sources)
        if unknown:
            raise EvidenceRepositoryError(
                f"Evidence artifact {record['id']} references undeclared sources: "
                f"{', '.join(sorted(unknown))}"
            )
        referenced_sources.update(artifact_sources)
        artifacts.append(ArchivedEvidence(
            id=record["id"], path=resolved_path, media_type=record["media_type"],
            content=content,
            provenance=tuple(_freeze(entry) for entry in record["provenance"]),
            population_batch=_freeze(record.get("population_batch")),
        ))

    unused_sources = set(known_sources) - referenced_sources
    if unused_sources:
        raise EvidenceRepositoryError(
            f"Evidence manifest declares unused sources: {', '.join(sorted(unused_sources))}"
        )
    return EvidenceBundle(manifest=_freeze(manifest), artifacts=tuple(artifacts))


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise EvidenceRepositoryError(f"Evidence manifest not found: {path}") from error
    except json.JSONDecodeError as error:
        raise EvidenceRepositoryError(f"Evidence manifest is not valid JSON: {path}") from error
    if not isinstance(document, dict):
        raise EvidenceRepositoryError("Evidence manifest must be a JSON object")
    try:
        validate_document(document, "evidence-manifest")
    except SchemaValidationError as error:
        raise EvidenceRepositoryError(str(error)) from error
    return document


def _load_sources(
    game: str, manifest: Mapping[str, Any], games_root: Path
) -> dict[str, Mapping[str, Any]]:
    sources: dict[str, Mapping[str, Any]] = {}
    for source_id in manifest["source_ids"]:
        try:
            sources[source_id] = load_source_record(
                game, manifest["product_id"], source_id, games_root=games_root
            )
        except SourceLoadError as error:
            raise EvidenceRepositoryError(
                f"Evidence manifest references invalid source {source_id}: {error}"
            ) from error
    return sources


def _validate_identifier(label: str, value: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a stable lowercase identifier")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


__all__ = [
    "ArchivedEvidence", "EvidenceBundle", "EvidenceRepositoryError",
    "evidence_manifest_path", "load_evidence_bundle",
]
