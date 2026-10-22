"""Original-byte boundary for exactly one complete proposal-checkpoint source unit.

The following f marker supplies structural ownership only. Its body is never
examined for content; fictional fixtures cannot establish source authority.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.bounded_mana_source import ANCHOR_TYPE, SPAN_POLICY, _physical_lines
from gameplay_rules.projection.contracts import ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, _freeze, _json
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from gameplay_rules.projection.source import _verified_bytes

SOURCE_ENV = "MTGLAB_SHARED_PROPOSAL_LEGALITY_SOURCE"
SELECTED_REFERENCES = ("601.2e",)
ANCHOR_ID_DOMAIN = "gameplay-cr-bounded-shared-proposal-legality-anchor-v1"
_CITATION = re.compile(rb"(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?![0-9A-Za-z]|\.[0-9A-Za-z])")


def _fail(code):
    raise GameplayContractError("shared_proposal_legality_source", code)


def anchor_identity(anchor):
    _canonical_candidate(anchor)
    if type(anchor) is not dict:
        _fail("PLAIN_SOURCE_ANCHOR_REQUIRED")
    body = {key: value for key, value in anchor.items() if key != "anchor_id"}
    return "sha256:" + sha256_identity({"domain": ANCHOR_ID_DOMAIN, "content": body})


def _anchor(start, end, digest, artifact_hash):
    result = {
        "rule_reference": "601.2e", "artifact_hash": artifact_hash,
        "effective_date": EFFECTIVE_DATE, "anchor_type": ANCHOR_TYPE,
        "span_policy": SPAN_POLICY, "starting_physical_line": 2472,
        "ending_physical_line": 2472, "line_count": 1, "owned_example_line_count": 0,
        "byte_start": start, "byte_end": end, "span_length": end - start,
        "span_sha256": "sha256:" + digest,
        "following_marker": {"rule_reference": "601.2f", "physical_line": 2474,
            "body_inspected": False},
    }
    result["anchor_id"] = anchor_identity(result)
    return result


VERIFIED_ANCHORS = _freeze([_anchor(298690, 298921,
    "6b30c02c87f09a559eba9525cc331b65ddf668783d526e9f27f52a8447b11249", ARTIFACT_HASH)])


def validate_spans(anchors):
    """Validate exact metadata and its own identity without claiming source access."""
    if anchors is VERIFIED_ANCHORS:
        anchors = _json(anchors)
    raw = _canonical_candidate(anchors)
    if (type(anchors) is not list or len(anchors) != 1 or type(anchors[0]) is not dict
            or raw != _canonical_candidate(_json(VERIFIED_ANCHORS))):
        _fail("EXACT_COMPLETE_E_ANCHOR_REQUIRED")
    if anchors[0]["anchor_id"] != anchor_identity(anchors[0]):
        _fail("SOURCE_ANCHOR_OWN_IDENTITY_INVALID")
    return anchors


def locate_anchors(data):
    """Return only metadata after inspecting e, separator and next marker prefix.

    Physical line positions are fixed to this release. Original terminators
    determine offsets and are excluded from the final owned line's raw span.
    This structural helper accepts invented fixtures but confers no real-source
    authority; verification below requires the exact artifact and fingerprint.
    """
    if type(data) is not bytes or not data or len(data) > ARTIFACT_BYTE_LENGTH + 1:
        _fail("INVALID_SOURCE_BYTES")
    lines = _physical_lines(data)
    if len(lines) < 2474:
        _fail("SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT")
    first, separator = lines[2471], lines[2472]
    if (not first[1].startswith(b"601.2e ") or not first[1][7:].strip()
            or separator[1] != b"\xc2\xa0" or lines[2473][1][:7] != b"601.2f "):
        _fail("SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT")
    start, end = first[0], first[0] + len(first[1])
    block = data[start:end]
    if _CITATION.findall(block[7:]) != [b"733"]:
        _fail("SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT")
    return [_anchor(start, end, hashlib.sha256(block).hexdigest(),
        "sha256:" + hashlib.sha256(data).hexdigest())]


def verify_bytes(data):
    """Reproduce e only from the exact original artifact; altered inputs fail."""
    if (type(data) is not bytes or len(data) != ARTIFACT_BYTE_LENGTH
            or "sha256:" + hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail("VERIFIED_SOURCE_ARTIFACT_MISMATCH")
    anchors = locate_anchors(data)
    if _canonical_candidate(anchors) != _canonical_candidate(_json(VERIFIED_ANCHORS)):
        _fail("SHARED_PROPOSAL_LEGALITY_SCOPE_INSUFFICIENT")
    validate_spans(anchors)
    return anchors


def verified_anchors(artifact_path, *, review_root):
    """Verify original bytes and retained lineage before e-only reproduction."""
    try:
        if type(artifact_path) not in (str, Path) and not isinstance(artifact_path, Path):
            _fail("SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID")
        root = Path(review_root)
        data = _verified_bytes(artifact_path,
            artifact_review_root=root / "gameplay-rules-artifact-verification",
            source_root=root / "gameplay-rules-source-versioning",
            discovery_root=root / "gameplay-rules-release-discovery-closure")
    except (OSError, TypeError, ValueError, GameplayContractError):
        _fail("SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID")
    return verify_bytes(data)
