"""Reconcile supplied observations and offline byte evidence without a fetch.

This lane supplements the original network evidence index. It never changes an
unsuccessful network observation into a successful request. Readiness identifies
an exact artifact for a future review; it grants no projection or source rights.
"""
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from .contracts import (MetadataContract, SourceReference, _date, _enum, _fail,
                        _hash, _int, _keys, _strings, _text, _version)
from .observations import ExternalSourceObservation, verify_source_binding
from .review import verify_review_package


def _candidate(body):
    _keys(body, {"game_id", "discovery_source_reference_id", "observation_id",
        "source_class", "title", "artifact_family", "artifact_types",
        "artifact_reference", "artifact_filename", "effective_date", "rules_version",
        "artifact_hash", "byte_length", "evidence_status", "lineage_scope"}, "observed_release")
    _text(body["game_id"], "game_id")
    for name in ("discovery_source_reference_id", "observation_id"): _hash(body[name], name)
    if body["source_class"] != "COMPREHENSIVE_RULES": _fail("source_class")
    _text(body["title"], "title")
    _text(body["artifact_family"], "artifact_family")
    _strings(body["artifact_types"], "artifact_types")
    if not body["artifact_types"] or not set(body["artifact_types"]) <= {"TXT", "PDF", "DOCX"}:
        _fail("artifact_types")
    # This record captures a discovery, not a replacement for byte verification.
    for name in ("artifact_reference", "artifact_filename", "artifact_hash", "byte_length"):
        if body[name] is not None: _fail(name, "unresolved discovery metadata must remain null")
    _date(body["effective_date"], "effective_date")
    _version(body["rules_version"], "rules_version", nullable=True)
    if body["evidence_status"] != "VERIFIED_METADATA_ONLY": _fail("evidence_status")
    if body["lineage_scope"] != "CURRENT_DESIGNATION_ONLY_NO_HISTORICAL_INTERVAL_CLAIM":
        _fail("lineage_scope")


@dataclass(frozen=True)
class ObservedReleaseCandidate(MetadataContract):
    """A release observed via an index, without inventing an artifact locator."""
    SCHEMA = "gameplay-observed-release-candidate-v1"
    ID_FIELD = "release_candidate_id"
    VALIDATOR = staticmethod(_candidate)

    @classmethod
    def from_observation(cls, observation):
        if not isinstance(observation, ExternalSourceObservation): _fail("observation", "typed observation required")
        observation.verify()
        designation = observation.observed_designation
        return cls.create({"game_id": observation.game_id,
            "discovery_source_reference_id": observation.source_reference_id,
            "observation_id": observation.identity, "source_class": "COMPREHENSIVE_RULES",
            "title": designation["title"], "artifact_family": designation["filename_date_token"],
            "artifact_types": list(designation["artifact_types"]), "artifact_reference": None,
            "artifact_filename": None, "effective_date": observation.effective_date,
            "rules_version": observation.source_provided_version, "artifact_hash": None,
            "byte_length": None, "evidence_status": "VERIFIED_METADATA_ONLY",
            "lineage_scope": "CURRENT_DESIGNATION_ONLY_NO_HISTORICAL_INTERVAL_CLAIM"})


def _review(body):
    _keys(body, {"game_id", "previous_package_id", "source_reference_id", "observation_id",
        "release_candidate_id", "verification_request_id", "artifact_verification_id",
        "reviewed_on", "reviewer", "status", "supported_claims", "limitations"}, "discovery_review")
    for name in ("game_id", "reviewer"): _text(body[name], name)
    for name in ("previous_package_id", "source_reference_id", "observation_id",
                 "release_candidate_id", "verification_request_id"): _hash(body[name], name)
    _hash(body["artifact_verification_id"], "artifact_verification_id", nullable=True)
    _date(body["reviewed_on"], "reviewed_on")
    _enum(body["status"], {"PENDING", "REVIEWED"}, "status")
    _strings(body["supported_claims"], "supported_claims")
    if not set(body["supported_claims"]) <= {"official_designation", "effective_date",
            "currentness_as_of", "identified_update_incorporation", "local_artifact_identity",
            "local_artifact_source_correspondence"}:
        _fail("supported_claims")
    _strings(body["limitations"], "limitations")
    if not body["limitations"]: _fail("limitations")


@dataclass(frozen=True)
class DiscoverySourceReview(MetadataContract):
    SCHEMA = "gameplay-discovery-source-review-v1"
    ID_FIELD = "discovery_review_id"
    VALIDATOR = staticmethod(_review)


