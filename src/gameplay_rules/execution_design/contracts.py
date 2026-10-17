"""Immutable, non-executable review and future-profile design records.

These records are metadata contracts. Their identities attest to their contents,
not to owner approval or runtime compatibility. They deliberately provide no
conversion to a gameplay snapshot, engine, action, or legality result.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import math
import re
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, Self

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.scope import SELECTED_REFERENCES


CANONICAL_MAIN = "90ce520be8b0319111ca74fdb385b01de522523a"
PROJECTION_PACKAGE_ID = "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea"
PROJECTION_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
SOURCE_BINDING = MappingProxyType({
    "artifact_hash": "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca",
    "byte_length": 977752,
    "effective_date": "2026-09-25",
    "verification_result_id": "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3",
    "correspondence_review_id": "sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def",
})

_FLAGS = MappingProxyType({
    "design_only": True,
    "real_rules_executable": False,
    "execution_authorized": False,
    "projection_authorized": False,
    "owner_execution_approval": "NOT_GRANTED",
    "source_policy_clearance": "not_granted",
    "source_body_retained": False,
})
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_RULE_REFERENCE = re.compile(r"[1-9][0-9]{2}(?:\.[0-9]+[a-z]?)?\Z")
_VERSION = re.compile(r"(?:[a-z][a-z0-9_-]*-)?v[1-9][0-9]*\Z")
_CLOSURES = frozenset({"CLOSED", "OPEN", "UNKNOWN"})
_READINESS = frozenset({"NOT_ASSESSED", "BLOCKED", "PARTIALLY_READY"})
_ROLES = frozenset({
    "REFERENCE_ONLY", "STATE_MODEL_SEMANTIC", "PRECEDENCE_SEMANTIC",
    "EXECUTION_PRIMITIVE_CANDIDATE", "BLOCKED_BY_DEPENDENCY",
    "BLOCKED_BY_EXCEPTION_SET",
})
_RULE_FIELDS = frozenset({
    "rule_reference", "projection_id", "source_anchor", "semantic_roles", "semantic_role",
    "direct_runtime_relevance", "state_model_relevance", "state_model_candidate",
    "required_semantic_primitives", "unknown_semantic_contexts", "explanation",
    "prerequisite_rules", "unresolved_dependencies", "unprojected_exceptions",
    "unsupported_required_semantic_primitives", "dependency_closure", "exception_closure",
    "known_dependency_closure", "known_exception_closure", "implementation_now_safe",
    "execution_ready", "execution_readiness", "blockers",
})
_CAPABILITY_FIELDS = frozenset({
    "capability_id", "supporting_rules", "semantic_roles", "notes", "dependency_closure",
    "exception_closure", "implementation_primitive_available", "execution_readiness",
    "blocking_references", "required_semantic_primitives", "unknown_semantic_contexts",
    "execution_supported",
})


def _fail(field: str, message: str = "invalid execution design contract") -> None:
    raise GameplayContractError("execution_design_contract", f"{field}: {message}")


def _json(value: Any, *, _depth: int = 0) -> Any:
    """Make a defensive JSON copy, retaining neither user objects nor containers."""
    if _depth > 64:
        _fail("JSON", "nesting limit exceeded")
    if isinstance(value, Mapping):
        copied = {}
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 256:
                _fail("JSON", "bounded string keys required")
            if key in copied:
                _fail("JSON", "duplicate object key")
            copied[key] = _json(item, _depth=_depth + 1)
        return copied
    if isinstance(value, (tuple, list)):
        return [_json(item, _depth=_depth + 1) for item in value]
    if type(value) is str and len(value) > 65536:
        _fail("JSON", "text limit exceeded")
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    _fail("JSON", "unsupported or non-finite value")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _keys(value: Any, fields: Any, field: str) -> None:
    if not isinstance(value, dict) or set(value) != set(fields):
        _fail(field, "missing or unexpected fields")


def _exact(value: Any, expected: Any, field: str) -> None:
    if deterministic_json(value) != deterministic_json(_json(expected)):
        _fail(field, "required design boundary or pinned identity differs")


def _text(value: Any, field: str, *, maximum: int = 4096) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        _fail(field, "nonempty bounded text required")


def _hash(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        _fail(field, "SHA-256 content identity required")


def _version(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _VERSION.fullmatch(value):
        _fail(field, "explicit versioned identifier required")
    if any(part in {"current", "latest"} for part in re.split(r"[-_]", value)):
        _fail(field, "mutable release aliases are forbidden")


def _enum(value: Any, permitted: Any, field: str) -> None:
    if not isinstance(value, str) or value not in permitted:
        _fail(field, "unknown state")


def _strings(value: Any, field: str, *, nonempty: bool = False, unique: bool = True) -> None:
    if not isinstance(value, list) or (nonempty and not value) or len(value) > 256:
        _fail(field, "bounded text list required")
    for item in value:
        _text(item, field)
    if unique and len(set(value)) != len(value):
        _fail(field, "duplicate entries")


def _references(value: Any, field: str, *, selected: bool = False) -> None:
    _strings(value, field)
    for item in value:
        if not _RULE_REFERENCE.fullmatch(item) or (selected and item not in SELECTED_REFERENCES):
            _fail(field, "invalid or out-of-scope rule reference")


def _document(value: Any, field: str, *, nonempty: bool = True) -> None:
    """Validate a structured authored finding whose schema lives in its builder."""
    if not isinstance(value, (list, dict)) or (nonempty and not value):
        _fail(field, "structured design metadata required")


def _false(value: Any, field: str) -> None:
    _exact(value, False, field)


def _source_binding(value: Any, field: str = "source_binding") -> None:
    _keys(value, SOURCE_BINDING, field)
    _exact(value, SOURCE_BINDING, field)


def _anchor(value: Any, reference: str) -> None:
    _keys(value, {
        "rule_reference", "artifact_hash", "byte_start", "byte_end", "line_number",
        "span_sha256", "span_policy",
    }, "source_anchor")
    _exact(value["rule_reference"], reference, "source_anchor.rule_reference")
    _exact(value["artifact_hash"], SOURCE_BINDING["artifact_hash"], "source_anchor.artifact_hash")
    _exact(value["span_policy"], "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR", "source_anchor.span_policy")
    for key in ("byte_start", "byte_end", "line_number"):
        if type(value[key]) is not int:
            _fail("source_anchor." + key, "integer required")
    if not 0 <= value["byte_start"] < value["byte_end"] <= SOURCE_BINDING["byte_length"]:
        _fail("source_anchor", "invalid source span bounds")
    if value["line_number"] < 1:
        _fail("source_anchor.line_number", "positive line required")
    _hash(value["span_sha256"], "source_anchor.span_sha256")


def _review_rule(row: Any, reference: str) -> None:
    _keys(row, _RULE_FIELDS, "rules." + reference)
    _exact(row["rule_reference"], reference, "rule_reference")
    _exact(row["projection_id"], PROJECTION_ID, "rule.projection_id")
    _anchor(row["source_anchor"], reference)
    _strings(row["semantic_roles"], "semantic_roles", nonempty=True)
    for role in row["semantic_roles"]:
        _enum(role, _ROLES, "semantic_roles")
    for key in ("semantic_role", "explanation"):
        _text(row[key], key)
    _enum(row["direct_runtime_relevance"], {"NONE", "FUTURE_STATE_MODEL", "FUTURE_PRIMITIVE", "FUTURE_PRECEDENCE"}, "direct_runtime_relevance")
    for key in ("state_model_relevance", "state_model_candidate"):
        if type(row[key]) is not bool:
            _fail(key, "boolean required")
    for key in ("required_semantic_primitives", "unknown_semantic_contexts",
                "unsupported_required_semantic_primitives", "blockers"):
        _strings(row[key], key)
    for key in ("prerequisite_rules", "unresolved_dependencies", "unprojected_exceptions"):
        _references(row[key], key)
    for key in ("dependency_closure", "exception_closure", "known_dependency_closure", "known_exception_closure"):
        _enum(row[key], _CLOSURES, key)
    for key in ("implementation_now_safe", "execution_ready"):
        _false(row[key], key)
    _enum(row["execution_readiness"], _READINESS, "execution_readiness")
    if row["execution_readiness"] == "PARTIALLY_READY" and (
            reference not in {"102.1", "102.2", "109.1", "109.3", "110.1", "400.1"}
            or not row["state_model_candidate"]):
        _fail("execution_readiness", "partial readiness is descriptive state vocabulary only")
    if row["unresolved_dependencies"] or row["unprojected_exceptions"]:
        _exact(row["execution_readiness"], "BLOCKED", "execution_readiness")
    if row["unresolved_dependencies"] and row["dependency_closure"] == "CLOSED":
        _fail("dependency_closure", "unresolved dependencies cannot be closed")
    if row["unresolved_dependencies"] and row["known_dependency_closure"] == "CLOSED":
        _fail("known_dependency_closure", "unresolved dependencies cannot be closed")
    if row["unprojected_exceptions"] and row["exception_closure"] == "CLOSED":
        _fail("exception_closure", "unprojected exceptions cannot be closed")
    if row["unprojected_exceptions"] and row["known_exception_closure"] == "CLOSED":
        _fail("known_exception_closure", "unprojected exceptions cannot be closed")
    required_dependency = {
        "101.1": "104.3a", "101.2a": "113.10", "108.3": "407",
        "108.4": "112.2", "110.2": "111.2",
    }.get(reference)
    if required_dependency and required_dependency not in row["unresolved_dependencies"]:
        _fail("unresolved_dependencies", "known required dependency omitted")
    required_exceptions = {
        "109.4": ["109.4" + suffix for suffix in "abcdefg"],
        "400.7": ["400.7" + suffix for suffix in "abcdefghijkm"],
    }.get(reference)
    if required_exceptions:
        if not set(required_exceptions) <= set(row["unprojected_exceptions"]):
            _fail("unprojected_exceptions", "known exception family omitted")
        _exact(row["exception_closure"], "OPEN", "exception_closure")
        _exact(row["execution_readiness"], "BLOCKED", "execution_readiness")
    if reference == "108.1":
        _exact(row["semantic_roles"], ["REFERENCE_ONLY"], "108.1.semantic_roles")
        _exact(row["direct_runtime_relevance"], "NONE", "108.1.direct_runtime_relevance")
        _exact(row["required_semantic_primitives"], [], "108.1.required_semantic_primitives")
        _exact(row["unsupported_required_semantic_primitives"], [], "108.1.unsupported_required_semantic_primitives")
        _false(row["state_model_relevance"], "108.1.state_model_relevance")
        _false(row["state_model_candidate"], "108.1.state_model_candidate")
        _exact(row["execution_readiness"], "BLOCKED", "108.1.execution_readiness")


def _duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            _fail("JSON", "duplicate object key")
        value[key] = item
    return value


def _nonfinite(_value: str) -> None:
    _fail("JSON", "non-finite number")


@dataclass(frozen=True)
class DesignRecord(Contract):
    """Defensively frozen JSON metadata with a domain-separated identity."""

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str] = ""
    ID_FIELD: ClassVar[str] = ""
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def __post_init__(self) -> None:
        try:
            if not self.SCHEMA or not self.ID_FIELD or not self.BODY_FIELDS:
                _fail("envelope", "concrete design record required")
            value = _json(self._payload)
            _keys(value, self.BODY_FIELDS | set(_FLAGS) | {"schema_version", self.ID_FIELD}, "envelope")
            _exact(value["schema_version"], self.SCHEMA, "schema_version")
            _hash(value[self.ID_FIELD], self.ID_FIELD)
            for key, expected in _FLAGS.items():
                _exact(value[key], expected, key)
            body = {key: value[key] for key in self.BODY_FIELDS}
            self._validate(body)
            content = {key: item for key, item in value.items() if key != self.ID_FIELD}
            expected = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": content})
            _exact(value[self.ID_FIELD], expected, self.ID_FIELD)
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
            _fail("envelope", "malformed design record")

    @classmethod
    def _validate(cls, body: dict[str, Any]) -> None:
        _keys(body, cls.BODY_FIELDS, "body")
        _exact(body["game_id"], "magic", "game_id")

    @classmethod
    def create(cls, body: Mapping[str, Any]) -> Self:
        try:
            value = _json(body)
            _keys(value, cls.BODY_FIELDS, "create")
            cls._validate(value)
            value.update(_FLAGS)
            value["schema_version"] = cls.SCHEMA
            value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
            return cls(value)
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
            _fail("create", "malformed design body")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Self:
        return cls(value)

    @classmethod
    def from_json(cls, value: bytes | str) -> Self:
        try:
            if not isinstance(value, (bytes, str)):
                _fail("JSON", "UTF-8 bytes or text required")
            return cls.from_dict(json.loads(value, object_pairs_hook=_duplicate_keys, parse_constant=_nonfinite))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
            _fail("JSON", "malformed design JSON")

    @property
    def identity(self) -> str:
        return self._payload[self.ID_FIELD]

    def to_dict(self) -> dict[str, Any]:
        return _json(self._payload)

    def serialize(self) -> str:
        return deterministic_json(self.to_dict())

    def verify(self) -> Self:
        type(self).from_dict(self.to_dict())
        return self

    def __getattr__(self, name: str) -> Any:
        payload = object.__getattribute__(self, "_payload")
        if name in payload:
            return payload[name]
        raise AttributeError(name)


@dataclass(frozen=True)
class FoundationalProjectionReview(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-foundational-projection-review-v1"
    ID_FIELD: ClassVar[str] = "projection_review_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "game_id", "review_version", "projection_package_id", "projection_id", "source_binding",
        "reviewer_class", "reviewed_on", "review_status", "rules", "dependency_findings",
        "exception_findings", "execution_readiness_findings", "limitations", "unsupported_dimensions",
    })

    @classmethod
    def _validate(cls, body: dict[str, Any]) -> None:
        super()._validate(body)
        _version(body["review_version"], "review_version")
        _exact(body["projection_package_id"], PROJECTION_PACKAGE_ID, "projection_package_id")
        _exact(body["projection_id"], PROJECTION_ID, "projection_id")
        _source_binding(body["source_binding"])
        _exact(body["reviewer_class"], "PROJECT_AUTHORED_EXECUTION_DESIGN_REVIEW", "reviewer_class")
        _exact(body["review_status"], "REVIEWED_FOR_EXECUTION_DESIGN", "review_status")
        _text(body["reviewed_on"], "reviewed_on", maximum=10)
        try:
            if date.fromisoformat(body["reviewed_on"]).isoformat() != body["reviewed_on"]:
                _fail("reviewed_on", "ISO calendar date required")
        except ValueError:
            _fail("reviewed_on", "ISO calendar date required")
        rows = body["rules"]
        if not isinstance(rows, list) or len(rows) != len(SELECTED_REFERENCES):
            _fail("rules", "exactly 20 ordered review rows required")
        previous_end = previous_line = 0
        for row, reference in zip(rows, SELECTED_REFERENCES):
            _review_rule(row, reference)
            anchor = row["source_anchor"]
            if anchor["byte_start"] < previous_end or anchor["line_number"] <= previous_line:
                _fail("source_anchor", "source spans must be ordered and nonoverlapping")
            previous_end, previous_line = anchor["byte_end"], anchor["line_number"]
        for key in ("dependency_findings", "exception_findings", "execution_readiness_findings"):
            _document(body[key], key)
        _exact(body["execution_readiness_findings"], {
            "overall": "BLOCKED", "rules_reviewed": 20,
            "reference_only": ["108.1"],
            "descriptive_state_model_candidates": [row["rule_reference"] for row in rows
                                                    if row["state_model_candidate"]],
            "partially_ready_designs": [row["rule_reference"] for row in rows
                                       if row["execution_readiness"] == "PARTIALLY_READY"],
            "execution_ready_rules": [], "available_real_primitives": [],
            "execution_approval": "NOT_GRANTED",
        }, "execution_readiness_findings")
        for key in ("limitations", "unsupported_dimensions"):
            _strings(body[key], key, nonempty=True)


@dataclass(frozen=True)
class RealRulesCapabilityMatrix(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-real-capability-design-matrix-v1"
    ID_FIELD: ClassVar[str] = "capability_matrix_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "game_id", "matrix_version", "projection_id", "projection_review_id", "capabilities",
        "coverage_policy", "overall_execution_readiness",
    })

    @classmethod
    def _validate(cls, body: dict[str, Any]) -> None:
        super()._validate(body)
        _version(body["matrix_version"], "matrix_version")
        _exact(body["projection_id"], PROJECTION_ID, "projection_id")
        _hash(body["projection_review_id"], "projection_review_id")
        _exact(body["overall_execution_readiness"], "BLOCKED", "overall_execution_readiness")
        _exact(body["coverage_policy"], {
            "projection_presence_does_not_support_execution": True,
            "partially_ready_means_descriptive_state_model_candidate_only": True,
            "real_execution_primitives_available": [],
            "unsupported_and_unknown_remain_distinct": True,
        }, "coverage_policy")
        rows = body["capabilities"]
        if not isinstance(rows, list) or not 13 <= len(rows) <= 64:
            _fail("capabilities", "bounded capability design rows required")
        identifiers = []
        for row in rows:
            _keys(row, _CAPABILITY_FIELDS, "capability")
            _text(row["capability_id"], "capability_id", maximum=128)
            identifiers.append(row["capability_id"])
            _references(row["supporting_rules"], "supporting_rules", selected=True)
            _strings(row["semantic_roles"], "semantic_roles", nonempty=True)
            for role in row["semantic_roles"]:
                _enum(role, _ROLES, "semantic_roles")
            for key in ("dependency_closure", "exception_closure"):
                _enum(row[key], _CLOSURES, key)
            for key in ("implementation_primitive_available", "execution_supported"):
                _false(row[key], key)
            _enum(row["execution_readiness"], _READINESS, "execution_readiness")
            _references(row["blocking_references"], "blocking_references")
            for key in ("required_semantic_primitives", "unknown_semantic_contexts"):
                _strings(row[key], key)
            if isinstance(row["notes"], str):
                _text(row["notes"], "notes")
            else:
                _strings(row["notes"], "notes", nonempty=True)
        if len(set(identifiers)) != len(identifiers):
            _fail("capability_id", "duplicate capability")


@dataclass(frozen=True)
class RealRulesExecutionProfileDesign(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-real-execution-profile-design-v1"
    ID_FIELD: ClassVar[str] = "execution_profile_design_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "game_id", "design_version", "target_profile_id", "target_label", "engine_compatibility_target",
        "source_binding", "foundational_projection_id", "foundational_package_id",
        "required_projection_review_id", "required_execution_approval_review_id", "required_rule_set_id",
        "capability_matrix_id", "capability_coverage", "required_dependency_closure",
        "required_exception_closure", "required_semantic_primitives", "unsupported_capabilities",
        "unknown_capabilities", "activation_requirements", "source_evidence_requirements",
        "projection_approval_requirements", "future_snapshot_design", "proof_trace_design",
        "release_update_policy", "epistemic_policy", "status", "limitations",
    })

    @classmethod
    def _validate(cls, body: dict[str, Any]) -> None:
        super()._validate(body)
        _version(body["design_version"], "design_version")
        for key, expected in (
            ("target_profile_id", "magic-comprehensive-rules-20260925-v1"),
            ("target_label", "DESIGN_TARGET_NOT_EXECUTABLE"),
            ("foundational_projection_id", PROJECTION_ID),
            ("foundational_package_id", PROJECTION_PACKAGE_ID),
            ("required_execution_approval_review_id", None),
            ("status", "DESIGN_ONLY"),
        ):
            _exact(body[key], expected, key)
        _source_binding(body["source_binding"])
        for key in ("required_projection_review_id", "required_rule_set_id", "capability_matrix_id"):
            _hash(body[key], key)
        for key in ("capability_coverage", "required_dependency_closure",
                    "required_exception_closure", "activation_requirements", "source_evidence_requirements",
                    "projection_approval_requirements", "future_snapshot_design", "proof_trace_design",
                    "release_update_policy", "epistemic_policy"):
            _document(body[key], key)
        for key in ("required_semantic_primitives", "unsupported_capabilities", "unknown_capabilities", "limitations"):
            _strings(body[key], key, nonempty=True)
        _exact(body["engine_compatibility_target"], {
            "observed_engine_contract": "gameplay-kernel-v1",
            "observed_execution_profile": "fictional-two-player-v1",
            "target_engine_contract": "gameplay-real-rules-kernel-v1",
            "target_implementation_status": "NOT_IMPLEMENTED",
            "compatible_with_current_runtime": False,
        }, "engine_compatibility_target")
        from .scope import ACTIVATION_REQUIREMENTS
        _exact(body["activation_requirements"], ACTIVATION_REQUIREMENTS, "activation_requirements")
        coverage = body["capability_coverage"]
        _keys(coverage, {
            "available_execution_capabilities", "descriptive_state_model_candidates",
            "blocked_capabilities", "reference_only", "none_is_activated",
        }, "capability_coverage")
        _exact(coverage["available_execution_capabilities"], [], "capability_coverage.available_execution_capabilities")
        _exact(coverage["none_is_activated"], True, "capability_coverage.none_is_activated")
        _exact(coverage["reference_only"], ["source_authority"], "capability_coverage.reference_only")
        for key in ("descriptive_state_model_candidates", "blocked_capabilities"):
            _strings(coverage[key], "capability_coverage." + key)
        if set(coverage["descriptive_state_model_candidates"]) & set(coverage["blocked_capabilities"]):
            _fail("capability_coverage", "candidate and blocked categories must be distinct")

        _exact(body["source_evidence_requirements"], {
            "exact_artifact": dict(SOURCE_BINDING),
            "retained_metadata_lineage_verified": True,
            "source_anchor_evidence": "RETAINED_VERIFIED_SOURCE_ANCHORS_NO_FRESH_SOURCE_ACCESS_CLAIM",
            "offline_design_reproducible": True,
            "external_txt_required_for_design": False,
            "future_activation_requires_bound_anchor_verification_evidence": True,
            "broader_source_content_permissions": "NOT_ESTABLISHED",
        }, "source_evidence_requirements")
        _exact(body["projection_approval_requirements"], {
            "design_review_id": body["required_projection_review_id"],
            "design_review_status": "REVIEWED_FOR_EXECUTION_DESIGN",
            "separate_execution_approval_required": True,
            "execution_approval": "NOT_GRANTED",
            "explicit_owner_activation_required": True,
            "projection_presence_is_not_execution_approval": True,
        }, "projection_approval_requirements")

        snapshot = body["future_snapshot_design"]
        _keys(snapshot, {
            "proposed_schema", "status", "snapshot_instantiated", "required_bindings", "loader_policy",
            "primitive_mapping_policy", "capability_policy", "exception_policy", "replay_policy",
        }, "future_snapshot_design")
        for key, expected in (("proposed_schema", "gameplay-real-rules-snapshot-v1"),
                              ("status", "DESIGN_ONLY"), ("snapshot_instantiated", False)):
            _exact(snapshot[key], expected, "future_snapshot_design." + key)
        _strings(snapshot["required_bindings"], "future_snapshot_design.required_bindings", nonempty=True)
        for key in ("loader_policy", "primitive_mapping_policy", "capability_policy", "exception_policy", "replay_policy"):
            _text(snapshot[key], "future_snapshot_design." + key)

        trace = body["proof_trace_design"]
        _keys(trace, {
            "status", "result_instantiated", "chain", "source_artifact_hash", "projection_id",
            "projection_review_id", "required_rule_set_id", "anchor_binding", "unsupported_policy",
        }, "proof_trace_design")
        for key, expected in (
            ("status", "DESIGN_ONLY"), ("result_instantiated", False),
            ("source_artifact_hash", SOURCE_BINDING["artifact_hash"]),
            ("projection_id", PROJECTION_ID),
            ("projection_review_id", body["required_projection_review_id"]),
            ("required_rule_set_id", body["required_rule_set_id"]),
            ("anchor_binding", "EXACT_RETAINED_SOURCE_ANCHORS"),
            ("unsupported_policy", "INDETERMINATE_OR_UNSUPPORTED"),
        ):
            _exact(trace[key], expected, "proof_trace_design." + key)
        _strings(trace["chain"], "proof_trace_design.chain", nonempty=True)

        release = body["release_update_policy"]
        _keys(release, {
            "implicit_latest_allowed", "mutation_allowed", "new_release_requires", "old_replays",
            "cross_profile_fallback",
        }, "release_update_policy")
        for key in ("implicit_latest_allowed", "mutation_allowed", "cross_profile_fallback"):
            _false(release[key], "release_update_policy." + key)
        _exact(release["old_replays"], "PINNED_IMMUTABLE_IDENTITIES", "release_update_policy.old_replays")
        _strings(release["new_release_requires"], "release_update_policy.new_release_requires", nonempty=True)
        _exact(body["epistemic_policy"], {
            "unresolved_or_unmodeled_result": "INDETERMINATE_OR_UNSUPPORTED",
            "definitive_legality_without_closure": False,
        }, "epistemic_policy")


@dataclass(frozen=True)
class RealRulesActivationGateDesign(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-real-activation-gate-design-v1"
    ID_FIELD: ClassVar[str] = "activation_gate_design_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "game_id", "gate_version", "profile_design_id", "projection_review_id", "required_rule_set_id",
        "requirements", "current_evidence", "assessment", "structural_proof_policy", "limitations",
    })

    @classmethod
    def _validate(cls, body: dict[str, Any]) -> None:
        super()._validate(body)
        _version(body["gate_version"], "gate_version")
        for key in ("profile_design_id", "projection_review_id", "required_rule_set_id"):
            _hash(body[key], key)
        # Import here keeps the immutable contract independent of builder imports.
        from .scope import ACTIVATION_REQUIREMENTS
        _exact(body["requirements"], ACTIVATION_REQUIREMENTS, "requirements")
        _keys(body["current_evidence"], ACTIVATION_REQUIREMENTS, "current_evidence")
        for value in body["current_evidence"].values():
            if type(value) is not bool:
                _fail("current_evidence", "boolean requirement evidence required")
        _false(body["current_evidence"]["explicit_owner_activation"], "current_evidence.explicit_owner_activation")
        _document(body["structural_proof_policy"], "structural_proof_policy")
        _strings(body["limitations"], "limitations", nonempty=True)
        assessment = body["assessment"]
        _keys(assessment, {
            "activation_denied", "status", "requirements_satisfied", "blockers", "failed_requirements",
        }, "assessment")
        for key, expected in (("activation_denied", True), ("status", "DENIED_DESIGN_ONLY"),
                              ("requirements_satisfied", False)):
            if key not in assessment:
                _fail("assessment", "missing negative activation boundary")
            _exact(assessment[key], expected, "assessment." + key)
        _strings(assessment.get("blockers"), "assessment.blockers", nonempty=True)
        _strings(assessment["failed_requirements"], "assessment.failed_requirements", nonempty=True)
        failed = [key for key in ACTIVATION_REQUIREMENTS if not body["current_evidence"][key]]
        _exact(assessment["failed_requirements"], failed, "assessment.failed_requirements")


@dataclass(frozen=True)
class RealRulesExecutionReadiness(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-real-execution-readiness-v1"
    ID_FIELD: ClassVar[str] = "execution_readiness_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "game_id", "assessment_version", "projection_review_id", "profile_design_id", "capability_matrix_id",
        "activation_gate_design_id", "overall_execution_readiness", "readiness_code", "per_rule_states",
        "unresolved_dependencies", "unprojected_exceptions", "unknown_semantic_contexts", "blockers",
        "next_milestone", "limitations",
    })

    @classmethod
    def _validate(cls, body: dict[str, Any]) -> None:
        super()._validate(body)
        _version(body["assessment_version"], "assessment_version")
        for key in ("projection_review_id", "profile_design_id", "capability_matrix_id", "activation_gate_design_id"):
            _hash(body[key], key)
        _exact(body["overall_execution_readiness"], "BLOCKED", "overall_execution_readiness")
        _exact(body["readiness_code"], "REAL_EXECUTION_PROFILE_NOT_READY", "readiness_code")
        for key in ("unresolved_dependencies", "unprojected_exceptions"):
            _references(body[key], key)
        for key in ("unknown_semantic_contexts", "blockers", "limitations"):
            _strings(body[key], key, nonempty=True)
        states = body["per_rule_states"]
        if isinstance(states, dict):
            _keys(states, SELECTED_REFERENCES, "per_rule_states")
            for state in states.values():
                _enum(state, _READINESS, "per_rule_states")
        elif isinstance(states, list) and len(states) == len(SELECTED_REFERENCES):
            for row, reference in zip(states, SELECTED_REFERENCES):
                _keys(row, {"rule_reference", "execution_readiness"}, "per_rule_states")
                _exact(row["rule_reference"], reference, "per_rule_states.rule_reference")
                _enum(row["execution_readiness"], _READINESS, "per_rule_states.execution_readiness")
        else:
            _fail("per_rule_states", "exactly 20 rule states required")
        milestone = body["next_milestone"]
        if not isinstance(milestone, dict) or "authorized" not in milestone:
            _fail("next_milestone", "explicit unauthorized recommendation required")
        _false(milestone["authorized"], "next_milestone.authorized")
