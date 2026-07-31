"""Fail-closed intake boundary for reviewed Card/Printing evidence packages.

This module validates a supplied Stage 2 package and produces a deterministic promotion
plan.  It deliberately performs no canonical writes: the real MB2 card-list artifact is
not retained in this repository, so promotion must wait for that evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .evidence_package import EvidencePackageError

_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_FORBIDDEN = {"products", "product_versions", "pack_definitions", "packs", "slots",
              "print_sheets", "sheets", "collation", "probabilities", "simulation"}


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidencePackageError(f"cannot load Stage 2 record: {path}") from error
    if not isinstance(value, dict):
        raise EvidencePackageError(f"Stage 2 record must be an object: {path}")
    return value


def _stable(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def prepare_reviewed_card_list_package(package_root: Path) -> dict[str, Any]:
    """Validate a complete reviewed package and return its deterministic promotion plan."""
    root = Path(package_root)
    manifest = _load(root / "manifest.json")
    for key in ("source_record", "dataset_record", "review_record", "card_list_artifact"):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise EvidencePackageError(f"manifest requires {key}")
    source = _load(root / manifest["source_record"])
    dataset = _load(root / manifest["dataset_record"])
    review = _load(root / manifest["review_record"])
    artifact_path = root / manifest["card_list_artifact"]
    artifact = _load(artifact_path)

    digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    if digest != source.get("sha256") or source.get("artifact_path") != manifest["card_list_artifact"]:
        raise EvidencePackageError("card-list hash or artifact path does not match source record")
    required_source = ("id", "dataset_id", "source_identifier", "captured_at", "captured_by",
                       "license_assessment", "terms_assessment", "sha256")
    if any(not source.get(key) for key in required_source):
        raise EvidencePackageError("source capture, identity, hash, and terms metadata are required")
    if source["license_assessment"].get("status") != "assessed" or source["terms_assessment"].get("status") != "assessed":
        raise EvidencePackageError("license and terms must be assessed")
    if dataset.get("id") != source["dataset_id"] or dataset.get("source_ids") != [source["id"]]:
        raise EvidencePackageError("dataset and source identities are inconsistent")
    if artifact.get("dataset_id") != dataset["id"] or artifact.get("product_id") != "mystery_booster_2":
        raise EvidencePackageError("artifact dataset or product scope is inconsistent")
    if set(artifact).intersection(_FORBIDDEN):
        raise EvidencePackageError("Stage 2 artifact must not contain topology or runtime data")

    cards, printings = artifact.get("cards"), artifact.get("printings")
    if not isinstance(cards, list) or not isinstance(printings, list) or not cards or not printings:
        raise EvidencePackageError("complete Stage 2 cards and printings arrays are required")
    declared = dataset.get("declared_counts")
    if declared != {"cards": len(cards), "printings": len(printings)}:
        raise EvidencePackageError("declared entity counts do not match the artifact")
    if dataset.get("completeness") != "complete_for_reviewed_card_membership":
        raise EvidencePackageError("bounded reviewed-card membership completeness is required")

    ids: dict[str, set[str]] = {"card": set(), "printing": set()}
    collector_keys: set[tuple[str, str, str]] = set()
    candidate_ids: list[str] = []
    for kind, records in (("card", cards), ("printing", printings)):
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("payload"), dict):
                raise EvidencePackageError(f"{kind} records require canonical payload objects")
            candidate_id, payload = record.get("candidate_id"), record["payload"]
            entity_id = payload.get("id")
            if not isinstance(candidate_id, str) or not _ID.fullmatch(candidate_id):
                raise EvidencePackageError(f"{kind} candidate requires a canonical identifier")
            if not isinstance(entity_id, str) or not _ID.fullmatch(entity_id):
                raise EvidencePackageError(f"{kind} payload requires a canonical identifier")
            if entity_id in ids[kind]:
                raise EvidencePackageError(f"duplicate {kind} identifier: {entity_id}")
            ids[kind].add(entity_id); candidate_ids.append(candidate_id)
            provenance = record.get("field_provenance")
            if not isinstance(provenance, list):
                raise EvidencePackageError(f"{kind} requires field-level provenance")
            by_field = {item.get("field_path") for item in provenance if isinstance(item, dict)
                        and item.get("source_id") == source["id"] and item.get("confidence") is not None}
            if not set(payload).issubset(by_field):
                raise EvidencePackageError(f"every {kind} payload field requires source provenance and confidence")
            unknowns = record.get("explicit_unknowns")
            if not isinstance(unknowns, list):
                raise EvidencePackageError(f"{kind} requires an explicit_unknowns array")
            if kind == "printing":
                for field in ("card_id", "set_id", "collector_number", "language"):
                    if not payload.get(field):
                        raise EvidencePackageError(f"printing requires evidenced {field}")
                key = (payload["set_id"], payload["language"], payload["collector_number"])
                if key in collector_keys:
                    raise EvidencePackageError("duplicate collector number in set/language namespace")
                collector_keys.add(key)
    if any(item["payload"]["card_id"] not in ids["card"] for item in printings):
        raise EvidencePackageError("printing refers to a card outside the reviewed dataset")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise EvidencePackageError("duplicate candidate identifier")
    if review.get("decision") != "approved" or review.get("reviewer") == source["captured_by"]:
        raise EvidencePackageError("independent approved review is required")
    if sorted(review.get("approved_candidate_ids", [])) != sorted(candidate_ids):
        raise EvidencePackageError("review must approve every and only imported candidate")

    plan_basis = {"dataset_id": dataset["id"], "artifact_sha256": digest,
                  "candidate_ids": sorted(candidate_ids), "review_id": review.get("id")}
    plan_id = "mb2-stage-2-plan-" + hashlib.sha256(_stable(plan_basis)).hexdigest()[:24]
    return {"package_id": manifest.get("id"), "dataset_id": dataset["id"],
            "artifact_sha256": digest, "entity_counts": declared, "candidate_ids": sorted(candidate_ids),
            "promotion_plan_id": plan_id, "validation_state": "valid",
            "promotion_ready": True, "promoted": False}


__all__ = ["prepare_reviewed_card_list_package"]
