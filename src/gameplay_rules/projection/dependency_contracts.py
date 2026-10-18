"""Immutable contracts for the bounded, non-executable dependency projection.

The original projection's validation and canonicalization helpers are reused.
This separately identified envelope cannot replace a gameplay rules snapshot;
offline integrity verification does not claim access to external source bytes.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, ClassVar, Mapping

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from .contracts import (
    ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, VERIFICATION_RESULT_ID,
    CORRESPONDENCE_REVIEW_ID, ARTIFACT_REVIEW_PACKAGE_ID, SELECTION_ID,
    _json, _freeze, _keys, _exact, _hash, _integer, _duplicate_keys, _nonfinite,
)
from .dependency_scope import (
    SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES, NEW_BOUNDARIES,
    UNSUPPORTED_DIMENSIONS,
)

FOUNDATIONAL_PROJECTION_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
TARGET_EXECUTION_PROFILE = "magic-comprehensive-rules-20260925-v1"
BODY_FIELDS = frozenset({
    "game_id", "projection_kind", "status", "milestone_status", "selected_rule_count",
    "foundational_projection_id", "source_binding", "authorization", "rules", "graph",
    "new_boundaries", "unsupported_dimensions", "boundary_flags",
})
SOURCE_BINDING = _freeze({
    "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
    "effective_date": EFFECTIVE_DATE, "verification_result_id": VERIFICATION_RESULT_ID,
    "correspondence_review_id": CORRESPONDENCE_REVIEW_ID,
    "artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID, "selection_id": SELECTION_ID,
})
AUTHORIZATION = _freeze({
    "scope": "DIRECT FOUNDATIONAL DEPENDENCY PROJECTION",
    "basis": "OWNER_EXPLICIT_TASK_AUTHORIZATION", "authorized_on": "2026-10-17",
    "source_policy_clearance": "not_granted", "execution_authorized": False,
})
BOUNDARY_FLAGS = _freeze({
    "non_executable": True, "execution_authorized": False, "real_rules_executable": False,
    "admission_eligible": False, "source_body_retained": False, "oracle_ingested": False,
    "source_policy_clearance": "not_granted", "private_retention": "NOT_ESTABLISHED",
    "redistribution": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED",
    "commercial_service": "NOT_ESTABLISHED", "ai_export": "NOT_ESTABLISHED",
})


def _fail(field: str, message: str = "invalid dependency projection contract") -> None:
    raise GameplayContractError("foundational_dependency_projection_contract", f"{field}: {message}")


def _validate(body: dict[str, Any]) -> None:
    _keys(body, BODY_FIELDS, "dependency_projection")
    for field, expected in (
        ("game_id", "magic"), ("projection_kind", "NON_EXECUTABLE"),
        ("status", "PROJECTED_FOR_REVIEW"),
        ("milestone_status", "DIRECT_FOUNDATIONAL_DEPENDENCIES_PROJECTED"),
        ("selected_rule_count", 12), ("foundational_projection_id", FOUNDATIONAL_PROJECTION_ID),
        ("source_binding", SOURCE_BINDING), ("authorization", AUTHORIZATION),
        ("boundary_flags", BOUNDARY_FLAGS), ("unsupported_dimensions", UNSUPPORTED_DIMENSIONS),
        ("new_boundaries", NEW_BOUNDARIES),
        ("graph", {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES}),
    ):
        _exact(body[field], expected, field)
    rules = body["rules"]
    if not isinstance(rules, list) or len(rules) != len(SELECTED_REFERENCES):
        _fail("rules", "exactly 12 authorized rule entries required")
    prior_end = 0
    prior_line = 0
    for rule, reference in zip(rules, SELECTED_REFERENCES):
        _keys(rule, {"rule_reference", "source_anchor", *RULE_CONTENT[reference]}, "rule")
        _exact(rule["rule_reference"], reference, "rule.rule_reference")
        for field, expected in RULE_CONTENT[reference].items():
            _exact(rule[field], expected, "rule." + field)
        anchor = rule["source_anchor"]
        _keys(anchor, {
            "rule_reference", "artifact_hash", "effective_date", "byte_start", "byte_end",
            "line_number", "span_sha256", "span_policy",
        }, "source_anchor")
        for field, expected in (
            ("rule_reference", reference), ("artifact_hash", ARTIFACT_HASH),
            ("effective_date", EFFECTIVE_DATE),
            ("span_policy", "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR"),
        ):
            _exact(anchor[field], expected, "source_anchor." + field)
        _integer(anchor["byte_start"], "source_anchor.byte_start", maximum=ARTIFACT_BYTE_LENGTH)
        _integer(anchor["byte_end"], "source_anchor.byte_end", minimum=1, maximum=ARTIFACT_BYTE_LENGTH)
        _integer(anchor["line_number"], "source_anchor.line_number", minimum=1)
        _hash(anchor["span_sha256"], "source_anchor.span_sha256")
        if anchor["byte_end"] <= anchor["byte_start"]:
            _fail("source_anchor", "source span must be nonempty")
        if anchor["byte_start"] < prior_end or anchor["line_number"] <= prior_line:
            _fail("source_anchor", "source spans must be ordered and nonoverlapping")
        prior_end = anchor["byte_end"]
        prior_line = anchor["line_number"]


@dataclass(frozen=True)
class DependencyProjection(Contract):
    """Fixed authored metadata with a distinct domain-separated identity."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str] = "gameplay-cr-foundational-dependency-projection-v1"
    ID_FIELD: ClassVar[str] = "projection_id"

    def __post_init__(self) -> None:
        try:
            value = _json(self._payload)
            _keys(value, BODY_FIELDS | {"schema_version", self.ID_FIELD}, "dependency_envelope")
            _exact(value["schema_version"], self.SCHEMA, "schema_version")
            _hash(value[self.ID_FIELD], self.ID_FIELD)
            body = {key: item for key, item in value.items() if key not in {"schema_version", self.ID_FIELD}}
            _validate(body)
            content = {key: item for key, item in value.items() if key != self.ID_FIELD}
            expected = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": content})
            if value[self.ID_FIELD] != expected:
                _fail(self.ID_FIELD, "dependency projection content identity mismatch")
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("envelope", "malformed dependency projection contract")

    @classmethod
    def create(cls, body: Mapping[str, Any]) -> DependencyProjection:
        try:
            value = _json(body)
            _keys(value, BODY_FIELDS, "create")
            _validate(value)
            value["schema_version"] = cls.SCHEMA
            value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
            return cls(value)
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("create", "malformed dependency projection body")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> DependencyProjection:
        return cls(value)

    @classmethod
    def from_json(cls, value: bytes | str) -> DependencyProjection:
        try:
            if not isinstance(value, (bytes, str)):
                _fail("JSON", "UTF-8 bytes or text required")
            return cls.from_dict(json.loads(value, object_pairs_hook=_duplicate_keys, parse_constant=_nonfinite))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            _fail("JSON", "malformed dependency projection JSON")

    @property
    def identity(self) -> str:
        return self._payload[self.ID_FIELD]

    def to_dict(self) -> dict[str, Any]:
        return _json(self._payload)

    def serialize(self) -> str:
        return deterministic_json(self.to_dict())

    def verify(self) -> DependencyProjection:
        type(self).from_dict(self.to_dict())
        return self

    def __getattr__(self, name: str) -> Any:
        payload = object.__getattribute__(self, "_payload")
        if name in payload:
            return payload[name]
        raise AttributeError(name)
