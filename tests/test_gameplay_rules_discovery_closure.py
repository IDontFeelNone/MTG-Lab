"""Reconciled supplied observations and explicit local verification reviews."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from evidence.contracts import deterministic_json
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.source_evidence.artifacts import (
    ArtifactVerificationResult, FICTIONAL_PROFILE_VERSION,
    build_artifact_verification_request, verify_local_artifact)
from gameplay_rules.source_evidence.closure import (
    DiscoverySelection, DiscoverySourceReview, ObservedReleaseCandidate,
    discovery_package_identity, select_discovered_release, verify_discovery_package)
from gameplay_rules.source_evidence.contracts import SourceReference
from gameplay_rules.source_evidence.observations import ExternalSourceObservation
from gameplay_rules.source_evidence.review import verify_review_package
from gameplay_rules_source_fixture import page_reference, unbound
from test_gameplay_rules_external_observation import observation_body


ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "reference-reviews/gameplay-rules-source-versioning"
PACKAGE = ROOT / "reference-reviews/gameplay-rules-release-discovery-closure"
PREVIOUS_ID = "sha256:63c904317a6b8406a759950074175acf8a1cee0b9d20b8aa9e37a62382eeeca9"


def fictional_chain():
    source = page_reference()
    body = observation_body(source)
    body.update(game_id=source.game_id, observer_class="PROJECT_AUTHORED_FICTIONAL_OBSERVATION",
        observed_on="2032-04-01", effective_date="2032-03-14",
        currentness={"claim": "CURRENT_DESIGNATION_OBSERVED", "as_of_date": "2032-04-01"},
        observed_markers=[{"marker_id": "fictional.71", "heading": "Empower Beacon"}])
    body["observed_designation"].update(title="Fictional Duel Comprehensive Rules", filename_date_token="20320314")
    body["relation_evidence"][0].update(publication_date="2032-03-01", marker_id="fictional.71", heading="Empower Beacon")
    observation = ExternalSourceObservation.create(body)
    candidate = ObservedReleaseCandidate.from_observation(observation)
    request = build_artifact_verification_request(game_id=source.game_id,
        release_candidate_id=candidate.identity, discovery_source_reference_id=source.identity,
        observation_id=observation.identity, verification_profile_version=FICTIONAL_PROFILE_VERSION)
    review = DiscoverySourceReview.create({"game_id": source.game_id, "previous_package_id": PREVIOUS_ID,
        "source_reference_id": source.identity, "observation_id": observation.identity,
        "release_candidate_id": candidate.identity, "verification_request_id": request.identity,
        "artifact_verification_id": None, "reviewed_on": "2032-04-01", "reviewer": "Fictional local reviewer",
        "status": "REVIEWED", "supported_claims": ["official_designation", "effective_date",
            "currentness_as_of", "identified_update_incorporation"],
        "limitations": ["Original fictional fixture, no source rights or projection authorization"]})
    return dict(candidate=candidate, observation=observation, source_reference=source,
                review=review, request=request, as_of_date="2032-04-01")


class GameplayRulesDiscoveryClosureTests(unittest.TestCase):
    def load(self, name): return json.loads((PACKAGE / name).read_bytes())

    def copy_package(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "metadata"
        shutil.copytree(PACKAGE, path)
        return path

    def rewrite(self, root, name, change, *, rebind=False):
        value = json.loads((root / name).read_bytes())
        change(value)
        (root / name).write_text(deterministic_json(value) + "\n")
        if rebind:
            manifest = json.loads((root / "manifest.json").read_bytes())
            raw = (root / name).read_bytes()
            manifest["files"][name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            manifest.pop("package_id")
            manifest["package_id"] = discovery_package_identity(manifest)
            (root / "manifest.json").write_text(deterministic_json(manifest) + "\n")

    def verification(self, chain):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "fictional-20320314-rules.txt"
        path.write_bytes(b"Fictional Duel Comprehensive Rules\nRules effective as of March 14, 2032\nfictional.71 Empower Beacon\nOriginal test-only source; no real rules.\n")
        request = chain["request"]
        return verify_local_artifact(path, request, expected_request_id=request.identity,
            expected_release_candidate_id=chain["candidate"].identity,
            expected_discovery_source_reference_id=chain["source_reference"].identity,
            game_id=chain["candidate"].game_id)

    def rebind(self, chain, *, observation_body=None, source=None, expected_hash=None):
        """Author a consistent fictional chain so failures test the changed fact."""
        source = chain["source_reference"] if source is None else source
        body = unbound(chain["observation"]) if observation_body is None else observation_body
        body["source_reference_id"] = source.identity
        observation = ExternalSourceObservation.create(body)
        candidate = ObservedReleaseCandidate.from_observation(observation)
        request = build_artifact_verification_request(game_id=source.game_id,
            release_candidate_id=candidate.identity, discovery_source_reference_id=source.identity,
            observation_id=observation.identity, verification_profile_version=FICTIONAL_PROFILE_VERSION,
            expected_artifact_hash=expected_hash)
        review = unbound(chain["review"])
        review.update(source_reference_id=source.identity, observation_id=observation.identity,
            release_candidate_id=candidate.identity, verification_request_id=request.identity,
            artifact_verification_id=None)
        chain.update(source_reference=source, observation=observation, candidate=candidate,
                     request=request, review=DiscoverySourceReview.create(review))

    def reviewed_verification(self, chain, **changes):
        body = unbound(self.verification(chain))
        body.update(changes)
        verification = ArtifactVerificationResult.create(body)
        review = unbound(chain["review"])
        review["artifact_verification_id"] = verification.identity
        for claim in ("local_artifact_identity", "local_artifact_source_correspondence"):
            if claim not in review["supported_claims"]:
                review["supported_claims"].append(claim)
        chain["review"] = DiscoverySourceReview.create(review)
        return verification

    def test_previous_fixed_package_remains_exact_and_unavailable(self):
        self.assertEqual(verify_review_package(PREVIOUS)["package_id"], PREVIOUS_ID)
        index = json.loads((PREVIOUS / "source-inventory.json").read_bytes())
        source = index["source_references"][0]
        self.assertEqual(source["access_outcome"], "ACCESS_UNAVAILABLE")
        self.assertIsNone(source["http_status"])
        self.assertEqual(index["release_candidates"], [])
        self.assertEqual(len(list(PREVIOUS.iterdir())), 8)

    def test_retained_metadata_verifies_deterministically_and_offline(self):
        with patch("socket.create_connection", side_effect=AssertionError("no network")):
            result = verify_discovery_package(PACKAGE, previous_root=PREVIOUS)
            self.assertEqual(result, verify_discovery_package(PACKAGE, previous_root=PREVIOUS))
        self.assertEqual(result["previous_package_id"], PREVIOUS_ID)
        self.assertEqual(result["blocking_reasons"], ["OFFICIAL_ARTIFACT_BYTES_NOT_VERIFIED"])
        self.assertEqual(result["status"], "NOT_READY_FOR_RULE_PROJECTION")
        self.assertFalse(result["projection_authorized"])

    def test_retained_currentness_release_and_narrow_marker_are_explicit(self):
        observation = self.load("pm-observation.json")
        selection = self.load("current-selection.json")
        self.assertEqual(observation["observer_class"], "PM_SUPPLIED_FIRST_PARTY_OBSERVATION")
        self.assertEqual(observation["observed_designation"]["filename_date_token"], "20260925")
        self.assertEqual(observation["observed_designation"]["date_token_artifact_types"], ["PDF", "TXT"])
        self.assertEqual(observation["observed_markers"], [{"marker_id": "701.71", "heading": "Empower Jace"}])
        self.assertTrue(observation["relation_evidence"][0]["at_least_identified_update_incorporated"])
        self.assertFalse(observation["relation_evidence"][0]["full_bulletin_diff_verified"])
        self.assertEqual(selection["as_of_date"], "2026-10-16")
        self.assertEqual(selection["effective_date"], "2026-09-25")
        self.assertEqual(selection["currentness_status"], "CURRENT_DESIGNATION_OBSERVED_AS_OF")
        for key in ("artifact_hash", "byte_length", "artifact_verification_id"): self.assertIsNone(selection[key])
        self.assertFalse(selection["codex_independently_fetched"])
        self.assertEqual(selection["artifact_evidence_state"], "METADATA_ONLY")

    def test_request_is_exact_handoff_without_invented_url_or_basename(self):
        candidate = self.load("release-candidate.json")
        request = self.load("artifact-verification-request.json")
        self.assertIsNone(candidate["artifact_reference"])
        self.assertIsNone(candidate["artifact_filename"])
        self.assertIsNone(candidate["rules_version"])
        self.assertEqual(request["release_candidate_id"], candidate["release_candidate_id"])
        self.assertEqual(request["artifact_filename_pattern"], "*20260925*.txt")
        self.assertIsNone(request["expected_artifact_hash"])
        self.assertFalse(request["content_retained"])
        self.assertFalse(request["source_body_copy_allowed"])

    def test_no_ready_without_exact_bytes_even_with_reviewed_metadata(self):
        chain = fictional_chain()
        selection = select_discovered_release(**chain)
        self.assertEqual(list(selection.blocking_reasons), ["OFFICIAL_ARTIFACT_BYTES_NOT_VERIFIED"])

    def test_successful_verification_still_requires_explicit_review_of_result(self):
        chain = fictional_chain()
        verification = self.verification(chain)
        selection = select_discovered_release(**chain, verification=verification)
        self.assertEqual(set(selection.blocking_reasons), {"LOCAL_ARTIFACT_VERIFICATION_REVIEW_REQUIRED",
            "LOCAL_ARTIFACT_SOURCE_CORRESPONDENCE_REVIEW_REQUIRED"})
        self.assertFalse(selection.projection_authorized)

    def test_future_reviewed_same_artifact_can_be_ready_without_authorization(self):
        chain = fictional_chain()
        verification = self.verification(chain)
        body = unbound(chain["review"])
        body["artifact_verification_id"] = verification.identity
        body["supported_claims"].extend(["local_artifact_identity", "local_artifact_source_correspondence"])
        chain["review"] = DiscoverySourceReview.create(body)
        selection = select_discovered_release(**chain, verification=verification)
        self.assertEqual(selection.status, "READY_FOR_RULE_PROJECTION")
        self.assertEqual(selection.artifact_hash, verification.artifact_hash)
        self.assertEqual(selection.byte_length, verification.byte_length)
        self.assertEqual(selection, select_discovered_release(**chain, verification=verification))
        self.assertFalse(selection.projection_authorized)
        self.assertFalse(selection.admission_eligible)
        self.assertEqual(selection.source_policy_clearance, "not_granted")
        self.assertFalse(selection.codex_independently_fetched)

    def test_local_identity_review_without_official_source_correspondence_is_not_ready(self):
        chain = fictional_chain()
        verification = self.verification(chain)
        body = unbound(chain["review"])
        body["artifact_verification_id"] = verification.identity
        body["supported_claims"].append("local_artifact_identity")
        chain["review"] = DiscoverySourceReview.create(body)
        selection = select_discovered_release(**chain, verification=verification)
        self.assertEqual(list(selection.blocking_reasons), ["LOCAL_ARTIFACT_SOURCE_CORRESPONDENCE_REVIEW_REQUIRED"])

    def test_future_currentness_is_not_inferred_from_last_observation(self):
        chain = fictional_chain()
        chain["as_of_date"] = "2032-04-02"
        self.assertIn("CURRENTNESS_SCOPE_NOT_OBSERVED", select_discovered_release(**chain).blocking_reasons)

    def test_missing_claim_pending_review_and_wrong_source_authority_do_not_select(self):
        for mode in ("claims", "review", "authority"):
            chain = fictional_chain()
            if mode == "authority":
                body = unbound(chain["source_reference"])
                body["authoritative_reference"] = "https://example.invalid/rules"
                new_source = SourceReference.create(body)
                # Changing the source also requires a new observation/candidate,
                # so the unrebound request is rejected rather than following it.
                chain["source_reference"] = new_source
                with self.subTest(mode=mode), self.assertRaises(GameplayContractError): select_discovered_release(**chain)
                continue
            body = unbound(chain["review"])
            if mode == "claims": body["supported_claims"].remove("effective_date")
            else: body["status"] = "PENDING"
            chain["review"] = DiscoverySourceReview.create(body)
            self.assertNotEqual(select_discovered_release(**chain).status, "READY_FOR_RULE_PROJECTION")

    def test_cross_snapshot_result_or_changed_observation_cannot_rebind(self):
        for field in ("observation_id", "release_candidate_id", "request_id", "discovery_source_reference_id"):
            chain = fictional_chain()
            body = unbound(self.verification(chain))
            body[field] = "sha256:" + "a" * 64
            verification = ArtifactVerificationResult.create(body)
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                select_discovered_release(**chain, verification=verification)

    def test_supplied_digest_or_length_conflict_blocks_even_after_explicit_review(self):
        for field in ("artifact_hash", "byte_length"):
            chain = fictional_chain()
            original = self.verification(chain)
            body = unbound(chain["observation"])
            body.update(artifact_hash=original.artifact_hash, byte_length=original.byte_length)
            body[field] = "sha256:" + "f" * 64 if field == "artifact_hash" else original.byte_length + 1
            self.rebind(chain, observation_body=body)
            verification = self.reviewed_verification(chain)
            with self.subTest(field=field):
                selection = select_discovered_release(**chain, verification=verification)
                self.assertEqual(list(selection.blocking_reasons), ["EXTERNAL_ARTIFACT_IDENTITY_CONFLICT"])
                self.assertEqual(selection.status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_source_review_cannot_predate_locally_observed_bytes(self):
        chain = fictional_chain()
        verification = self.reviewed_verification(chain, observed_at="2032-04-02T12:00:00Z")
        selection = select_discovered_release(**chain, verification=verification)
        self.assertEqual(list(selection.blocking_reasons), ["SOURCE_REVIEW_PREDATES_VERIFICATION"])
        self.assertEqual(selection.status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_observed_title_and_marker_must_match_the_fixed_verification_request(self):
        for field in ("title", "marker", "dated_artifact_types"):
            chain = fictional_chain()
            body = unbound(chain["observation"])
            if field == "title":
                body["observed_designation"]["title"] = "Different Fictional Rules"
            elif field == "marker":
                body["observed_markers"][0]["heading"] = "Different Fictional Heading"
                body["relation_evidence"][0]["heading"] = "Different Fictional Heading"
            else:
                body["observed_designation"]["date_token_artifact_types"] = ["PDF"]
            self.rebind(chain, observation_body=body)
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                select_discovered_release(**chain)

    def test_rehashed_success_cannot_bypass_an_expected_artifact_digest(self):
        chain = fictional_chain()
        self.rebind(chain, expected_hash="sha256:" + "f" * 64)
        self.assertEqual(self.verification(chain).status, "HASH_MISMATCH")
        verification = self.reviewed_verification(chain,
            status="VERIFIED_EXPECTED_ARTIFACT",
            independent_verification_status="ARTIFACT_BYTES_VERIFIED_LOCALLY")
        with self.assertRaises(GameplayContractError):
            select_discovered_release(**chain, verification=verification)

    def test_altered_verification_profile_is_rejected_before_selection(self):
        body = unbound(self.verification(fictional_chain()))
        body["verification_profile_id"] = "sha256:" + "f" * 64
        with self.assertRaises(GameplayContractError): ArtifactVerificationResult.create(body)

    def test_wrong_request_cannot_become_valid_by_rebinding_only_the_review(self):
        chain = fictional_chain()
        request = build_artifact_verification_request(game_id=chain["candidate"].game_id,
            release_candidate_id=chain["candidate"].identity,
            discovery_source_reference_id=chain["source_reference"].identity,
            observation_id="sha256:" + "f" * 64,
            verification_profile_version=FICTIONAL_PROFILE_VERSION)
        review = unbound(chain["review"])
        review["verification_request_id"] = request.identity
        chain.update(request=request, review=DiscoverySourceReview.create(review))
        with self.assertRaises(GameplayContractError): select_discovered_release(**chain)

    def test_nondefault_official_host_port_does_not_establish_authority(self):
        chain = fictional_chain()
        source = unbound(chain["source_reference"])
        source["authoritative_reference"] = "https://magic.wizards.com:8443/en/rules"
        self.rebind(chain, source=SourceReference.create(source))
        verification = self.reviewed_verification(chain)
        selection = select_discovered_release(**chain, verification=verification)
        self.assertEqual(list(selection.blocking_reasons), ["OFFICIAL_RULES_INDEX_REQUIRED"])
        self.assertEqual(selection.status, "NOT_READY_FOR_RULE_PROJECTION")

    def test_review_cannot_refer_to_an_absent_verification(self):
        chain = fictional_chain()
        body = unbound(chain["review"])
        body["artifact_verification_id"] = "sha256:" + "b" * 64
        chain["review"] = DiscoverySourceReview.create(body)
        with self.assertRaises(GameplayContractError): select_discovered_release(**chain)

    def test_untyped_or_changed_candidate_fails_closed(self):
        chain = fictional_chain()
        chain["candidate"] = chain["candidate"].to_dict()
        with self.assertRaises(GameplayContractError): select_discovered_release(**chain)
        chain = fictional_chain()
        body = unbound(chain["candidate"])
        body["effective_date"] = "2032-03-15"
        chain["candidate"] = ObservedReleaseCandidate.create(body)
        with self.assertRaises(GameplayContractError): select_discovered_release(**chain)

    def test_package_relocation_preserves_identity_without_body_copy(self):
        self.assertEqual(verify_discovery_package(self.copy_package(), previous_root=PREVIOUS),
                         verify_discovery_package(PACKAGE, previous_root=PREVIOUS))

    def test_tampered_missing_extra_and_symlink_metadata_fail_closed(self):
        for mode in ("tamper", "missing", "extra", "symlink"):
            root = self.copy_package()
            if mode == "tamper": (root / "readiness.json").write_bytes(b"{}")
            elif mode == "missing": (root / "readiness.json").unlink()
            elif mode == "extra": (root / "source.txt").write_text("forbidden extra body")
            else:
                (root / "readiness.json").unlink()
                (root / "readiness.json").symlink_to(PACKAGE / "readiness.json")
            with self.subTest(mode=mode), self.assertRaises(GameplayContractError):
                verify_discovery_package(root, previous_root=PREVIOUS)

    def test_rehash_cannot_upgrade_readiness_permissions_or_add_corpus_field(self):
        for field, value in (("status", "READY_FOR_RULE_PROJECTION"),
                ("all_source_operation_states", "ESTABLISHED"), ("source_body", "unretained source")):
            root = self.copy_package()
            self.rewrite(root, "readiness.json", lambda row: row.update({field: value}), rebind=True)
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                verify_discovery_package(root, previous_root=PREVIOUS)

    def test_no_real_verification_receipt_or_body_retained_and_permissions_unchanged(self):
        self.assertEqual({p.name for p in PACKAGE.iterdir()}, {"pm-observation.json", "release-candidate.json",
            "artifact-verification-request.json", "source-review.json", "current-selection.json", "readiness.json", "manifest.json"})
        self.assertLess(sum(p.stat().st_size for p in PACKAGE.iterdir()), 20_000)
        self.assertFalse(self.load("readiness.json")["real_rules_executable"])
        matrix = json.loads((PREVIOUS / "permission-matrix.json").read_bytes())
        for row in matrix["components"]:
            self.assertEqual({p["status"] for p in row["permission_status"].values()}, {"NOT_ESTABLISHED"})
        for path in PACKAGE.iterdir():
            self.assertEqual(path.suffix, ".json")
            self.assertNotIn("%PDF", path.read_text())


if __name__ == "__main__": unittest.main()
