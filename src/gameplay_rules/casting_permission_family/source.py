"""Closed 601.3 family: marker freeze precedes owned-body inspection.

Only metadata is returned. Exact artifact and historical lineage verification
precede all source reproduction; other rule bodies are never selected.
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
from .scope import SELECTED_REFERENCES

SOURCE_ENV = "MTGLAB_CASTING_PERMISSION_FAMILY_SOURCE"
ANCHOR_ID_DOMAIN = "gameplay-cr-casting-permission-family-anchor-v1"
# Frozen from marker-only inspection, after fresh complete artifact/lineage verification.
# ref, first/last owned lines, byte interval, fingerprint, following marker/line, examples.
FAMILY_SPEC = (
    ("601.3", 2483, 2483, 301086, 301243, "555ec7a88f05e7b3f2af60d4002da6dde0d2f0071a289cbdc1af24152d4ad5c8", "601.3a", 2485, 0),
    ("601.3a", 2485, 2486, 301247, 301920, "5a02aaed5bd1642e183aa591a80e03d2c286d826d275ce5b5494ba57247fd977", "601.3b", 2488, 1),
    ("601.3b", 2488, 2489, 301924, 302571, "6a8ee79679d0a6db1b60619730d7c64320a088e27070a3f0fe16e32bf7bee6d8", "601.3c", 2491, 1),
    ("601.3c", 2491, 2491, 302575, 302765, "2c2ffb71ffee09d75106148d5e5e44cc865a14acc9612f555a5f294ced43cb45", "601.3d", 2493, 0),
    ("601.3d", 2493, 2493, 302769, 302935, "68011e022c5b15f8fff223cbac005e1c32413d9c014794450bab567c38034c3a", "601.3e", 2495, 0),
    ("601.3e", 2495, 2497, 302939, 304033, "5b0b0971df4012a5301071738d630def17273b66c7972512023b84be6ef395e0", "601.3f", 2499, 2),
    ("601.3f", 2499, 2499, 304037, 304241, "a71eac5447cd09c8b33862cd591fe584e1ed21a15aeadf9b10c385135bc0ce13", "601.4", 2501, 0),
)
_MARKER = re.compile(rb"^([1-9][0-9]{2}\.[0-9]+[a-z]*)(?:\. | )")
_CITATION = re.compile(rb"(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?![0-9A-Za-z]|\.[0-9A-Za-z])")


def _fail(code):
    raise GameplayContractError("casting_permission_family_source", code)


def anchor_identity(anchor):
    raw = _canonical_candidate(anchor)
    if type(anchor) is not dict:
        _fail("PLAIN_SOURCE_ANCHOR_REQUIRED")
    body = {k: v for k, v in json.loads(raw).items() if k != "anchor_id"}
    return "sha256:" + sha256_identity({"domain": ANCHOR_ID_DOMAIN, "content": body})


def _anchor(ref, first, last, start, end, digest, following, next_line, examples, artifact_hash):
    value = {"rule_reference": ref, "artifact_hash": artifact_hash, "effective_date": EFFECTIVE_DATE,
        "anchor_type": ANCHOR_TYPE, "span_policy": SPAN_POLICY,
        "starting_physical_line": first, "ending_physical_line": last,
        "line_count": last-first+1, "owned_continuation_line_count": last-first,
        "owned_example_line_count": examples, "byte_start": start, "byte_end": end,
        "span_length": end-start, "span_sha256": "sha256:"+digest,
        "following_marker": {"rule_reference": following, "physical_line": next_line,
            "body_inspected_as_boundary_context": False}}
    value["anchor_id"] = anchor_identity(value)
    return value


VERIFIED_ANCHORS = _freeze([_anchor(*spec, ARTIFACT_HASH) for spec in FAMILY_SPEC])
FROZEN_INVENTORY = _freeze({"selection_basis": "EXACT_STRUCTURAL_FAMILY_MARKER_ONLY_BEFORE_BODY",
    "selected_references": list(SELECTED_REFERENCES), "selected_unit_count": len(FAMILY_SPEC),
    "markers": [{"rule_reference": s[0], "physical_line": s[1]} for s in FAMILY_SPEC],
    "following_boundary": {"rule_reference": "601.4", "physical_line": 2501},
    "outgoing_dependency_traversal": False})


def validate_spans(anchors):
    if anchors is VERIFIED_ANCHORS:
        anchors = _json(anchors)
    raw = _canonical_candidate(anchors)
    if type(anchors) is not list or raw != _canonical_candidate(_json(VERIFIED_ANCHORS)):
        _fail("EXACT_FROZEN_COMPLETE_FAMILY_ANCHORS_REQUIRED")
    snapshot = json.loads(raw)
    for anchor in snapshot:
        if anchor["anchor_id"] != anchor_identity(anchor):
            _fail("SOURCE_ANCHOR_OWN_IDENTITY_INVALID")
    return snapshot


def marker_inventory(data):
    """Use numbered prefixes only; 601.30 is a sibling, never a child."""
    if type(data) is not bytes or not data or len(data) > ARTIFACT_BYTE_LENGTH + 1:
        _fail("INVALID_SOURCE_BYTES")
    markers = []
    for number, (_, body, _) in enumerate(_physical_lines(data), 1):
        match = _MARKER.match(body[:32])
        if match:
            markers.append((match[1].decode("ascii"), number))
    parents = [i for i, row in enumerate(markers) if row[0] == "601.3"]
    if len(parents) != 1:
        _fail("CASTING_PERMISSION_FAMILY_SCOPE_INSUFFICIENT")
    i = parents[0]
    selected = [markers[i]]
    for row in markers[i+1:]:
        if re.fullmatch(r"601\.3[a-z]+", row[0]):
            selected.append(row)
        else:
            boundary = row
            break
    else:
        _fail("CASTING_PERMISSION_FAMILY_SCOPE_INSUFFICIENT")
    if tuple(selected) != tuple((s[0], s[1]) for s in FAMILY_SPEC) or boundary != ("601.4", 2501):
        _fail("CASTING_PERMISSION_FAMILY_SCOPE_INSUFFICIENT")
    return _json(FROZEN_INVENTORY)


def locate_anchors(data):
    """Check the frozen family before selecting bodies; invented fixtures are not authority."""
    marker_inventory(data)
    lines = _physical_lines(data)
    result = []
    artifact_hash = "sha256:" + hashlib.sha256(data).hexdigest()
    for ref, first, last, _, _, _, following, next_line, examples in FAMILY_SPEC:
        owned = lines[first-1:last]
        prefix = (ref + (". " if ref[-1].isdigit() else " ")).encode("ascii")
        boundary_prefix = (following + (". " if following[-1].isdigit() else " ")).encode("ascii")
        if (len(owned) != last-first+1 or not owned[0][1].startswith(prefix)
                or not owned[0][1][len(prefix):].strip()
                or any(not row[1].startswith(b"Example: ") for row in owned[1:])
                or len(owned)-1 != examples
                or next_line != last+2 or lines[last][1] != b"\xc2\xa0"
                or not lines[next_line-1][1][:len(boundary_prefix)] == boundary_prefix):
            _fail("CASTING_PERMISSION_FAMILY_SCOPE_INSUFFICIENT")
        start, end = owned[0][0], owned[-1][0] + len(owned[-1][1])
        block = data[start:end]
        if _CITATION.findall(block[len(prefix):]):
            _fail("UNEXPECTED_LITERAL_NUMBERED_REFERENCE")
        result.append(_anchor(ref, first, last, start, end, hashlib.sha256(block).hexdigest(),
            following, next_line, examples, artifact_hash))
    return result


def verify_bytes(data):
    if (type(data) is not bytes or len(data) != ARTIFACT_BYTE_LENGTH
            or "sha256:"+hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail("VERIFIED_SOURCE_ARTIFACT_MISMATCH")
    return validate_spans(locate_anchors(data))


def verified_anchors(artifact_path, *, review_root):
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
