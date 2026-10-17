"""Transient inspection of exactly twenty pinned physical rule lines.

This is a release-specific locator, not a general CR parser. Source bytes and
official prose never enter the returned projection or an on-disk source store.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.source_evidence.artifacts import (
    ArtifactVerificationRequest, ArtifactVerificationResult,
    _open_regular_no_symlinks, verify_local_artifact)
from gameplay_rules.source_evidence.artifact_review import verify_artifact_review_package

from .contracts import (ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE,
                        VERIFICATION_RESULT_ID, CORRESPONDENCE_REVIEW_ID,
                        ARTIFACT_REVIEW_PACKAGE_ID, SELECTION_ID, FoundationalProjection)
from .scope import (SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES,
                    UNSUPPORTED_DIMENSIONS)


def _fail(field):
    raise GameplayContractError("foundational_projection_source", field)


def _control_json(path):
    # Existing package verification checks the same files with strict JSON and
    # immutable identities. Re-open bounded control metadata without symlinks.
    descriptor = _open_regular_no_symlinks(path)
    if descriptor is None:
        _fail("required source control metadata unavailable")
    with os.fdopen(descriptor, "rb") as stream:
        raw = stream.read(64_001)
    if len(raw) > 64_000:
        _fail("source control metadata exceeds limit")
    return json.loads(raw)


def _verified_bytes(artifact_path, *, artifact_review_root, source_root, discovery_root):
    lineage = verify_artifact_review_package(artifact_review_root,
        source_root=source_root, discovery_root=discovery_root)
    for field, expected in (("package_id", ARTIFACT_REVIEW_PACKAGE_ID),
            ("verification_result_id", VERIFICATION_RESULT_ID),
            ("correspondence_review_id", CORRESPONDENCE_REVIEW_ID), ("selection_id", SELECTION_ID)):
        if lineage[field] != expected:
            _fail("source verification lineage mismatch")
    request = ArtifactVerificationRequest.from_dict(_control_json(
        Path(discovery_root) / "artifact-verification-request.json"))
    retained = ArtifactVerificationResult.from_dict(_control_json(
        Path(artifact_review_root) / "artifact-verification-result.json"))
    # Reproduce the historical result, including its explicitly retained
    # timestamp; this does not claim a fresh first-party observation.
    result = verify_local_artifact(artifact_path, request,
        expected_request_id=request.identity,
        expected_release_candidate_id=request.release_candidate_id,
        expected_discovery_source_reference_id=request.discovery_source_reference_id,
        game_id="magic", observed_at=retained.observed_at)
    if (result.status != "VERIFIED_EXPECTED_ARTIFACT" or result.artifact_hash != ARTIFACT_HASH
            or result.byte_length != ARTIFACT_BYTE_LENGTH or result.identity != VERIFICATION_RESULT_ID
            or result.to_dict() != retained.to_dict()):
        _fail("VERIFIED_SOURCE_ARTIFACT_MISMATCH")
    descriptor = _open_regular_no_symlinks(artifact_path)
    if descriptor is None:
        _fail("verified artifact unavailable")
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        data = stream.read(ARTIFACT_BYTE_LENGTH + 1)
        after = os.fstat(stream.fileno())
    if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) !=
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            or len(data) != ARTIFACT_BYTE_LENGTH
            or "sha256:" + hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail("VERIFIED_SOURCE_ARTIFACT_MISMATCH")
    return data


def _locate_anchors(data, *, references=SELECTED_REFERENCES):
    """Locate only the immutable allowlist; no other rule body is extracted."""
    patterns = {reference: re.compile(rb"^" + re.escape(reference.encode("ascii")) + rb"\.?[ \t]+")
                for reference in references}
    anchors = {}
    offset = 0
    for line_number, physical_line in enumerate(data.splitlines(keepends=True), 1):
        line = physical_line.rstrip(b"\r\n")
        for reference, pattern in patterns.items():
            if pattern.match(line):
                if reference in anchors:
                    _fail("selected rule line is ambiguous")
                anchors[reference] = {
                    "rule_reference": reference, "artifact_hash": ARTIFACT_HASH,
                    "byte_start": offset, "byte_end": offset + len(line),
                    "line_number": line_number,
                    "span_sha256": "sha256:" + hashlib.sha256(line).hexdigest(),
                    "span_policy": "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR",
                }
        offset += len(physical_line)
    if set(anchors) != set(references):
        _fail("selected rule line missing")
    return [anchors[reference] for reference in references]


def build_projection(artifact_path, *, artifact_review_root, source_root, discovery_root):
    """Bind authored descriptions to exact source spans without retaining prose."""
    data = _verified_bytes(artifact_path, artifact_review_root=artifact_review_root,
        source_root=source_root, discovery_root=discovery_root)
    anchors = _locate_anchors(data)
    body = {
        "game_id": "magic", "projection_kind": "NON_EXECUTABLE",
        "status": "IMPLEMENTED_PENDING_REVIEW", "selected_rule_count": 20,
        "source_binding": {
            "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
            "effective_date": EFFECTIVE_DATE, "verification_result_id": VERIFICATION_RESULT_ID,
            "correspondence_review_id": CORRESPONDENCE_REVIEW_ID,
            "artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID, "selection_id": SELECTION_ID,
        },
        "authorization": {
            "scope": "Core Comprehensive Rules Projection — Foundational Rules Subset",
            "basis": "OWNER_EXPLICIT_TASK_AUTHORIZATION", "authorized_on": "2026-10-17",
            "source_policy_clearance": "not_granted",
        },
        "rules": [{"rule_reference": anchor["rule_reference"],
                   **RULE_CONTENT[anchor["rule_reference"]], "source_anchor": anchor}
                  for anchor in anchors],
        "graph": {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES},
        "unsupported_dimensions": list(UNSUPPORTED_DIMENSIONS),
        "boundary_flags": {"non_executable": True, "real_rules_executable": False,
            "admission_eligible": False, "source_body_retained": False,
            "oracle_ingested": False, "source_policy_clearance": "not_granted"},
    }
    return FoundationalProjection.create(body)


def verify_projection_source(projection, artifact_path, *, artifact_review_root, source_root, discovery_root):
    """Recompute every anchor against the real external source; never infer access."""
    if not isinstance(projection, FoundationalProjection):
        _fail("typed non-executable projection required")
    projection.verify()
    reproduced = build_projection(artifact_path, artifact_review_root=artifact_review_root,
        source_root=source_root, discovery_root=discovery_root)
    if projection.to_dict() != reproduced.to_dict():
        _fail("projection source spans or authored content do not reproduce")
    return {"status": "VERIFIED_EXACT_SOURCE_SPANS", "projection_id": projection.identity,
            "selected_rule_count": 20, "artifact_hash": ARTIFACT_HASH,
            "byte_length": ARTIFACT_BYTE_LENGTH, "source_body_retained": False,
            "real_rules_executable": False}
