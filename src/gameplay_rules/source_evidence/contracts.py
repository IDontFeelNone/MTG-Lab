"""Immutable, metadata-only Gameplay Rules source/version review contracts.

These are discovery/review records, never admitted evidence or executable rules.
Unknown licensing is retained truthfully without bypassing the existing evidence
registry's supported-licensing requirement. No source body is a contract field.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
import math
import re
from types import MappingProxyType
from typing import Any, ClassVar, Mapping
from urllib.parse import urlsplit

from evidence.contracts import Contract, deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError


PERMISSION_OPERATIONS = (
    "discovery_metadata_processing", "transient_inspection", "private_raw_retention",
    "public_metadata_retention", "public_source_content_redistribution", "free_service_use",
    "commercial_service_use", "ai_model_export",
)
PERMISSION_STATES = frozenset({"ESTABLISHED", "ESTABLISHED_WITH_CONDITIONS", "NOT_ESTABLISHED",
                              "NOT_APPLICABLE", "EVIDENCE_UNAVAILABLE", "NEEDS_REVIEW"})
EVIDENCE_STATES = frozenset({"VERIFIED_ARTIFACT", "VERIFIED_METADATA_ONLY", "DISCOVERED_UNVERIFIED",
                           "EVIDENCE_UNAVAILABLE", "AMBIGUOUS", "SUPERSEDED", "CONFLICTING"})
SOURCE_CLASSES = frozenset({"RULES_INDEX", "COMPREHENSIVE_RULES", "UPDATE_BULLETIN", "RELEASE_NOTES",
                          "RULES_BLOG", "ORACLE", "FORMAT_POLICY", "PROJECT_AUTHORED_FICTIONAL"})
AUTHORITY_RANKS = {
    "RULES_INDEX": "INDEX", "COMPREHENSIVE_RULES": "PRIMARY",
    "UPDATE_BULLETIN": "SECONDARY", "RELEASE_NOTES": "SECONDARY",
    "RULES_BLOG": "EXPLANATORY", "ORACLE": "SEPARATE_FUTURE",
    "FORMAT_POLICY": "SEPARATE_FUTURE", "PROJECT_AUTHORED_FICTIONAL": "FICTIONAL",
}
ACCESS_OUTCOMES = frozenset({"AVAILABLE", "ACCESS_UNAVAILABLE", "HTTP_403", "HTTP_404", "TIMEOUT",
                            "REDIRECT_BLOCKED", "CONTENT_TYPE_UNSUPPORTED", "ARTIFACT_TOO_LARGE",
                            "PARSE_METADATA_FAILED", "NOT_ATTEMPTED"})
RELATIONS = frozenset({"DESIGNATES", "SUPERSEDES", "SUMMARIZES", "EXPLAINS", "CONFLICTS_WITH",
                      "ANNOUNCES_RULE_CHANGE", "DESCRIBES_CHANGES_FOR", "EXPECTED_TO_BE_INCORPORATED_IN"})
CLAIMS = frozenset({"artifact_identity", "version", "effective_date", "current_designation",
                   "supersession", "as_of_scope", "release_scope"})
FLAGS = {"metadata_only": True, "admission_eligible": False, "projection_authorized": False}
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _fail(field, message="invalid metadata contract"):
    raise GameplayContractError("source_evidence_contract", f"{field}: {message}")


def _json(value):
    if isinstance(value, MetadataContract): return value.to_dict()
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value): _fail("JSON", "string keys required")
        return {key: _json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [_json(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)): return value
    if isinstance(value, float) and math.isfinite(value): return value
    _fail("JSON", "unsupported or non-finite value")


def _freeze(value):
    if isinstance(value, dict): return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list): return tuple(_freeze(item) for item in value)
    return value


def _keys(value, expected, field):
    if not isinstance(value, dict) or set(value) != set(expected): _fail(field, "missing or unexpected fields")


def _text(value, field, *, nullable=False):
    if nullable and value is None: return
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        _fail(field, "bounded nonempty string required")


def _hash(value, field, *, nullable=False):
    if nullable and value is None: return
    if not isinstance(value, str) or not _HASH.fullmatch(value): _fail(field, "SHA-256 content identity required")


def _enum(value, expected, field):
    if not isinstance(value, str) or value not in expected: _fail(field, "unsupported metadata value")


def _int(value, field, *, nullable=False, maximum=None):
    if nullable and value is None: return
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum): _fail(field, "nonnegative integer required")


def _date(value, field, *, nullable=False):
    if nullable and value is None: return
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value: _fail(field, "ISO date required")
    except ValueError: _fail(field, "ISO date required")


def _timestamp(value, field, *, nullable=False):
    if nullable and value is None: return
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None: _fail(field, "timezone required")
    except (ValueError, TypeError, AttributeError): _fail(field, "ISO timestamp required")


def _version(value, field, *, nullable=False):
    if nullable and value is None: return
    _text(value, field)
    if value.strip().lower() in {"latest", "current", "unknown"}: _fail(field, "explicit source-provided version or null required")


def _strings(value, field, *, identities=False):
    if not isinstance(value, list): _fail(field, "array required")
    for item in value: (_hash if identities else _text)(item, field)
    if len(set(value)) != len(value): _fail(field, "duplicate entries")


def _reference(value, field, *, nullable=False):
    if nullable and value is None: return
    _text(value, field)
    if "\\" in value or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value):
        _fail(field, "ambiguous public source reference")
    try:
        parsed = urlsplit(value)
        if parsed.query or parsed.fragment: _fail(field, "query and fragment material forbidden in source reference")
        if parsed.scheme == "urn": return
        if parsed.scheme != "https" or not parsed.netloc or parsed.username is not None or parsed.password is not None:
            _fail(field, "public HTTPS or fictional URN reference required")
        if any(word in parsed.query.lower() for word in ("token=", "secret=", "password=", "authorization=")):
            _fail(field, "credential-bearing reference forbidden")
    except ValueError: _fail(field, "invalid public source reference")


def _permissions(value):
    _keys(value, PERMISSION_OPERATIONS, "permission_status")
    for operation, entry in value.items():
        _keys(entry, {"status", "evidence_references", "conditions"}, "permission_status." + operation)
        _enum(entry["status"], PERMISSION_STATES, "permission_status.status")
        _strings(entry["evidence_references"], "permission_status.evidence_references")
        _strings(entry["conditions"], "permission_status.conditions")
        if entry["status"] in {"ESTABLISHED", "ESTABLISHED_WITH_CONDITIONS"} and not entry["evidence_references"]:
            _fail("permission_status", "established status requires explicit evidence references")
        if entry["status"] == "ESTABLISHED_WITH_CONDITIONS" and not entry["conditions"]:
            _fail("permission_status", "conditional status requires explicit conditions")


def _source(body):
    fields = {"source_id", "game_id", "source_class", "issuer", "title", "authoritative_reference", "resolved_reference",
              "discovered_at", "observed_at", "accessibility", "access_outcome", "http_status", "media_type",
              "effective_date", "rules_version", "artifact_hash", "byte_length", "supersedes", "superseded_by",
              "authority_rank", "provenance", "permission_status", "retention_status", "completeness", "review_status",
              "evidence_status"}
    _keys(body, fields, "source_reference")
    for name in ("source_id", "game_id", "issuer", "title"): _text(body[name], name)
    _enum(body["source_class"], SOURCE_CLASSES, "source_class")
    if body["authority_rank"] != AUTHORITY_RANKS[body["source_class"]]: _fail("authority_rank", "source-class authority mismatch")
    _reference(body["authoritative_reference"], "authoritative_reference")
    _reference(body["resolved_reference"], "resolved_reference", nullable=True)
    _timestamp(body["discovered_at"], "discovered_at")
    _timestamp(body["observed_at"], "observed_at", nullable=True)
    _enum(body["accessibility"], {"AVAILABLE", "UNAVAILABLE", "NOT_ATTEMPTED", "UNKNOWN"}, "accessibility")
    _enum(body["access_outcome"], ACCESS_OUTCOMES, "access_outcome")
    _int(body["http_status"], "http_status", nullable=True, maximum=599)
    if body["http_status"] is not None and body["http_status"] < 100: _fail("http_status", "invalid HTTP status")
    _text(body["media_type"], "media_type", nullable=True)
    _date(body["effective_date"], "effective_date", nullable=True)
    _version(body["rules_version"], "rules_version", nullable=True)
    _hash(body["artifact_hash"], "artifact_hash", nullable=True)
    _int(body["byte_length"], "byte_length", nullable=True)
    if (body["artifact_hash"] is None) != (body["byte_length"] is None): _fail("artifact_hash", "hash and byte count must be bound together")
    for name in ("supersedes", "superseded_by"): _strings(body[name], name, identities=True)
    _strings(body["provenance"], "provenance")
    _permissions(body["permission_status"])
    _enum(body["retention_status"], {"METADATA_ONLY", "REFERENCE_ONLY", "NOT_RETAINED"}, "retention_status")
    _enum(body["completeness"], {"COMPLETE", "PARTIAL", "UNKNOWN"}, "completeness")
    _enum(body["review_status"], {"PENDING", "REVIEWED"}, "review_status")
    _enum(body["evidence_status"], EVIDENCE_STATES, "evidence_status")
    if body["accessibility"] == "AVAILABLE" and body["http_status"] not in {None, 200}:
        _fail("http_status", "failed HTTP status cannot establish available source evidence")
    if body["access_outcome"] == "AVAILABLE" and body["accessibility"] != "AVAILABLE": _fail("accessibility", "access outcome contradiction")
    if body["access_outcome"] in {"HTTP_403", "HTTP_404", "TIMEOUT", "ACCESS_UNAVAILABLE", "REDIRECT_BLOCKED"} and body["accessibility"] != "UNAVAILABLE":
        _fail("accessibility", "unavailable access cannot be available")
    if body["access_outcome"] in {"HTTP_403", "HTTP_404"} and body["http_status"] != int(body["access_outcome"].split("_")[1]): _fail("http_status", "access outcome contradiction")
    if body["evidence_status"] == "VERIFIED_ARTIFACT" and (body["accessibility"] != "AVAILABLE" or body["access_outcome"] != "AVAILABLE" or body["observed_at"] is None or body["artifact_hash"] is None):
        _fail("evidence_status", "verified artifact requires successful observed bytes and exact hash/length")
    if body["evidence_status"] == "VERIFIED_METADATA_ONLY" and (body["accessibility"] != "AVAILABLE" or body["access_outcome"] != "AVAILABLE" or body["observed_at"] is None):
        _fail("evidence_status", "verified metadata requires a successful observation")
    if body["evidence_status"] == "EVIDENCE_UNAVAILABLE" and body["accessibility"] == "AVAILABLE": _fail("evidence_status", "unavailable evidence cannot be verified available")


def _candidate(body):
    _keys(body, {"game_id", "release_id", "artifact_source_reference_id", "rules_version", "effective_date",
                 "artifact_hash", "byte_length", "evidence_status", "completeness", "supersedes", "unresolved_questions"}, "release_candidate")
    for name in ("game_id", "release_id"): _text(body[name], name)
    _hash(body["artifact_source_reference_id"], "artifact_source_reference_id")
    _version(body["rules_version"], "rules_version", nullable=True)
    _date(body["effective_date"], "effective_date", nullable=True)
    _hash(body["artifact_hash"], "artifact_hash", nullable=True)
    _int(body["byte_length"], "byte_length", nullable=True)
    if (body["artifact_hash"] is None) != (body["byte_length"] is None): _fail("artifact_hash", "hash and byte count must be bound together")
    _enum(body["evidence_status"], EVIDENCE_STATES, "evidence_status")
    _enum(body["completeness"], {"COMPLETE", "PARTIAL", "UNKNOWN"}, "completeness")
    _strings(body["supersedes"], "supersedes", identities=True)
    _strings(body["unresolved_questions"], "unresolved_questions")
    if body["evidence_status"] == "VERIFIED_ARTIFACT" and body["artifact_hash"] is None: _fail("evidence_status", "artifact bytes not verified")


def _review(body):
    _keys(body, {"game_id", "source_reference_ids", "release_candidate_ids", "reviewer", "reviewed_at", "status", "supported_claims", "limitations"}, "source_review")
    _text(body["game_id"], "game_id")
    for name in ("source_reference_ids", "release_candidate_ids"): _strings(body[name], name, identities=True)
    _text(body["reviewer"], "reviewer", nullable=True)
    _timestamp(body["reviewed_at"], "reviewed_at", nullable=True)
    _enum(body["status"], {"PENDING", "REVIEWED"}, "status")
    if body["status"] == "REVIEWED" and (body["reviewer"] is None or body["reviewed_at"] is None): _fail("status", "reviewed annotation requires reviewer and retained timestamp")
    _strings(body["limitations"], "limitations")
    if not isinstance(body["supported_claims"], list): _fail("supported_claims", "array required")
    seen = []
    for claim in body["supported_claims"]:
        _keys(claim, {"claim", "release_candidate_id", "source_reference_ids", "value"}, "supported_claim")
        _enum(claim["claim"], CLAIMS, "claim")
        _hash(claim["release_candidate_id"], "release_candidate_id")
        if claim["release_candidate_id"] not in body["release_candidate_ids"]: _fail("supported_claim", "unbound review candidate")
        _strings(claim["source_reference_ids"], "claim.source_reference_ids", identities=True)
        if not claim["source_reference_ids"] or not set(claim["source_reference_ids"]) <= set(body["source_reference_ids"]): _fail("supported_claim", "unbound review evidence")
        kind, value = claim["claim"], claim["value"]
        if kind == "artifact_identity": _hash(value, "claim.value")
        elif kind == "version": _version(value, "claim.value")
        elif kind in {"effective_date", "current_designation"}: _date(value, "claim.value")
        elif kind == "supersession": _strings(value, "claim.value", identities=True)
        elif kind == "as_of_scope":
            _keys(value, {"valid_from", "valid_until"}, "claim.value")
            _date(value["valid_from"], "claim.valid_from")
            _date(value["valid_until"], "claim.valid_until", nullable=True)
            if value["valid_until"] is not None and value["valid_until"] < value["valid_from"]: _fail("as_of_scope", "reversed date range")
        else: _text(value, "claim.value")
        seen.append((kind, claim["release_candidate_id"]))
    if len(set(seen)) != len(seen): _fail("supported_claims", "duplicate candidate claim")


def _index(body):
    _keys(body, {"game_id", "source_references", "release_candidates", "reviews", "relations"}, "evidence_index")
    _text(body["game_id"], "game_id")
    collections = {}
    for name, model in (("source_references", SourceReference), ("release_candidates", ReleaseCandidate), ("reviews", SourceReview)):
        if not isinstance(body[name], list): _fail(name, "array required")
        records = [model.from_dict(value) for value in body[name]]
        if any(record.game_id != body["game_id"] for record in records): _fail(name, "game mismatch")
        if len({record.identity for record in records}) != len(records): _fail(name, "duplicate content identity")
        collections[name] = {record.identity: record.to_dict() for record in records}
    sources, candidates, reviews = (collections[name] for name in ("source_references", "release_candidates", "reviews"))
    for source in sources.values():
        if not (set(source["supersedes"]) | set(source["superseded_by"])) <= set(sources): _fail("source_references", "missing supersession reference")
        if source["source_reference_id"] in source["supersedes"] + source["superseded_by"]: _fail("source_references", "self supersession")
    for candidate in candidates.values():
        source = sources.get(candidate["artifact_source_reference_id"])
        if source is None: _fail("release_candidates", "missing artifact source reference")
        if source["source_class"] not in {"COMPREHENSIVE_RULES", "PROJECT_AUTHORED_FICTIONAL"}: _fail("release_candidates", "secondary document is not a comprehensive-rules release")
        for name in ("artifact_hash", "byte_length", "rules_version", "effective_date"):
            if candidate[name] != source[name]: _fail("release_candidates", "artifact source correspondence mismatch")
        if candidate["evidence_status"] == "VERIFIED_ARTIFACT" and source["evidence_status"] != "VERIFIED_ARTIFACT": _fail("release_candidates", "artifact verification cannot inherit metadata-only evidence")
        if not set(candidate["supersedes"]) <= set(candidates) or candidate["release_candidate_id"] in candidate["supersedes"]: _fail("release_candidates", "unbound or self supersession")
    for review in reviews.values():
        if not set(review["source_reference_ids"]) <= set(sources) or not set(review["release_candidate_ids"]) <= set(candidates): _fail("reviews", "review dependency closure incomplete")
        for claim in review["supported_claims"]:
            candidate = candidates[claim["release_candidate_id"]]
            field = {"artifact_identity": "artifact_hash", "version": "rules_version", "effective_date": "effective_date"}.get(claim["claim"])
            if field and claim["value"] != candidate[field]: _fail("supported_claim", "candidate fact correspondence mismatch")
            if claim["claim"] == "supersession" and not set(claim["value"]) <= set(candidates): _fail("supported_claim", "missing supersession candidate")
    if not isinstance(body["relations"], list): _fail("relations", "array required")
    seen = []
    for edge in body["relations"]:
        _keys(edge, {"relation", "from_reference_id", "to_reference_id", "evidence_reference_ids"}, "relation")
        _enum(edge["relation"], RELATIONS, "relation.kind")
        for name in ("from_reference_id", "to_reference_id"):
            _hash(edge[name], name)
            if edge[name] not in sources: _fail("relation", "unbound source endpoint")
        _strings(edge["evidence_reference_ids"], "evidence_reference_ids", identities=True)
        if not edge["evidence_reference_ids"] or not set(edge["evidence_reference_ids"]) <= set(sources): _fail("relation", "missing explicit relation evidence")
        seen.append((edge["relation"], edge["from_reference_id"], edge["to_reference_id"]))
    if len(set(seen)) != len(seen): _fail("relations", "duplicate relation")


def _selection(body):
    _keys(body, {"game_id", "evidence_index_id", "scope", "as_of_date", "release_id", "selected_release_candidate_id",
                 "source_review_id", "evidence_reference_ids", "lineage_candidate_ids", "status", "blocking_reasons"}, "version_selection")
    _text(body["game_id"], "game_id")
    _hash(body["evidence_index_id"], "evidence_index_id")
    _enum(body["scope"], {"current_designation", "as_of_date", "set_release"}, "scope")
    _date(body["as_of_date"], "as_of_date")
    _text(body["release_id"], "release_id", nullable=True)
    if body["scope"] == "set_release" and body["release_id"] is None: _fail("release_id", "explicit set/release key required")
    if body["scope"] != "set_release" and body["release_id"] is not None: _fail("release_id", "release key belongs to set-release scope")
    for name in ("selected_release_candidate_id", "source_review_id"): _hash(body[name], name, nullable=True)
    for name in ("evidence_reference_ids", "lineage_candidate_ids"): _strings(body[name], name, identities=True)
    _enum(body["status"], {"READY_FOR_RULE_PROJECTION", "NOT_READY_FOR_RULE_PROJECTION"}, "status")
    _strings(body["blocking_reasons"], "blocking_reasons")
    if body["status"] == "READY_FOR_RULE_PROJECTION":
        if body["blocking_reasons"] or body["selected_release_candidate_id"] is None or body["source_review_id"] is None or not body["evidence_reference_ids"] or not body["lineage_candidate_ids"]:
            _fail("status", "ready metadata requires explicit selected candidate, review, evidence and lineage without blockers")
    elif not body["blocking_reasons"]: _fail("blocking_reasons", "blocked review requires explicit reasons")


def _duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result: _fail("JSON", "duplicate metadata key")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("JSON", "non-finite metadata number")


@dataclass(frozen=True)
class MetadataContract(Contract):
    """Verified metadata envelope; full serialization hashes use evidence.Contract.

    ``identity`` is the domain-separated record ID. The inherited
    ``identity_sha256`` is the SHA-256 of its complete serialized envelope.
    Neither is permission, admission, projection or execution authorization.
    """
    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str]
    ID_FIELD: ClassVar[str]
    VALIDATOR: ClassVar[Any]

    def __post_init__(self):
        try:
            value = _json(self._payload)
            if not isinstance(value, dict): _fail("envelope", "object required")
            if value.get("schema_version") != self.SCHEMA: _fail("schema_version", "unsupported metadata contract version")
            supplied = value.get(self.ID_FIELD)
            _hash(supplied, self.ID_FIELD)
            for name, expected in FLAGS.items():
                if type(value.get(name)) is not bool or value[name] is not expected: _fail(name, "metadata-only non-admissible flags are fixed")
            body = {key: item for key, item in value.items() if key not in {"schema_version", self.ID_FIELD, *FLAGS}}
            self.VALIDATOR(body)
            hashed = {key: item for key, item in value.items() if key != self.ID_FIELD}
            expected_id = "sha256:" + sha256_identity({"domain": self.SCHEMA, "content": hashed})
            if supplied != expected_id: _fail(self.ID_FIELD, "metadata content identity mismatch")
            object.__setattr__(self, "_payload", _freeze(value))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError):
            _fail("envelope", "malformed metadata contract")

    @classmethod
    def create(cls, body):
        try:
            value = _json(body)
            if not isinstance(value, dict) or cls.ID_FIELD in value: _fail("create", "unbound metadata body required")
            if "schema_version" in value and value["schema_version"] != cls.SCHEMA: _fail("schema_version")
            value["schema_version"] = cls.SCHEMA
            for name, expected in FLAGS.items():
                if name in value and (type(value[name]) is not bool or value[name] is not expected): _fail(name, "fixed metadata authority boundary")
                value[name] = expected
            value[cls.ID_FIELD] = "sha256:" + sha256_identity({"domain": cls.SCHEMA, "content": value})
            return cls(value)
        except GameplayContractError:
            raise
        except (ValueError, TypeError, RecursionError):
            _fail("create", "malformed metadata body")

    @classmethod
    def from_dict(cls, value): return cls(value)

    @classmethod
    def from_json(cls, value):
        try:
            return cls.from_dict(json.loads(value, object_pairs_hook=_duplicate_keys, parse_constant=_nonfinite))
        except GameplayContractError:
            raise
        except (ValueError, TypeError, UnicodeError, RecursionError):
            _fail("JSON", "malformed metadata JSON")

    @property
    def identity(self): return self._payload[self.ID_FIELD]

    @property
    def identity_key(self): return self.ID_FIELD

    def to_dict(self): return _json(self._payload)

    def verify(self):
        type(self).from_dict(self.to_dict())
        return self

    def __getattr__(self, name):
        payload = object.__getattribute__(self, "_payload")
        if name in payload: return payload[name]
        raise AttributeError(name)


@dataclass(frozen=True)
class SourceReference(MetadataContract):
    SCHEMA = "gameplay-source-reference-v1"
    ID_FIELD = "source_reference_id"
    VALIDATOR = staticmethod(_source)


@dataclass(frozen=True)
class ReleaseCandidate(MetadataContract):
    SCHEMA = "gameplay-release-candidate-v1"
    ID_FIELD = "release_candidate_id"
    VALIDATOR = staticmethod(_candidate)


@dataclass(frozen=True)
class SourceReview(MetadataContract):
    SCHEMA = "gameplay-source-review-v1"
    ID_FIELD = "source_review_id"
    VALIDATOR = staticmethod(_review)


@dataclass(frozen=True)
class EvidenceIndex(MetadataContract):
    SCHEMA = "gameplay-evidence-index-v1"
    ID_FIELD = "evidence_index_id"
    VALIDATOR = staticmethod(_index)


@dataclass(frozen=True)
class VersionSelection(MetadataContract):
    SCHEMA = "gameplay-version-selection-v1"
    ID_FIELD = "version_selection_id"
    VALIDATOR = staticmethod(_selection)
