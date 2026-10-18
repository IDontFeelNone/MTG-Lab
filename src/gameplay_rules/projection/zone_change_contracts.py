"""Closed immutable contracts for the bounded zone-change exception projection.

Offline identity verification checks fixed authored content and anchor shape;
actual correspondence requires the external artifact through the source verifier.
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
from .zone_change_scope import (
    SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES,
    NEW_BOUNDARIES, UNSUPPORTED_DIMENSIONS, LETTERING_POLICY,
)

FOUNDATIONAL_PROJECTION_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
FOUNDATIONAL_PACKAGE_ID = "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea"
DEPENDENCY_PROJECTION_ID = "sha256:23c7882d3291c0b5bccadff2a4c0422d5680412308cbff2cd0137401fd4fc7f1"
DEPENDENCY_PACKAGE_ID = "sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a"
OBJECT_CONTROL_PROJECTION_ID = "sha256:f4b75e686bfb5202f54818dc4fc9247a49a6e6ef84e2d57f070e990c25b6cce9"
OBJECT_CONTROL_PACKAGE_ID = "sha256:f8cf8053b8bf9e7cc9471520eb02cc3e1e29a716f99a2ac623ec36b40343acab"
OBJECT_CONTROL_ANOMALY_ID = "sha256:4825f549d8e7a59935ac23ab0d5d068e11deb55adcb163bdc18f1f8658c0b74e"
TARGET_EXECUTION_PROFILE = "magic-comprehensive-rules-20260925-v1"
RULE_ID_DOMAIN = "gameplay-cr-zone-change-exception-rule-v1"
SOURCE_BINDING = _freeze({
    "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
    "effective_date": EFFECTIVE_DATE, "verification_result_id": VERIFICATION_RESULT_ID,
    "correspondence_review_id": CORRESPONDENCE_REVIEW_ID,
    "artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID, "selection_id": SELECTION_ID,
})
AUTHORIZATION = _freeze({
    "scope": "ZONE-CHANGE IDENTITY EXCEPTION FAMILY PROJECTION",
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
    "source_binding", "authorization", "lettering_policy", "rules", "graph", "new_boundaries",
    "unsupported_dimensions", "boundary_flags",
})


def _fail(field, message="invalid zone-change review contract"):
    raise GameplayContractError("zone_change_projection_contract", f"{field}: {message}")


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
    """Identify one authored exception record and its exact source anchor."""
    content = {key: item for key, item in _json(rule).items() if key != "rule_id"}
    return "sha256:" + sha256_identity({"domain": RULE_ID_DOMAIN, "content": content})


def _validate_projection(body):
    _keys(body, PROJECTION_BODY_FIELDS, "zone_change_projection")
    for field, expected in (
        ("game_id", "magic"), ("projection_kind", "NON_EXECUTABLE"),
        ("status", "PROJECTED_FOR_REVIEW"),
        ("milestone_status", "ZONE_CHANGE_EXCEPTION_FAMILY_PROJECTED"),
        ("selected_rule_count", 12), ("foundational_projection_id", FOUNDATIONAL_PROJECTION_ID),
        ("dependency_projection_id", DEPENDENCY_PROJECTION_ID),
        ("object_control_projection_id", OBJECT_CONTROL_PROJECTION_ID),
        ("source_binding", SOURCE_BINDING), ("authorization", AUTHORIZATION),
        ("lettering_policy", LETTERING_POLICY), ("boundary_flags", BOUNDARY_FLAGS),
        ("unsupported_dimensions", UNSUPPORTED_DIMENSIONS), ("new_boundaries", NEW_BOUNDARIES),
        ("graph", {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES}),
    ):
        _exact(body[field], expected, field)
    rules = body["rules"]
    if not isinstance(rules, list) or len(rules) != len(SELECTED_REFERENCES):
        _fail("rules", "exactly twelve authorized exception records required")
    prior_end = prior_line = 0
    for rule, reference in zip(rules, SELECTED_REFERENCES):
        _keys(rule, {"rule_reference", "source_anchor", "rule_id", *RULE_CONTENT[reference]}, "rule")
        _exact(rule["rule_reference"], reference, "rule.rule_reference")
        for field, expected in RULE_CONTENT[reference].items():
            _exact(rule[field], expected, "rule." + field)
        anchor = rule["source_anchor"]
        _validate_anchor(anchor, reference)
        if anchor["byte_start"] < prior_end or anchor["line_number"] <= prior_line:
            _fail("source_anchor", "source spans must be ordered and nonoverlapping")
        prior_end, prior_line = anchor["byte_end"], anchor["line_number"]
        _hash(rule["rule_id"], "rule.rule_id")
        _exact(rule["rule_id"], rule_identity(rule), "rule.rule_id")


@dataclass(frozen=True)
class ZoneChangeProjection(Contract):
    """Exactly twelve source-anchored, separately identified review records."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str] = "gameplay-cr-zone-change-exception-projection-v1"
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
            _fail("envelope", "malformed zone-change review contract")

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
            _fail("create", "malformed zone-change review body")

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
            _fail("JSON", "malformed zone-change review JSON")

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
