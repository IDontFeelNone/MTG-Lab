"""Future rule-block anchor contract and proofs using fictional bytes only.

This module does not inspect a Comprehensive Rules artifact and cannot accept
real numbered rule labels.  The small ``FIC`` fixture grammar below proves raw
byte and boundary properties; it is not the future real-source parser.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, ClassVar, Iterable, Mapping

from .common import DesignRecord, _exact, _fail as _design_fail, _keys


SINGLE_LINE_RULE_ANCHOR = "SINGLE_LINE_RULE_ANCHOR"
MULTI_LINE_RULE_BLOCK_ANCHOR = "MULTI_LINE_RULE_BLOCK_ANCHOR"
RULE_BLOCK_POLICY = "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR"
FICTIONAL_END = b"[[FIC_END]]"
_FIC_REF = re.compile(r"FIC\.[1-9][0-9]*(?:[a-z])?\Z", re.ASCII)
_FIC_MARKER = re.compile(rb"(FIC\.[1-9][0-9]*(?:[a-z])?)\. ([^\r\n]+)\Z", re.ASCII)
_FIC_EXAMPLE = re.compile(rb"FIC_EXAMPLE\[(FIC\.[1-9][0-9]*(?:[a-z])?)\]: (.+)\Z", re.ASCII)
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)


def _fail(field: str, message: str) -> None:
    _design_fail(field + ": " + message)


def _anchor_body() -> dict[str, Any]:
    """Authored schema descriptions, never concrete real-source anchors."""
    return {
        "compatibility": {
            "historical_anchor_type": SINGLE_LINE_RULE_ANCHOR,
            "historical_policy": "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR",
            "historical_anchor_conversion": "FORBIDDEN",
            "historical_anchor_identity_changes": False,
            "future_contract_declares_anchor_type": True,
            "supported_anchor_types": [SINGLE_LINE_RULE_ANCHOR, MULTI_LINE_RULE_BLOCK_ANCHOR],
        },
        "future_anchor_contract": {
            "anchor_type": MULTI_LINE_RULE_BLOCK_ANCHOR,
            "span_policy": RULE_BLOCK_POLICY,
            "single_physical_line_block": "PERMITTED_WITH_LINE_COUNT_ONE",
            "fields": {
                "rule_reference": "EXACT_NUMBERED_RULE_REFERENCE",
                "artifact_identity": "EXACT_FULL_ARTIFACT_SHA256",
                "effective_date": "VERIFIED_RELEASE_DATE",
                "starting_physical_line": "ONE_BASED_INCLUSIVE",
                "ending_physical_line": "ONE_BASED_INCLUSIVE",
                "byte_start": "ZERO_BASED_INCLUSIVE",
                "byte_end": "ZERO_BASED_EXCLUSIVE",
                "line_count": "ENDING_LINE_MINUS_STARTING_LINE_PLUS_ONE",
                "span_sha256": "SHA256_OF_COMPLETE_SELECTED_RAW_BYTE_BLOCK",
            },
            "internal_line_terminators": "PRESERVE_EXACT_RAW_BYTES",
            "final_line_terminator": "EXCLUDED",
            "normalize_whitespace": False,
            "normalize_line_endings": False,
            "source_prose_retained": False,
            "concrete_real_source_anchors_created": 0,
            "real_source_verification_implemented": False,
        },
        "boundary_contract": {
            "start": "EXACT_NUMBERED_RULE_MARKER_AT_PHYSICAL_LINE_START",
            "continue": "ONLY_CONTINUATION_LINES_PROVEN_TO_BELONG_TO_SELECTED_RULE",
            "termination": "BEFORE_NEXT_SAME_LEVEL_RULE_OR_SUBRULE_OR_NEXT_SOURCE_UNIT",
            "preceding_separator_lines": "EXCLUDE_WHEN_PROVEN_NOT_PART_OF_RULE_BODY",
            "example_ownership": "REQUIRE_UNAMBIGUOUS_OWNERSHIP_NEVER_SWALLOW_FOLLOWING_RULE_EXAMPLES",
            "failure_states": [
                "MISSING_RULE_START", "DUPLICATE_RULE_START", "AMBIGUOUS_TERMINATION",
                "OVERLAPPING_SELECTED_SPANS", "MALFORMED_NUMBERING",
                "AMBIGUOUS_CONTINUATION", "AMBIGUOUS_EXAMPLE_OWNERSHIP",
            ],
            "last_rule_boundary": "EXPLICIT_UNAMBIGUOUS_END_OF_SOURCE_UNIT_REQUIRED",
            "general_comprehensive_rules_parser": False,
            "source_verified_future_milestone_required": True,
        },
        "fictional_proof_contract": {
            "authority": "FICTIONAL_FIXTURE_ONLY",
            "real_rule_labels_accepted": False,
            "real_source_bytes_read": False,
            "inter_unit_blank_separator_proof": "UNCLASSIFIED_BLANK_LINES_REJECTED_RATHER_THAN_GUESSED",
            "fixture_marker_grammar": "FIC.<positive integer><optional lowercase suffix>. <authored text>",
            "continuation_grammar": "TWO_SPACE_INDENTED_AUTHORED_TEXT",
            "example_grammar": "FIC_EXAMPLE[<owning fictional reference>]: <authored text>",
            "terminator": "[[FIC_END]]",
            "proofs": [
                "INTERNAL_LINE_ENDINGS_AFFECT_HASH", "FINAL_LINE_ENDING_EXCLUDED_FROM_SPAN_HASH",
                "FULL_ARTIFACT_HASH_BINDS_ALL_BYTES", "FIRST_AND_LAST_LINES_RETAINED",
                "EXACT_BYTE_SPAN", "NONOVERLAPPING_SELECTED_SPANS", "FAIL_CLOSED_BOUNDARIES",
            ],
            "no_general_real_source_parser": True,
            "gameplay_execution": False,
        },
    }


@dataclass(frozen=True)
class MultiLineSourceAnchorDesign(DesignRecord):
    """Immutable proposed policy; it contains no new CR source evidence."""

    SCHEMA: ClassVar[str] = "gameplay-rules-multiline-source-anchor-design-v1"
    ID_FIELD: ClassVar[str] = "source_anchor_design_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "compatibility", "future_anchor_contract", "boundary_contract", "fictional_proof_contract",
    })

    @staticmethod
    def _validate_body(body: Mapping[str, Any]) -> None:
        _keys(body, MultiLineSourceAnchorDesign.BODY_FIELDS, "source_anchor_design")
        _exact(body, _anchor_body(), "source_anchor_design")


def build_source_anchor_design() -> MultiLineSourceAnchorDesign:
    return MultiLineSourceAnchorDesign.create(_anchor_body())


@dataclass(frozen=True)
class FictionalRuleBlock:
    """Synthetic span proof; no source prose or real-source authority retained."""

    rule_reference: str
    artifact_identity: str
    starting_physical_line: int
    ending_physical_line: int
    byte_start: int
    byte_end: int
    line_count: int
    span_sha256: str
    anchor_type: str = MULTI_LINE_RULE_BLOCK_ANCHOR
    span_policy: str = RULE_BLOCK_POLICY
    source_authority: str = "FICTIONAL_FIXTURE_ONLY"
    status: str = "DESIGN_ONLY"
    design_only: bool = True
    non_executable: bool = True
    real_source_verified: bool = False
    source_body_retained: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.rule_reference, str) or not _FIC_REF.fullmatch(self.rule_reference):
            _fail("fictional_rule_reference", "only fictional labels are accepted")
        for name in ("artifact_identity", "span_sha256"):
            value = getattr(self, name)
            if not isinstance(value, str) or not _HASH.fullmatch(value):
                _fail(name, "fictional content hash required")
        for name in ("starting_physical_line", "ending_physical_line", "byte_start", "byte_end", "line_count"):
            if type(getattr(self, name)) is not int:
                _fail(name, "integer coordinate required")
        if not (1 <= self.starting_physical_line <= self.ending_physical_line
                and 0 <= self.byte_start < self.byte_end
                and self.line_count == self.ending_physical_line - self.starting_physical_line + 1):
            _fail("fictional_span", "inconsistent span coordinates")
        _exact(self.anchor_type, MULTI_LINE_RULE_BLOCK_ANCHOR, "anchor_type")
        _exact(self.span_policy, RULE_BLOCK_POLICY, "span_policy")
        _exact(self.source_authority, "FICTIONAL_FIXTURE_ONLY", "source_authority")
        _exact(self.status, "DESIGN_ONLY", "status")
        for name in ("design_only", "non_executable"):
            _exact(getattr(self, name), True, name)
        for name in ("real_source_verified", "source_body_retained"):
            _exact(getattr(self, name), False, name)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def validate_fictional_block_spans(blocks: Iterable[FictionalRuleBlock]) -> None:
    """Reject duplicate references, mixed fixtures, or overlapping proof spans."""
    records = tuple(blocks)
    if not records or any(type(item) is not FictionalRuleBlock for item in records):
        _fail("fictional_spans", "nonempty fictional proof records required")
    if len({item.rule_reference for item in records}) != len(records):
        _fail("fictional_spans", "DUPLICATE_RULE_START")
    if len({item.artifact_identity for item in records}) != 1:
        _fail("fictional_spans", "proof spans must bind the same fictional fixture")
    ordered = sorted(records, key=lambda item: item.byte_start)
    for previous, current in zip(ordered, ordered[1:]):
        if previous.byte_end > current.byte_start or previous.ending_physical_line >= current.starting_physical_line:
            _fail("fictional_spans", "OVERLAPPING_SELECTED_SPANS")


def _physical_lines(data: bytes) -> list[tuple[int, bytes, bytes]]:
    """Split only physical CR/LF terminators while retaining their exact bytes."""
    lines: list[tuple[int, bytes, bytes]] = []
    cursor = 0
    for match in re.finditer(rb"[^\r\n]*(?:\r\n|\r|\n|\Z)", data):
        raw = match.group()
        if not raw:
            continue
        if raw.endswith(b"\r\n"):
            body, terminator = raw[:-2], b"\r\n"
        elif raw.endswith((b"\r", b"\n")):
            body, terminator = raw[:-1], raw[-1:]
        else:
            body, terminator = raw, b""
        lines.append((cursor, body, terminator))
        cursor += len(raw)
    return lines


def verify_fictional_rule_blocks(data: bytes, selected_refs: Iterable[str]) -> tuple[FictionalRuleBlock, ...]:
    """Prove block slicing with the bounded fictional fixture grammar.

    Start lines are ``FIC.1a. Authored text``; continuation lines begin with two
    spaces.  An optional ``FIC_EXAMPLE[FIC.1a]: Authored text`` must explicitly
    name the currently open fictional rule.  Every fixture ends at the explicit
    ``[[FIC_END]]`` line, optionally followed by one line terminator.  Blank or
    unclassified lines fail closed.  Real numbered references are never accepted.
    The returned records retain hashes and positions, not fixture prose.
    """
    if type(data) is not bytes or not data or len(data) > 65536:
        _fail("fictional_bytes", "bounded nonempty synthetic bytes required")
    if isinstance(selected_refs, (str, bytes)):
        _fail("selected_refs", "fictional reference sequence required")
    try:
        selected = tuple(selected_refs)
    except TypeError:
        _fail("selected_refs", "fictional reference sequence required")
    if not selected or len(selected) > 64:
        _fail("selected_refs", "bounded nonempty fictional reference sequence required")
    if any(not isinstance(ref, str) or not _FIC_REF.fullmatch(ref) for ref in selected):
        _fail("selected_refs", "real rule labels are forbidden in fictional proofs")
    if len(set(selected)) != len(selected):
        _fail("selected_refs", "DUPLICATE_RULE_START")
    lines = _physical_lines(data)
    if not lines or lines[-1][1] != FICTIONAL_END:
        _fail("fictional_boundary", "AMBIGUOUS_TERMINATION")
    starts: list[tuple[str, int]] = []
    seen: set[str] = set()
    current: str | None = None
    for index, (_offset, body, _terminator) in enumerate(lines):
        if body == FICTIONAL_END:
            if index != len(lines) - 1 or current is None:
                _fail("fictional_boundary", "AMBIGUOUS_TERMINATION")
            continue
        marker = _FIC_MARKER.fullmatch(body)
        if marker:
            ref = marker[1].decode("ascii")
            if ref in seen:
                _fail("fictional_marker", "DUPLICATE_RULE_START")
            seen.add(ref)
            starts.append((ref, index))
            current = ref
            continue
        if body.startswith(b"FIC."):
            _fail("fictional_marker", "MALFORMED_NUMBERING")
        example = _FIC_EXAMPLE.fullmatch(body)
        if example:
            if current != example[1].decode("ascii"):
                _fail("fictional_example", "AMBIGUOUS_EXAMPLE_OWNERSHIP")
            continue
        if body.startswith(b"FIC_EXAMPLE"):
            _fail("fictional_example", "AMBIGUOUS_EXAMPLE_OWNERSHIP")
        if body.startswith(b"  ") and body[2:].strip() and current is not None:
            if body[2:].lstrip().startswith((b"FIC.", b"FIC_EXAMPLE", b"[[FIC_END]]")):
                _fail("fictional_continuation", "MALFORMED_NUMBERING")
            continue
        _fail("fictional_continuation", "AMBIGUOUS_CONTINUATION")
    if not set(selected) <= seen:
        _fail("selected_refs", "MISSING_RULE_START")
    artifact_id = "sha256:" + hashlib.sha256(data).hexdigest()
    spans: dict[str, FictionalRuleBlock] = {}
    for position, (ref, start_line) in enumerate(starts):
        next_line = starts[position + 1][1] if position + 1 < len(starts) else len(lines) - 1
        final_line = next_line - 1
        byte_start = lines[start_line][0]
        byte_end = lines[final_line][0] + len(lines[final_line][1])
        spans[ref] = FictionalRuleBlock(
            rule_reference=ref, artifact_identity=artifact_id,
            starting_physical_line=start_line + 1, ending_physical_line=final_line + 1,
            byte_start=byte_start, byte_end=byte_end, line_count=final_line - start_line + 1,
            span_sha256="sha256:" + hashlib.sha256(data[byte_start:byte_end]).hexdigest(),
        )
    result = tuple(spans[ref] for ref in selected)
    validate_fictional_block_spans(result)
    return result
