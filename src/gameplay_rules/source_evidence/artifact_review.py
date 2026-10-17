"""Immutable correspondence review of existing metadata, never source bodies.

Artifact bytes are checked only by the existing offline verifier. This module
binds its result to an explicit owner-origin review and reproduces readiness
using the existing selector. It neither acquires nor projects rules content.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from .artifacts import ArtifactVerificationRequest, ArtifactVerificationResult, _open_regular_no_symlinks
from .closure import (DiscoverySelection, DiscoverySourceReview, ObservedReleaseCandidate,
                      select_discovered_release, verify_discovery_package)
from .contracts import (MetadataContract, SourceReference, _date, _enum, _fail,
                        _hash, _int, _keys, _strings, _text)
from .observations import ExternalSourceObservation
from .review import verify_review_package, _unique, _nonfinite


CHECKS = frozenset({"local_artifact_identity", "official_designation_correspondence",
    "effective_date", "artifact_family", "structural_markers", "owner_origin_statement"})
PACKAGE_SCHEMA = "gameplay-rules-artifact-review-package-v1"
REVIEW_FILES = frozenset({"artifact-verification-result.json", "artifact-correspondence-review.json",
                         "current-selection.json", "readiness.json"})


def _review(body):
    _keys(body, {"game_id", "prior_source_package_id", "prior_discovery_package_id", "prior_review_id",
        "verification_result_id", "owner_provenance", "evaluated_artifact", "checks", "source_review",
        "limitations", "content_retained", "source_body_copied", "network_used"}, "artifact_correspondence_review")
    _text(body["game_id"], "game_id")
    for name in ("prior_source_package_id", "prior_discovery_package_id", "prior_review_id", "verification_result_id"):
        _hash(body[name], name)
    owner = body["owner_provenance"]
    _keys(owner, {"provenance_class", "statement", "downloaded_from_designated_official_txt",
        "not_intentionally_modified", "source_reference_id", "pm_observation_id", "artifact_family",
        "artifact_type", "effective_date", "codex_independent_network_verification",
        "cryptographic_authentication", "source_permission_established", "local_path_retained"}, "owner_provenance")
    if owner["provenance_class"] != "OWNER_SUPPLIED_ARTIFACT_PROVENANCE": _fail("provenance_class")
    _text(owner["statement"], "owner_statement")
    if len(owner["statement"]) > 500 or any(ord(c) < 32 or ord(c) == 127 for c in owner["statement"]): _fail("owner_statement", "bounded authored provenance required")
    for name in ("downloaded_from_designated_official_txt", "not_intentionally_modified"):
        if type(owner[name]) is not bool: _fail(name)
    for name in ("source_reference_id", "pm_observation_id"): _hash(owner[name], name)
    _text(owner["artifact_family"], "artifact_family")
    if owner["artifact_type"] != "TXT": _fail("artifact_type")
    _date(owner["effective_date"], "effective_date")
    for name in ("codex_independent_network_verification", "cryptographic_authentication",
                 "source_permission_established", "local_path_retained"):
        if owner[name] is not False: _fail(name, "owner provenance is not authentication, permission or path retention")
    artifact = body["evaluated_artifact"]
    _keys(artifact, {"artifact_hash", "byte_length", "effective_date", "artifact_family", "artifact_type",
        "verification_status", "verification_profile_id", "verification_profile_version", "checked_markers"}, "evaluated_artifact")
    _hash(artifact["artifact_hash"], "artifact_hash", nullable=True)
    _int(artifact["byte_length"], "byte_length", nullable=True)
    if (artifact["artifact_hash"] is None) != (artifact["byte_length"] is None): _fail("artifact_hash")
    _date(artifact["effective_date"], "effective_date", nullable=True)
    for name in ("artifact_family", "artifact_type", "verification_status", "verification_profile_version"): _text(artifact[name], name)
    _hash(artifact["verification_profile_id"], "verification_profile_id")
    if not isinstance(artifact["checked_markers"], list) or len(artifact["checked_markers"]) != 4: _fail("checked_markers")
    for marker in artifact["checked_markers"]:
        _keys(marker, {"marker_id", "matched"}, "marker")
        _enum(marker["marker_id"], {"title", "effective_date_marker", "rule_reference", "rule_heading"}, "marker_id")
        if type(marker["matched"]) is not bool: _fail("matched")
    _keys(body["checks"], CHECKS, "correspondence_checks")
    for value in body["checks"].values(): _enum(value, {"MATCH", "MISMATCH", "UNKNOWN"}, "check")
    review = DiscoverySourceReview.from_dict(body["source_review"])
    if len(review.reviewer) > 500 or any(ord(c) < 32 or ord(c) == 127 for c in review.reviewer):
        _fail("reviewer", "bounded authored review metadata required")
    if not 1 <= len(review.limitations) <= 8 or any(len(value) > 500 or any(ord(c) < 32 or ord(c) == 127 for c in value) for value in review.limitations):
        _fail("source_review.limitations", "bounded single-line metadata required")
    if review.game_id != body["game_id"] or review.artifact_verification_id != body["verification_result_id"] or review.previous_package_id != body["prior_discovery_package_id"]:
        _fail("source_review", "review lineage/result differs from correspondence envelope")
    claims = set(review.supported_claims)
    if "local_artifact_identity" in claims and body["checks"]["local_artifact_identity"] != "MATCH":
        _fail("local_artifact_identity", "an identity claim requires a matching evaluation")
    if "local_artifact_source_correspondence" in claims and (set(body["checks"].values()) != {"MATCH"} or not owner["downloaded_from_designated_official_txt"] or not owner["not_intentionally_modified"]):
        _fail("local_artifact_source_correspondence", "a correspondence claim requires all reviewed checks and supplied origin")
    _strings(body["limitations"], "limitations")
    if not 1 <= len(body["limitations"]) <= 8 or any(len(value) > 500 or any(ord(c) < 32 or ord(c) == 127 for c in value) for value in body["limitations"]): _fail("limitations", "bounded metadata limitations required")
    for name in ("content_retained", "source_body_copied", "network_used"):
        if body[name] is not False: _fail(name, "metadata-only review boundary")


@dataclass(frozen=True)
class ArtifactCorrespondenceReview(MetadataContract):
    SCHEMA = "gameplay-artifact-correspondence-review-v1"
    ID_FIELD = "artifact_correspondence_review_id"
    VALIDATOR = staticmethod(_review)


def evaluated_artifact(verification, request):
    """Project only already verified metadata; no file path or source body."""
    if not isinstance(verification, ArtifactVerificationResult) or not isinstance(request, ArtifactVerificationRequest):
        _fail("artifact_review", "typed verification result and request required")
    verification.verify()
    request.verify()
    return {**{name: verification.to_dict()[name] for name in ("artifact_hash", "byte_length", "effective_date",
        "artifact_type", "verification_profile_id", "verification_profile_version", "checked_markers")},
        "artifact_family": request.artifact_family, "verification_status": verification.status}


def correspondence_checks(verification, request, candidate, owner):
    """Deterministic fact checks; none can supply an owner-origin statement."""
    matched = lambda value: "MATCH" if value else "MISMATCH"
    identity = verification.status == "VERIFIED_EXPECTED_ARTIFACT"
    effective = verification.effective_date == candidate.effective_date == owner["effective_date"]
    family = request.artifact_family == candidate.artifact_family == owner["artifact_family"]
    markers = [row["marker_id"] for row in verification.checked_markers] == [row["marker_id"] for row in request.required_markers] and all(row["matched"] for row in verification.checked_markers)
    origin = owner["downloaded_from_designated_official_txt"] and owner["not_intentionally_modified"]
    return {"local_artifact_identity": matched(identity), "effective_date": matched(effective),
        "artifact_family": matched(family), "structural_markers": matched(markers),
        "owner_origin_statement": matched(origin),
        "official_designation_correspondence": matched(identity and effective and family and markers and origin)}


def select_reviewed_artifact(review, verification, candidate, observation, source_reference, request,
        *, as_of_date, prior_source_package_id, prior_discovery_package_id, prior_review_id):
    """Check the explicit correspondence review, then call the unchanged selector."""
    if not isinstance(review, ArtifactCorrespondenceReview): _fail("review", "typed correspondence review required")
    review.verify()
    for value, cls in ((verification, ArtifactVerificationResult), (candidate, ObservedReleaseCandidate),
            (observation, ExternalSourceObservation), (source_reference, SourceReference), (request, ArtifactVerificationRequest)):
        if not isinstance(value, cls): _fail("review", "typed evidence inputs required")
        value.verify()
    if verification.observed_at is None:
        _fail("observed_at", "this owner-artifact review lane requires an explicit retained operation timestamp")
    for name, expected in (("game_id", verification.game_id), ("verification_result_id", verification.identity),
            ("prior_source_package_id", prior_source_package_id), ("prior_discovery_package_id", prior_discovery_package_id),
            ("prior_review_id", prior_review_id)):
        if getattr(review, name) != expected: _fail(name, "correspondence review binding mismatch")
    value = review.to_dict()
    owner = value["owner_provenance"]
    if owner["source_reference_id"] != source_reference.identity or owner["pm_observation_id"] != observation.identity:
        _fail("owner_provenance", "supplied origin refers to another designation")
    if value["evaluated_artifact"] != evaluated_artifact(verification, request): _fail("evaluated_artifact", "reviewed facts differ from verified metadata")
    if value["checks"] != correspondence_checks(verification, request, candidate, owner): _fail("checks", "correspondence checks do not reproduce")
    source_review = DiscoverySourceReview.from_dict(value["source_review"])
    return select_discovered_release(candidate, observation, source_reference, source_review,
                                    request, as_of_date=as_of_date, verification=verification)


def package_identity(body):
    return "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": body})


def _metadata(path):
    descriptor = _open_regular_no_symlinks(path)
    if descriptor is None: _fail("review_package", "required metadata file missing")
    with os.fdopen(descriptor, "rb") as stream:
        data = stream.read(64_001)
    if len(data) > 64_000: _fail("review_package", "metadata size limit exceeded")
    return json.loads(data.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_nonfinite), data


def verify_artifact_review_package(root, *, source_root, discovery_root):
    """Verify metadata integrity/readiness offline, without requiring source bytes."""
    try:
        root = Path(root)
        if not root.is_dir() or any(path.is_symlink() for path in (root, *root.parents)):
            _fail("review_package", "explicit ordinary metadata directory required")
        paths = list(root.iterdir())
        if {path.name for path in paths} != REVIEW_FILES | {"manifest.json"} or any(path.is_symlink() or not path.is_file() for path in paths):
            _fail("review_package", "fixed metadata-only file inventory differs")
        documents, raw = {}, {}
        for path in paths: documents[path.name], raw[path.name] = _metadata(path)
        manifest = documents["manifest.json"]
        _keys(manifest, {"schema_version", "package_id", "source_package_id", "discovery_package_id", "files",
            "verification_result_id", "correspondence_review_id", "selection_id", "metadata_only",
            "content_retained", "projection_authorized", "admission_eligible", "source_policy_clearance"}, "manifest")
        if manifest["schema_version"] != PACKAGE_SCHEMA or manifest["package_id"] != package_identity({k:v for k,v in manifest.items() if k != "package_id"}): _fail("manifest", "package identity/schema mismatch")
        for name, expected in (("metadata_only", True), ("content_retained", False), ("projection_authorized", False), ("admission_eligible", False), ("source_policy_clearance", "not_granted")):
            matches = manifest[name] is expected if type(expected) is bool else manifest[name] == expected
            if not matches: _fail(name, "fixed metadata-only authority boundary")
        if set(manifest["files"]) != REVIEW_FILES: _fail("manifest", "metadata bindings inventory differs")
        for name, binding in manifest["files"].items():
            _keys(binding, {"sha256", "bytes"}, "file_binding")
            if type(binding["bytes"]) is not int or binding["bytes"] != len(raw[name]) or binding["sha256"] != hashlib.sha256(raw[name]).hexdigest(): _fail("file_binding", "metadata bytes differ")
        previous = verify_review_package(source_root)
        discovery = verify_discovery_package(discovery_root, previous_root=source_root)
        if manifest["source_package_id"] != previous["package_id"] or manifest["discovery_package_id"] != discovery["package_id"]: _fail("prior_packages", "historical package identity mismatch")
        def prior(name): return _metadata(Path(discovery_root) / name)[0]
        observation = ExternalSourceObservation.from_dict(prior("pm-observation.json"))
        candidate = ObservedReleaseCandidate.from_dict(prior("release-candidate.json"))
        request = ArtifactVerificationRequest.from_dict(prior("artifact-verification-request.json"))
        original_review = DiscoverySourceReview.from_dict(prior("source-review.json"))
        index = _metadata(Path(source_root) / "source-inventory.json")[0]
        sources = [SourceReference.from_dict(row) for row in index["source_references"] if row["source_reference_id"] == observation.source_reference_id]
        if len(sources) != 1: _fail("source_reference", "selected discovery source missing")
        verification = ArtifactVerificationResult.from_dict(documents["artifact-verification-result.json"])
        if verification.status != "VERIFIED_EXPECTED_ARTIFACT": _fail("verification", "successful artifact verification required")
        review = ArtifactCorrespondenceReview.from_dict(documents["artifact-correspondence-review.json"])
        selection = DiscoverySelection.from_dict(documents["current-selection.json"])
        reproduced = select_reviewed_artifact(review, verification, candidate, observation, sources[0], request,
            as_of_date=selection.as_of_date, prior_source_package_id=previous["package_id"],
            prior_discovery_package_id=discovery["package_id"], prior_review_id=original_review.identity)
        if selection.to_dict() != reproduced.to_dict(): _fail("selection", "readiness selection does not reproduce")
        if (manifest["verification_result_id"], manifest["correspondence_review_id"], manifest["selection_id"]) != (verification.identity, review.identity, selection.identity): _fail("manifest", "result/review/selection binding mismatch")
        expected = {"schema_version": "gameplay-artifact-readiness-v1", "selection_id": selection.identity,
            "correspondence_review_id": review.identity, "verification_result_id": verification.identity,
            "status": selection.status, "blocking_reasons": list(selection.blocking_reasons),
            "currentness_as_of": selection.as_of_date, "effective_date": selection.effective_date,
            "permission_matrix_package_id": previous["package_id"], "all_source_operation_states": "NOT_ESTABLISHED",
            "projection_authorized": False, "admission_eligible": False, "source_policy_clearance": "not_granted",
            "real_rules_executable": False, "content_retained": False}
        if documents["readiness.json"] != expected: _fail("readiness", "readiness or permission state differs")
        return {"package_id": manifest["package_id"], "verification_result_id": verification.identity,
            "correspondence_review_id": review.identity, "selection_id": selection.identity,
            "status": selection.status, "blocking_reasons": list(selection.blocking_reasons),
            "projection_authorized": False, "admission_eligible": False, "source_policy_clearance": "not_granted",
            "content_retained": False, "integrity_verified": True}
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        _fail("review_package", "missing, unreadable or malformed metadata package")
