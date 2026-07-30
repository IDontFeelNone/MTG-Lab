"""Evidence coverage assessment without domain-specific sufficiency inference."""

from __future__ import annotations

from typing import Any, Mapping


def assess_completeness(
    manifest: Mapping[str, Any], valid_artifact_ids: set[str], valid_source_ids: set[str]
) -> dict[str, Any]:
    required = set(manifest.get("required_artifact_ids", []))
    missing = sorted(required - valid_artifact_ids)
    claims = [claim for claim in manifest.get("claims", []) if isinstance(claim, dict)]
    supported: list[str] = []
    unsupported: list[str] = []
    referenced_artifacts: set[str] = set()
    for claim in claims:
        claim_id = str(claim.get("id", "<unknown>"))
        artifact_ids = set(claim.get("artifact_ids", []))
        source_ids = set(claim.get("source_ids", []))
        referenced_artifacts.update(item for item in artifact_ids if isinstance(item, str))
        if artifact_ids and source_ids and artifact_ids <= valid_artifact_ids and source_ids <= valid_source_ids:
            supported.append(claim_id)
        else:
            unsupported.append(claim_id)

    all_artifact_ids = {
        artifact["id"] for artifact in manifest.get("artifacts", [])
        if isinstance(artifact, dict) and isinstance(artifact.get("id"), str)
    }
    orphaned = sorted(all_artifact_ids - referenced_artifacts)
    checks = len(required) + len(claims)
    successes = len(required - set(missing)) + len(supported)
    score = round(100 * successes / checks) if checks else 0
    return {
        "supported_claim_ids": sorted(supported),
        "unsupported_claim_ids": sorted(unsupported),
        "missing_artifact_ids": missing,
        "orphaned_artifact_ids": orphaned,
        "score": score,
    }


__all__ = ["assess_completeness"]
