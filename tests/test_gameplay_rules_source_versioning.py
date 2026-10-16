"""Immutable source metadata and explicit reviewed-version selection contracts.

All successful fixtures are original local test records. A READY result means
metadata is ready for a separately authorized projection review, never execution,
source permission, admission, or an owner decision.
"""
from copy import deepcopy
import hashlib
import json
import socket
import tempfile
import unittest
from unittest.mock import patch

from evidence.contracts import AcquisitionMetadata, Contract, EvidenceArtifact, LicensingMetadata
from evidence.registry import ReferenceDatasetRegistry, RegistryValidationError
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import GameplayRulesSnapshot
from gameplay_rules.source_evidence.contracts import (
    AUTHORITY_RANKS, EVIDENCE_STATES, PERMISSION_OPERATIONS, EvidenceIndex,
    ReleaseCandidate, SourceReference, SourceReview, VersionSelection,
)
from gameplay_rules.source_evidence.selection import select_version
from gameplay_rules_source_fixture import (
    ARTIFACT_BODY, ARTIFACT_URL, AS_OF, BULLETIN_URL, EFFECTIVE_DATE, NEXT_ARTIFACT_URL,
    OBSERVED_AT, PAGE_URL, RULES_VERSION, designation, evidence_index, page_reference,
    permissions, release_candidate, reviewed_claims, reviewed_fixture, source_reference,
    unbound,
)


class GameplayRulesSourceContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = reviewed_fixture()

    def test_five_metadata_contracts_are_distinct_immutable_evidence_contracts(self):
        selection = select_version(self.fixture["index"], scope="current_designation", as_of_date=AS_OF,
                                   review_id=self.fixture["review"].identity)
        objects = [self.fixture[name] for name in ("artifact", "candidate", "review", "index")] + [selection]
        self.assertEqual(len({item.identity for item in objects}), 5)
        for item in objects:
            with self.subTest(type=type(item).__name__):
                self.assertIsInstance(item, Contract)
                item.verify()
                self.assertEqual(type(item).from_json(item.serialize()).to_dict(), item.to_dict())
                self.assertTrue(item.metadata_only)
                self.assertFalse(item.admission_eligible)
                self.assertFalse(item.projection_authorized)
                self.assertNotEqual(item.identity, item.identity_sha256)
                with self.assertRaises((AttributeError, TypeError)):
                    item.metadata_only = False
        changed = self.fixture["artifact"].to_dict()
        changed["permission_status"][PERMISSION_OPERATIONS[0]]["status"] = "ESTABLISHED"
        self.assertEqual(self.fixture["artifact"].permission_status[PERMISSION_OPERATIONS[0]]["status"], "NOT_ESTABLISHED")

    def test_same_metadata_is_deterministic_and_internal_id_is_not_source_version_or_hash(self):
        first, second = source_reference(), source_reference()
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.identity, second.identity)
        self.assertNotEqual(first.identity, first.source_id)
        self.assertNotEqual(first.identity, first.rules_version)
        self.assertNotEqual(first.identity, first.artifact_hash)
        self.assertNotEqual(self.fixture["page"].artifact_hash, first.artifact_hash)

    def test_source_dates_are_distinct_and_unknown_effective_version_remain_null(self):
        item = source_reference(effective_date=None, rules_version=None)
        self.assertIsNone(item.effective_date)
        self.assertIsNone(item.rules_version)
        self.assertEqual(item.observed_at, OBSERVED_AT)
        self.assertEqual(item.discovered_at, OBSERVED_AT)
        self.assertNotEqual(item.observed_at, EFFECTIVE_DATE)

    def test_new_observation_changed_bytes_or_changed_date_creates_new_record_not_overwrite(self):
        original = source_reference()
        for changes in ({"observed_at": "2032-01-07T12:00:00Z"},
                        {"artifact_hash": "sha256:" + hashlib.sha256(b"new original fixture").hexdigest()},
                        {"effective_date": "2032-01-02"}, {"rules_version": "fictional-local-version-2"}):
            with self.subTest(changes=changes):
                changed = source_reference(**changes)
                self.assertNotEqual(original.identity, changed.identity)
                self.assertEqual(original.to_dict(), source_reference().to_dict())

    def test_fixed_metadata_flags_cannot_be_used_as_admission_or_projection_switch(self):
        for key, value in (("metadata_only", False), ("admission_eligible", True), ("projection_authorized", True)):
            body = unbound(self.fixture["artifact"])
            body[key] = value
            with self.subTest(key=key), self.assertRaises(GameplayContractError):
                SourceReference.create(body)

    def test_all_eight_operation_permissions_are_explicit_without_provider_inheritance(self):
        statuses = self.fixture["artifact"].to_dict()["permission_status"]
        self.assertEqual(len(PERMISSION_OPERATIONS), 8)
        self.assertEqual(set(statuses), set(PERMISSION_OPERATIONS))
        self.assertEqual({row["status"] for row in statuses.values()}, {"NOT_ESTABLISHED"})
        for operation in PERMISSION_OPERATIONS:
            body = unbound(self.fixture["artifact"])
            del body["permission_status"][operation]
            with self.subTest(operation=operation), self.assertRaises(GameplayContractError):
                SourceReference.create(body)

    def test_established_permission_requires_specific_evidence_and_conditions(self):
        body = unbound(self.fixture["artifact"])
        operation = PERMISSION_OPERATIONS[0]
        body["permission_status"][operation]["status"] = "ESTABLISHED"
        with self.assertRaises(GameplayContractError):
            SourceReference.create(body)
        body["permission_status"][operation]["evidence_references"] = ["urn:fictional:test:authorship"]
        established = SourceReference.create(body)
        self.assertEqual(established.permission_status[operation]["status"], "ESTABLISHED")
        for other in PERMISSION_OPERATIONS[1:]:
            self.assertEqual(established.permission_status[other]["status"], "NOT_ESTABLISHED")
        body["permission_status"][operation]["status"] = "ESTABLISHED_WITH_CONDITIONS"
        with self.assertRaises(GameplayContractError):
            SourceReference.create(body)

    def test_access_unavailable_is_not_permission_or_prohibition(self):
        for code in (403, 404):
            item = source_reference(accessibility="UNAVAILABLE", access_outcome="HTTP_" + str(code),
                                    http_status=code, effective_date=None, rules_version=None,
                                    artifact_hash=None, byte_length=None, evidence_status="EVIDENCE_UNAVAILABLE")
            with self.subTest(code=code):
                self.assertEqual({row["status"] for row in item.permission_status.values()}, {"NOT_ESTABLISHED"})
                self.assertEqual(list(item.supersedes), [])
                self.assertEqual(list(item.superseded_by), [])
                self.assertIsNone(item.artifact_hash)

    def test_http_failure_cannot_be_represented_as_verified_artifact(self):
        with self.assertRaises(GameplayContractError):
            source_reference(accessibility="UNAVAILABLE", access_outcome="HTTP_403", http_status=403)
        with self.assertRaises(GameplayContractError):
            source_reference(accessibility="AVAILABLE", access_outcome="HTTP_404", http_status=404)

    def test_available_artifact_cannot_conceal_http_403_or_404(self):
        for code in (403, 404):
            with self.subTest(code=code), self.assertRaises(GameplayContractError):
                source_reference(http_status=code)

    def test_source_class_authority_ranks_remain_distinct(self):
        expected = {"COMPREHENSIVE_RULES": "PRIMARY", "UPDATE_BULLETIN": "SECONDARY",
                    "RELEASE_NOTES": "SECONDARY", "RULES_BLOG": "EXPLANATORY",
                    "FORMAT_POLICY": "SEPARATE_FUTURE", "ORACLE": "SEPARATE_FUTURE"}
        for source_class, rank in expected.items():
            with self.subTest(source_class=source_class):
                self.assertEqual(source_reference(source_class=source_class).authority_rank, rank)
        with self.assertRaises(GameplayContractError):
            source_reference(source_class="UPDATE_BULLETIN", authority_rank="PRIMARY")

    def test_rules_source_metadata_never_becomes_executable_snapshot(self):
        for name in ("artifact", "candidate", "review", "index"):
            with self.subTest(name=name), self.assertRaises(GameplayContractError):
                GameplayRulesSnapshot.from_dict(self.fixture[name].to_dict())

    def test_metadata_discovery_does_not_weaken_existing_registry_license_gate(self):
        reference = self.fixture["artifact"]
        licensing = LicensingMetadata("", "unknown", "unknown", "", "")
        capture = AcquisitionMetadata(OBSERVED_AT, OBSERVED_AT, "fictional-local-metadata", ARTIFACT_URL)
        artifact = EvidenceArtifact("fictional-fixture", "rules-source", "fictional-artifact",
                                    reference.artifact_hash.split(":", 1)[1], "text/plain",
                                    reference.byte_length, capture, licensing)
        with tempfile.TemporaryDirectory() as temporary:
            registry = ReferenceDatasetRegistry(temporary)
            with self.assertRaisesRegex(RegistryValidationError, "licensing"):
                registry.register_artifact(artifact)
            self.assertEqual(registry.artifacts(), [])

    def test_no_raw_corpus_headers_credentials_or_executable_fields_in_contract(self):
        for key in ("content", "body", "raw_payload", "headers", "cookies", "authorization", "script"):
            body = unbound(self.fixture["artifact"])
            body[key] = "Original unretained synthetic value"
            with self.subTest(key=key), self.assertRaises(GameplayContractError):
                SourceReference.create(body)
        for reference in ("https://user:secret@magic.wizards.com/en/rules", PAGE_URL + "?token=secret"):
            with self.assertRaises(GameplayContractError):
                source_reference(authoritative_reference=reference)

    def test_public_source_references_reject_queries_fragments_controls_and_ambiguity(self):
        references = (PAGE_URL + "?api_key=fictional-secret", PAGE_URL + "?safe=1",
                      PAGE_URL + "#fragment", PAGE_URL + "\n", PAGE_URL + "\x00",
                      "https://magic.wizards.com\\ambiguous/path")
        for field in ("authoritative_reference", "resolved_reference"):
            for reference in references:
                with self.subTest(field=field, reference=reference), self.assertRaises(GameplayContractError):
                    source_reference(**{field: reference})
        fictional = source_reference(authoritative_reference="urn:mtglab:fictional:source-reference")
        self.assertEqual(fictional.authoritative_reference, "urn:mtglab:fictional:source-reference")

    def test_source_and_release_cannot_claim_implicit_latest_version(self):
        for version in ("latest", "current", "unknown"):
            with self.subTest(version=version), self.assertRaises(GameplayContractError):
                source_reference(rules_version=version)

    def test_changed_or_missing_hash_binding_and_byte_length_are_rejected(self):
        for changes in ({"artifact_hash": None}, {"byte_length": None}, {"artifact_hash": "bad"}, {"byte_length": True}):
            with self.subTest(changes=changes), self.assertRaises(GameplayContractError):
                source_reference(**changes)

    def test_candidate_cannot_substitute_page_hash_or_different_artifact_metadata(self):
        candidate = release_candidate(self.fixture["artifact"], artifact_hash=self.fixture["page"].artifact_hash)
        with self.assertRaises(GameplayContractError):
            evidence_index([self.fixture["artifact"], self.fixture["page"]], [candidate])
        candidate = release_candidate(self.fixture["artifact"], effective_date="2032-02-01")
        with self.assertRaises(GameplayContractError):
            evidence_index([self.fixture["artifact"]], [candidate])

    def test_secondary_documents_cannot_be_registered_as_comprehensive_release(self):
        for source_class in ("UPDATE_BULLETIN", "RELEASE_NOTES", "RULES_BLOG", "FORMAT_POLICY", "ORACLE", "RULES_INDEX"):
            source = source_reference(source_class=source_class)
            candidate = release_candidate(source)
            with self.subTest(source_class=source_class), self.assertRaises(GameplayContractError):
                evidence_index([source], [candidate])

    def test_source_review_is_candidate_and_evidence_bound_not_owner_authorization(self):
        review = self.fixture["review"]
        self.assertEqual(review.status, "REVIEWED")
        self.assertFalse(review.projection_authorized)
        self.assertFalse(review.admission_eligible)
        body = unbound(review)
        body["supported_claims"][0]["source_reference_ids"] = ["sha256:" + "f" * 64]
        with self.assertRaises(GameplayContractError):
            SourceReview.create(body)

    def test_index_missing_source_or_review_dependency_fails_closed(self):
        with self.assertRaises(GameplayContractError):
            evidence_index([self.fixture["page"]], [self.fixture["candidate"]])
        with self.assertRaises(GameplayContractError):
            evidence_index([self.fixture["artifact"]], [self.fixture["candidate"]], [self.fixture["review"]])

    def test_duplicate_json_keys_nonfinite_or_tampered_record_fails_closed(self):
        for raw in ('{"source_id":"one","source_id":"two"}', '{"number":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(GameplayContractError):
                SourceReference.from_json(raw)
        for name, key in (("artifact", "title"), ("candidate", "release_id"), ("review", "reviewer")):
            item = self.fixture[name]
            body = item.to_dict()
            body[key] = "changed original fixture"
            with self.subTest(name=name), self.assertRaises(GameplayContractError):
                type(item).from_dict(body)


class GameplayRulesVersionSelectionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = reviewed_fixture()

    def select(self, index=None, *, scope="current_designation", as_of_date=AS_OF, review=None, **args):
        return select_version(index or self.fixture["index"], scope=scope, as_of_date=as_of_date,
                              review_id=(review or self.fixture["review"]).identity, **args)

    def test_exact_current_designation_selection_requires_explicit_review(self):
        result = self.select()
        self.assertEqual(result.status, "READY_FOR_RULE_PROJECTION")
        self.assertEqual(result.selected_release_candidate_id, self.fixture["candidate"].identity)
        self.assertEqual(result.source_review_id, self.fixture["review"].identity)
        self.assertEqual(result.as_of_date, AS_OF)
        self.assertFalse(result.projection_authorized)
        self.assertFalse(result.admission_eligible)
        self.assertEqual({row["status"] for row in self.fixture["artifact"].permission_status.values()}, {"NOT_ESTABLISHED"})

    def test_missing_explicit_review_is_blocked_not_automatic_newest_selection(self):
        result = select_version(self.fixture["index"], scope="current_designation", as_of_date=AS_OF)
        self.assertEqual(result.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertIsNone(result.selected_release_candidate_id)
        self.assertTrue(result.blocking_reasons)

    def test_explicit_scope_and_as_of_are_required_without_clock_or_latest(self):
        with self.assertRaises(TypeError):
            select_version(self.fixture["index"], scope="current_designation")
        for scope, asof in (("latest", AS_OF), ("current_designation", None), ("as_of_date", "2032-1-6")):
            with self.subTest(scope=scope, asof=asof), self.assertRaises(ValueError):
                self.select(scope=scope, as_of_date=asof)

    def test_as_of_scope_uses_explicit_reviewed_interval_not_max_effective_date(self):
        result = self.select(scope="as_of_date", as_of_date="2032-01-08")
        self.assertEqual(result.status, "READY_FOR_RULE_PROJECTION")
        self.assertEqual(result.selected_release_candidate_id, self.fixture["candidate"].identity)
        result = self.select(scope="as_of_date", as_of_date="2031-12-31")
        self.assertEqual(result.status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_current_designation_cannot_be_extended_to_unreviewed_observation_date(self):
        result = self.select(as_of_date="2032-01-07")
        self.assertEqual(result.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertIsNone(result.selected_release_candidate_id)

    def test_set_release_scope_requires_exact_explicit_release_key(self):
        with self.assertRaises(ValueError):
            self.select(scope="set_release")
        result = self.select(scope="set_release", release_id=self.fixture["candidate"].release_id)
        self.assertEqual(result.status, "READY_FOR_RULE_PROJECTION")
        result = self.select(scope="set_release", release_id="unreviewed-fictional-release")
        self.assertEqual(result.status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_pending_review_cannot_become_selection_authority(self):
        body = unbound(self.fixture["review"])
        body.update(status="PENDING", reviewer=None, reviewed_at=None)
        pending = SourceReview.create(body)
        index = evidence_index([self.fixture["artifact"], self.fixture["page"]], [self.fixture["candidate"]],
                               [pending], [designation(self.fixture["page"], self.fixture["artifact"])])
        self.assertEqual(self.select(index, review=pending).status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_missing_reviewed_artifact_version_or_effective_date_claim_blocks(self):
        for missing in ("artifact_identity", "version", "effective_date", "supersession"):
            review = reviewed_claims(self.fixture["candidate"], self.fixture["artifact"], self.fixture["page"], without=[missing])
            index = evidence_index([self.fixture["artifact"], self.fixture["page"]], [self.fixture["candidate"]],
                                   [review], [designation(self.fixture["page"], self.fixture["artifact"])])
            with self.subTest(missing=missing):
                self.assertEqual(self.select(index, review=review).status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_rules_index_designation_is_separate_from_verified_artifact(self):
        index = evidence_index([self.fixture["artifact"], self.fixture["page"]], [self.fixture["candidate"]],
                               [self.fixture["review"]], [])
        self.assertEqual(self.select(index).status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_unverified_or_unobserved_index_cannot_support_current_designation(self):
        for observed_at in (None, OBSERVED_AT):
            page = page_reference(observed_at=observed_at, evidence_status="DISCOVERED_UNVERIFIED")
            review = reviewed_claims(self.fixture["candidate"], self.fixture["artifact"], page)
            index = evidence_index([self.fixture["artifact"], page], [self.fixture["candidate"]],
                                   [review], [designation(page, self.fixture["artifact"])])
            with self.subTest(observed_at=observed_at):
                self.assertEqual(self.select(index, review=review).status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_official_index_requested_url_cannot_hide_third_party_resolved_reference(self):
        page = page_reference(resolved_reference="https://third-party.invalid/pretending-official")
        review = reviewed_claims(self.fixture["candidate"], self.fixture["artifact"], page)
        index = evidence_index([self.fixture["artifact"], page], [self.fixture["candidate"]],
                               [review], [designation(page, self.fixture["artifact"])])
        self.assertEqual(self.select(index, review=review).status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_reviewed_interval_end_requires_bound_superseding_release(self):
        body = unbound(self.fixture["review"])
        next(claim for claim in body["supported_claims"] if claim["claim"] == "as_of_scope")["value"]["valid_until"] = "2032-02-01"
        review = SourceReview.create(body)
        index = evidence_index([self.fixture["artifact"], self.fixture["page"]], [self.fixture["candidate"]],
                               [review], [designation(self.fixture["page"], self.fixture["artifact"])])
        result = self.select(index, review=review, scope="as_of_date", as_of_date="2032-01-10")
        self.assertEqual(result.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertIn("REVIEWED_INTERVAL_END_NOT_BOUND_TO_SUCCESSOR", result.blocking_reasons)

    def test_unavailable_index_or_primary_artifact_cannot_support_current_selection(self):
        source = source_reference(accessibility="UNAVAILABLE", access_outcome="HTTP_403", http_status=403,
                                  effective_date=None, rules_version=None, artifact_hash=None, byte_length=None,
                                  evidence_status="EVIDENCE_UNAVAILABLE")
        index = evidence_index([source], [])
        result = select_version(index, scope="current_designation", as_of_date=AS_OF)
        self.assertEqual(result.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertIsNone(result.selected_release_candidate_id)
        self.assertTrue(any("UNAVAILABLE" in reason for reason in result.blocking_reasons))

    def test_secondary_bulletin_cannot_replace_primary_rules_authority(self):
        bulletin = source_reference(source_class="UPDATE_BULLETIN", source_id="fixture-update",
                                    authoritative_reference=BULLETIN_URL, resolved_reference=BULLETIN_URL)
        index = evidence_index([self.fixture["artifact"], self.fixture["page"], bulletin], [self.fixture["candidate"]],
                               [self.fixture["review"]], [designation(self.fixture["page"], self.fixture["artifact"]),
                               {"relation": "DESCRIBES_CHANGES_FOR", "from_reference_id": bulletin.identity,
                                "to_reference_id": self.fixture["artifact"].identity, "evidence_reference_ids": [bulletin.identity]}])
        result = self.select(index)
        self.assertEqual(result.status, "READY_FOR_RULE_PROJECTION")
        self.assertEqual(result.selected_release_candidate_id, self.fixture["candidate"].identity)
        self.assertNotEqual(result.selected_release_candidate_id, bulletin.identity)

    def test_conflicting_logical_release_id_does_not_choose_newest_or_one_hash(self):
        alternative = source_reference(source_id="fixture-alternative-bytes",
                                       artifact_hash="sha256:" + hashlib.sha256(b"different original fixture").hexdigest())
        other = release_candidate(alternative)
        index = evidence_index([self.fixture["artifact"], self.fixture["page"], alternative],
                               [self.fixture["candidate"], other], [self.fixture["review"]],
                               [designation(self.fixture["page"], self.fixture["artifact"])])
        result = self.select(index)
        self.assertEqual(result.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertIn("CONFLICTING_RELEASE_IDENTITY", result.blocking_reasons)

    def test_authored_release_alias_cannot_hide_conflicting_source_version_bytes(self):
        alternative = source_reference(source_id="fixture-conflicting-version-bytes",
                                       artifact_hash="sha256:" + hashlib.sha256(b"changed fictional version bytes").hexdigest())
        candidate = release_candidate(alternative, release_id="different-authored-release-alias")
        index = evidence_index([self.fixture["artifact"], self.fixture["page"], alternative],
                               [self.fixture["candidate"], candidate], [self.fixture["review"]],
                               [designation(self.fixture["page"], self.fixture["artifact"])])
        result = self.select(index)
        self.assertEqual(result.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertTrue(any("CONFLICTING" in reason for reason in result.blocking_reasons))

    def test_multiple_reviewed_candidates_for_same_scope_are_ambiguous(self):
        alternative = source_reference(source_id="fixture-alternative-release", rules_version="fictional-other-version")
        candidate = release_candidate(alternative, release_id="fictional-release-other")
        other_review = reviewed_claims(candidate, alternative, self.fixture["page"])
        body = unbound(self.fixture["review"])
        body["source_reference_ids"].append(alternative.identity)
        body["release_candidate_ids"].append(candidate.identity)
        body["supported_claims"].extend(other_review.to_dict()["supported_claims"])
        combined = SourceReview.create(body)
        index = evidence_index([self.fixture["artifact"], self.fixture["page"], alternative],
                               [self.fixture["candidate"], candidate], [combined],
                               [designation(self.fixture["page"], self.fixture["artifact"]), designation(self.fixture["page"], alternative)])
        result = self.select(index, review=combined)
        self.assertEqual(result.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertIsNone(result.selected_release_candidate_id)
        self.assertIn("AMBIGUOUS_REVIEWED_SCOPE", result.blocking_reasons)

    def test_supersession_is_explicit_and_preserves_old_interpretability(self):
        newer = source_reference(source_id="fixture-second-release", authoritative_reference=NEXT_ARTIFACT_URL,
                                 resolved_reference=NEXT_ARTIFACT_URL, effective_date="2032-02-01",
                                 rules_version="fictional-local-version-2", supersedes=[self.fixture["artifact"].identity])
        candidate = release_candidate(newer, release_id="fictional-release-2", supersedes=[self.fixture["candidate"].identity])
        review = reviewed_claims(candidate, newer, self.fixture["page"])
        index = evidence_index([self.fixture["artifact"], self.fixture["page"], newer],
                               [self.fixture["candidate"], candidate], [self.fixture["review"], review],
                               [designation(self.fixture["page"], self.fixture["artifact"]), designation(self.fixture["page"], newer)])
        historic = self.select(index, scope="as_of_date", as_of_date="2032-01-10")
        self.assertEqual(historic.status, "READY_FOR_RULE_PROJECTION")
        self.assertEqual(historic.selected_release_candidate_id, self.fixture["candidate"].identity)
        superseded = self.select(index, scope="as_of_date", as_of_date="2032-02-02")
        self.assertEqual(superseded.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertIn("SUPERSEDED_AS_OF_SCOPE", superseded.blocking_reasons)
        current = self.select(index, scope="as_of_date", as_of_date="2032-02-02", review=review)
        self.assertEqual(current.status, "READY_FOR_RULE_PROJECTION")
        self.assertEqual(set(current.lineage_candidate_ids), {candidate.identity, self.fixture["candidate"].identity})

    def test_404_observation_is_not_supersession_evidence(self):
        unavailable = source_reference(source_id="fixture-old-url-404", accessibility="UNAVAILABLE",
                                        access_outcome="HTTP_404", http_status=404, effective_date=None,
                                        rules_version=None, artifact_hash=None, byte_length=None, evidence_status="EVIDENCE_UNAVAILABLE")
        index = evidence_index([self.fixture["artifact"], self.fixture["page"], unavailable],
                               [self.fixture["candidate"]], [self.fixture["review"]],
                               [designation(self.fixture["page"], self.fixture["artifact"])])
        result = self.select(index)
        self.assertEqual(result.status, "READY_FOR_RULE_PROJECTION")
        self.assertEqual(set(result.lineage_candidate_ids), {self.fixture["candidate"].identity})

    def test_selection_and_index_remain_deterministic_without_network_or_wall_clock(self):
        with patch.object(socket, "socket", side_effect=AssertionError("No network")), \
             patch("time.time", side_effect=AssertionError("No clock")):
            first, second = self.select(), self.select()
        self.assertEqual(first.identity, second.identity)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(EvidenceIndex.from_json(self.fixture["index"].serialize()).identity, self.fixture["index"].identity)
        changed = first.to_dict()
        changed["as_of_date"] = "2032-01-07"
        with self.assertRaises(GameplayContractError):
            VersionSelection.from_dict(changed)
