"""Closed immutable contract for the single non-executable allocation unit."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, ClassVar, Mapping

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import (
    ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, VERIFICATION_RESULT_ID,
    CORRESPONDENCE_REVIEW_ID, ARTIFACT_REVIEW_PACKAGE_ID, SELECTION_ID,
    _json, _freeze, _keys, _exact, _hash, _duplicate_keys, _nonfinite,
)
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from .scope import SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES, UNSUPPORTED_DIMENSIONS
from .source import VERIFIED_ANCHORS, SPAN_POLICY, validate_spans

CANONICAL_MAIN = "d0331139ae10d6709bd448ac83b28ea4e2b45969"
RULE_ID_DOMAIN = "gameplay-cr-bounded-shared-target-allocation-rule-v1"
DESIGN_PACKAGE_ID = "sha256:4ec995686f7ebb851fae1d6a3b732b1669a9f8cbe7d7ad547f939d928b6c729f"
SOURCE_BINDING = _freeze({
    "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
    "effective_date": EFFECTIVE_DATE, "verification_result_id": VERIFICATION_RESULT_ID,
    "correspondence_review_id": CORRESPONDENCE_REVIEW_ID,
    "artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID, "selection_id": SELECTION_ID,
})
AUTHORIZATION = _freeze({
    "scope": "BOUNDED SHARED TARGET-ALLOCATION STAGE PROJECTION",
    "basis": "OWNER_EXPLICIT_TASK_AUTHORIZATION", "authorized_on": "2026-10-21",
    "source_policy_clearance": "not_granted", "selected_source_units": list(SELECTED_REFERENCES),
    "execution_authorized": False, "subsequent_milestone_authorized": False,
})
BOUNDARY_FLAGS = _freeze({
    "non_executable": True, "execution_authorized": False, "real_rules_executable": False,
    "admission_eligible": False, "source_body_retained": False, "oracle_ingested": False,
    "real_snapshot_created": False, "real_profile_activated": False,
    "owner_execution_approval": "NOT_GRANTED", "source_policy_clearance": "not_granted",
    "private_retention": "NOT_ESTABLISHED", "redistribution": "NOT_ESTABLISHED",
    "free_service": "NOT_ESTABLISHED", "commercial_service": "NOT_ESTABLISHED",
    "ai_export": "NOT_ESTABLISHED",
})
_FIELDS = frozenset({
    "game_id", "canonical_base", "projection_kind", "status", "milestone_status",
    "selected_references", "selected_rule_count", "new_source_units_projected",
    "total_projected_rule_count", "resulting_projection_count", "source_binding",
    "authorization", "prior_design_package_id", "source_anchor_policy", "rules",
    "graph", "unsupported_dimensions", "boundary_flags",
})


def _fail(field):
    raise GameplayContractError("shared_target_allocation_contract", field)


def rule_identity(rule):
    _canonical_candidate(rule)
    if type(rule) is not dict:
        _fail("PLAIN_RULE_RECORD_REQUIRED")
    body = {key: value for key, value in rule.items() if key != "rule_id"}
    return "sha256:" + sha256_identity({"domain": RULE_ID_DOMAIN, "content": body})


def _fixed_body():
    return {
        "game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "projection_kind": "NON_EXECUTABLE", "status": "PROJECTED_FOR_REVIEW",
        "milestone_status": "BOUNDED_SHARED_TARGET_ALLOCATION_STAGE_PROJECTED",
        "selected_references": list(SELECTED_REFERENCES), "selected_rule_count": 1,
        "new_source_units_projected": 1, "total_projected_rule_count": 90,
        "resulting_projection_count": 12, "source_binding": _json(SOURCE_BINDING),
        "authorization": _json(AUTHORIZATION), "prior_design_package_id": DESIGN_PACKAGE_ID,
        "source_anchor_policy": SPAN_POLICY,
        "graph": {"nodes": _json(GRAPH_NODES), "edges": _json(GRAPH_EDGES)},
        "unsupported_dimensions": _json(UNSUPPORTED_DIMENSIONS),
        "boundary_flags": _json(BOUNDARY_FLAGS),
    }


def _validate(body):
    _keys(body, _FIELDS, "projection")
    for field, expected in _fixed_body().items():
        _exact(body[field], expected, field)
    rules = body["rules"]
    if type(rules) is not list or len(rules) != 1 or type(rules[0]) is not dict:
        _fail("EXACTLY_ONE_COMPLETE_D_UNIT_REQUIRED")
    rule = rules[0]
    _keys(rule, {"rule_reference", "rule_id", "source_anchor", *RULE_CONTENT["601.2d"]}, "rule")
    _exact(rule["rule_reference"], "601.2d", "rule_reference")
    validate_spans([rule["source_anchor"]])
    for field, expected in RULE_CONTENT["601.2d"].items():
        _exact(rule[field], expected, "rule." + field)
    _exact(rule["rule_id"], rule_identity(rule), "rule_id")


@dataclass(frozen=True)
class BoundedSharedTargetAllocationProjection(Contract):
    """Knowledge only; no runtime authority or execution profile is supplied."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str] = "gameplay-cr-bounded-shared-target-allocation-projection-v1"
    ID_FIELD: ClassVar[str] = "projection_id"

    def __post_init__(self):
        try:
            _canonical_candidate(self._payload)
            value = _json(self._payload)
            _keys(value, _FIELDS | {"schema_version", self.ID_FIELD}, "envelope")
            _exact(value["schema_version"], self.SCHEMA, "schema_version")
            _hash(value[self.ID_FIELD], self.ID_FIELD)
            _validate({key: item for key, item in value.items() if key not in ("schema_version", self.ID_FIELD)})
            body = {key: item for key, item in value.items() if key != self.ID_FIELD}
            expected = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": body})
            _exact(value[self.ID_FIELD], expected, self.ID_FIELD)
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (KeyError, TypeError, ValueError, RecursionError):
            _fail("MALFORMED_PROJECTION_ENVELOPE")

    @classmethod
    def create(cls, body):
        try:
            _canonical_candidate(body)
            value = _json(body)
            _validate(value)
            value["schema_version"] = cls.SCHEMA
            value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
            return cls(value)
        except GameplayContractError:
            raise
        except (KeyError, TypeError, ValueError, RecursionError):
            _fail("MALFORMED_PROJECTION_BODY")

    @classmethod
    def from_dict(cls, value):
        return cls(value)

    @classmethod
    def from_json(cls, value):
        try:
            if type(value) not in (bytes, str):
                _fail("CANONICAL_UTF8_JSON_REQUIRED")
            raw = value.encode("utf-8") if type(value) is str else value
            record = cls.from_dict(json.loads(raw, object_pairs_hook=_duplicate_keys, parse_constant=_nonfinite))
            if raw != record.serialize().encode("utf-8"):
                _fail("NONCANONICAL_PROJECTION_BYTES")
            return record
        except GameplayContractError:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            _fail("MALFORMED_PROJECTION_JSON")

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


def create_projection(anchors):
    """Build the fixed authored rule after exact complete-anchor validation."""
    try:
        if anchors is not VERIFIED_ANCHORS:
            _canonical_candidate(anchors)
        anchors = _json(anchors)
        validate_spans(anchors)
        rule = {"rule_reference": "601.2d", **_json(RULE_CONTENT["601.2d"]), "source_anchor": anchors[0]}
        rule["rule_id"] = rule_identity(rule)
        return BoundedSharedTargetAllocationProjection.create({**_fixed_body(), "rules": [rule]})
    except GameplayContractError:
        raise
    except (KeyError, TypeError, ValueError, RecursionError):
        _fail("MALFORMED_SELECTED_ANCHOR")
