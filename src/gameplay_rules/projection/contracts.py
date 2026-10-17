"""Immutable review contracts for the authorized foundational CR projection.

This envelope contains project-authored descriptions and source-span metadata.
It is never an executable rules snapshot, an execution profile, or admitted
gameplay evidence. Offline validation checks the retained metadata and content
identity; binding a span to actual source bytes requires the source verifier.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from types import MappingProxyType
from typing import Any, ClassVar, Mapping

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError

from .scope import GRAPH_EDGES, GRAPH_NODES, RULE_CONTENT, SELECTED_REFERENCES, UNSUPPORTED_DIMENSIONS


ARTIFACT_HASH = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
ARTIFACT_BYTE_LENGTH = 977752
EFFECTIVE_DATE = "2026-09-25"
VERIFICATION_RESULT_ID = "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3"
CORRESPONDENCE_REVIEW_ID = "sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def"
ARTIFACT_REVIEW_PACKAGE_ID = "sha256:b5ad8b6f59c0311a33726e1733dc9bb239804bd0ab387ed789caf0d870aba36a"
SELECTION_ID = "sha256:5f22a1aa78b5fd2ec5a0ae7d942d6065a8b065a5cc4ee79db300514a5ebe5f63"

_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_BODY_FIELDS = frozenset({
    "game_id", "projection_kind", "status", "selected_rule_count", "source_binding",
    "authorization", "rules", "graph", "unsupported_dimensions", "boundary_flags",
})
_AUTHORIZATION = {
    "scope": "Core Comprehensive Rules Projection — Foundational Rules Subset",
    "basis": "OWNER_EXPLICIT_TASK_AUTHORIZATION",
    "authorized_on": "2026-10-17",
    "source_policy_clearance": "not_granted",
}
_BOUNDARY_FLAGS = {
    "non_executable": True,
    "real_rules_executable": False,
    "admission_eligible": False,
    "source_body_retained": False,
    "oracle_ingested": False,
    "source_policy_clearance": "not_granted",
}


def _fail(field: str, message: str = "invalid projection contract") -> None:
    raise GameplayContractError("foundational_projection_contract", f"{field}: {message}")


def _json(value: Any) -> Any:
    """Copy JSON-compatible values without retaining caller-owned containers."""
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            _fail("JSON", "string keys required")
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    _fail("JSON", "unsupported or non-finite value")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _keys(value: Any, expected: Any, field: str) -> None:
    if not isinstance(value, dict) or set(value) != set(expected):
        _fail(field, "missing or unexpected fields")


def _exact(value: Any, expected: Any, field: str) -> None:
    # Canonical JSON comparison preserves distinctions such as true versus 1.
    if deterministic_json(value) != deterministic_json(_json(expected)):
        _fail(field, "outside the fixed authorized projection scope")


def _hash(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        _fail(field, "SHA-256 content identity required")


def _integer(value: Any, field: str, *, minimum: int = 0, maximum: int | None = None) -> None:
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        _fail(field, "integer outside the permitted source bounds")


def _validate(body: dict[str, Any]) -> None:
    _keys(body, _BODY_FIELDS, "projection")
    for field, expected in (
        ("game_id", "magic"),
        ("projection_kind", "NON_EXECUTABLE"),
        ("status", "IMPLEMENTED_PENDING_REVIEW"),
        ("selected_rule_count", 20),
    ):
        _exact(body[field], expected, field)

    binding = body["source_binding"]
    _keys(binding, {
        "artifact_hash", "byte_length", "effective_date", "verification_result_id",
        "correspondence_review_id", "artifact_review_package_id", "selection_id",
    }, "source_binding")
    for field, expected in (
        ("artifact_hash", ARTIFACT_HASH),
        ("byte_length", ARTIFACT_BYTE_LENGTH),
        ("effective_date", EFFECTIVE_DATE),
        ("verification_result_id", VERIFICATION_RESULT_ID),
        ("correspondence_review_id", CORRESPONDENCE_REVIEW_ID),
        ("artifact_review_package_id", ARTIFACT_REVIEW_PACKAGE_ID),
        ("selection_id", SELECTION_ID),
    ):
        _exact(binding[field], expected, "source_binding." + field)

    _exact(body["authorization"], _AUTHORIZATION, "authorization")
    _exact(body["boundary_flags"], _BOUNDARY_FLAGS, "boundary_flags")
    _exact(body["unsupported_dimensions"], UNSUPPORTED_DIMENSIONS, "unsupported_dimensions")
    _exact(body["graph"], {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES}, "graph")

    rules = body["rules"]
    if not isinstance(rules, list) or len(rules) != 20:
        _fail("rules", "exactly 20 authorized rule entries required")
    prior_end = 0
    prior_line = 0
    for rule, reference in zip(rules, SELECTED_REFERENCES):
        _keys(rule, {
            "rule_reference", "topic", "paraphrase", "limitations", "concept_tags", "source_anchor",
        }, "rule")
        _exact(rule["rule_reference"], reference, "rule.rule_reference")
        for field in ("topic", "paraphrase", "limitations", "concept_tags"):
            _exact(rule[field], RULE_CONTENT[reference][field], "rule." + field)

        anchor = rule["source_anchor"]
        _keys(anchor, {
            "rule_reference", "artifact_hash", "byte_start", "byte_end", "line_number",
            "span_sha256", "span_policy",
        }, "source_anchor")
        _exact(anchor["rule_reference"], reference, "source_anchor.rule_reference")
        _exact(anchor["artifact_hash"], ARTIFACT_HASH, "source_anchor.artifact_hash")
        _exact(anchor["span_policy"], "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR", "source_anchor.span_policy")
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


def _duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("JSON", "duplicate projection key")
        result[key] = value
    return result


def _nonfinite(_value: str) -> None:
    _fail("JSON", "non-finite projection number")


@dataclass(frozen=True)
class FoundationalProjection(Contract):
    """A fixed, non-executable projection with immutable nested payload values.

    ``verify`` validates the envelope and its domain-separated content identity.
    It does not establish source-span correspondence without source-byte access.
    """

    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str] = "gameplay-cr-foundational-projection-v1"
    ID_FIELD: ClassVar[str] = "projection_id"

    def __post_init__(self) -> None:
        try:
            value = _json(self._payload)
            _keys(value, _BODY_FIELDS | {"schema_version", self.ID_FIELD}, "envelope")
            _exact(value["schema_version"], self.SCHEMA, "schema_version")
            _hash(value[self.ID_FIELD], self.ID_FIELD)
            body = {key: item for key, item in value.items() if key not in {"schema_version", self.ID_FIELD}}
            _validate(body)
            content = {key: item for key, item in value.items() if key != self.ID_FIELD}
            expected = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": content})
            if value[self.ID_FIELD] != expected:
                _fail(self.ID_FIELD, "projection content identity mismatch")
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("envelope", "malformed projection contract")

    @classmethod
    def create(cls, body: Mapping[str, Any]) -> FoundationalProjection:
        try:
            value = _json(body)
            _keys(value, _BODY_FIELDS, "create")
            _validate(value)
            value["schema_version"] = cls.SCHEMA
            value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
            return cls(value)
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("create", "malformed projection body")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> FoundationalProjection:
        return cls(value)

    @classmethod
    def from_json(cls, value: bytes | str) -> FoundationalProjection:
        try:
            if not isinstance(value, (bytes, str)):
                _fail("JSON", "UTF-8 bytes or text required")
            return cls.from_dict(json.loads(value, object_pairs_hook=_duplicate_keys, parse_constant=_nonfinite))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            _fail("JSON", "malformed projection JSON")

    @property
    def identity(self) -> str:
        return self._payload[self.ID_FIELD]

    def to_dict(self) -> dict[str, Any]:
        return _json(self._payload)

    def serialize(self) -> str:
        return deterministic_json(self.to_dict())

    def verify(self) -> FoundationalProjection:
        type(self).from_dict(self.to_dict())
        return self

    def __getattr__(self, name: str) -> Any:
        payload = object.__getattribute__(self, "_payload")
        if name in payload:
            return payload[name]
        raise AttributeError(name)
