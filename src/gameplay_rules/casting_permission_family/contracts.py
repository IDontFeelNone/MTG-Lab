"""Strict immutable contract for the one complete casting-permission family projection."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, ClassVar, Mapping

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import (
    ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, VERIFICATION_RESULT_ID,
    CORRESPONDENCE_REVIEW_ID, ARTIFACT_REVIEW_PACKAGE_ID, SELECTION_ID,
    _json, _freeze, _duplicate_keys, _nonfinite,
)
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate
from .scope import SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES, UNSUPPORTED_DIMENSIONS
from .source import VERIFIED_ANCHORS, SPAN_POLICY, validate_spans

CANONICAL_MAIN = "d294835929a320fce01fb4025bdb3a4934e2eeaa"
RULE_ID_DOMAIN = "gameplay-cr-casting-permission-family-rule-v1"
PRIOR_PACKAGE_ID = "sha256:72536eb1bbbc3422797215a3630a9f512b9d2a0b758e8a852e4903e71e047e82"
SOURCE_BINDING = _freeze({
    "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
    "effective_date": EFFECTIVE_DATE, "verification_result_id": VERIFICATION_RESULT_ID,
    "correspondence_review_id": CORRESPONDENCE_REVIEW_ID,
    "artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID, "selection_id": SELECTION_ID,
})
AUTHORIZATION = _freeze({
    "scope": "CASTING-PERMISSION FAMILY BATCH",
    "basis": "OWNER_EXPLICIT_TASK_AUTHORIZATION", "authorized_on": "2026-10-22",
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


def _fail(field):
    raise GameplayContractError("casting_permission_family_contract", field)


def _snapshot(value):
    """Validate original JSON types before taking a private builtin-only copy."""
    return json.loads(_canonical_candidate(value))


def rule_identity(rule):
    value = _snapshot(rule)
    if type(value) is not dict:
        _fail("PLAIN_RULE_RECORD_REQUIRED")
    body = {key: child for key, child in value.items() if key != "rule_id"}
    return "sha256:" + sha256_identity({"domain": RULE_ID_DOMAIN, "content": body})


def _fixed_body():
    return {"game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "projection_kind": "NON_EXECUTABLE", "status": "PROJECTED_FOR_REVIEW",
        "milestone_status": "CASTING_PERMISSION_FAMILY_PROJECTED",
        "selected_references": list(SELECTED_REFERENCES), "selected_rule_count": len(SELECTED_REFERENCES),
        "new_source_units_projected": len(SELECTED_REFERENCES), "total_projected_rule_count": 100,
        "resulting_projection_count": 15, "source_binding": _json(SOURCE_BINDING),
        "authorization": _json(AUTHORIZATION), "prior_casting_stage_package_id": PRIOR_PACKAGE_ID,
        "source_anchor_policy": SPAN_POLICY,
        "graph": {"nodes": _json(GRAPH_NODES), "edges": _json(GRAPH_EDGES)},
        "unsupported_dimensions": _json(UNSUPPORTED_DIMENSIONS),
        "boundary_flags": _json(BOUNDARY_FLAGS)}


def _body(anchors):
    rules = []
    for reference, anchor in zip(SELECTED_REFERENCES, anchors):
        rule = {"rule_reference": reference, **_json(RULE_CONTENT[reference]), "source_anchor": anchor}
        rule["rule_id"] = rule_identity(rule)
        rules.append(rule)
    return {**_fixed_body(), "rules": rules}


def _validate(body):
    if type(body) is not dict:
        _fail("PLAIN_PROJECTION_BODY_REQUIRED")
    # Comparing canonical bytes preserves every bool/int/float distinction and
    # rejects coherent rehashes of claims outside this exact authored boundary.
    if _canonical_candidate(body) != _canonical_candidate(_body(_json(VERIFIED_ANCHORS))):
        _fail("EXACT_COMPLETE_FAMILY_AUTHORED_PROJECTION_REQUIRED")
    validate_spans([rule["source_anchor"] for rule in body["rules"]])
    for rule in body["rules"]:
        if rule["rule_id"] != rule_identity(rule):
            _fail("RULE_OWN_IDENTITY_INVALID")


@dataclass(frozen=True)
class CastingPermissionFamilyProjection(Contract):
    """Descriptive knowledge only; no snapshot, execution profile or runtime."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str] = "gameplay-cr-casting-permission-family-projection-v1"
    ID_FIELD: ClassVar[str] = "projection_id"

    def __post_init__(self):
        try:
            value = _snapshot(self._payload)
            if (type(value) is not dict or type(value.get("schema_version")) is not str
                    or value["schema_version"] != self.SCHEMA
                    or type(value.get(self.ID_FIELD)) is not str):
                _fail("PROJECTION_ENVELOPE_REQUIRED")
            body = {key: item for key, item in value.items() if key not in ("schema_version", self.ID_FIELD)}
            _validate(body)
            identity_body = {key: item for key, item in value.items() if key != self.ID_FIELD}
            identity = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": identity_body})
            if value[self.ID_FIELD] != identity:
                _fail("PROJECTION_OWN_IDENTITY_INVALID")
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (KeyError, TypeError, ValueError, RecursionError):
            _fail("MALFORMED_PROJECTION_ENVELOPE")

    @classmethod
    def create(cls, body):
        try:
            value = _snapshot(body)
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
    """Use the privately owned, exactly validated complete-family anchor snapshot."""
    try:
        snapshot = validate_spans(anchors)
        return CastingPermissionFamilyProjection.create(_body(snapshot))
    except GameplayContractError:
        raise
    except (KeyError, TypeError, ValueError, RecursionError):
        _fail("MALFORMED_SELECTED_ANCHORS")
