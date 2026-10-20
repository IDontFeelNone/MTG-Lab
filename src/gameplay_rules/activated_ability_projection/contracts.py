"""Closed immutable contract for exactly three non-executable procedure units."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any, ClassVar, Mapping

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.contracts import (
    ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, VERIFICATION_RESULT_ID,
    CORRESPONDENCE_REVIEW_ID, ARTIFACT_REVIEW_PACKAGE_ID, SELECTION_ID,
    _json, _freeze, _keys, _exact, _hash, _duplicate_keys, _nonfinite,
)
from .scope import (
    SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES, UNSUPPORTED_DIMENSIONS,
)
from .source import VERIFIED_ANCHORS, SPAN_POLICY, validate_spans

CANONICAL_MAIN = "2aa01764db0cfbcd89bc3a30a4433c4f24ea5893"
RULE_ID_DOMAIN = "gameplay-cr-bounded-activated-ability-rule-v1"
DESIGN_PACKAGE_ID = "sha256:cfe499b63d673af2337beac94134d30b1dac2a14097e244e79742670ed2ec1b1"
SOURCE_BINDING = _freeze({
    "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
    "effective_date": EFFECTIVE_DATE, "verification_result_id": VERIFICATION_RESULT_ID,
    "correspondence_review_id": CORRESPONDENCE_REVIEW_ID,
    "artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID, "selection_id": SELECTION_ID,
})
AUTHORIZATION = _freeze({
    "scope": "BOUNDED ACTIVATED ABILITY PROCEDURE PROJECTION",
    "basis": "OWNER_EXPLICIT_TASK_AUTHORIZATION", "authorized_on": "2026-10-20",
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


def _fail(field, message="invalid bounded activated ability projection"):
    raise GameplayContractError("bounded_activated_ability_contract", f"{field}: {message}")


def _plain_candidate(value):
    """Reject coercible containers and numeric subclasses at public boundaries."""
    kind = type(value)
    if kind is dict:
        for key, item in value.items():
            if type(key) is not str:
                _fail("JSON", "plain string keys required")
            _plain_candidate(item)
    elif kind is list:
        for item in value:
            _plain_candidate(item)
    elif kind is float:
        if not math.isfinite(value):
            _fail("JSON", "finite numbers required")
    elif kind not in (str, bool, int, type(None)):
        _fail("JSON", "plain JSON types required without coercion")


def rule_identity(rule):
    content = {key: value for key, value in _json(rule).items() if key != "rule_id"}
    return "sha256:" + sha256_identity({"domain": RULE_ID_DOMAIN, "content": content})


def _fixed_body():
    return {
        "game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "projection_kind": "NON_EXECUTABLE", "status": "PROJECTED_FOR_REVIEW",
        "milestone_status": "BOUNDED_ACTIVATED_ABILITY_PROCEDURE_PROJECTED",
        "selected_references": list(SELECTED_REFERENCES), "selected_rule_count": 3,
        "new_source_units_projected": 3, "total_projected_rule_count": 88,
        "resulting_projection_count": 10, "source_binding": _json(SOURCE_BINDING),
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
    if type(rules) is not list or len(rules) != 3:
        _fail("rules", "exactly three source units are authorized")
    validate_spans([rule.get("source_anchor") if type(rule) is dict else None for rule in rules])
    for reference, rule, anchor in zip(SELECTED_REFERENCES, rules, VERIFIED_ANCHORS):
        _keys(rule, {"rule_reference", "rule_id", "source_anchor", *RULE_CONTENT[reference]}, "rule")
        _exact(rule["rule_reference"], reference, "rule_reference")
        for field, expected in RULE_CONTENT[reference].items():
            _exact(rule[field], expected, "rule." + field)
        _exact(rule["source_anchor"], anchor, "source_anchor")
        _exact(rule["rule_id"], rule_identity(rule), "rule_id")


@dataclass(frozen=True)
class BoundedActivatedAbilityProjection(Contract):
    """Knowledge-only contract; no runtime module consumes it as rules authority."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str] = "gameplay-cr-bounded-activated-ability-projection-v1"
    ID_FIELD: ClassVar[str] = "projection_id"

    def __post_init__(self):
        try:
            _plain_candidate(self._payload)
            value = _json(self._payload)
            _keys(value, _FIELDS | {"schema_version", self.ID_FIELD}, "envelope")
            _exact(value["schema_version"], self.SCHEMA, "schema_version")
            _hash(value[self.ID_FIELD], self.ID_FIELD)
            _validate({key: item for key, item in value.items()
                       if key not in ("schema_version", self.ID_FIELD)})
            content = {key: item for key, item in value.items() if key != self.ID_FIELD}
            expected = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": content})
            _exact(value[self.ID_FIELD], expected, self.ID_FIELD)
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (KeyError, TypeError, ValueError, RecursionError):
            _fail("envelope", "malformed evidence contract")

    @classmethod
    def create(cls, body):
        try:
            _plain_candidate(body)
            value = _json(body)
            _validate(value)
            value["schema_version"] = cls.SCHEMA
            value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
            return cls(value)
        except GameplayContractError:
            raise
        except (KeyError, TypeError, ValueError, RecursionError):
            _fail("create", "malformed evidence body")

    @classmethod
    def from_dict(cls, value):
        return cls(value)

    @classmethod
    def from_json(cls, value):
        try:
            if type(value) not in (bytes, str):
                _fail("JSON", "canonical UTF-8 bytes or text required")
            raw = value.encode("utf-8") if type(value) is str else value
            record = cls.from_dict(json.loads(raw, object_pairs_hook=_duplicate_keys, parse_constant=_nonfinite))
            if raw != record.serialize().encode("utf-8"):
                _fail("JSON", "noncanonical projection bytes")
            return record
        except GameplayContractError:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            _fail("JSON", "malformed projection JSON")

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
    """Validate the exact anchor set and construct only the fixed authored rules."""
    try:
        # The module-owned immutable constant is the explicit offline metadata
        # route. Caller-owned candidates must already have plain JSON types.
        if anchors is not VERIFIED_ANCHORS:
            _plain_candidate(anchors)
        anchors = _json(anchors)
        validate_spans(anchors)
        _exact(anchors, VERIFIED_ANCHORS, "anchors")
        rules = []
        for reference, anchor in zip(SELECTED_REFERENCES, anchors):
            rule = {"rule_reference": reference, **_json(RULE_CONTENT[reference]), "source_anchor": anchor}
            rule["rule_id"] = rule_identity(rule)
            rules.append(rule)
        return BoundedActivatedAbilityProjection.create({**_fixed_body(), "rules": rules})
    except GameplayContractError:
        raise
    except (KeyError, TypeError, ValueError, RecursionError):
        _fail("anchors", "malformed selected anchors")
