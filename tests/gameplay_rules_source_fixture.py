"""Original local test doubles for metadata-only gameplay source intake.

Official-style URLs name request boundaries only. Every body, date, version and
claim in these helpers is project-authored synthetic test data, never a fetched
Wizards document or a source-permission decision.
"""
from copy import deepcopy

PAGE_URL = "https://magic.wizards.com/en/rules"
ARTIFACT_URL = "https://media.wizards.com/fixture/gameplay-fictional-rules-v1.txt"
NEXT_ARTIFACT_URL = "https://media.wizards.com/fixture/gameplay-fictional-rules-v2.txt"
BULLETIN_URL = "https://magic.wizards.com/en/news/fixture-fictional-update"
FORMAT_URL = "https://magic.wizards.com/en/banned-restricted-list"
OBSERVED_AT = "2032-01-06T12:00:00Z"
AS_OF = "2032-01-06"
RULES_VERSION = "fictional-local-version-1"
EFFECTIVE_DATE = "2032-01-01"
HTML_BODY = ("<!doctype html><html><head>"
             '<meta name="rules-effective-date" content="2032-01-01">'
             '<meta name="rules-version" content="fictional-local-version-1">'
             "</head><body>Original fictional metadata transport fixture. "
             '<a href="' + ARTIFACT_URL + '">Fictional comprehensive rules artifact</a>'
             "</body></html>").encode("utf-8")
ARTIFACT_BODY = b"Original fictional local transport test artifact; no real game rules.\n"


class LocalMetadataTransport:
    """Explicit fake transport; no socket, environment, credentials or fallback."""

    def __init__(self, responses=None):
        self.responses = deepcopy(responses or {})
        self.calls = []

    def fetch(self, url, *, max_response_bytes, timeout_seconds):
        from gameplay_rules.source_evidence.intake import MetadataTransportResponse
        self.calls.append({"url": url, "max_response_bytes": max_response_bytes,
                           "timeout_seconds": timeout_seconds})
        if url not in self.responses:
            raise AssertionError("Unconfigured fictional transport request")
        value = self.responses[url]
        if isinstance(value, Exception):
            raise value
        return MetadataTransportResponse(**value)


def response(url=PAGE_URL, *, status=200, content_type="text/html", body=HTML_BODY,
             location=None, content_encoding="identity"):
    return {"status": status, "url": url, "content_type": content_type, "body": body,
            "location": location, "content_encoding": content_encoding}


def permissions(status="NOT_ESTABLISHED"):
    from gameplay_rules.source_evidence.contracts import PERMISSION_OPERATIONS
    return {name: {"status": status, "evidence_references": [], "conditions": []}
            for name in PERMISSION_OPERATIONS}


def unbound(model):
    value = model.to_dict()
    for name in (model.identity_key, "schema_version", "metadata_only", "admission_eligible", "projection_authorized"):
        value.pop(name)
    return value


def source_reference(*, source_class="COMPREHENSIVE_RULES", **changes):
    import hashlib
    from gameplay_rules.source_evidence.contracts import AUTHORITY_RANKS, SourceReference
    body = {
        "source_id": "fixture-comprehensive-rules-artifact-1", "game_id": "fictional-source-contract",
        "source_class": source_class, "issuer": "Original local transport test issuer",
        "title": "Original fictional source metadata; not an official observation",
        "authoritative_reference": ARTIFACT_URL, "resolved_reference": ARTIFACT_URL,
        "discovered_at": OBSERVED_AT, "observed_at": OBSERVED_AT,
        "accessibility": "AVAILABLE", "access_outcome": "AVAILABLE", "http_status": 200,
        "media_type": "text/plain", "effective_date": EFFECTIVE_DATE, "rules_version": RULES_VERSION,
        "artifact_hash": "sha256:" + hashlib.sha256(ARTIFACT_BODY).hexdigest(),
        "byte_length": len(ARTIFACT_BODY), "supersedes": [], "superseded_by": [],
        "authority_rank": AUTHORITY_RANKS[source_class],
        "provenance": ["Original project-authored local source-contract fixture; no real source acquisition"],
        "permission_status": permissions(), "retention_status": "METADATA_ONLY",
        "completeness": "COMPLETE", "review_status": "PENDING", "evidence_status": "VERIFIED_ARTIFACT",
    }
    body.update(deepcopy(changes))
    return SourceReference.create(body)


def page_reference(**changes):
    import hashlib
    args = {"source_class": "RULES_INDEX", "source_id": "fixture-rules-index-observation-1",
            "authoritative_reference": PAGE_URL, "resolved_reference": PAGE_URL,
            "media_type": "text/html", "artifact_hash": "sha256:" + hashlib.sha256(HTML_BODY).hexdigest(),
            "byte_length": len(HTML_BODY), "effective_date": None, "rules_version": None,
            "evidence_status": "VERIFIED_METADATA_ONLY"}
    args.update(changes)
    return source_reference(**args)


def release_candidate(source, **changes):
    from gameplay_rules.source_evidence.contracts import ReleaseCandidate
    body = {"game_id": source.game_id, "release_id": "fictional-release-1",
            "artifact_source_reference_id": source.identity, "rules_version": source.rules_version,
            "effective_date": source.effective_date, "artifact_hash": source.artifact_hash,
            "byte_length": source.byte_length, "evidence_status": source.evidence_status,
            "completeness": "COMPLETE", "supersedes": [], "unresolved_questions": []}
    body.update(deepcopy(changes))
    return ReleaseCandidate.create(body)


def reviewed_claims(candidate, artifact, page, *, without=(), **changes):
    from gameplay_rules.source_evidence.contracts import SourceReview
    values = {"artifact_identity": candidate.artifact_hash, "version": candidate.rules_version,
              "effective_date": candidate.effective_date, "current_designation": AS_OF,
              "as_of_scope": {"valid_from": candidate.effective_date, "valid_until": None},
              "release_scope": candidate.release_id, "supersession": list(candidate.supersedes)}
    claims = [{"claim": name, "release_candidate_id": candidate.identity,
               "source_reference_ids": [page.identity if name == "current_designation" else artifact.identity],
               "value": value} for name, value in values.items() if name not in without]
    body = {"game_id": candidate.game_id, "source_reference_ids": [artifact.identity, page.identity],
            "release_candidate_ids": [candidate.identity], "reviewer": "fictional-local-review",
            "reviewed_at": OBSERVED_AT, "status": "REVIEWED", "supported_claims": claims,
            "limitations": ["Synthetic fixture review, not owner approval or executable rules projection"]}
    body.update(deepcopy(changes))
    return SourceReview.create(body)


def designation(page, artifact):
    return {"relation": "DESIGNATES", "from_reference_id": page.identity,
            "to_reference_id": artifact.identity, "evidence_reference_ids": [page.identity]}


def evidence_index(sources, candidates, reviews=(), relations=()):
    from gameplay_rules.source_evidence.contracts import EvidenceIndex
    return EvidenceIndex.create({"game_id": "fictional-source-contract",
                                 "source_references": [item.to_dict() for item in sources],
                                 "release_candidates": [item.to_dict() for item in candidates],
                                 "reviews": [item.to_dict() for item in reviews],
                                 "relations": list(relations)})


def reviewed_fixture():
    artifact = source_reference()
    page = page_reference()
    candidate = release_candidate(artifact)
    review = reviewed_claims(candidate, artifact, page)
    index = evidence_index([artifact, page], [candidate], [review], [designation(page, artifact)])
    return {"artifact": artifact, "page": page, "candidate": candidate, "review": review, "index": index}