def _selection(body):
    _keys(body, {"game_id", "previous_package_id", "source_reference_id", "observation_id",
        "release_candidate_id", "verification_request_id", "discovery_review_id",
        "artifact_verification_id", "as_of_date", "effective_date", "currentness_status",
        "artifact_hash", "byte_length", "artifact_evidence_state", "status", "blocking_reasons",
        "codex_independently_fetched", "content_retained", "source_policy_clearance"}, "discovery_selection")
    _text(body["game_id"], "game_id")
    for name in ("previous_package_id", "source_reference_id", "observation_id", "release_candidate_id",
                 "verification_request_id", "discovery_review_id"): _hash(body[name], name)
    _hash(body["artifact_verification_id"], "artifact_verification_id", nullable=True)
    for name in ("as_of_date", "effective_date"): _date(body[name], name)
    _enum(body["currentness_status"], {"CURRENT_DESIGNATION_OBSERVED_AS_OF", "CURRENTNESS_SCOPE_NOT_OBSERVED"}, "currentness_status")
    _hash(body["artifact_hash"], "artifact_hash", nullable=True)
    _int(body["byte_length"], "byte_length", nullable=True)
    if (body["artifact_hash"] is None) != (body["byte_length"] is None): _fail("artifact_hash")
    _enum(body["artifact_evidence_state"], {"METADATA_ONLY", "ARTIFACT_BYTES_VERIFIED_LOCALLY"}, "artifact_evidence_state")
    _enum(body["status"], {"READY_FOR_RULE_PROJECTION", "NOT_READY_FOR_RULE_PROJECTION"}, "status")
    _strings(body["blocking_reasons"], "blocking_reasons")
    if (body["status"] == "READY_FOR_RULE_PROJECTION") != (not body["blocking_reasons"]): _fail("blocking_reasons")
    if body["status"] == "READY_FOR_RULE_PROJECTION" and (body["artifact_hash"] is None or not body["byte_length"] or body["artifact_verification_id"] is None or body["artifact_evidence_state"] != "ARTIFACT_BYTES_VERIFIED_LOCALLY"):
        _fail("status", "readiness requires exact local artifact evidence")
    if body["codex_independently_fetched"] is not False or body["content_retained"] is not False or body["source_policy_clearance"] != "not_granted":
        _fail("authority", "readiness cannot assert a fetch, source retention or permission")


@dataclass(frozen=True)
class DiscoverySelection(MetadataContract):
    SCHEMA = "gameplay-discovery-selection-v1"
    ID_FIELD = "discovery_selection_id"
    VALIDATOR = staticmethod(_selection)


