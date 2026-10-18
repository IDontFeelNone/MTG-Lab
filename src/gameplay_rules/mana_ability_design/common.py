"""Closed immutable metadata envelopes, separate from gameplay authority."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, ClassVar, Mapping

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.execution_design.contracts import _json, _freeze

PM_INPUT = "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED"

CANONICAL_MAIN = "3d403a62c66b8cb678eda9c07038da3ac59ae659"
RELEASE_DATE = "2026-09-25"
PERMISSIONS = {name: "NOT_ESTABLISHED" for name in
              ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")}
FLAGS = {
    "canonical_base": CANONICAL_MAIN, "release_date": RELEASE_DATE,
    "status": "DESIGN_ONLY", "design_only": True, "non_executable": True,
    "execution_authorized": False, "projection_authorized": False,
    "new_source_units_projected": 0, "projected_real_source_units": 68,
    "source_artifact_required": False, "new_real_source_anchors_created": 0,
    "source_verification_claimed": False,
    "source_body_retained": False, "real_rules_executable": False,
    "owner_execution_approval": "NOT_GRANTED", "source_policy_clearance": "not_granted",
    "oracle_ingested": False, "real_snapshot_created": False, "real_profile_activated": False,
    "permissions": PERMISSIONS,
}
PERMISSIONS = _freeze(PERMISSIONS)
FLAGS = _freeze(FLAGS)


def _fail(message="invalid non-executable mana-ability design"):
    raise GameplayContractError("mana_ability_design", message)


def _keys(value, fields, field="record"):
    if not isinstance(value, dict) or set(value) != set(fields):
        _fail(field + ": missing or unexpected fields")


def _exact(value, expected, field="record"):
    if deterministic_json(value) != deterministic_json(_json(expected)):
        _fail(field + ": fixed design invariant differs")


def _text(value, field="text", *, maximum=4096):
    if type(value) is not str or not value.strip() or len(value) > maximum:
        _fail(field + ": bounded nonempty text required")


def _hash(value, field="identity"):
    if type(value) is not str or not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        _fail(field + ": content identity required")


def _integer(value, field="integer", *, minimum=0, maximum=1_000_000_000):
    if type(value) is not int or not minimum <= value <= maximum:
        _fail(field + ": bounded integer required")


def _enum(value, permitted, field="state"):
    if type(value) is not str or value not in permitted:
        _fail(field + ": unsupported state")


def _strings(value, field="values", *, nonempty=False, unique=True):
    if not isinstance(value, list) or len(value) > 256 or (nonempty and not value):
        _fail(field + ": bounded list required")
    for item in value:
        _text(item, field)
    if unique and len(set(value)) != len(value):
        _fail(field + ": duplicates forbidden")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON field")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("non-finite JSON value")


def _boundaries(value):
    """Do not let reidentified design records acquire execution/source authority."""
    fixed = {"execution_ready": False, "execution_supported": False,
             "implementation_available": False, "runtime_conversion": False,
             "source_verified": False, "complete_casting_implied": False,
             "fictional_runtime_authority_inherited": False, "payment_executed": False,
             "calculation_executed": False, "gameplay_executed": False, "authorized": False,
             "runtime_implemented": False, "classification_evaluated": False,
             "activation_performed": False, "trigger_detected": False,
             "resolution_executed": False, "mana_produced": False,
             "mana_pool_mutated": False, "controller_assigned": False,
             "fictional_mana_satisfies_real_605": False, "source_body_retained": False,
             "real_snapshot_created": False, "real_profile_activated": False,
             "required_primitives_available": False, "real_execution_primitives_available": [],
             "classification_implies_execution": False, "source_coverage_implies_execution": False,
             "source_policy_clearance": "not_granted"}
    forbidden = {"source_anchor", "source_anchors", "span_sha256", "byte_start", "byte_end",
                 "line_number", "source_text", "source_prose", "official_text", "official_examples",
                 "oracle_text", "raw_source", "source_excerpt", "artifact_path", "attachment_path"}
    if isinstance(value, dict):
        if set(value) & forbidden:
            _fail("source prose or a newly claimed source anchor is forbidden")
        for key, item in value.items():
            if key in fixed:
                _exact(item, fixed[key], key)
            if key == "execution_readiness" and item not in {"NOT_IMPLEMENTED", "BLOCKED", "UNSUPPORTED", "EXECUTION_BLOCKED"}:
                _fail("design execution readiness cannot be promoted")
            _boundaries(item)
    elif isinstance(value, list):
        for item in value:
            _boundaries(item)


@dataclass(frozen=True)
class DesignRecord(Contract):
    """Identity records design input, never approval or an executable result."""

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
            _keys(value, self.BODY_FIELDS | set(FLAGS) | {"schema_version", self.ID_FIELD})
            _exact(value["schema_version"], self.SCHEMA, "schema_version")
            for key, expected in FLAGS.items():
                _exact(value[key], expected, key)
            body = {key: value[key] for key in self.BODY_FIELDS}
            self._validate_body(body)
            _boundaries(value)
            content = {key: item for key, item in value.items() if key != self.ID_FIELD}
            _hash(value[self.ID_FIELD])
            _exact(value[self.ID_FIELD], "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": content}), self.ID_FIELD)
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            _fail()

    @classmethod
    def create(cls, body):
        try:
            value = _json(body)
            # Accept our own fixed flags when callers derive a revised design.
            for key in set(value) & set(FLAGS):
                _exact(value.pop(key), FLAGS[key], key)
            _keys(value, cls.BODY_FIELDS)
            cls._validate_body(value)
            value.update(_json(FLAGS))
            value["schema_version"] = cls.SCHEMA
            value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
            return cls(value)
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            _fail()

    @classmethod
    def from_dict(cls, value):
        return cls(value)

    @classmethod
    def from_json(cls, value):
        try:
            return cls.from_dict(json.loads(value, object_pairs_hook=_pairs, parse_constant=_nonfinite))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            _fail("malformed design JSON")

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
