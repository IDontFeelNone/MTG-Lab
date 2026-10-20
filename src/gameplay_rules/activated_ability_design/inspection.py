"""Review-only inspection of three fixed September 2026 source blocks.

This release-specific check returns project-authored observations and locator
metadata. It creates no projection, rule identity, registered source anchor or
coverage edge. The external bytes and source wording remain transient.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import re

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.bounded_mana_source import _physical_lines
from gameplay_rules.projection.contracts import (
    ARTIFACT_BYTE_LENGTH, ARTIFACT_HASH, EFFECTIVE_DATE, VERIFICATION_RESULT_ID,
)
from gameplay_rules.projection.source import _verified_bytes


CANDIDATE_REFERENCES = ("602.2", "602.2a", "602.2b")
IMPORTED_STAGES = tuple("601.2" + member for member in "bcdefghi")
_MARKERS = {
    "602.2": b"602.2. ", "602.2a": b"602.2a ",
    "602.2b": b"602.2b ", "602.3": b"602.3. ",
}
_CITATION = re.compile(
    rb"(?<![0-9A-Za-z.])([1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?)"
    rb"(?![0-9A-Za-z]|\.[0-9A-Za-z])"
)
_EXPECTED = {
    "authority": "NEW_EXACT_SOURCE_INSPECTION",
    "purpose": "REVIEW_ONLY_NOT_PROJECTED",
    "review_only": True,
    "projected": False,
    "source_body_retained": False,
    "artifact_hash": ARTIFACT_HASH,
    "byte_length": ARTIFACT_BYTE_LENGTH,
    "effective_date": EFFECTIVE_DATE,
    "artifact_verification_id": VERIFICATION_RESULT_ID,
    "candidate_references": list(CANDIDATE_REFERENCES),
    "locator_policy": "REVIEW_ONLY_RAW_BLOCK_EXCLUDING_FINAL_LINE_TERMINATOR",
    "review_spans": [
        {"reference": "602.2", "starting_physical_line": 2533,
         "ending_physical_line": 2533, "line_count": 1,
         "byte_start": 308743, "byte_end": 309432,
         "span_sha256": "sha256:91a325f8311b0796b927e19e83e95564ee1dff3bbdc1daf03e964a82f8296761"},
        {"reference": "602.2a", "starting_physical_line": 2535,
         "ending_physical_line": 2535, "line_count": 1,
         "byte_start": 309436, "byte_end": 309979,
         "span_sha256": "sha256:e36fbb27a8bc6cccc20d5bc22f5a6d1bc4cc7f8fb377ec070478d7de5ffaefb6"},
        {"reference": "602.2b", "starting_physical_line": 2537,
         "ending_physical_line": 2537, "line_count": 1,
         "byte_start": 309983, "byte_end": 310314,
         "span_sha256": "sha256:d76ff3ff7e6bfa31f6866ba002f6cfaf941025f6cc260d754459ad294125b835"},
    ],
    "structure": {
        "parent": "602.2", "immediate_children": ["602.2a", "602.2b"],
        "next_marker": "602.3", "next_marker_physical_line": 2539,
        "next_body_inspected": False,
        "relationship_kind": "STRUCTURAL_NOT_DIRECT_REFERENCE",
    },
    "literal_direct_references": [
        {"from": "602.2", "to": "733", "target_coverage": "UNPROJECTED"},
        {"from": "602.2a", "to": "701.20a", "target_coverage": "UNPROJECTED"},
        {"from": "602.2b", "to": "601.2f", "target_coverage": "PROJECTED"},
    ],
    "range_import": {
        "from": "602.2b", "start": "601.2b", "end": "601.2i",
        "members": list(IMPORTED_STAGES),
        "qualification": "REMAINING_ACTIVATION_PROCESS_USES_LISTED_CASTING_STEPS",
        "application": "LISTED_RULES_APPLY_TO_ACTIVATION_AS_TO_CASTING",
        "additional_applicability_qualifier_found": False,
        "imports_601_2a": False,
        "projects_missing_members": False,
    },
    "cost_mapping": {
        "relationship_kind": "SOURCE_EXPLICIT_CONCEPT_ANALOGY",
        "casting_concept": "SPELL_MANA_COST",
        "casting_reference": "601.2f",
        "activation_concept": "ACTIVATION_COST",
        "payment_implemented": False,
        "actions_interchangeable": False,
    },
    "responsibility_findings": {
        "602.2": [
            "GENERAL_STACK_AND_COST_PROCEDURE_OVERVIEW",
            "OBJECT_CONTROLLER_AUTHORITY_WITH_OWNER_FALLBACK_WHEN_NO_CONTROLLER",
            "OBJECT_SPECIFIC_AUTHORITY_EXCEPTION",
            "ORDERED_PROCEDURE",
            "INABILITY_TO_COMPLETE_STEPS_IS_ILLEGAL_AND_REQUIRES_ROLLBACK",
            "ANNOUNCEMENTS_AND_PAYMENTS_CANNOT_BE_REVISED_AFTER_MAKING_THEM",
            "RESOLUTION_IS_EVENTUAL_DOWNSTREAM_CONTEXT",
        ],
        "602.2a": [
            "ACTIVATION_ANNOUNCEMENT",
            "HIDDEN_ZONE_ABILITY_REVEAL_CONTEXT",
            "TOPMOST_NONCARD_ABILITY_STACK_OBJECT",
            "ABILITY_TEXT_WITHOUT_OTHER_CHARACTERISTICS",
            "ACTIVATOR_IS_ABILITY_CONTROLLER",
            "STACK_RESIDENCE_UNTIL_COUNTERED_RESOLVED_OR_MOVED",
        ],
        "602.2b": [
            "REMAINING_ACTIVATION_PROCESS_REUSES_EXACT_CASTING_RANGE",
            "MANA_COST_TO_ACTIVATION_COST_CONCEPT_ANALOGY",
        ],
    },
    "source_inspection_resolves_projected_dependencies": False,
    "new_projected_rule_count": 0,
    "execution_readiness": "BLOCKED",
}


def _fail(code: str) -> None:
    raise GameplayContractError("activated_ability_design_inspection", code)


def expected_inspection() -> dict:
    """Return retained metadata for offline validation, without reading source.

    These are the findings made by this task's source inspection. Calling this
    function does not reproduce or newly verify that external inspection.
    """
    return deepcopy(_EXPECTED)


def verify_bytes(data: bytes) -> dict:
    """Require exact raw artifact bytes and inspect only the candidate blocks.

    Missing members, changed types or source mismatches cannot fall back to
    metadata. Every returned locator is explicitly review-only.
    """
    if (type(data) is not bytes or len(data) != ARTIFACT_BYTE_LENGTH
            or "sha256:" + hashlib.sha256(data).hexdigest() != ARTIFACT_HASH):
        _fail("VERIFIED_SOURCE_ARTIFACT_MISMATCH")
    # Only the small release header is read for the effective-date assertion.
    if not re.search(rb"effective[^\r\n]*September 25, 2026", data[:3000], re.I):
        _fail("EFFECTIVE_DATE_MISMATCH")
    lines = _physical_lines(data)
    starts = {}
    for index, (_, body, _) in enumerate(lines):
        for reference, marker in _MARKERS.items():
            if body.startswith(marker):
                if reference in starts:
                    _fail("DUPLICATE_LOCAL_MARKER")
                starts[reference] = index
    if set(starts) != set(_MARKERS):
        _fail("MISSING_LOCAL_MARKER")
    if tuple(sorted(starts, key=starts.get)) != tuple(_MARKERS):
        _fail("UNEXPECTED_LOCAL_STRUCTURE")
    if starts["602.3"] + 1 != _EXPECTED["structure"]["next_marker_physical_line"]:
        _fail("UNEXPECTED_LOCAL_STRUCTURE")

    observed_spans = []
    bodies = {}
    for reference, next_reference in zip(CANDIDATE_REFERENCES, (*CANDIDATE_REFERENCES[1:], "602.3")):
        first = starts[reference]
        terminal = starts[next_reference]
        # The exact source has three one-line blocks, each followed by one
        # separator. No next-rule body or outgoing dependency is inspected.
        if terminal != first + 2 or lines[first + 1][1] != b"\xc2\xa0":
            _fail("UNEXPECTED_LOCAL_BLOCK_SHAPE")
        start, block, _ = lines[first]
        end = start + len(block)
        observed_spans.append({
            "reference": reference, "starting_physical_line": first + 1,
            "ending_physical_line": first + 1, "line_count": 1,
            "byte_start": start, "byte_end": end,
            "span_sha256": "sha256:" + hashlib.sha256(block).hexdigest(),
        })
        bodies[reference] = block[len(_MARKERS[reference]):]
    if observed_spans != _EXPECTED["review_spans"]:
        _fail("REVIEW_ONLY_SPANS_MISMATCH")

    expected_citations = {
        "602.2": ("733",), "602.2a": ("701.20a",),
        # The first token belongs to the compact range, not a new direct edge.
        "602.2b": ("601.2b", "601.2f"),
    }
    for reference, body in bodies.items():
        citations = tuple(match.group(1).decode("ascii") for match in _CITATION.finditer(body))
        if citations != expected_citations[reference]:
            _fail("OUTGOING_REFERENCE_MISMATCH")
    remaining = bodies["602.2b"].decode("utf-8")
    if len(re.findall(r"601\.2b\u2013i", remaining)) != 1:
        _fail("IMPORTED_RANGE_MISMATCH")
    # Exact block fingerprints bind the authored semantic findings. These
    # narrow checks additionally distinguish the range and cost analogy.
    if (not re.search(r"remainder.*identical.*casting.*spell", remaining)
            or not re.search(r"rules.*apply.*activating.*ability.*just as.*casting.*spell", remaining)
            or not re.search(r"analog.*mana cost.*activation cost", remaining)
            or not re.search(r"mana cost[^()]*\([^()]*601\.2f[^()]*\)", remaining)
            or re.search(r"applicable|appropriate|similar|except|necessary", remaining)):
        _fail("IMPORT_OR_COST_MAPPING_FINDING_MISMATCH")
    return expected_inspection()


def inspect_source(artifact_path, *, review_root=None) -> dict:
    """Reproduce exact source verification and bounded review-only inspection.

    The inherited verifier independently checks historical artifact lineage,
    regular-file access and stable bytes. Errors never contain source paths.
    """
    root = (Path(__file__).resolve().parents[3] / "reference-reviews"
            if review_root is None else Path(review_root))
    try:
        data = _verified_bytes(
            artifact_path,
            artifact_review_root=root / "gameplay-rules-artifact-verification",
            source_root=root / "gameplay-rules-source-versioning",
            discovery_root=root / "gameplay-rules-release-discovery-closure",
        )
    except (OSError, TypeError, ValueError):
        _fail("SOURCE_ARTIFACT_OR_VERIFICATION_LINEAGE_INVALID")
    return verify_bytes(data)
