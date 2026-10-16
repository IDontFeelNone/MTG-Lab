"""Externally supplied first-party observations in the metadata-only review lane.

An observer label describes provenance, not authentication, source permission or
an independent fetch by this program.  Existing network observations remain
separate SourceReference records, including an unsuccessful original request.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .contracts import (
    AUTHORITY_RANKS, SOURCE_CLASSES, MetadataContract, SourceReference,
    _date, _enum, _fail, _hash, _int, _keys, _reference, _strings, _text, _version,
)


EXTERNAL_OBSERVER_CLASSES = frozenset({
    "PM_SUPPLIED_FIRST_PARTY_OBSERVATION",
    "OPERATOR_SUPPLIED_FIRST_PARTY_OBSERVATION",
    "PROJECT_AUTHORED_FICTIONAL_OBSERVATION",
})


def _bounded_text(value, field, maximum=200):
    _text(value, field)
    if len(value) > maximum or any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail(field, "bounded single-line metadata required")


def _marker(value, field):
    _keys(value, {"marker_id", "heading"}, field)
    _bounded_text(value["marker_id"], field + ".marker_id", 80)
    _bounded_text(value["heading"], field + ".heading")


def _observation(body):
    _keys(body, {
        "game_id", "observer_class", "observation_method", "observed_on",
        "source_class", "authority_rank", "source_reference_id",
        "observed_designation", "effective_date", "source_provided_version",
        "currentness", "observed_markers", "relation_evidence", "artifact_hash",
        "byte_length", "source_body_retained", "artifact_bytes_verified",
        "independent_verification_status", "codex_independently_fetched",
        "evidence_status", "observation_state", "review_status", "limitations",
        "provenance",
    }, "external_source_observation")
    _text(body["game_id"], "game_id")
    _enum(body["observer_class"], EXTERNAL_OBSERVER_CLASSES, "observer_class")
    _text(body["observation_method"], "observation_method")
    _date(body["observed_on"], "observed_on")
    _enum(body["source_class"], SOURCE_CLASSES, "source_class")
    if body["authority_rank"] != AUTHORITY_RANKS[body["source_class"]]:
        _fail("authority_rank", "source-class authority mismatch")
    _hash(body["source_reference_id"], "source_reference_id")
    designation = body["observed_designation"]
    _keys(designation, {"title", "artifact_types", "filename_date_token", "date_token_artifact_types",
                        "artifact_reference", "artifact_filename"},
          "observed_designation")
    _bounded_text(designation["title"], "observed_designation.title")
    _strings(designation["artifact_types"], "artifact_types")
    if not designation["artifact_types"] or not set(designation["artifact_types"]) <= {"DOCX", "PDF", "TXT"}:
        _fail("artifact_types", "explicit observed artifact types required")
    token = designation["filename_date_token"]
    if token is not None and (not isinstance(token, str) or not re.fullmatch(r"[0-9]{8}", token)):
        _fail("filename_date_token", "source-observed date token or null required")
    _strings(designation["date_token_artifact_types"], "date_token_artifact_types")
    if not set(designation["date_token_artifact_types"]) <= set(designation["artifact_types"]):
        _fail("date_token_artifact_types", "date-token types must have been observed in the designation")
    if (token is None) != (not designation["date_token_artifact_types"]):
        _fail("date_token_artifact_types", "explicit artifact-type scope for the observed date token required")
    _reference(designation["artifact_reference"], "artifact_reference", nullable=True)
    filename = designation["artifact_filename"]
    if filename is not None:
        _bounded_text(filename, "artifact_filename")
        if filename in {".", ".."} or "/" in filename or "\\" in filename:
            _fail("artifact_filename", "source-observed basename required")
        if token is not None and token not in filename:
            _fail("artifact_filename", "observed filename/date token contradiction")
    _date(body["effective_date"], "effective_date", nullable=True)
    _version(body["source_provided_version"], "source_provided_version", nullable=True)
    if body["effective_date"] is not None and body["effective_date"] > body["observed_on"]:
        _fail("effective_date", "current designation cannot yet be effective in the future")
    currentness = body["currentness"]
    _keys(currentness, {"claim", "as_of_date"}, "currentness")
    if currentness["claim"] != "CURRENT_DESIGNATION_OBSERVED":
        _fail("currentness.claim", "explicit dated designation observation required")
    _date(currentness["as_of_date"], "currentness.as_of_date")
    if currentness["as_of_date"] != body["observed_on"]:
        _fail("currentness", "currentness is scoped to the actual observation date")
    markers = body["observed_markers"]
    if not isinstance(markers, list) or len(markers) > 16:
        _fail("observed_markers", "bounded marker metadata array required")
    for value in markers:
        _marker(value, "observed_marker")
    marker_pairs = {(value["marker_id"], value["heading"]) for value in markers}
    if len(marker_pairs) != len(markers) or len({value["marker_id"] for value in markers}) != len(markers):
        _fail("observed_markers", "duplicate or contradictory marker")
    relations = body["relation_evidence"]
    if not isinstance(relations, list) or len(relations) > 16:
        _fail("relation_evidence", "bounded relationship metadata array required")
    for relation in relations:
        _keys(relation, {"source_class", "source_reference", "publication_date", "relation", "marker_id",
                         "heading", "at_least_identified_update_incorporated", "full_bulletin_diff_verified"},
              "relation_evidence")
        _enum(relation["source_class"], {"UPDATE_BULLETIN", "RELEASE_NOTES", "RULES_BLOG"}, "relation.source_class")
        _reference(relation["source_reference"], "relation.source_reference", nullable=True)
        _date(relation["publication_date"], "relation.publication_date", nullable=True)
        if relation["publication_date"] is not None and relation["publication_date"] > body["observed_on"]:
            _fail("relation.publication_date", "future publication cannot have been observed")
        _enum(relation["relation"], {"ANNOUNCES_RULE_CHANGE", "DESCRIBES_CHANGES_FOR", "EXPLAINS"}, "relation.relation")
        _marker({"marker_id": relation["marker_id"], "heading": relation["heading"]}, "relation.marker")
        if type(relation["at_least_identified_update_incorporated"]) is not bool:
            _fail("relation.at_least_identified_update_incorporated", "explicit boolean required")
        if relation["at_least_identified_update_incorporated"] and (relation["marker_id"], relation["heading"]) not in marker_pairs:
            _fail("relation_evidence", "incorporation requires the exact observed marker")
        if relation["full_bulletin_diff_verified"] is not False:
            _fail("full_bulletin_diff_verified", "bounded marker observation does not verify a full bulletin diff")
    _hash(body["artifact_hash"], "artifact_hash", nullable=True)
    _int(body["byte_length"], "byte_length", nullable=True)
    if (body["artifact_hash"] is None) != (body["byte_length"] is None):
        _fail("artifact_hash", "supplied hash and byte count must be bound together")
    # A supplied digest remains an external metadata claim.  Only the separate
    # local-verification contract can attest to independently inspected bytes.
    fixed = {
        "source_body_retained": False, "artifact_bytes_verified": False,
        "independent_verification_status": "NOT_INDEPENDENTLY_REPRODUCED",
        "codex_independently_fetched": False, "evidence_status": "VERIFIED_METADATA_ONLY",
        "observation_state": "EXTERNALLY_OBSERVED_FIRST_PARTY",
    }
    for name, expected in fixed.items():
        if body[name] != expected or (type(expected) is bool and type(body[name]) is not bool):
            _fail(name, "external metadata cannot claim independent bytes, fetch or source-body retention")
    _enum(body["review_status"], {"PENDING", "REVIEWED"}, "review_status")
    for name in ("limitations", "provenance"):
        _strings(body[name], name)
        if not body[name] or len(body[name]) > 16:
            _fail(name, "bounded explicit provenance and evidence limitations required")
        for item in body[name]:
            _bounded_text(item, name, 500)


@dataclass(frozen=True)
class ExternalSourceObservation(MetadataContract):
    """Immutable reviewed input; neither authenticated attestation nor approval."""

    SCHEMA = "gameplay-external-source-observation-v1"
    ID_FIELD = "external_observation_id"
    VALIDATOR = staticmethod(_observation)


def verify_source_binding(observation, source_reference):
    """Verify an explicit anchor without upgrading its access/evidence outcome."""
    if not isinstance(observation, ExternalSourceObservation) or not isinstance(source_reference, SourceReference):
        _fail("observation_binding", "typed observation and source reference required")
    observation.verify()
    source_reference.verify()
    if observation.source_reference_id != source_reference.identity:
        _fail("source_reference_id", "observation anchor identity mismatch")
    if observation.game_id != source_reference.game_id or observation.source_class != source_reference.source_class:
        _fail("observation_binding", "source anchor game/class mismatch")
    return observation
