"""Immutable review contracts for object-control exceptions and a source anomaly.

Offline verification establishes identities and bounded authored scope. Actual
source correspondence requires the separate verifier with the external bytes.
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
from .object_control_scope import (
    SELECTED_REFERENCES, PARENT_REFERENCE, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES,
    NEW_BOUNDARIES, UNSUPPORTED_DIMENSIONS,
)

FOUNDATIONAL_PROJECTION_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
DEPENDENCY_PROJECTION_ID = "sha256:23c7882d3291c0b5bccadff2a4c0422d5680412308cbff2cd0137401fd4fc7f1"
TARGET_EXECUTION_PROFILE = "magic-comprehensive-rules-20260925-v1"
RULE_ID_DOMAIN = "gameplay-cr-object-control-exception-rule-v1"
SOURCE_BINDING = _freeze({
    "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
    "effective_date": EFFECTIVE_DATE, "verification_result_id": VERIFICATION_RESULT_ID,
    "correspondence_review_id": CORRESPONDENCE_REVIEW_ID,
    "artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID, "selection_id": SELECTION_ID,
})
AUTHORIZATION = _freeze({
    "scope": "OBJECT-CONTROL EXCEPTION FAMILY PROJECTION",
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
    "foundational_projection_id", "dependency_projection_id", "source_binding", "authorization",
    "rules", "graph", "new_boundaries", "unsupported_dimensions", "boundary_flags",
})
ANOMALY_BODY_FIELDS = frozenset({
    "game_id", "status", "anomaly_type", "parent", "parent_declared_count", "enumerated_subrule_count",
    "enumerated_refs", "source_release", "source_binding", "parent_source_anchor", "observation_method",
    "correction_applied", "interpretation", "source_intent_inferred", "subrule_invalidity_inferred",
    "limitations", "boundary_flags",
})
ANOMALY_LIMITATIONS = (
    "This records a source count discrepancy only; the parent is not projected again.",
    "No source correction is applied and no intended count is attributed to the source author.",
    "Every authorized exception is retained; no exception is discarded or treated as invalid.",
    "Enumeration coverage does not establish semantic closure or execution readiness.",
)


def _fail(field, message="invalid object-control review contract"):
    raise GameplayContractError("object_control_projection_contract", f"{field}: {message}")


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
    """Identify one authored rule record, including its exact source anchor."""
    content = {key: item for key, item in _json(rule).items() if key != "rule_id"}
    return "sha256:" + sha256_identity({"domain": RULE_ID_DOMAIN, "content": content})


def _validate_projection(body):
    _keys(body, PROJECTION_BODY_FIELDS, "object_control_projection")
    for field, expected in (
        ("game_id", "magic"), ("projection_kind", "NON_EXECUTABLE"),
        ("status", "PROJECTED_FOR_REVIEW"),
        ("milestone_status", "OBJECT_CONTROL_EXCEPTION_FAMILY_PROJECTED"),
        ("selected_rule_count", 7), ("foundational_projection_id", FOUNDATIONAL_PROJECTION_ID),
        ("dependency_projection_id", DEPENDENCY_PROJECTION_ID),
        ("source_binding", SOURCE_BINDING), ("authorization", AUTHORIZATION),
        ("boundary_flags", BOUNDARY_FLAGS), ("unsupported_dimensions", UNSUPPORTED_DIMENSIONS),
        ("new_boundaries", NEW_BOUNDARIES), ("graph", {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES}),
    ):
        _exact(body[field], expected, field)
    rules = body["rules"]
    if not isinstance(rules, list) or len(rules) != 7:
        _fail("rules", "exactly seven authorized exception records required")
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


def _validate_anomaly(body):
    _keys(body, ANOMALY_BODY_FIELDS, "source_anomaly")
    for field, expected in (
        ("game_id", "magic"), ("status", "PROJECTED_FOR_REVIEW"),
        ("anomaly_type", "DECLARED_ENUMERATED_COUNT_MISMATCH"), ("parent", PARENT_REFERENCE),
        ("parent_declared_count", 6), ("enumerated_subrule_count", 7),
        ("enumerated_refs", SELECTED_REFERENCES), ("source_release", EFFECTIVE_DATE),
        ("source_binding", SOURCE_BINDING),
        ("observation_method", "BOUNDED_PARENT_COUNT_AND_AUTHORIZED_SUBRULE_ENUMERATION"),
        ("correction_applied", False), ("interpretation", "SOURCE_INCONSISTENCY_RETAINED"),
        ("source_intent_inferred", False), ("subrule_invalidity_inferred", False),
        ("limitations", ANOMALY_LIMITATIONS), ("boundary_flags", BOUNDARY_FLAGS),
    ):
        _exact(body[field], expected, field)
    _validate_anchor(body["parent_source_anchor"], PARENT_REFERENCE)


@dataclass(frozen=True)
class _ReviewContract(Contract):
    """Shared immutable envelope mechanics; each subtype fixes its own scope."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str]
    ID_FIELD: ClassVar[str]
    BODY_FIELDS: ClassVar[frozenset[str]]

    @staticmethod
    def _validate_body(body):
        raise NotImplementedError

    def __post_init__(self):
        try:
            value = _json(self._payload)
            _keys(value, self.BODY_FIELDS | {"schema_version", self.ID_FIELD}, "envelope")
            _exact(value["schema_version"], self.SCHEMA, "schema_version")
            _hash(value[self.ID_FIELD], self.ID_FIELD)
            body = {key: item for key, item in value.items() if key not in {"schema_version", self.ID_FIELD}}
            self._validate_body(body)
            content = {key: item for key, item in value.items() if key != self.ID_FIELD}
            expected = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": content})
            if value[self.ID_FIELD] != expected:
                _fail(self.ID_FIELD, "review content identity mismatch")
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("envelope", "malformed object-control review contract")

    @classmethod
    def create(cls, body):
        try:
            value = _json(body)
            _keys(value, cls.BODY_FIELDS, "create")
            cls._validate_body(value)
            value["schema_version"] = cls.SCHEMA
            value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
            return cls(value)
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("create", "malformed object-control review body")

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
            _fail("JSON", "malformed object-control review JSON")

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


@dataclass(frozen=True)
class ObjectControlProjection(_ReviewContract):
    """Exactly seven separately identified, non-executable exception records."""

    SCHEMA = "gameplay-cr-object-control-exception-projection-v1"
    ID_FIELD = "projection_id"
    BODY_FIELDS = PROJECTION_BODY_FIELDS
    _validate_body = staticmethod(_validate_projection)


@dataclass(frozen=True)
class SourceAnomaly(_ReviewContract):
    """Evidence-quality observation with no source correction or intent claim."""

    SCHEMA = "gameplay-cr-object-control-source-anomaly-v1"
    ID_FIELD = "anomaly_id"
    BODY_FIELDS = ANOMALY_BODY_FIELDS
    _validate_body = staticmethod(_validate_anomaly)