def select_discovered_release(candidate, observation, source_reference, review, request,
                              *, as_of_date, verification=None):
    """Reproduce one dated review; no automatic selection, rebind or projection."""
    from .artifacts import ArtifactVerificationRequest, ArtifactVerificationResult
    for value, expected in ((candidate, ObservedReleaseCandidate),
            (observation, ExternalSourceObservation), (source_reference, SourceReference),
            (review, DiscoverySourceReview), (request, ArtifactVerificationRequest)):
        if not isinstance(value, expected): _fail("selection", "typed verified inputs required")
        value.verify()
    _date(as_of_date, "as_of_date")
    verify_source_binding(observation, source_reference)
    if candidate.to_dict() != ObservedReleaseCandidate.from_observation(observation).to_dict():
        _fail("release_candidate", "candidate differs from its supplied observation")
    game = observation.game_id
    if any(value.game_id != game for value in (candidate, source_reference, review, request)):
        _fail("game_id", "cross-game discovery inputs")
    expected = {"source_reference_id": source_reference.identity, "observation_id": observation.identity,
        "release_candidate_id": candidate.identity, "verification_request_id": request.identity}
    if any(getattr(review, name) != value for name, value in expected.items()):
        _fail("review", "review does not bind the exact discovery inputs")
    if request.release_candidate_id != candidate.identity or request.discovery_source_reference_id != source_reference.identity or request.observation_id != observation.identity:
        _fail("verification_request", "request does not bind the selected release")
    if request.effective_date != candidate.effective_date or request.artifact_family != candidate.artifact_family or request.artifact_type not in candidate.artifact_types:
        _fail("verification_request", "request metadata contradicts the observed release")
    markers = {row["marker_id"]: row["value"] for row in request.required_markers}
    marker_pair = (markers["rule_reference"], markers["rule_heading"])
    if candidate.title != markers["title"] or marker_pair not in {(row["marker_id"], row["heading"]) for row in observation.observed_markers} or request.artifact_type not in observation.observed_designation["date_token_artifact_types"]:
        _fail("verification_request", "request markers differ from the observed designation")
    reasons = []
    if observation.source_class != "RULES_INDEX" or source_reference.authority_rank != "INDEX":
        reasons.append("OFFICIAL_RULES_INDEX_REQUIRED")
    url = urlsplit(source_reference.authoritative_reference)
    if url.scheme != "https" or url.hostname not in {"magic.wizards.com", "www.magic.wizards.com"} or url.port not in {None, 443}:
        reasons.append("OFFICIAL_RULES_INDEX_REQUIRED")
    if as_of_date != observation.observed_on:
        reasons.append("CURRENTNESS_SCOPE_NOT_OBSERVED")
    if observation.review_status != "REVIEWED" or review.status != "REVIEWED": reasons.append("EXPLICIT_SOURCE_REVIEW_REQUIRED")
    if review.reviewed_on < observation.observed_on: reasons.append("SOURCE_REVIEW_PREDATES_OBSERVATION")
    claims = set(review.supported_claims)
    required = {"official_designation", "effective_date", "currentness_as_of", "identified_update_incorporation"}
    if not required <= claims: reasons.append("SOURCE_REVIEW_CLAIMS_INCOMPLETE")
    if not any(row["source_class"] == "UPDATE_BULLETIN" and row["at_least_identified_update_incorporated"] and (row["marker_id"], row["heading"]) == marker_pair for row in observation.relation_evidence):
        reasons.append("IDENTIFIED_UPDATE_INCORPORATION_NOT_OBSERVED")
    artifact_hash, byte_length, verification_id = None, None, None
    if verification is None:
        if review.artifact_verification_id is not None: _fail("verification", "reviewed verification is missing")
        reasons.append("OFFICIAL_ARTIFACT_BYTES_NOT_VERIFIED")
    else:
        if not isinstance(verification, ArtifactVerificationResult): _fail("verification", "typed local verification required")
        verification.verify()
        verification_id = verification.identity
        if verification.game_id != game or verification.release_candidate_id != candidate.identity or verification.discovery_source_reference_id != source_reference.identity or verification.request_id != request.identity or verification.observation_id != observation.identity:
            _fail("verification", "local result belongs to another request, release or game")
        if verification.status != "VERIFIED_EXPECTED_ARTIFACT":
            reasons.append("OFFICIAL_ARTIFACT_BYTES_NOT_VERIFIED")
        else:
            artifact_hash, byte_length = verification.artifact_hash, verification.byte_length
            if verification.effective_date != candidate.effective_date or verification.verification_profile_id != request.verification_profile_id:
                _fail("verification", "local result metadata/profile mismatch")
            if request.expected_artifact_hash is not None and verification.artifact_hash != request.expected_artifact_hash:
                _fail("verification", "local result differs from the explicitly expected digest")
            if observation.artifact_hash is not None and (verification.artifact_hash != observation.artifact_hash or verification.byte_length != observation.byte_length):
                reasons.append("EXTERNAL_ARTIFACT_IDENTITY_CONFLICT")
            if verification.observed_at is not None and review.reviewed_on < datetime.fromisoformat(verification.observed_at.replace("Z", "+00:00")).date().isoformat():
                reasons.append("SOURCE_REVIEW_PREDATES_VERIFICATION")
            if review.artifact_verification_id != verification.identity or "local_artifact_identity" not in claims:
                reasons.append("LOCAL_ARTIFACT_VERIFICATION_REVIEW_REQUIRED")
            if "local_artifact_source_correspondence" not in claims:
                reasons.append("LOCAL_ARTIFACT_SOURCE_CORRESPONDENCE_REVIEW_REQUIRED")
    return DiscoverySelection.create({"game_id": game, "previous_package_id": review.previous_package_id,
        **expected, "discovery_review_id": review.identity, "artifact_verification_id": verification_id,
        "as_of_date": as_of_date, "effective_date": candidate.effective_date,
        "currentness_status": "CURRENT_DESIGNATION_OBSERVED_AS_OF" if as_of_date == observation.observed_on else "CURRENTNESS_SCOPE_NOT_OBSERVED",
        "artifact_hash": artifact_hash, "byte_length": byte_length,
        "artifact_evidence_state": "ARTIFACT_BYTES_VERIFIED_LOCALLY" if artifact_hash is not None else "METADATA_ONLY",
        "status": "NOT_READY_FOR_RULE_PROJECTION" if reasons else "READY_FOR_RULE_PROJECTION",
        "blocking_reasons": sorted(set(reasons)), "codex_independently_fetched": False,
        "content_retained": False, "source_policy_clearance": "not_granted"})


DISCOVERY_FILES = frozenset({"pm-observation.json", "release-candidate.json",
    "artifact-verification-request.json", "source-review.json", "current-selection.json", "readiness.json"})
PACKAGE_SCHEMA = "gameplay-rules-discovery-closure-v1"


def discovery_package_identity(body):
    return "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})


