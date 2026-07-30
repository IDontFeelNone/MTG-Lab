"""Mechanical duplicate and claim-conflict detection."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping


def duplicate_artifacts(manifest: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Find repeated identities, paths, or content hashes."""
    indexes: dict[str, dict[str, list[str]]] = {
        field: defaultdict(list) for field in ("id", "path", "sha256")
    }
    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        label = artifact.get("id", "<unknown>")
        for field, index in indexes.items():
            value = artifact.get(field)
            if isinstance(value, str):
                index[value].append(str(label))
    results = []
    for field in ("id", "path", "sha256"):
        for value, artifact_ids in indexes[field].items():
            if len(artifact_ids) > 1:
                results.append({"field": field, "value": value, "artifact_ids": sorted(artifact_ids)})
    return tuple(sorted(results, key=lambda item: (item["field"], item["value"])))


def conflicting_claims(manifest: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Find claims that declare different values for the same explicit topic."""
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in manifest.get("claims", []):
        if isinstance(claim, dict) and isinstance(claim.get("topic"), str):
            by_topic[claim["topic"]].append(claim)
    conflicts = []
    for topic, claims in by_topic.items():
        values = {str(claim.get("value")) for claim in claims}
        if len(values) > 1:
            conflicts.append({
                "topic": topic,
                "claim_ids": sorted(str(claim.get("id", "<unknown>")) for claim in claims),
                "values": sorted(values),
            })
    return tuple(sorted(conflicts, key=lambda item: item["topic"]))


__all__ = ["conflicting_claims", "duplicate_artifacts"]
