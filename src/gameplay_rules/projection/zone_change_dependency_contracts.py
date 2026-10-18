"""Closed immutable contracts for the direct zone-change dependency projection.

Offline validation proves bounded authored records and immutable identities;
correspondence to the artifact still requires actual verified source bytes.
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
from .zone_change_contracts import (
    FOUNDATIONAL_PROJECTION_ID, FOUNDATIONAL_PACKAGE_ID, DEPENDENCY_PROJECTION_ID,
    DEPENDENCY_PACKAGE_ID, OBJECT_CONTROL_PROJECTION_ID, OBJECT_CONTROL_PACKAGE_ID,
    TARGET_EXECUTION_PROFILE,
)
from .zone_change_dependency_scope import (
    SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES, NEW_BOUNDARIES,
    UNSUPPORTED_DIMENSIONS,
)

ZONE_CHANGE_PROJECTION_ID = "sha256:0b32e8c16fc2089949d50c0ece4b2afb7b69355f2573f041cfc8b932aa4db141"
ZONE_CHANGE_PACKAGE_ID = "sha256:4836f6ea330cc40365540f85541160ef2251ff6ed88f7959f9d9e594031f7875"
RULE_ID_DOMAIN = "gameplay-cr-zone-change-direct-dependency-rule-v1"
SOURCE_BINDING = _freeze({
    "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
    "effective_date": EFFECTIVE_DATE, "verification_result_id": VERIFICATION_RESULT_ID,
    "correspondence_review_id": CORRESPONDENCE_REVIEW_ID,
    "artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID, "selection_id": SELECTION_ID,
})
AUTHORIZATION = _freeze({
    "scope": "ZONE-CHANGE DIRECT DEPENDENCY PROJECTION",
    "basis": "OWNER_EXPLICIT_TASK_AUTHORIZATION", "authorized_on": "2026-10-18",
    "source_policy_clearance": "not_granted", "execution_authorized": False,
})
BOUNDARY_FLAGS = _freeze({
    "non_executable": True, "execution_authorized": False, "real_rules_executable": False,
    "admission_eligible": False, "source_body_retained": False, "oracle_ingested": False,
    "source_policy_clearance": "not_granted", "private_retention": "NOT_ESTABLISHED",
    "redistribution": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED",
    "commercial_service": "NOT_ESTABLISHED", "ai_export": "NOT_ESTABLISHED",
})
PROJECTION_BODY_FIELDS = frozenset({
    "game_id", "projection_kind", "status", "milestone_status", "selected_rule_count",
    "foundational_projection_id", "dependency_projection_id", "object_control_projection_id",
    "zone_change_projection_id", "source_binding", "authorization", "rules", "graph", "new_boundaries",
    "unsupported_dimensions", "boundary_flags",
})


def _fail(field, message="invalid direct zone-change dependency review contract"):
    raise GameplayContractError("zone_change_dependency_projection_contract", f"{field}: {message}")


def _validate_anchor(anchor, reference):
    _keys(anchor, {"rule_reference", "artifact_hash", "effective_date", "byte_start", "byte_end",
                   "line_number", "span_sha256", "span_policy"}, "source_anchor")
    for field, expected in (("rule_reference", reference), ("artifact_hash", ARTIFACT_HASH),
                            ("effective_date", EFFECTIVE_DATE),
                            ("span_policy", "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR")):
        _exact(anchor[field], expected, "source_anchor." + field)
    _integer(anchor["byte_start"], "source_anchor.byte_start", maximum=ARTIFACT_BYTE_LENGTH)
    _integer(anchor["byte_end"], "source_anchor.byte_end", minimum=1, maximum=ARTIFACT_BYTE_LENGTH)
    _integer(anchor["line_number"], "source_anchor.line_number", minimum=1)
    _hash(anchor["span_sha256"], "source_anchor.span_sha256")
    if anchor["byte_end"] <= anchor["byte_start"]:
        _fail("source_anchor", "source span must be nonempty")


def rule_identity(rule):
    """Identify the authored dependency evidence and its complete source anchor."""
    content = {key: item for key, item in _json(rule).items() if key != "rule_id"}
    return "sha256:" + sha256_identity({"domain": RULE_ID_DOMAIN, "content": content})


def _validate_projection(body):
    _keys(body, PROJECTION_BODY_FIELDS, "zone_change_dependency_projection")
    for field, expected in (
        ("game_id", "magic"), ("projection_kind", "NON_EXECUTABLE"), ("status", "PROJECTED_FOR_REVIEW"),
        ("milestone_status", "ZONE_CHANGE_DIRECT_DEPENDENCIES_PROJECTED"), ("selected_rule_count", 12),
        ("foundational_projection_id", FOUNDATIONAL_PROJECTION_ID),
        ("dependency_projection_id", DEPENDENCY_PROJECTION_ID),
        ("object_control_projection_id", OBJECT_CONTROL_PROJECTION_ID),
        ("zone_change_projection_id", ZONE_CHANGE_PROJECTION_ID),
        ("source_binding", SOURCE_BINDING), ("authorization", AUTHORIZATION),
        ("boundary_flags", BOUNDARY_FLAGS), ("unsupported_dimensions", UNSUPPORTED_DIMENSIONS),
        ("new_boundaries", NEW_BOUNDARIES), ("graph", {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES}),
    ):
        _exact(body[field], expected, field)
    rules = body["rules"]
    if not isinstance(rules, list) or len(rules) != len(SELECTED_REFERENCES):
        _fail("rules", "exactly twelve authorized dependency records required")
    anchors = []
    for rule, reference in zip(rules, SELECTED_REFERENCES):
        _keys(rule, {"rule_reference", "source_anchor", "rule_id", *RULE_CONTENT[reference]}, "rule")
        _exact(rule["rule_reference"], reference, "rule.rule_reference")
        for field, expected in RULE_CONTENT[reference].items():
            _exact(rule[field], expected, "rule." + field)
        _validate_anchor(rule["source_anchor"], reference)
        anchors.append(rule["source_anchor"])
        _hash(rule["rule_id"], "rule.rule_id")
        _exact(rule["rule_id"], rule_identity(rule), "rule.rule_id")
    # Owner-selected record order differs from physical source order. Validate
    # uniqueness and nonoverlap by physical position without changing that order.
    prior_end = prior_line = 0
    for anchor in sorted(anchors, key=lambda item: item["byte_start"]):
        if anchor["byte_start"] < prior_end or anchor["line_number"] <= prior_line:
            _fail("source_anchor", "source spans must be unique and nonoverlapping in physical order")
        prior_end, prior_line = anchor["byte_end"], anchor["line_number"]


@dataclass(frozen=True)
class ZoneChangeDependencyProjection(Contract):
    """Exactly twelve independently source-anchored non-executable records."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str] = "gameplay-cr-zone-change-direct-dependency-projection-v1"
    ID_FIELD: ClassVar[str] = "projection_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = PROJECTION_BODY_FIELDS

    def __post_init__(self):
        try:
            value = _json(self._payload)
            _keys(value, self.BODY_FIELDS | {"schema_version", self.ID_FIELD}, "envelope")
            _exact(value["schema_version"], self.SCHEMA, "schema_version")
            _hash(value[self.ID_FIELD], self.ID_FIELD)
            body = {key: item for key, item in value.items() if key not in {"schema_version", self.ID_FIELD}}
            _validate_projection(body)
            content = {key: item for key, item in value.items() if key != self.ID_FIELD}
            expected = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": content})
            if value[self.ID_FIELD] != expected:
                _fail(self.ID_FIELD, "review content identity mismatch")
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("envelope", "malformed direct dependency review contract")

    @classmethod
    def create(cls, body):
        try:
            value = _json(body)
            _keys(value, cls.BODY_FIELDS, "create")
            _validate_projection(value)
            value["schema_version"] = cls.SCHEMA
            value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
            return cls(value)
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("create", "malformed direct dependency review body")

    @classmethod
    def from_dict(cls, value):
        return cls(value)

    @classmethod
    def from_json(cls, value):
        try:
            if not isinstance(value, (bytes, str)):
                _fail("JSON", "UTF-8 bytes or text required")
            return cls.from_dict(json.loads(value, object_pairs_hook=_duplicate_keys, parse_constant=_nonfinite))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            _fail("JSON", "malformed direct dependency review JSON")

    @property
    def identity(self):
        return self._payload[self.ID_FIELD]

    def to_dict(self):
        return _json(self._payload)

    def serialize(self):
        return deterministic_json(self.to_dict())

    def verify(self):
        type(self).from_dict(self.to_dict())
        return self

    def __getattr__(self, name):
        payload = object.__getattribute__(self, "_payload")
        if name in payload:
            return payload[name]
        raise AttributeError(name)
