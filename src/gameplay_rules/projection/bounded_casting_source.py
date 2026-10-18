"""Release-specific source blocks for five authorized casting source units.

The locator recognizes only this allowlist and its fixed immediate boundaries.
It returns hashes and offsets, never source text. Structural fixture inspection
does not verify an artifact; production construction requires the retained
verification lineage and exact external artifact bytes.
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
_REFERENCES = ("601.2", "601.2b", "601.2f", "601.2g", "601.2h")
_NEXT = {
    "601.2": "601.2a", "601.2b": "601.2c", "601.2f": "601.2g",
    "601.2g": "601.2h", "601.2h": "601.2i",
}
_TOKENS = ("601.2", *("601.2" + suffix for suffix in "abcdefghi"))
_MARKERS = {
    reference: (reference + (". " if reference == "601.2" else " ")).encode("ascii")
    for reference in _TOKENS
}
_SEPARATOR = b"\xc2\xa0"
_EXAMPLE = b"Example: "
_NUMBERED_START = re.compile(rb"^[1-9][0-9]{2}\.[0-9]+[a-z]?(?:\.)?(?:[ \t]|$)")
_FAMILY_TOKEN = re.compile(rb"^601\.2([A-Za-z0-9.]*)(?:[ \t]|$)")
_CITATION = re.compile(
    rb"(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)(?![0-9A-Za-z.])"
)
_DIRECT = {
    "601.2": frozenset(("601.2a", "601.2b", "601.2c", "601.2d",
                         "601.2f", "601.2g", "601.2h", "601.3", "733")),
    "601.2b": frozenset(("700.2", "702.47", "118.8", "118.9", "601.2f", "107.3")),
    "601.2f": frozenset(("601.2b",)),
    "601.2g": frozenset(("605",)),
    "601.2h": frozenset(),
}


def _fail(code: str) -> None:
    raise GameplayContractError("bounded_casting_source", code)


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


# Independently verified metadata only. No historical anchor is converted.
VERIFIED_ANCHORS = tuple(MappingProxyType(anchor) for anchor in (
    _anchor("601.2", 2461, 2461, 293557, 294277,
            "539f57186e7b00730332bdc37ab8971487c841808f98711f966902ef936ccd32"),
    _anchor("601.2b", 2465, 2465, 294960, 296466,
            "b29d06932bab059464552b9ff28166320206bd0def60de3639b155e1798308b2"),
    _anchor("601.2f", 2474, 2474, 298925, 299886,
            "0e5bab9baa20723de7bca986f8aad67092fb5cb90121850d21971bc7c6ec7df8"),
    _anchor("601.2g", 2476, 2476, 299890, 300089,
            "2e1360bd5e7e13b76ca1eb35e53e1958252a84074b0d270c0d7c697834e5c24e"),
    _anchor("601.2h", 2478, 2479, 300093, 300737,
            "1f64adef4e78920e04ee3b815aafed7884e3c340b4cf187f85c9ce78f9ec4e5f"),
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
    for reference, marker in _MARKERS.items():
        if body.startswith(marker):
            if not body[len(marker):].strip():
                _fail("MALFORMED_NUMBERING")
            return reference
    if _FAMILY_TOKEN.match(body):
        _fail("MALFORMED_NUMBERING")
    return None


def validate_bounded_casting_spans(anchors) -> None:
    """Reject invalid or overlapping metadata without claiming byte access."""
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


def locate_bounded_casting_anchors(data: bytes) -> list[dict]:
    """Inspect the fixed five-unit structure, including synthetic fixtures.

    This function deliberately does not grant verified-artifact authority. Its
    artifact hash describes the supplied bytes. Exact source verification is a
    separate mandatory operation for a real projection.
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
                if not body.startswith(_EXAMPLE) or not body[len(_EXAMPLE):].strip() or example_seen:
                    _fail("AMBIGUOUS_EXAMPLE_OWNERSHIP")
                example_seen = True
                last = index
                index += 1
                continue
            if body.startswith(b"  ") and body[2:].strip():
                stripped = body.lstrip(b" \t")
                if stripped.startswith(b"Example:"):
                    _fail("AMBIGUOUS_EXAMPLE_OWNERSHIP")
                if _NUMBERED_START.match(stripped) or stripped.startswith(b"601.2"):
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
    validate_bounded_casting_spans(anchors)
    return anchors


def _verify_selected_citations(data: bytes, anchors: list[dict]) -> None:
    """Check citations only inside the five selected, already bounded units."""
    for anchor in anchors:
        reference = anchor["rule_reference"]
        block = data[anchor["byte_start"]:anchor["byte_end"]]
        body = block[len(_MARKERS[reference]):]
        citations = {match.group(1).decode("ascii") for match in _CITATION.finditer(body)}
        if reference == "601.2":
            for first, final in (("a", "d"), ("f", "h")):
                marker = ("601.2" + first + "\u2013" + final).encode("utf-8")
                if marker not in body:
                    _fail("SOURCE_CITATION_RANGE_MISMATCH")
                citations.update("601.2" + chr(value)
                                 for value in range(ord(first), ord(final) + 1))
        if citations != _DIRECT[reference]:
            _fail("SOURCE_DIRECT_REFERENCE_MISMATCH")


def verify_bounded_casting_bytes(data: bytes) -> list[dict]:
    """Require the exact artifact before creating verified block metadata."""
    if (not isinstance(data, bytes) or len(data) != ARTIFACT_BYTE_LENGTH
            or "sha256:" + hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail("VERIFIED_SOURCE_ARTIFACT_MISMATCH")
    anchors = locate_bounded_casting_anchors(data)
    if anchors != [dict(anchor) for anchor in VERIFIED_ANCHORS]:
        _fail("VERIFIED_SOURCE_BLOCK_MISMATCH")
    _verify_selected_citations(data, anchors)
    return anchors


def build_bounded_casting_projection(artifact_path, *, artifact_review_root,
                                    source_root, discovery_root):
    """Reproduce retained source verification and create the authorized record."""
    from .bounded_casting_contracts import create_projection
    try:
        if artifact_path is None or not Path(artifact_path).is_file():
            _fail("MISSING_VERIFIED_SOURCE_ARTIFACT")
    except (OSError, TypeError, ValueError):
        _fail("MISSING_VERIFIED_SOURCE_ARTIFACT")
    data = _verified_bytes(artifact_path, artifact_review_root=artifact_review_root,
                           source_root=source_root, discovery_root=discovery_root)
    return create_projection(verify_bounded_casting_bytes(data))


def verify_bounded_casting_projection_source(projection, artifact_path, *,
        artifact_review_root, source_root, discovery_root):
    """Reproduce all anchors and authored metadata against the real artifact."""
    from .bounded_casting_contracts import BoundedCastingProjection
    if not isinstance(projection, BoundedCastingProjection):
        _fail("TYPED_NON_EXECUTABLE_PROJECTION_REQUIRED")
    projection.verify()
    reproduced = build_bounded_casting_projection(artifact_path,
        artifact_review_root=artifact_review_root, source_root=source_root,
        discovery_root=discovery_root)
    if projection.to_dict() != reproduced.to_dict():
        _fail("PROJECTION_SOURCE_DOES_NOT_REPRODUCE")
    return {
        "status": "VERIFIED_EXACT_SOURCE_BLOCKS", "projection_id": projection.identity,
        "selected_rule_count": 5, "artifact_hash": ARTIFACT_HASH,
        "byte_length": ARTIFACT_BYTE_LENGTH, "anchor_type": ANCHOR_TYPE,
        "span_policy": SPAN_POLICY, "source_body_retained": False,
        "real_rules_executable": False,
    }
