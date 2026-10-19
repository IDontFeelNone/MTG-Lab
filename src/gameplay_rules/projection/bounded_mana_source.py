"""Exact release-specific blocks for thirteen authorized mana-ability units.

Only the fixed 605 family and its immediate heading boundaries are recognized.
The locator returns offsets and hashes, never official prose. Fixture inspection
has no verified-source authority; real projection construction requires both
retained verification lineage and the exact owner-supplied artifact bytes.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from gameplay_rules.errors import GameplayContractError

from .contracts import ARTIFACT_BYTE_LENGTH, ARTIFACT_HASH, EFFECTIVE_DATE
from .source import _verified_bytes


ANCHOR_TYPE = "MULTI_LINE_RULE_BLOCK_ANCHOR"
SPAN_POLICY = "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR"
_REFERENCES = (
    "605.1", "605.1a", "605.1b", "605.2", "605.3", "605.3a", "605.3b",
    "605.3c", "605.4", "605.4a", "605.5", "605.5a", "605.5b",
)
_NEXT = dict(zip(_REFERENCES, (*_REFERENCES[1:], "606")))
_MARKERS = {
    reference: (reference + (". " if reference[-1].isdigit() else " ")).encode("ascii")
    for reference in _REFERENCES
}
_SECTION = b"605. Mana Abilities"
_TERMINAL = b"606. Loyalty Abilities"
_SEPARATOR = b"\xc2\xa0"
_EXAMPLE = b"Example: "
_EXAMPLE_OWNERS = frozenset(("605.2", "605.4a"))
_NUMBERED_START = re.compile(rb"^[1-9][0-9]{2}\.[0-9]+[a-z]?(?:\.)?(?:[ \t]|$)")
_FAMILY_TOKEN = re.compile(rb"^605(?:\.[^ \t]*)?(?:[ \t]|$)")
_WELL_FORMED_FAMILY = re.compile(rb"^605\.[1-9][0-9]*(?:\.[ \t]|[a-z][ \t])")
_CITATION = re.compile(
    rb"(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?![0-9A-Za-z]|\.[0-9A-Za-z])"
)
_DIRECT = {
    "605.1": frozenset(),
    "605.1a": frozenset(("115.6", "606")),
    "605.1b": frozenset(("115.6", "605.1a")),
    "605.2": frozenset(),
    "605.3": frozenset(("602.2",)),
    "605.3a": frozenset(),
    "605.3b": frozenset(("405.6c",)),
    "605.3c": frozenset(),
    "605.4": frozenset(("603",)),
    "605.4a": frozenset(),
    "605.5": frozenset(("605.1a", "605.1b")),
    "605.5a": frozenset(),
    "605.5b": frozenset(),
}


def _fail(code: str) -> None:
    raise GameplayContractError("bounded_mana_source", code)


def _anchor(reference: str, first: int, last: int, start: int, end: int,
            digest: str, *, artifact_hash: str = ARTIFACT_HASH) -> dict:
    return {
        "rule_reference": reference,
        "artifact_hash": artifact_hash,
        "effective_date": EFFECTIVE_DATE,
        "anchor_type": ANCHOR_TYPE,
        "span_policy": SPAN_POLICY,
        "starting_physical_line": first,
        "ending_physical_line": last,
        "line_count": last - first + 1,
        "byte_start": start,
        "byte_end": end,
        "span_sha256": "sha256:" + digest,
    }


# Independently verified hash-only metadata; no historical anchor is converted.
VERIFIED_ANCHORS = tuple(MappingProxyType(anchor) for anchor in (
    _anchor("605.1", 2687, 2687, 335736, 336080,
            "18954479ef81599aac41cb624e13c2b7378512f8d16fe31d59e0bd9340ece880"),
    _anchor("605.1a", 2689, 2689, 336084, 336550,
            "ab1518e4c1e43bc256e57837e21bf57b5244655d36b7753201efb02d1a648e89"),
    _anchor("605.1b", 2691, 2691, 336554, 336900,
            "86aa199197be997cd5ef423dd76cebe7b22049f8a1dd1dc48c2d2da20228d297"),
    _anchor("605.2", 2693, 2694, 336904, 337212,
            "e6da5a5017653d1a73cdc706a64d4d137b5bec7a8b7a83c6fb3d2cca6d74a765"),
    _anchor("605.3", 2696, 2696, 337216, 337369,
            "7727aab49f9e6b26f0dd7a93d79585a85566931539f9c873cc14546a9a3a68f7"),
    _anchor("605.3a", 2698, 2698, 337373, 337699,
            "815b98f7997a3391832e90c81d0a8252f686ba180e5bd3dd7c52da44832b3f09"),
    _anchor("605.3b", 2700, 2700, 337703, 337901,
            "07ca77acc153aa35336d59801f8e65acaac715840389af7957b94d1cb580df50"),
    _anchor("605.3c", 2702, 2702, 337905, 338023,
            "d99f3e22c43fb6df2d5cc184df5924c97946ca7e067944df1d96a215c116ba49"),
    _anchor("605.4", 2704, 2704, 338027, 338191,
            "4eeae4d67334e5a4733746b15ec5742590bc81daa31692c7b4e62ef0667cce78"),
    _anchor("605.4a", 2706, 2707, 338195, 338691,
            "3bf1fafa66595e0114c76f9ac5693ce55314d6a53d6f8d0ac2048b981ca85cfe"),
    _anchor("605.5", 2709, 2709, 338695, 338808,
            "9b1f6687ddc70ab7e37c947d49553a41552e61995a02d3a7feabd4d5bac0c22e"),
    _anchor("605.5a", 2711, 2711, 338812, 339249,
            "260dca3d7bd54ad30b44b2abcd699a3d58de1e57b290b03f6574ef36742eb9b5"),
    _anchor("605.5b", 2713, 2713, 339253, 339572,
            "6d80a3dad14c0b2173afe348e083d3548ab0546bbe0c99d6b3fc862f98dd82b3"),
))


def _physical_lines(data: bytes) -> list[tuple[int, bytes, int]]:
    """Transient physical lines: byte start, body, end including terminator."""
    lines = []
    for match in re.finditer(rb"[^\r\n]*(?:\r\n|\r|\n|$)", data):
        if match.start() == match.end():
            continue
        raw = match.group()
        if raw.endswith(b"\r\n"):
            body = raw[:-2]
        elif raw.endswith((b"\r", b"\n")):
            body = raw[:-1]
        else:
            body = raw
        lines.append((match.start(), body, match.end()))
    return lines


def _marker(body: bytes) -> str | None:
    if body == _SECTION:
        return "605"
    if body == _TERMINAL:
        return "606"
    for reference, marker in _MARKERS.items():
        if body.startswith(marker):
            if not body[len(marker):].strip():
                _fail("MALFORMED_NUMBERING")
            return reference
    if _FAMILY_TOKEN.match(body):
        if _WELL_FORMED_FAMILY.match(body):
            _fail("UNEXPECTED_SELECTED_FAMILY_SHAPE")
        _fail("MALFORMED_NUMBERING")
    return None


def validate_bounded_mana_spans(anchors) -> None:
    """Reject malformed or overlapping metadata without claiming byte access."""
    if not isinstance(anchors, (tuple, list)) or len(anchors) != len(_REFERENCES):
        _fail("MISSING_RULE_START")
    if any(not isinstance(anchor, Mapping) for anchor in anchors):
        _fail("MALFORMED_SOURCE_SPAN")
    if tuple(anchor.get("rule_reference") for anchor in anchors) != _REFERENCES:
        _fail("MISSING_OR_DUPLICATE_SELECTED_REFERENCE")
    prior_end = prior_last = -1
    for anchor in anchors:
        fields = ("byte_start", "byte_end", "starting_physical_line",
                  "ending_physical_line", "line_count")
        if any(type(anchor.get(field)) is not int for field in fields):
            _fail("MALFORMED_SOURCE_SPAN")
        start, end = anchor["byte_start"], anchor["byte_end"]
        first, last = anchor["starting_physical_line"], anchor["ending_physical_line"]
        if start < 0 or end <= start or first < 1 or last < first:
            _fail("MALFORMED_SOURCE_SPAN")
        if anchor["line_count"] != last - first + 1:
            _fail("MALFORMED_SOURCE_SPAN")
        if start < prior_end or first <= prior_last:
            _fail("OVERLAPPING_SELECTED_SPANS")
        prior_end, prior_last = end, last


def locate_bounded_mana_anchors(data: bytes) -> list[dict]:
    """Inspect only the fixed family, including synthetic structural fixtures.

    This operation does not verify an artifact. Its returned artifact hash
    describes the supplied bytes, including fixture bytes. Production source
    authority requires the separate exact-artifact verification operation.
    """
    if not isinstance(data, bytes) or not data or len(data) > ARTIFACT_BYTE_LENGTH + 1:
        _fail("INVALID_SOURCE_BYTES")
    lines = _physical_lines(data)
    starts = {}
    markers = {}
    for index, (_, body, _) in enumerate(lines):
        reference = _marker(body)
        if reference is not None:
            markers[index] = reference
        if reference in _REFERENCES:
            if reference in starts:
                _fail("DUPLICATE_RULE_START")
            starts[reference] = index
    if set(starts) != set(_REFERENCES):
        _fail("MISSING_RULE_START")
    if tuple(sorted(starts, key=starts.get)) != _REFERENCES:
        _fail("UNEXPECTED_SELECTED_FAMILY_SHAPE")
    first_selected = starts[_REFERENCES[0]]
    heading = first_selected - 1
    if heading >= 0 and lines[heading][1] == _SEPARATOR:
        heading -= 1
    if heading < 0 or markers.get(heading) != "605":
        _fail("UNEXPECTED_SELECTED_FAMILY_SHAPE")

    artifact_hash = "sha256:" + hashlib.sha256(data).hexdigest()
    anchors = []
    for reference in _REFERENCES:
        first = starts[reference]
        last = first
        example_seen = False
        index = first + 1
        while True:
            if index >= len(lines):
                _fail("AMBIGUOUS_TERMINATION")
            body = lines[index][1]
            next_reference = markers.get(index)
            if next_reference is not None:
                if next_reference != _NEXT[reference]:
                    _fail("AMBIGUOUS_TERMINATION")
                break
            if body == _SEPARATOR:
                following = index + 1
                if following < len(lines) and lines[following][1].startswith(b"Example:"):
                    _fail("AMBIGUOUS_EXAMPLE_OWNERSHIP")
                if following >= len(lines) or markers.get(following) != _NEXT[reference]:
                    _fail("AMBIGUOUS_TERMINATION")
                break
            if body.startswith(b"Example:"):
                if (reference not in _EXAMPLE_OWNERS or not body.startswith(_EXAMPLE)
                        or not body[len(_EXAMPLE):].strip() or example_seen):
                    _fail("AMBIGUOUS_EXAMPLE_OWNERSHIP")
                example_seen = True
                last = index
                index += 1
                continue
            if body.startswith(b"  ") and body[2:].strip():
                stripped = body.lstrip(b" \t")
                if stripped.startswith(b"Example:"):
                    _fail("AMBIGUOUS_EXAMPLE_OWNERSHIP")
                if _NUMBERED_START.match(stripped) or stripped.startswith(b"605."):
                    _fail("MALFORMED_NUMBERING")
                last = index
                index += 1
                continue
            if _NUMBERED_START.match(body):
                _fail("AMBIGUOUS_TERMINATION")
            _fail("AMBIGUOUS_CONTINUATION")
        start = lines[first][0]
        end = lines[last][0] + len(lines[last][1])
        anchors.append(_anchor(reference, first + 1, last + 1, start, end,
            hashlib.sha256(data[start:end]).hexdigest(), artifact_hash=artifact_hash))
    validate_bounded_mana_spans(anchors)
    return anchors


def _verify_selected_citations(data: bytes, anchors: list[dict]) -> None:
    """Check numbered citations solely inside the thirteen selected blocks."""
    for anchor in anchors:
        reference = anchor["rule_reference"]
        block = data[anchor["byte_start"]:anchor["byte_end"]]
        body = block[len(_MARKERS[reference]):]
        citations = {match.group(1).decode("ascii") for match in _CITATION.finditer(body)}
        if reference == "605.5":
            if "605.1a\u2013b".encode("utf-8") not in body:
                _fail("SOURCE_CITATION_RANGE_MISMATCH")
            citations.add("605.1b")
        if citations != _DIRECT[reference]:
            _fail("SOURCE_DIRECT_REFERENCE_MISMATCH")


def verify_bounded_mana_bytes(data: bytes) -> list[dict]:
    """Require the exact artifact before creating verified block metadata."""
    if (not isinstance(data, bytes) or len(data) != ARTIFACT_BYTE_LENGTH
            or "sha256:" + hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail("VERIFIED_SOURCE_ARTIFACT_MISMATCH")
    anchors = locate_bounded_mana_anchors(data)
    if anchors != [dict(anchor) for anchor in VERIFIED_ANCHORS]:
        _fail("VERIFIED_SOURCE_BLOCK_MISMATCH")
    _verify_selected_citations(data, anchors)
    return anchors


def build_bounded_mana_projection(artifact_path, *, artifact_review_root,
                                 source_root, discovery_root):
    """Reproduce retained source lineage and build the non-executable record."""
    from .bounded_mana_contracts import create_projection
    try:
        if artifact_path is None or not Path(artifact_path).is_file():
            _fail("MISSING_VERIFIED_SOURCE_ARTIFACT")
    except (OSError, TypeError, ValueError):
        _fail("MISSING_VERIFIED_SOURCE_ARTIFACT")
    data = _verified_bytes(artifact_path, artifact_review_root=artifact_review_root,
                           source_root=source_root, discovery_root=discovery_root)
    return create_projection(verify_bounded_mana_bytes(data))


def verify_bounded_mana_source(projection, artifact_path, *,
        artifact_review_root, source_root, discovery_root):
    """Reproduce all block anchors and authored metadata against actual bytes."""
    from .bounded_mana_contracts import BoundedManaProjection
    if not isinstance(projection, BoundedManaProjection):
        _fail("TYPED_NON_EXECUTABLE_PROJECTION_REQUIRED")
    projection.verify()
    reproduced = build_bounded_mana_projection(artifact_path,
        artifact_review_root=artifact_review_root, source_root=source_root,
        discovery_root=discovery_root)
    if projection.to_dict() != reproduced.to_dict():
        _fail("PROJECTION_SOURCE_DOES_NOT_REPRODUCE")
    return {
        "status": "VERIFIED_EXACT_SOURCE_BLOCKS", "projection_id": projection.identity,
        "selected_rule_count": 13, "artifact_hash": ARTIFACT_HASH,
        "byte_length": ARTIFACT_BYTE_LENGTH, "anchor_type": ANCHOR_TYPE,
        "span_policy": SPAN_POLICY, "source_body_retained": False,
        "real_rules_executable": False,
    }


# Retain the established projection-source API spelling for callers.
verify_bounded_mana_projection_source = verify_bounded_mana_source
