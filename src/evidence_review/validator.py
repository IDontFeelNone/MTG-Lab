"""Structural, integrity, and reference validation for evidence handoffs."""

from __future__ import annotations

import hashlib
from typing import Any

from validation import SchemaValidationError, validate_document

from .loader import EvidenceHandoff


def validate_handoff(handoff: EvidenceHandoff) -> tuple[dict[str, Any], ...]:
    """Return deterministic validation findings; never infer domain rules."""
    findings: list[dict[str, Any]] = []
    try:
        validate_document(handoff.manifest, "evidence-handoff")
    except SchemaValidationError as error:
        findings.append(_finding("invalid_manifest", "critical", str(error)))

    for message in handoff.load_errors:
        findings.append(_finding("artifact_unreadable", "critical", message))

    sources = handoff.manifest.get("sources", [])
    source_ids = {
        item["id"] for item in sources
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    } if isinstance(sources, list) else set()
    artifacts = handoff.manifest.get("artifacts", [])
    artifact_ids: set[str] = set()
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if not isinstance(artifact, dict) or not isinstance(artifact.get("id"), str):
                continue
            artifact_id = artifact["id"]
            artifact_ids.add(artifact_id)
            unknown_sources = set(artifact.get("source_ids", [])) - source_ids
            if unknown_sources:
                findings.append(_finding(
                    "unknown_source_reference", "critical",
                    f"{artifact_id}: {', '.join(sorted(unknown_sources))}",
                ))
            content = handoff.artifact_content.get(artifact_id)
            if content is None:
                continue
            if isinstance(artifact.get("byte_size"), int) and len(content) != artifact["byte_size"]:
                findings.append(_finding("size_mismatch", "critical", artifact_id))
            digest = hashlib.sha256(content).hexdigest()
            if isinstance(artifact.get("sha256"), str) and digest != artifact["sha256"]:
                findings.append(_finding("hash_mismatch", "critical", artifact_id))
    unknown_required = set(handoff.manifest.get("required_artifact_ids", [])) - artifact_ids
    for artifact_id in sorted(unknown_required):
        findings.append(_finding("undeclared_required_artifact", "critical", artifact_id))
    return tuple(sorted(findings, key=lambda item: (item["code"], item["detail"])))


def _finding(code: str, severity: str, detail: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "detail": detail}


__all__ = ["validate_handoff"]
