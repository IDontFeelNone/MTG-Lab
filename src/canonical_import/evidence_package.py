"""Generic import boundary for reviewed, immutable product-identity evidence packages."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from ingestion.candidate_validation import validate_candidate_artifact
from repository.promotion import CandidateReview, ProductPromotionService, ReviewDecision


class EvidencePackageError(ValueError):
    """The retained package is incomplete, mutable, or not independently reviewed."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise EvidencePackageError(f"cannot load package record: {path}") from error
    if not isinstance(value, dict):
        raise EvidencePackageError(f"package record must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_reviewed_product_package(
    package_root: Path, destination: Path, *, games_seed: Path | None = None
) -> dict[str, Any]:
    """Verify and promote one reviewed Product candidate through the existing writer."""
    package_root, destination = Path(package_root), Path(destination)
    manifest = _load(package_root / "manifest.json")
    source = _load(package_root / manifest["source_record"])
    dataset = _load(package_root / manifest["dataset_record"])
    review = _load(package_root / manifest["review_record"])
    parsed = _load(package_root / manifest["parsed_artifact"])
    candidate = _load(package_root / manifest["candidate_artifact"])
    raw_path = package_root / source["artifact_path"]
    digest = _sha256(raw_path)
    if digest != source["sha256"] or digest != candidate["raw_evidence_hash"]:
        raise EvidencePackageError("source hash does not match retained evidence bytes")
    if source.get("review_status") != "approved" or review.get("decision") != "approved":
        raise EvidencePackageError("promotion requires an approved review record")
    if review.get("reviewer") == source.get("captured_by"):
        raise EvidencePackageError("source capture and review must be independent")
    if dataset.get("source_ids") != [source.get("id")]:
        raise EvidencePackageError("dataset does not resolve exactly to its source")
    if not manifest.get("bounded_completeness", {}).get("official_product_identity_fields"):
        raise EvidencePackageError("bounded product-identity completeness is not declared")
    if any(manifest.get("entity_counts", {}).get(kind, 0) for kind in
           ("product_versions", "pack_definitions", "slots", "print_sheets")):
        raise EvidencePackageError("Stage 1 package must not contain pack topology")
    validation = validate_candidate_artifact(candidate, parsed)
    if validation.state.value != "valid":
        raise EvidencePackageError("candidate failed validation: " + "; ".join(validation.errors))

    games_root = destination / "canonical" / "games"
    if games_seed is not None and not games_root.exists():
        shutil.copytree(Path(games_seed), games_root)
    raw_destination = destination / "sources" / source["id"] / digest / raw_path.name
    raw_destination.parent.mkdir(parents=True, exist_ok=True)
    if raw_destination.exists() and raw_destination.read_bytes() != raw_path.read_bytes():
        raise EvidencePackageError("immutable destination contains different bytes")
    raw_destination.write_bytes(raw_path.read_bytes())
    decision = CandidateReview(ReviewDecision.APPROVED, review["reviewer"],
                               review["reviewed_at"], review["reason"])
    audit = ProductPromotionService(games_root=games_root,
                                    audit_root=destination / "audit" / "promotions").review(
        candidate, parsed, candidate["candidates"][0]["id"], decision)
    return {
        "package_id": manifest["id"], "dataset_id": dataset["id"],
        "source_hashes": [digest], "candidate_ids": [candidate["candidates"][0]["id"]],
        "canonical_ids": [audit["entity_id"]], "promotion_audit_ids": [audit["id"]],
        "promotion_outcomes": [audit["outcome"]], "entity_counts": manifest["entity_counts"],
        "bounded_completeness": manifest["bounded_completeness"],
    }


__all__ = ["EvidencePackageError", "import_reviewed_product_package"]
