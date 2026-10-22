"""Original-byte verification of exactly the complete a/i casting-stage units.

All other rule access is limited to structural marker prefixes. Returned values
contain metadata only; source bytes, bodies and paths are never retained.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.bounded_mana_source import ANCHOR_TYPE, SPAN_POLICY, _physical_lines
from gameplay_rules.projection.contracts import ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, _freeze, _json
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from gameplay_rules.projection.source import _verified_bytes
from .scope import SELECTED_REFERENCES, STAGE_REFERENCES

SOURCE_ENV = "MTGLAB_CASTING_STAGE_FAMILY_COMPLETION_SOURCE"
ANCHOR_ID_DOMAIN = "gameplay-cr-casting-stage-family-completion-anchor-v1"
_CITATION = re.compile(rb"(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?![0-9A-Za-z]|\.[0-9A-Za-z])")
_RANGE = b"601.2a\xe2\x80\x93h"
_MARKER = re.compile(rb"^(601\.2[a-z]?|601\.3)(?:\.)? ")
_INVENTORY = (("601.2", 2461), *zip(STAGE_REFERENCES, (2463, 2465, 2467, 2470, 2472, 2474, 2476, 2478, 2481)), ("601.3", 2483))
_SPECS = (
    ("601.2a", 2463, 294281, 294956, "794572517487b69d9a61c04e331719c8dab511b88efbcc763585786a4535aa6b", "601.2b", 2465),
    ("601.2i", 2481, 300741, 301082, "483c59e2092745af49cee6e5aa79339b165456084f22b33164dd4a24f6caa596", "601.3", 2483),
)


def _fail(code):
    raise GameplayContractError("casting_stage_family_completion_source", code)


def anchor_identity(anchor):
    raw = _canonical_candidate(anchor)
    if type(anchor) is not dict:
        _fail("PLAIN_SOURCE_ANCHOR_REQUIRED")
    body = {key: value for key, value in json.loads(raw).items() if key != "anchor_id"}
    return "sha256:" + sha256_identity({"domain": ANCHOR_ID_DOMAIN, "content": body})


def _anchor(reference, line, start, end, digest, following, following_line, artifact_hash):
    result = {"rule_reference": reference, "artifact_hash": artifact_hash,
        "effective_date": EFFECTIVE_DATE, "anchor_type": ANCHOR_TYPE, "span_policy": SPAN_POLICY,
        "starting_physical_line": line, "ending_physical_line": line, "line_count": 1,
        "owned_example_line_count": 0, "byte_start": start, "byte_end": end,
        "span_length": end - start, "span_sha256": "sha256:" + digest,
        "following_marker": {"rule_reference": following, "physical_line": following_line,
            "body_inspected": False}}
    result["anchor_id"] = anchor_identity(result)
    return result


VERIFIED_ANCHORS = _freeze([_anchor(*spec, ARTIFACT_HASH) for spec in _SPECS])


def validate_spans(anchors):
    """Own strict validated metadata without claiming fresh source access."""
    if anchors is VERIFIED_ANCHORS:
        anchors = _json(anchors)
    raw = _canonical_candidate(anchors)
    if (type(anchors) is not list or raw != _canonical_candidate(_json(VERIFIED_ANCHORS))):
        _fail("EXACT_COMPLETE_A_I_ANCHORS_REQUIRED")
    result = json.loads(raw)
    for anchor in result:
        if anchor["anchor_id"] != anchor_identity(anchor):
            _fail("SOURCE_ANCHOR_OWN_IDENTITY_INVALID")
    return result


def marker_inventory(data):
    """Enumerate only stage/adjacent marker prefixes, never their bodies."""
    if type(data) is not bytes or not data or len(data) > ARTIFACT_BYTE_LENGTH + 1:
        _fail("INVALID_SOURCE_BYTES")
    found = []
    for line_number, row in enumerate(_physical_lines(data), 1):
        match = _MARKER.match(row[1][:7])
        if match:
            found.append((match[1].decode("ascii"), line_number))
    if tuple(found) != _INVENTORY:
        _fail("CASTING_STAGE_BATCH_SCOPE_INSUFFICIENT")
    return [{"rule_reference": ref, "physical_line": line, "inspection": "MARKER_PREFIX_ONLY"}
        for ref, line in found]


def locate_anchors(data):
    """Inspect selected complete one-line units plus separator/marker boundaries.

    Invented fixtures may exercise ownership checks but supply no real source
    authority. Exact artifact verification is mandatory in verify_bytes.
    """
    marker_inventory(data)
    lines = _physical_lines(data)
    artifact_hash = "sha256:" + hashlib.sha256(data).hexdigest()
    result = []
    for reference, line, _, _, _, following, following_line in _SPECS:
        first, separator, next_line = lines[line - 1], lines[line], lines[following_line - 1]
        prefix = (reference + " ").encode("ascii")
        next_prefix = (following + (". " if following[-1].isdigit() else " ")).encode("ascii")
        if (not first[1].startswith(prefix) or not first[1][len(prefix):].strip()
                or separator[1] != b"\xc2\xa0"
                or next_line[1][:len(next_prefix)] != next_prefix):
            _fail("CASTING_STAGE_BATCH_SCOPE_INSUFFICIENT")
        start, end = first[0], first[0] + len(first[1])
        block = data[start:end]
        citations = _CITATION.findall(block[len(prefix):])
        if ((reference == "601.2a" and citations != [b"611.2f", b"610.5"])
                or (reference == "601.2i" and (citations != [b"601.2a"] or block.count(_RANGE) != 1))):
            _fail("CASTING_STAGE_BATCH_SCOPE_INSUFFICIENT")
        result.append(_anchor(reference, line, start, end, hashlib.sha256(block).hexdigest(),
            following, following_line, artifact_hash))
    return result


def verify_bytes(data):
    """Reproduce both complete units only after exact raw-artifact verification."""
    if (type(data) is not bytes or len(data) != ARTIFACT_BYTE_LENGTH
            or "sha256:" + hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail("VERIFIED_SOURCE_ARTIFACT_MISMATCH")
    return validate_spans(locate_anchors(data))


def verified_anchors(artifact_path, *, review_root):
    """Reproduce retained verification lineage before a/i body inspection."""
    try:
        if type(artifact_path) is not str and not isinstance(artifact_path, Path):
            _fail("SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID")
        root = Path(review_root)
        data = _verified_bytes(artifact_path,
            artifact_review_root=root / "gameplay-rules-artifact-verification",
            source_root=root / "gameplay-rules-source-versioning",
            discovery_root=root / "gameplay-rules-release-discovery-closure")
    except (OSError, TypeError, ValueError, GameplayContractError):
        _fail("SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID")
    return verify_bytes(data)
