"""Closed, immutable evidence envelopes for thirteen mana-ability source units.

These records describe retained source knowledge. They cannot classify real
abilities, act as gameplay snapshots, or confer activation, mana or payment authority.
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
    _json, _freeze, _keys, _exact, _hash, _duplicate_keys, _nonfinite,
)
from .bounded_mana_scope import (
    SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES, UNSUPPORTED_DIMENSIONS,
)

CANONICAL_MAIN = "6d7542f7d375e6c75e3de7bf6ce3010868ca04ad"
RULE_ID_DOMAIN = "gameplay-cr-bounded-mana-rule-v1"
SOURCE_BINDING = _freeze({
    "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH,
    "effective_date": EFFECTIVE_DATE, "verification_result_id": VERIFICATION_RESULT_ID,
    "correspondence_review_id": CORRESPONDENCE_REVIEW_ID,
    "artifact_review_package_id": ARTIFACT_REVIEW_PACKAGE_ID, "selection_id": SELECTION_ID,
})
AUTHORIZATION = _freeze({
    "scope": "BOUNDED MANA ABILITY RULES PROJECTION", "basis": "OWNER_EXPLICIT_TASK_AUTHORIZATION",
    "authorized_on": "2026-10-18", "source_policy_clearance": "not_granted",
    "selected_source_units": list(SELECTED_REFERENCES), "execution_authorized": False,
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
PRIOR_PACKAGE_IDS = _freeze({'bounded_casting_projection': 'sha256:d2b1832f170d1bbd6ef21efe3d3452923880cc47c57dad523f7aefff4bc427d7',
 'direct_foundational_dependencies': 'sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a',
 'execution_profile_design': 'sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687',
 'foundational': 'sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea',
 'madness_casting_dependency_design': 'sha256:06cd012d08d204f10337d834f312bcf19b060a3569ef3cf879c46714d30944c8',
 'mana_ability_dependency_design': 'sha256:6b1d0165bc0fab488ff7fd4aa84aa5bf5ccdb0e991c99a989d1ef6d3a6a09ce1',
 'object_control_exceptions': 'sha256:f8cf8053b8bf9e7cc9471520eb02cc3e1e29a716f99a2ac623ec36b40343acab',
 'zone_change_direct_dependencies': 'sha256:d51fab1425f6aa9b82e4621ac8c88d4b83d736c6906a4f4c589c41ff1aeadba4',
 'zone_change_exceptions': 'sha256:4836f6ea330cc40365540f85541160ef2251ff6ed88f7959f9d9e594031f7875'})
DESIGN_IDS = _freeze({'behavior_design_id': 'sha256:3fc6944f1bb527715d35b82ce26bbe99fa3a5d9c85cb98fd0188d2682926d83a',
 'classification_design_id': 'sha256:794c246ea5c65592b24da266540dd4cc3f4ebb79b1bb2b596d1f90e682079630',
 'consumer_matrix_id': 'sha256:d290476928524b4b83e175667a720a3a287777c9dc96413dff3a15b0a4097134',
 'controller_design_id': 'sha256:2fee7d411ef855b5e639949b2482e1c0a0f3b1c3cbbcd311de55a781f375330f',
 'projection_frontier_id': 'sha256:82e467501fd2dae85dc829217d94b2a5a4c8f062348bc6dcabf250ba599f24c9',
 'readiness_id': 'sha256:9b82b78f79177a20a27a8e1808e48f23c41eb790307728201c987eb680534cdf'})
PROJECTION_FIELDS = frozenset({
    "game_id", "canonical_base", "projection_kind", "status", "milestone_status",
    "selected_rule_count", "new_source_units_projected", "total_projected_rule_count",
    "source_binding", "authorization", "prior_design_package_id", "source_anchor_policy",
    "rules", "graph", "unsupported_dimensions", "boundary_flags",
})
REVIEW_KINDS = frozenset({
    "design_source_correspondence", "family_closure_review", "consumer_reassessment",
    "classification_readiness", "behavior_readiness", "overall_readiness", "composite_coverage",
})
REVIEW_FIELDS = frozenset({
    "game_id", "canonical_base", "review_kind", "status", "bounded_mana_projection_id",
    "source_binding", "prior_package_ids", "design_ids", "findings", "boundary_flags",
})


def _fail(field, message="invalid bounded mana ability evidence"):
    raise GameplayContractError("bounded_mana_projection_contract", f"{field}: {message}")


def rule_identity(rule):
    body = {key: item for key, item in _json(rule).items() if key != "rule_id"}
    return "sha256:" + sha256_identity({"domain": RULE_ID_DOMAIN, "content": body})


def _validate_anchor(anchor, reference):
    # These pins are metadata calculated from the attached exact artifact. An
    # offline load checks retained evidence; only the source entry point opens
    # and verifies artifact bytes to establish fresh source correspondence.
    from .bounded_mana_source import VERIFIED_ANCHORS
    expected = next(item for item in VERIFIED_ANCHORS if item["rule_reference"] == reference)
    _exact(anchor, expected, "source_anchor")


def _validate_projection(body):
    _keys(body, PROJECTION_FIELDS, "projection")
    for field, expected in {
        "game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "projection_kind": "NON_EXECUTABLE", "status": "PROJECTED_FOR_REVIEW",
        "milestone_status": "BOUNDED_MANA_ABILITY_RULES_PROJECTED", "selected_rule_count": 13,
        "new_source_units_projected": 13, "total_projected_rule_count": 81,
        "source_binding": SOURCE_BINDING, "authorization": AUTHORIZATION,
        "prior_design_package_id": PRIOR_PACKAGE_IDS["mana_ability_dependency_design"],
        "source_anchor_policy": "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR",
        "boundary_flags": BOUNDARY_FLAGS, "unsupported_dimensions": UNSUPPORTED_DIMENSIONS,
        "graph": {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES},
    }.items():
        _exact(body[field], expected, field)
    rules = body["rules"]
    if not isinstance(rules, list) or len(rules) != 13:
        _fail("rules", "exactly thirteen source units are authorized")
    for rule, reference in zip(rules, SELECTED_REFERENCES):
        _keys(rule, {"rule_reference", "rule_id", "source_anchor", *RULE_CONTENT[reference]}, "rule")
        _exact(rule["rule_reference"], reference, "rule_reference")
        for field, expected in RULE_CONTENT[reference].items():
            _exact(rule[field], expected, "rule." + field)
        _validate_anchor(rule["source_anchor"], reference)
        _exact(rule["rule_id"], rule_identity(rule), "rule_id")


def _safe_findings(value):
    """Reject authority promotion, execution and prose even after a rehash."""
    forbidden = {"source_prose", "source_text", "official_prose", "official_examples", "raw_bytes",
                 "attachment_path", "artifact_path", "source_path", "runtime_transition"}
    fixed = {
        "execution_ready": False, "execution_authorized": False, "real_rules_executable": False,
        "real_snapshot_created": False, "real_profile_activated": False,
        "source_body_retained": False, "oracle_ingested": False, "authorized": False,
        "semantic_closure": "OPEN", "mutated": False,
        "source_policy_clearance": "not_granted", "runtime_implemented": False,
        "fictional_mana_satisfies_real_605": False, "payment_executed": False,
        "cost_calculation_implemented": False,
        "classification_implemented": False, "mana_production_implemented": False,
        "mana_pool_implemented": False, "controller_assignment_implemented": False,
        "activated_abilities_implemented": False, "triggered_abilities_implemented": False,
        "fictional_mana_satisfies_real_605_execution": False,
        "required_primitives_available": False, "real_execution_primitives_available": [],
        "implies_complete_spell_casting": False, "parent_projection_satisfies_siblings": False,
        "satisfied_by_parent_projection": False, "satisfies_unprojected_stages": False,
        "historical_design_package_mutated": False, "historical_anchors_converted": False,
        "readiness_code": "REAL_EXECUTION_PROFILE_NOT_READY",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if key in forbidden:
                _fail("findings", "source prose or execution fields are forbidden")
            if key in fixed:
                _exact(item, fixed[key], "findings." + key)
            if key == "execution_readiness" and item not in ("BLOCKED", "EXECUTION_BLOCKED"):
                _fail("findings.execution_readiness", "execution remains blocked")
            _safe_findings(item)
    elif isinstance(value, list):
        for item in value:
            _safe_findings(item)


@dataclass(frozen=True)
class _BoundedManaRecord(Contract):
    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str]
    ID_FIELD: ClassVar[str]
    BODY_FIELDS: ClassVar[frozenset[str]]

    def __post_init__(self):
        try:
            value = _json(self._payload)
            _keys(value, self.BODY_FIELDS | {"schema_version", self.ID_FIELD}, "envelope")
            _exact(value["schema_version"], self.SCHEMA, "schema_version")
            _hash(value[self.ID_FIELD], self.ID_FIELD)
            body = {key: item for key, item in value.items() if key not in {"schema_version", self.ID_FIELD}}
            self._validate_body(body)
            expected = "sha256:" + sha256_identity({"domain": self.SCHEMA,
                "content": {key: item for key, item in value.items() if key != self.ID_FIELD}})
            _exact(value[self.ID_FIELD], expected, self.ID_FIELD)
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("envelope", "malformed evidence contract")

    @classmethod
    def create(cls, body):
        value = _json(body)
        _keys(value, cls.BODY_FIELDS, "create")
        cls._validate_body(value)
        value["schema_version"] = cls.SCHEMA
        value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
        return cls(value)

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
            _fail("JSON", "malformed evidence JSON")

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
class BoundedManaProjection(_BoundedManaRecord):
    SCHEMA: ClassVar[str] = "gameplay-cr-bounded-mana-projection-v1"
    ID_FIELD: ClassVar[str] = "projection_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = PROJECTION_FIELDS
    _validate_body = staticmethod(_validate_projection)


@dataclass(frozen=True)
class BoundedManaReview(_BoundedManaRecord):
    SCHEMA: ClassVar[str] = "gameplay-cr-bounded-mana-review-v1"
    ID_FIELD: ClassVar[str] = "review_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = REVIEW_FIELDS

    @staticmethod
    def _validate_body(body):
        _keys(body, REVIEW_FIELDS, "review")
        for field, expected in {
            "game_id": "magic", "canonical_base": CANONICAL_MAIN,
            "status": "APPEND_ONLY_REVIEW", "source_binding": SOURCE_BINDING,
            "prior_package_ids": PRIOR_PACKAGE_IDS, "design_ids": DESIGN_IDS,
            "boundary_flags": BOUNDARY_FLAGS,
        }.items():
            _exact(body[field], expected, field)
        _hash(body["bounded_mana_projection_id"], "bounded_mana_projection_id")
        if body["review_kind"] not in REVIEW_KINDS or not isinstance(body["findings"], dict):
            _fail("review_kind", "closed review kind and findings required")
        _safe_findings(body["findings"])


def create_projection(anchors):
    """Construct only the fixed authored records with pinned verified metadata."""
    anchors = list(anchors)
    if len(anchors) != 13:
        _fail("anchors", "exactly thirteen selected anchors required")
    rules = []
    for reference, anchor in zip(SELECTED_REFERENCES, anchors):
        rule = {"rule_reference": reference, **_json(RULE_CONTENT[reference]), "source_anchor": _json(anchor)}
        rule["rule_id"] = rule_identity(rule)
        rules.append(rule)
    return BoundedManaProjection.create({
        "game_id": "magic", "canonical_base": CANONICAL_MAIN,
        "projection_kind": "NON_EXECUTABLE", "status": "PROJECTED_FOR_REVIEW",
        "milestone_status": "BOUNDED_MANA_ABILITY_RULES_PROJECTED", "selected_rule_count": 13,
        "new_source_units_projected": 13, "total_projected_rule_count": 81,
        "source_binding": SOURCE_BINDING, "authorization": AUTHORIZATION,
        "prior_design_package_id": PRIOR_PACKAGE_IDS["mana_ability_dependency_design"],
        "source_anchor_policy": "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR",
        "rules": rules, "graph": {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES},
        "unsupported_dimensions": UNSUPPORTED_DIMENSIONS, "boundary_flags": BOUNDARY_FLAGS,
    })
