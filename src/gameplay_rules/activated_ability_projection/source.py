"""Fresh raw-byte anchors for exactly the authorized three activation units.

This fixed release locator returns metadata, never source bodies. Fixture
location is separate from exact-artifact verification and retained lineage.
The terminal 602.3 marker is structural context; its body is never inspected.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
from collections.abc import Mapping

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.bounded_mana_source import (
    ANCHOR_TYPE, SPAN_POLICY, _physical_lines,
)
from gameplay_rules.projection.contracts import (
    ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, _freeze, _json,
)
from gameplay_rules.projection.source import _verified_bytes

SELECTED_REFERENCES = ("602.2", "602.2a", "602.2b")
IMPORTED_STAGES = tuple("601.2" + letter for letter in "bcdefghi")
DIRECT_REFERENCES = _freeze({
    "602.2": ["733"], "602.2a": ["701.20a"], "602.2b": ["601.2f"],
})
ANCHOR_ID_DOMAIN = "gameplay-cr-bounded-activated-ability-anchor-v1"
_MARKERS = {
    "602.2": b"602.2. ", "602.2a": b"602.2a ",
    "602.2b": b"602.2b ", "602.3": b"602.3. ",
}
_CITATION = re.compile(
    rb"(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)"
    rb"(?![0-9A-Za-z]|\.[0-9A-Za-z])"
)


def _fail(code):
    raise GameplayContractError("bounded_activated_ability_source", code)


def anchor_identity(anchor):
    body = {key: value for key, value in _json(anchor).items() if key != "anchor_id"}
    return "sha256:" + sha256_identity({"domain": ANCHOR_ID_DOMAIN, "content": body})


def _anchor(reference, line, start, end, digest, *, artifact_hash=ARTIFACT_HASH):
    result = {
        "rule_reference": reference, "artifact_hash": artifact_hash,
        "effective_date": EFFECTIVE_DATE, "anchor_type": ANCHOR_TYPE,
        "span_policy": SPAN_POLICY, "starting_physical_line": line,
        "ending_physical_line": line, "line_count": 1,
        "byte_start": start, "byte_end": end, "span_sha256": "sha256:" + digest,
    }
    result["anchor_id"] = anchor_identity(result)
    return result


# Independently reproduced from this task's exact owner artifact. Matching raw
# spans confirm the historical review fingerprints without converting them.
VERIFIED_ANCHORS = _freeze([
    _anchor("602.2", 2533, 308743, 309432,
            "91a325f8311b0796b927e19e83e95564ee1dff3bbdc1daf03e964a82f8296761"),
    _anchor("602.2a", 2535, 309436, 309979,
            "e36fbb27a8bc6cccc20d5bc22f5a6d1bc4cc7f8fb377ec070478d7de5ffaefb6"),
    _anchor("602.2b", 2537, 309983, 310314,
            "d76ff3ff7e6bfa31f6866ba002f6cfaf941025f6cc260d754459ad294125b835"),
])


def validate_spans(anchors):
    """Check exact types and identities without claiming source-byte access."""
    if not isinstance(anchors, (list, tuple)) or len(anchors) != 3:
        _fail("EXACT_THREE_RULE_ALLOWLIST_REQUIRED")
    if any(not isinstance(anchor, Mapping) for anchor in anchors):
        _fail("MALFORMED_SOURCE_SPAN")
    if tuple(anchor.get("rule_reference") for anchor in anchors) != SELECTED_REFERENCES:
        _fail("EXACT_THREE_RULE_ALLOWLIST_REQUIRED")
    prior_end = prior_line = -1
    for anchor in anchors:
        if set(anchor) != set(VERIFIED_ANCHORS[0]):
            _fail("MALFORMED_SOURCE_SPAN")
        numeric = ("byte_start", "byte_end", "starting_physical_line", "ending_physical_line", "line_count")
        if any(type(anchor.get(key)) is not int for key in numeric):
            _fail("MALFORMED_SOURCE_SPAN")
        if (anchor["byte_start"] < 0 or anchor["byte_end"] <= anchor["byte_start"]
                or anchor["byte_end"] > ARTIFACT_BYTE_LENGTH
                or anchor["starting_physical_line"] < 1
                or anchor["line_count"] != 1
                or anchor["ending_physical_line"] != anchor["starting_physical_line"]):
            _fail("MALFORMED_SOURCE_SPAN")
        if anchor["byte_start"] < prior_end or anchor["starting_physical_line"] <= prior_line:
            _fail("OVERLAPPING_SELECTED_SPANS")
        for field in ("artifact_hash", "span_sha256", "anchor_id"):
            if type(anchor[field]) is not str or not re.fullmatch(r"sha256:[0-9a-f]{64}", anchor[field]):
                _fail("MALFORMED_SOURCE_SPAN")
        if (anchor["effective_date"] != EFFECTIVE_DATE or anchor["anchor_type"] != ANCHOR_TYPE
                or anchor["span_policy"] != SPAN_POLICY
                or anchor["anchor_id"] != anchor_identity(anchor)):
            _fail("MALFORMED_SOURCE_SPAN")
        prior_end, prior_line = anchor["byte_end"], anchor["ending_physical_line"]


def locate_anchors(data):
    """Locate only four fixed markers and inspect only the selected bodies.

    One body line per selected block plus a separator is the reviewed local
    structure. Any changed structure requires a new scope decision. The final
    line terminator and separator are excluded without byte normalization.
    """
    if type(data) is not bytes or not data or len(data) > ARTIFACT_BYTE_LENGTH + 1:
        _fail("INVALID_SOURCE_BYTES")
    lines = _physical_lines(data)
    starts = {}
    for index, (_, body, _) in enumerate(lines):
        for reference, marker in _MARKERS.items():
            if body.startswith(marker):
                if reference in starts:
                    _fail("DUPLICATE_LOCAL_MARKER")
                if reference != "602.3" and not body[len(marker):].strip():
                    _fail("MALFORMED_NUMBERING")
                starts[reference] = index
            elif (body.startswith(reference.encode("ascii"))
                    and (len(body) == len(reference)
                         or body[len(reference):len(reference)+1] in (b".", b" ", b"\t"))):
                _fail("MALFORMED_NUMBERING")
    if set(starts) != set(_MARKERS):
        _fail("MISSING_LOCAL_MARKER")
    if tuple(sorted(starts, key=starts.get)) != tuple(_MARKERS):
        _fail("ACTIVATED_ABILITY_PROCEDURE_SCOPE_INSUFFICIENT")
    result = []
    for reference, next_reference in zip(SELECTED_REFERENCES, (*SELECTED_REFERENCES[1:], "602.3")):
        first, terminal = starts[reference], starts[next_reference]
        if terminal != first + 2 or lines[first + 1][1] != b"\xc2\xa0":
            _fail("ACTIVATED_ABILITY_PROCEDURE_SCOPE_INSUFFICIENT")
        start, block, _ = lines[first]
        result.append(_anchor(reference, first + 1, start, start + len(block),
            hashlib.sha256(block).hexdigest(), artifact_hash="sha256:" + hashlib.sha256(data).hexdigest()))
    validate_spans(result)
    return result


def verify_bytes(data):
    """Reproduce fresh anchors and relationships from the exact original bytes."""
    if (type(data) is not bytes or len(data) != ARTIFACT_BYTE_LENGTH
            or "sha256:" + hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail("VERIFIED_SOURCE_ARTIFACT_MISMATCH")
    if not re.search(rb"effective[^\r\n]*September 25, 2026", data[:3000], re.I):
        _fail("EFFECTIVE_DATE_MISMATCH")
    anchors = locate_anchors(data)
    if deterministic_json(anchors) != deterministic_json(_json(VERIFIED_ANCHORS)):
        _fail("VERIFIED_SOURCE_BLOCK_MISMATCH")
    for anchor in anchors:
        reference = anchor["rule_reference"]
        block = data[anchor["byte_start"]:anchor["byte_end"]]
        body = block[len(_MARKERS[reference]):]
        citations = tuple(match.group(1).decode("ascii") for match in _CITATION.finditer(body))
        expected = (("601.2b", "601.2f") if reference == "602.2b"
                    else tuple(DIRECT_REFERENCES[reference]))
        if citations != expected:
            _fail("OUTGOING_REFERENCE_MISMATCH")
        if reference == "602.2b":
            if body.count("601.2b\u2013i".encode("utf-8")) != 1:
                _fail("IMPORTED_RANGE_MISMATCH")
            if re.search(rb"applicable|appropriate|similar|except|necessary", body):
                _fail("IMPORT_QUALIFIER_MISMATCH")
    return anchors


def verified_anchors(artifact_path, *, review_root):
    """Verify source lineage before returning newly reproduced anchor records."""
    root = Path(review_root)
    try:
        data = _verified_bytes(artifact_path,
            artifact_review_root=root / "gameplay-rules-artifact-verification",
            source_root=root / "gameplay-rules-source-versioning",
            discovery_root=root / "gameplay-rules-release-discovery-closure")
    except (OSError, TypeError, ValueError):
        _fail("SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID")
    return verify_bytes(data)


verify_source = verified_anchors
