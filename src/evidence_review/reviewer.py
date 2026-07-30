"""Orchestration for deterministic evidence review."""

from __future__ import annotations

import hashlib
from typing import Any

from .completeness import assess_completeness
from .conflict_detector import conflicting_claims, duplicate_artifacts
from .loader import EvidenceHandoff
from .validator import validate_handoff


def review_handoff(handoff: EvidenceHandoff) -> dict[str, Any]:
    """Review a handoff and return a schema-valid report-ready document."""
    manifest = handoff.manifest
    findings = list(validate_handoff(handoff))
    artifacts = [item for item in manifest.get("artifacts", []) if isinstance(item, dict)]
    sources = [item for item in manifest.get("sources", []) if isinstance(item, dict)]
    valid_artifacts = {
        item["id"] for item in artifacts
        if isinstance(item.get("id"), str)
        and item["id"] in handoff.artifact_content
        and len(handoff.artifact_content[item["id"]]) == item.get("byte_size")
        and hashlib.sha256(handoff.artifact_content[item["id"]]).hexdigest()
        == item.get("sha256")
    }
    valid_sources = {item["id"] for item in sources if isinstance(item.get("id"), str)}
    duplicates = list(duplicate_artifacts(manifest))
    conflicts = list(conflicting_claims(manifest))
    completeness = assess_completeness(manifest, valid_artifacts, valid_sources)

    if findings or duplicates or conflicts:
        recommendation = "Reject"
    elif (completeness["unsupported_claim_ids"] or completeness["missing_artifact_ids"]
          or completeness["orphaned_artifact_ids"]):
        recommendation = "Needs additional evidence"
    else:
        recommendation = "Ready for verification"

    return {
        "schema_version": "v1",
        "handoff_id": str(manifest.get("id", "unknown")),
        "evidence_inventory": [
            {
                "id": str(item.get("id", "<unknown>")),
                "path": str(item.get("path", "")),
                "media_type": str(item.get("media_type", "")),
                "integrity_verified": item.get("id") in valid_artifacts,
                "source_ids": sorted(item.get("source_ids", [])),
            }
            for item in sorted(artifacts, key=lambda value: str(value.get("id", "")))
        ],
        "supported_claims": completeness["supported_claim_ids"],
        "unsupported_claims": completeness["unsupported_claim_ids"],
        "conflicting_claims": conflicts,
        "missing_evidence": completeness["missing_artifact_ids"],
        "orphaned_artifacts": completeness["orphaned_artifact_ids"],
        "duplicate_artifacts": duplicates,
        "completeness_score": completeness["score"],
        "provenance_summary": {
            "declared_source_count": len(valid_sources),
            "referenced_source_ids": sorted({
                source_id for item in artifacts for source_id in item.get("source_ids", [])
                if isinstance(source_id, str)
            }),
        },
        "validation_findings": findings,
        "recommendation": recommendation,
    }


__all__ = ["review_handoff"]