def verify_discovery_package(root, *, previous_root):
    """Verify a fixed metadata-only append, including the unchanged prior review."""
    from .artifacts import ArtifactVerificationRequest
    from .review import _unique, _nonfinite
    try:
        root = Path(root)
        if not root.is_dir() or any(path.is_symlink() for path in (root, *root.parents)):
            _fail("discovery_package", "ordinary explicit directory required")
        paths = list(root.iterdir())
        if {path.name for path in paths} != DISCOVERY_FILES | {"manifest.json"} or any(path.is_symlink() or not path.is_file() for path in paths):
            _fail("discovery_package", "fixed metadata-only inventory mismatch")
        documents, raw = {}, {}
        for path in paths:
            if path.stat().st_size > 64_000: _fail("discovery_package", "metadata size limit")
            data = path.read_bytes()
            if len(data) > 64_000: _fail("discovery_package", "metadata size limit")
            raw[path.name] = data
            documents[path.name] = json.loads(data.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_nonfinite)
        manifest = documents["manifest.json"]
        _keys(manifest, {"schema_version", "package_id", "previous_package_id", "files",
            "selection_id", "metadata_only", "source_body_retained", "projection_authorized"}, "discovery_manifest")
        body = {key: value for key, value in manifest.items() if key != "package_id"}
        if manifest["schema_version"] != PACKAGE_SCHEMA or manifest["package_id"] != discovery_package_identity(body): _fail("manifest", "identity/schema mismatch")
        if manifest["metadata_only"] is not True or manifest["source_body_retained"] is not False or manifest["projection_authorized"] is not False: _fail("manifest", "fixed authority flags differ")
        if set(manifest["files"]) != DISCOVERY_FILES: _fail("manifest", "file inventory mismatch")
        for name, binding in manifest["files"].items():
            _keys(binding, {"bytes", "sha256"}, "binding")
            if type(binding["bytes"]) is not int or binding["bytes"] != len(raw[name]) or binding["sha256"] != hashlib.sha256(raw[name]).hexdigest():
                _fail("binding", "metadata byte integrity mismatch")
        previous = verify_review_package(previous_root)
        if previous["package_id"] != manifest["previous_package_id"]: _fail("previous_package", "historical package identity differs")
        permissions = json.loads((Path(previous_root) / "permission-matrix.json").read_bytes())
        if any(operation["status"] != "NOT_ESTABLISHED" for row in permissions["components"] for operation in row["permission_status"].values()):
            _fail("permissions", "discovery closure requires the bound unresolved source-permission assessment")
        index_data = json.loads((Path(previous_root) / "source-inventory.json").read_bytes())
        observation = ExternalSourceObservation.from_dict(documents["pm-observation.json"])
        sources = [SourceReference.from_dict(row) for row in index_data["source_references"] if row["source_reference_id"] == observation.source_reference_id]
        if len(sources) != 1: _fail("source_reference", "historical observation anchor missing")
        candidate = ObservedReleaseCandidate.from_dict(documents["release-candidate.json"])
        review = DiscoverySourceReview.from_dict(documents["source-review.json"])
        request = ArtifactVerificationRequest.from_dict(documents["artifact-verification-request.json"])
        selection = DiscoverySelection.from_dict(documents["current-selection.json"])
        if review.previous_package_id != previous["package_id"]: _fail("review", "previous package mismatch")
        reproduced = select_discovered_release(candidate, observation, sources[0], review, request, as_of_date=selection.as_of_date)
        if selection.to_dict() != reproduced.to_dict() or manifest["selection_id"] != selection.identity:
            _fail("selection", "selection fails deterministic reproduction")
        readiness = documents["readiness.json"]
        _keys(readiness, {"schema_version", "selection_id", "status", "blocking_reasons",
            "permission_matrix_package_id", "all_source_operation_states", "projection_authorized",
            "real_rules_executable", "source_body_retained"}, "readiness")
        expected = {"schema_version": "gameplay-discovery-readiness-v1", "selection_id": selection.identity,
            "status": selection.status, "blocking_reasons": list(selection.blocking_reasons),
            "permission_matrix_package_id": previous["package_id"], "all_source_operation_states": "NOT_ESTABLISHED",
            "projection_authorized": False, "real_rules_executable": False, "source_body_retained": False}
        if readiness != expected: _fail("readiness", "readiness or permission authority mismatch")
        return {"package_id": manifest["package_id"], "previous_package_id": previous["package_id"],
            "selection_id": selection.identity, "status": selection.status,
            "blocking_reasons": list(selection.blocking_reasons), "integrity_verified": True,
            "projection_authorized": False, "source_body_retained": False}
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        _fail("discovery_package", "missing, unreadable or malformed metadata closure")
