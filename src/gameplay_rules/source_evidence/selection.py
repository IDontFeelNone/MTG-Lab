"""Explicit reviewed release selection, without a clock, network or projection.

Dates order an already reviewed validity interval; they never choose the newest
filename, hash or candidate. A result is an evidence-readiness statement only.
"""
from datetime import date
from urllib.parse import urlsplit

from .contracts import EvidenceIndex, VersionSelection


_SCOPES = {"current_designation", "as_of_date", "set_release"}
_OFFICIAL_HOSTS = {"magic.wizards.com", "www.magic.wizards.com", "media.wizards.com"}


def _explicit_date(value):
    if not isinstance(value, str):
        raise ValueError("an explicit ISO as-of date is required")
    try:
        if date.fromisoformat(value).isoformat() == value:
            return value
    except ValueError:
        pass
    raise ValueError("an explicit ISO as-of date is required")


def _official(reference):
    try:
        url = urlsplit(reference)
        return (url.scheme == "https" and url.hostname in _OFFICIAL_HOSTS
                and url.username is None and url.password is None
                and url.port in {None, 443} and not url.query and not url.fragment)
    except (TypeError, ValueError):
        return False


def select_version(index, *, scope, as_of_date, release_id=None, review_id=None):
    """Return a deterministic decision from one explicitly named source review.

    ``release_id`` is the declared set/release key for ``set_release`` scope,
    not an automatically chosen rules release. Every scope requires an as-of
    date. Missing evidence/review is an honest NOT_READY result, not a fallback.
    """
    if not isinstance(index, EvidenceIndex):
        raise TypeError("a verified gameplay EvidenceIndex is required")
    index.verify()
    if scope not in _SCOPES:
        raise ValueError("an explicit supported evidence selection scope is required")
    as_of_date = _explicit_date(as_of_date)
    if scope == "set_release":
        if not isinstance(release_id, str) or not release_id.strip():
            raise ValueError("set-release selection requires an explicit release key")
    elif release_id is not None:
        raise ValueError("a release key belongs only to set-release scope")
    value = index.to_dict()
    sources = {row["source_reference_id"]: row for row in value["source_references"]}
    candidates = {row["release_candidate_id"]: row for row in value["release_candidates"]}
    reviews = {row["source_review_id"]: row for row in value["reviews"]}
    reasons, references, lineage = [], set(), set()
    selected = None

    def outcome():
        return VersionSelection.create({
            "game_id": value["game_id"], "evidence_index_id": index.identity,
            "scope": scope, "as_of_date": as_of_date, "release_id": release_id,
            "selected_release_candidate_id": selected,
            "source_review_id": review_id,
            "evidence_reference_ids": sorted(references),
            "lineage_candidate_ids": sorted(lineage),
            "status": "NOT_READY_FOR_RULE_PROJECTION" if reasons else "READY_FOR_RULE_PROJECTION",
            "blocking_reasons": sorted(set(reasons)),
        })

    if not candidates:
        reasons.append("NO_VERIFIED_RELEASE_CANDIDATE")
        if any(row["accessibility"] == "UNAVAILABLE" for row in sources.values()):
            reasons.append("EVIDENCE_UNAVAILABLE")
    if review_id is None:
        reasons.append("EXPLICIT_SOURCE_REVIEW_REQUIRED")
        return outcome()
    if review_id not in reviews:
        raise ValueError("the selected source review is not in this evidence index")
    review = reviews[review_id]
    if review["status"] != "REVIEWED":
        reasons.append("SOURCE_REVIEW_PENDING")
        return outcome()
    claims = review["supported_claims"]

    def matches_scope(claim):
        if scope == "current_designation":
            return claim["claim"] == "current_designation" and claim["value"] == as_of_date
        if scope == "set_release":
            return claim["claim"] == "release_scope" and claim["value"] == release_id
        if claim["claim"] != "as_of_scope":
            return False
        interval = claim["value"]
        return interval["valid_from"] <= as_of_date and (
            interval["valid_until"] is None or as_of_date < interval["valid_until"])

    eligible_claims = [claim for claim in claims if matches_scope(claim)]
    targets = {claim["release_candidate_id"] for claim in eligible_claims}
    if len(targets) != 1:
        reasons.append("AMBIGUOUS_REVIEWED_SCOPE" if len(targets) > 1 else "REVIEWED_SCOPE_NOT_ESTABLISHED")
        return outcome()
    selected = targets.pop()
    candidate = candidates[selected]
    artifact = sources[candidate["artifact_source_reference_id"]]
    references.add(artifact["source_reference_id"])
    target_claims = [claim for claim in claims if claim["release_candidate_id"] == selected]
    for claim in target_claims:
        references.update(claim["source_reference_ids"])
    logical_versions = [row for row in candidates.values() if row["release_id"] == candidate["release_id"]]
    # New observations may reference identical release bytes. Observation IDs
    # are provenance, not evidence of contradictory release content.
    release_facts = {(row["rules_version"], row["effective_date"], row["artifact_hash"],
                      row["byte_length"], tuple(sorted(row["supersedes"])))
                     for row in logical_versions}
    if len(release_facts) != 1 or candidate["evidence_status"] == "CONFLICTING":
        reasons.append("CONFLICTING_RELEASE_IDENTITY")
    same_version = [row for row in candidates.values()
                    if row["rules_version"] == candidate["rules_version"]
                    and row["effective_date"] == candidate["effective_date"]]
    if candidate["rules_version"] is not None and len({row["artifact_hash"] for row in same_version if row["artifact_hash"] is not None}) > 1:
        reasons.append("CONFLICTING_SOURCE_PROVIDED_VERSION")
    if candidate["evidence_status"] in {"AMBIGUOUS", "EVIDENCE_UNAVAILABLE"}:
        reasons.append(candidate["evidence_status"])
    if candidate["evidence_status"] != "VERIFIED_ARTIFACT" or candidate["completeness"] != "COMPLETE":
        reasons.append("EXACT_ARTIFACT_NOT_VERIFIED")
    if artifact["source_class"] != "COMPREHENSIVE_RULES" or artifact["authority_rank"] != "PRIMARY":
        reasons.append("PRIMARY_COMPREHENSIVE_RULES_AUTHORITY_REQUIRED")
    if artifact["accessibility"] != "AVAILABLE" or artifact["evidence_status"] != "VERIFIED_ARTIFACT":
        reasons.append("PRIMARY_ARTIFACT_EVIDENCE_UNAVAILABLE")
    if not _official(artifact["resolved_reference"] or artifact["authoritative_reference"]):
        reasons.append("OFFICIAL_ARTIFACT_REFERENCE_REQUIRED")
    for field in ("artifact_hash", "byte_length", "effective_date", "rules_version"):
        if candidate[field] is None or candidate[field] != artifact[field]:
            reasons.append("ARTIFACT_BINDING_INCOMPLETE:" + field)
    if candidate["byte_length"] == 0:
        reasons.append("EMPTY_RULES_ARTIFACT")
    if candidate["effective_date"] is not None and candidate["effective_date"] > as_of_date:
        reasons.append("RELEASE_NOT_EFFECTIVE_AS_OF")

    required = {"artifact_identity": candidate["artifact_hash"],
                "version": candidate["rules_version"],
                "effective_date": candidate["effective_date"]}
    for name, expected in required.items():
        if expected is None or not any(claim["claim"] == name and claim["value"] == expected
                and artifact["source_reference_id"] in claim["source_reference_ids"]
                for claim in target_claims):
            reasons.append("REVIEWED_BINDING_REQUIRED:" + name)

    # The index is a discovery authority, never a substitute for artifact bytes.
    designations = [edge for edge in value["relations"] if edge["relation"] == "DESIGNATES"
                    and edge["to_reference_id"] == artifact["source_reference_id"]
                    and edge["from_reference_id"] in sources]
    designations = [edge for edge in designations if
                    sources[edge["from_reference_id"]]["source_class"] == "RULES_INDEX"
                    and sources[edge["from_reference_id"]]["accessibility"] == "AVAILABLE"
                    and sources[edge["from_reference_id"]]["access_outcome"] == "AVAILABLE"
                    and sources[edge["from_reference_id"]]["observed_at"] is not None
                    and sources[edge["from_reference_id"]]["evidence_status"] in {"VERIFIED_ARTIFACT", "VERIFIED_METADATA_ONLY"}
                    and _official(sources[edge["from_reference_id"]]["authoritative_reference"])
                    and _official(sources[edge["from_reference_id"]]["resolved_reference"]
                                  or sources[edge["from_reference_id"]]["authoritative_reference"])]
    if not designations:
        reasons.append("OFFICIAL_RULES_INDEX_DESIGNATION_REQUIRED")
    elif scope == "current_designation":
        valid = []
        for edge in designations:
            page = sources[edge["from_reference_id"]]
            if page["observed_at"][:10] == as_of_date and any(
                    claim["claim"] == "current_designation" and claim["value"] == as_of_date
                    and page["source_reference_id"] in claim["source_reference_ids"]
                    for claim in target_claims):
                valid.append(edge)
        if not valid:
            reasons.append("REVIEWED_CURRENT_DESIGNATION_AS_OF_REQUIRED")
    for edge in designations:
        references.add(edge["from_reference_id"])
        references.update(edge["evidence_reference_ids"])

    predecessors = candidate["supersedes"]
    lineage.update(predecessors)
    lineage.add(selected)
    if not any(claim["claim"] == "supersession" and sorted(claim["value"]) == sorted(predecessors)
               for claim in target_claims):
        reasons.append("REVIEWED_SUPERSESSION_LINEAGE_REQUIRED")
    successors = [row for row in candidates.values() if selected in row["supersedes"]]
    if any(row["effective_date"] is not None and row["effective_date"] <= as_of_date for row in successors):
        reasons.append("SUPERSEDED_AS_OF_SCOPE")
    if scope == "as_of_date":
        intervals = [claim["value"] for claim in eligible_claims
                     if claim["release_candidate_id"] == selected]
        if any(interval["valid_from"] != candidate["effective_date"] for interval in intervals):
            reasons.append("REVIEWED_EFFECTIVE_INTERVAL_MISMATCH")
        for interval in intervals:
            end = interval["valid_until"]
            if end is not None and not any(row["effective_date"] == end for row in successors):
                reasons.append("REVIEWED_INTERVAL_END_NOT_BOUND_TO_SUCCESSOR")
    if any(edge["relation"] == "CONFLICTS_WITH" and
           ({edge["from_reference_id"], edge["to_reference_id"]} & {selected, artifact["source_reference_id"]})
           for edge in value["relations"]):
        reasons.append("CONFLICTING_OFFICIAL_EVIDENCE_REQUIRES_REVIEW")
    return outcome()
