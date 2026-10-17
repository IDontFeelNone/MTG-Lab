"""Reviewed byte identity is evidence readiness, never rule/source authority.

The supplied official document is deliberately not available to public tests.
Successful verification is exercised with project-authored fictional text; the
real retained package is verified solely through its bounded metadata chain.
"""
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from evidence.contracts import deterministic_json
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.source_evidence.artifact_review import (
    ArtifactCorrespondenceReview, correspondence_checks, evaluated_artifact,
    package_identity, select_reviewed_artifact, verify_artifact_review_package)
from gameplay_rules.source_evidence.artifacts import (
    ArtifactVerificationResult, verify_local_artifact)
from gameplay_rules.source_evidence.closure import (
    DiscoverySourceReview, select_discovered_release, verify_discovery_package)
from gameplay_rules.source_evidence.review import verify_review_package
from gameplay_rules_source_fixture import unbound
from test_gameplay_rules_artifact_verifier import FICTIONAL_TEXT
from test_gameplay_rules_discovery_closure import fictional_chain


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reference-reviews/gameplay-rules-source-versioning"
DISCOVERY = ROOT / "reference-reviews/gameplay-rules-release-discovery-closure"
PACKAGE = ROOT / "reference-reviews/gameplay-rules-artifact-verification"
SOURCE_ID = "sha256:63c904317a6b8406a759950074175acf8a1cee0b9d20b8aa9e37a62382eeeca9"
DISCOVERY_ID = "sha256:3e6c83491ade17d6e5cce5b9970eca5d59f8e0955f50e4f65234ad499d941e7d"
REQUEST_ID = "sha256:c5c8746050b9d12bfce010c120e56d859301f6df07f2ca54c20f352e682997f5"
CANDIDATE_ID = "sha256:9a6cabf4d5780f436669d2945341935bdf13fe35f8009f681aa6a0bf4be34d62"
REFERENCE_ID = "sha256:60d5449dc03af1e5b233eef9a5da6639ea23f5706afbf17fe3f0ebcf7d9a0f4f"
OBSERVATION_ID = "sha256:4452ad76e7902b183294d5c60b829e311e98da213511e6d51a4358a94efd005c"
RESULT_ID = "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3"
ARTIFACT_HASH = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
OTHER = "sha256:" + "f" * 64


class GameplayRulesArtifactCorrespondenceTests(unittest.TestCase):
    def fixture(self):
        chain = fictional_chain()
        temporary = tempfile.TemporaryDirectory(prefix="mtglab-fictional-correspondence-")
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "fictional-20320314.txt"
        path.write_bytes(FICTIONAL_TEXT)
        result = self.verify_fictional(path, chain)
        owner = {"provenance_class": "OWNER_SUPPLIED_ARTIFACT_PROVENANCE",
            "statement": "Fictional owner supplied original test-only bytes from the designated fictional source.",
            "downloaded_from_designated_official_txt": True, "not_intentionally_modified": True,
            "source_reference_id": chain["source_reference"].identity,
            "pm_observation_id": chain["observation"].identity,
            "artifact_family": chain["candidate"].artifact_family, "artifact_type": "TXT",
            "effective_date": chain["candidate"].effective_date,
            "codex_independent_network_verification": False, "cryptographic_authentication": False,
            "source_permission_established": False, "local_path_retained": False}
        source_review = unbound(chain["review"])
        source_review.update(previous_package_id=DISCOVERY_ID, artifact_verification_id=result.identity)
        source_review["supported_claims"].extend(["local_artifact_identity", "local_artifact_source_correspondence"])
        body = {"game_id": chain["candidate"].game_id, "prior_source_package_id": SOURCE_ID,
            "prior_discovery_package_id": DISCOVERY_ID, "prior_review_id": chain["review"].identity,
            "verification_result_id": result.identity, "owner_provenance": owner,
            "evaluated_artifact": evaluated_artifact(result, chain["request"]),
            "checks": correspondence_checks(result, chain["request"], chain["candidate"], owner),
            "source_review": DiscoverySourceReview.create(source_review).to_dict(),
            "limitations": ["Fictional origin statement is not independent network authentication or source permission."],
            "content_retained": False, "source_body_copied": False, "network_used": False}
        return chain, result, body, path

    def verify_fictional(self, path, chain, **changes):
        request = chain["request"]
        return verify_local_artifact(path, request, expected_request_id=request.identity,
            expected_release_candidate_id=chain["candidate"].identity,
            expected_discovery_source_reference_id=chain["source_reference"].identity,
            game_id=chain["candidate"].game_id, observed_at="2032-04-01T12:00:00Z", **changes)

    def select(self, chain, result, body, **changes):
        args = dict(as_of_date=chain["as_of_date"], prior_source_package_id=SOURCE_ID,
            prior_discovery_package_id=DISCOVERY_ID, prior_review_id=chain["review"].identity)
        args.update(changes)
        review = ArtifactCorrespondenceReview.create(body)
        return select_reviewed_artifact(review, result, chain["candidate"], chain["observation"],
            chain["source_reference"], chain["request"], **args)

    def test_successful_fictional_verification_requires_explicit_review(self):
        chain, result, body, _ = self.fixture()
        unreviewed = select_discovered_release(**chain, verification=result)
        self.assertEqual(unreviewed.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertIn("LOCAL_ARTIFACT_SOURCE_CORRESPONDENCE_REVIEW_REQUIRED", unreviewed.blocking_reasons)
        selected = self.select(chain, result, body)
        self.assertEqual(selected.status, "READY_FOR_RULE_PROJECTION")
        self.assertEqual(selected.artifact_hash, result.artifact_hash)
        self.assertEqual(selected.byte_length, len(FICTIONAL_TEXT))
        self.assertFalse(selected.projection_authorized)
        self.assertFalse(selected.admission_eligible)
        self.assertEqual(selected.source_policy_clearance, "not_granted")

    def test_fictional_chain_needs_explicit_file_without_network_or_retention(self):
        chain, result, body, path = self.fixture()
        with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")), \
             patch("pathlib.Path.write_bytes", side_effect=AssertionError("source copy forbidden")), \
             patch("pathlib.Path.write_text", side_effect=AssertionError("source copy forbidden")):
            reproduced = self.verify_fictional(path, chain)
            selected = self.select(chain, reproduced, body)
        self.assertEqual(result.to_dict(), reproduced.to_dict())
        self.assertEqual(selected.status, "READY_FOR_RULE_PROJECTION")
        missing = self.verify_fictional(path.with_name("missing-20320314.txt"), chain)
        self.assertEqual(missing.status, "ARTIFACT_UNAVAILABLE")

    def test_same_explicit_inputs_reproduce_identity_and_changed_bytes_do_not(self):
        chain, result, body, path = self.fixture()
        self.assertEqual(result.artifact_hash, "sha256:" + hashlib.sha256(FICTIONAL_TEXT).hexdigest())
        self.assertEqual(self.verify_fictional(path, chain).identity, result.identity)
        self.assertEqual(self.select(chain, result, body), self.select(chain, result, body))
        path.write_bytes(FICTIONAL_TEXT + b"Additional original fictional note.\n")
        changed = self.verify_fictional(path, chain)
        self.assertNotEqual(changed.identity, result.identity)
        self.assertNotEqual(changed.artifact_hash, result.artifact_hash)
        with self.assertRaises(GameplayContractError): self.select(chain, changed, body)

    def test_origin_missing_or_modified_cannot_claim_source_correspondence(self):
        for field in ("downloaded_from_designated_official_txt", "not_intentionally_modified"):
            chain, result, body, _ = self.fixture()
            body["owner_provenance"][field] = False
            body["checks"] = correspondence_checks(result, chain["request"], chain["candidate"], body["owner_provenance"])
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                ArtifactCorrespondenceReview.create(body)
            source_review = unbound(DiscoverySourceReview.from_dict(body["source_review"]))
            source_review["supported_claims"].remove("local_artifact_source_correspondence")
            body["source_review"] = DiscoverySourceReview.create(source_review).to_dict()
            selected = self.select(chain, result, body)
            self.assertEqual(selected.status, "NOT_READY_FOR_RULE_PROJECTION")
            self.assertIn("LOCAL_ARTIFACT_SOURCE_CORRESPONDENCE_REVIEW_REQUIRED", selected.blocking_reasons)

    def test_source_review_without_identity_claim_is_not_ready(self):
        chain, result, body, _ = self.fixture()
        source_review = unbound(DiscoverySourceReview.from_dict(body["source_review"]))
        source_review["supported_claims"].remove("local_artifact_identity")
        body["source_review"] = DiscoverySourceReview.create(source_review).to_dict()
        selected = self.select(chain, result, body)
        self.assertIn("LOCAL_ARTIFACT_VERIFICATION_REVIEW_REQUIRED", selected.blocking_reasons)

    def test_currentness_does_not_extend_past_reviewed_date(self):
        chain, result, body, _ = self.fixture()
        selected = self.select(chain, result, body, as_of_date="2032-04-02")
        self.assertEqual(selected.status, "NOT_READY_FOR_RULE_PROJECTION")
        self.assertIn("CURRENTNESS_SCOPE_NOT_OBSERVED", selected.blocking_reasons)

    def test_missing_explicit_verification_timestamp_cannot_be_reviewed(self):
        chain, result, body, _ = self.fixture()
        changed = unbound(result)
        changed["observed_at"] = None
        result = ArtifactVerificationResult.create(changed)
        body["verification_result_id"] = result.identity
        body["evaluated_artifact"] = evaluated_artifact(result, chain["request"])
        source_review = unbound(DiscoverySourceReview.from_dict(body["source_review"]))
        source_review["artifact_verification_id"] = result.identity
        body["source_review"] = DiscoverySourceReview.create(source_review).to_dict()
        with self.assertRaises(GameplayContractError): self.select(chain, result, body)

    def test_review_prose_is_bounded_metadata_not_a_source_excerpt_lane(self):
        for field, value in (("reviewer", "Authored reviewer\nwith a hidden passage"),
                             ("reviewer", "X" * 501), ("limitations", ["X" * 501]),
                             ("limitations", ["Bounded line\nplus another line"]),
                             ("limitations", [f"Bounded metadata {i}" for i in range(9)])):
            _, _, body, _ = self.fixture()
            source_review = unbound(DiscoverySourceReview.from_dict(body["source_review"]))
            source_review[field] = value
            body["source_review"] = DiscoverySourceReview.create(source_review).to_dict()
            with self.subTest(field=field, value=value), self.assertRaises(GameplayContractError):
                ArtifactCorrespondenceReview.create(body)

    def test_wrong_source_observation_and_prior_package_bindings_fail_closed(self):
        for location, field in (("owner_provenance", "source_reference_id"), ("owner_provenance", "pm_observation_id"),
                                (None, "prior_source_package_id"), (None, "prior_discovery_package_id"),
                                (None, "prior_review_id"), (None, "verification_result_id")):
            chain, result, body, _ = self.fixture()
            target = body if location is None else body[location]
            target[field] = OTHER
            with self.subTest(field=field), self.assertRaises(GameplayContractError): self.select(chain, result, body)

    def test_rehashed_fact_edits_are_not_accepted_as_reviewed_bytes(self):
        for field, value in (("artifact_hash", OTHER), ("byte_length", len(FICTIONAL_TEXT) + 1),
                             ("artifact_family", "20320315"), ("verification_profile_id", OTHER)):
            chain, result, body, _ = self.fixture()
            body["evaluated_artifact"][field] = value
            with self.subTest(field=field), self.assertRaises(GameplayContractError): self.select(chain, result, body)

    def test_marker_and_check_mutations_do_not_reproduce(self):
        for mode in ("marker", "check"):
            chain, result, body, _ = self.fixture()
            if mode == "marker": body["evaluated_artifact"]["checked_markers"][0]["matched"] = False
            else: body["checks"]["effective_date"] = "UNKNOWN"
            with self.subTest(mode=mode), self.assertRaises(GameplayContractError): self.select(chain, result, body)

    def test_review_cannot_turn_owner_statement_into_authentication_or_permission(self):
        for field in ("codex_independent_network_verification", "cryptographic_authentication",
                      "source_permission_established", "local_path_retained"):
            _, _, body, _ = self.fixture()
            body["owner_provenance"][field] = True
            with self.subTest(field=field), self.assertRaises(GameplayContractError): ArtifactCorrespondenceReview.create(body)
        for field in ("content_retained", "source_body_copied", "network_used"):
            _, _, body, _ = self.fixture()
            body[field] = True
            with self.subTest(field=field), self.assertRaises(GameplayContractError): ArtifactCorrespondenceReview.create(body)

    def test_review_is_immutable_defensive_and_typed(self):
        chain, result, body, _ = self.fixture()
        review = ArtifactCorrespondenceReview.create(body)
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)): review._payload = {}
        edited = review.to_dict()
        edited["checks"]["effective_date"] = "UNKNOWN"
        self.assertEqual(review.checks["effective_date"], "MATCH")
        with self.assertRaises(GameplayContractError): ArtifactCorrespondenceReview.from_dict(edited)
        with self.assertRaises(GameplayContractError):
            select_reviewed_artifact(review.to_dict(), result, chain["candidate"], chain["observation"],
                chain["source_reference"], chain["request"], as_of_date=chain["as_of_date"],
                prior_source_package_id=SOURCE_ID, prior_discovery_package_id=DISCOVERY_ID,
                prior_review_id=chain["review"].identity)


class GameplayRulesArtifactReviewPackageTests(unittest.TestCase):
    def load(self, name): return json.loads((PACKAGE / name).read_bytes())

    def verify(self, root=PACKAGE):
        return verify_artifact_review_package(root, source_root=SOURCE, discovery_root=DISCOVERY)

    def copy_package(self):
        temporary = tempfile.TemporaryDirectory(prefix="mtglab-metadata-package-")
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "review"
        shutil.copytree(PACKAGE, path)
        return path

    def rewrite(self, root, name, value, *, rebind=False):
        (root / name).write_text(deterministic_json(value) + "\n", encoding="utf-8")
        if rebind:
            manifest = json.loads((root / "manifest.json").read_bytes())
            raw = (root / name).read_bytes()
            manifest["files"][name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            manifest.pop("package_id")
            manifest["package_id"] = package_identity(manifest)
            self.rewrite(root, "manifest.json", manifest)

    def test_retained_package_reproduces_offline_without_owner_document(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("raw retention forbidden")), \
             patch("gameplay_rules.source_evidence.artifacts.verify_local_artifact", side_effect=AssertionError("owner document not a CI dependency")), \
             patch("pathlib.Path.write_text", side_effect=AssertionError("no writes")), \
             patch("pathlib.Path.write_bytes", side_effect=AssertionError("no writes")):
            first, second = self.verify(), self.verify()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "READY_FOR_RULE_PROJECTION")
        self.assertEqual(first["blocking_reasons"], [])
        self.assertTrue(first["integrity_verified"])

    def test_exact_reviewed_request_release_source_and_observation_are_bound(self):
        result = self.load("artifact-verification-result.json")
        self.assertEqual(result["request_id"], REQUEST_ID)
        self.assertEqual(result["release_candidate_id"], CANDIDATE_ID)
        self.assertEqual(result["discovery_source_reference_id"], REFERENCE_ID)
        self.assertEqual(result["observation_id"], OBSERVATION_ID)
        self.assertEqual(result["artifact_verification_result_id"], RESULT_ID)
        self.assertEqual(result["artifact_hash"], ARTIFACT_HASH)
        self.assertEqual(result["byte_length"], 977752)
        self.assertEqual(result["observed_at"], "2026-10-16T22:15:00-04:00")
        self.assertEqual(result["effective_date"], "2026-09-25")
        self.assertEqual(result["status"], "VERIFIED_EXPECTED_ARTIFACT")
        self.assertEqual(result["checked_markers"], [
            {"marker_id": "title", "matched": True}, {"marker_id": "effective_date_marker", "matched": True},
            {"marker_id": "rule_reference", "matched": True}, {"marker_id": "rule_heading", "matched": True}])

    def test_exact_original_packages_remain_unchanged_and_independently_valid(self):
        self.assertEqual(verify_review_package(SOURCE)["package_id"], SOURCE_ID)
        self.assertEqual(verify_discovery_package(DISCOVERY, previous_root=SOURCE)["package_id"], DISCOVERY_ID)
        self.assertEqual(len(list(SOURCE.iterdir())), 8)
        self.assertEqual(len(list(DISCOVERY.iterdir())), 7)
        original = json.loads((SOURCE / "source-inventory.json").read_bytes())["source_references"][0]
        self.assertEqual(original["access_outcome"], "ACCESS_UNAVAILABLE")
        self.assertIsNone(original["http_status"])
        self.assertIsNone(original["artifact_hash"])
        self.assertIsNone(json.loads((DISCOVERY / "release-candidate.json").read_bytes())["artifact_hash"])

    def test_ready_retains_provenance_limits_and_no_projection_admission_or_permission(self):
        selection = self.load("current-selection.json")
        readiness = self.load("readiness.json")
        review = self.load("artifact-correspondence-review.json")
        self.assertEqual(selection["release_candidate_id"], CANDIDATE_ID)
        self.assertEqual(selection["as_of_date"], "2026-10-16")
        self.assertEqual(selection["effective_date"], "2026-09-25")
        self.assertEqual(selection["artifact_hash"], ARTIFACT_HASH)
        self.assertFalse(selection["codex_independently_fetched"])
        self.assertEqual(review["owner_provenance"]["provenance_class"], "OWNER_SUPPLIED_ARTIFACT_PROVENANCE")
        for value in (selection, readiness, self.load("manifest.json")):
            self.assertFalse(value["projection_authorized"])
            self.assertFalse(value["admission_eligible"])
            self.assertEqual(value["source_policy_clearance"], "not_granted")
        self.assertFalse(readiness["real_rules_executable"])
        self.assertEqual(readiness["all_source_operation_states"], "NOT_ESTABLISHED")
        permissions = json.loads((SOURCE / "permission-matrix.json").read_bytes())
        for component in permissions["components"]:
            self.assertEqual({entry["status"] for entry in component["permission_status"].values()}, {"NOT_ESTABLISHED"})

    def test_reality_fracture_claim_stays_narrow(self):
        observation = json.loads((DISCOVERY / "pm-observation.json").read_bytes())
        relations = observation["relation_evidence"]
        self.assertTrue(any(row["marker_id"] == "701.71" and row["heading"] == "Empower Jace"
                            and row["at_least_identified_update_incorporated"] for row in relations))
        self.assertTrue(all(not row["full_bulletin_diff_verified"] for row in relations))

    def test_package_is_bounded_metadata_only_without_source_paths_or_corpus(self):
        self.assertEqual({path.name for path in PACKAGE.iterdir()}, {"artifact-verification-result.json",
            "artifact-correspondence-review.json", "current-selection.json", "readiness.json", "manifest.json"})
        for path in PACKAGE.iterdir():
            raw = path.read_bytes()
            with self.subTest(path=path.name):
                self.assertEqual(path.suffix, ".json")
                self.assertLess(len(raw), 16000)
                self.assertNotIn(b"%PDF", raw)
                self.assertNotIn(b"/tmp/", raw)
                self.assertNotIn(b"/workspace/", raw)
                self.assertNotIn(b"codex-remote-attachments", raw)
                self.assertNotIn(b"\n701.71.", raw)
                self.assertNotIn(b"\n100.1.", raw)
                json.loads(raw)

    def test_metadata_package_relocation_preserves_identity(self):
        self.assertEqual(self.verify(self.copy_package()), self.verify())

    def test_missing_metadata_or_extra_source_file_fails_closed(self):
        path = self.copy_package()
        (path / "artifact-correspondence-review.json").unlink()
        with self.assertRaises(GameplayContractError): self.verify(path)
        for name in ("copied-rules.txt", "rules.pdf", "rules.docx", "unknown.json"):
            path = self.copy_package()
            (path / name).write_bytes(b"Original fictional sentinel, not source content.")
            with self.subTest(name=name), self.assertRaises(GameplayContractError): self.verify(path)

    def test_symlink_metadata_is_rejected(self):
        path = self.copy_package()
        target = path / "artifact-verification-result.json"
        target.unlink()
        target.symlink_to(PACKAGE / target.name)
        with self.assertRaises(GameplayContractError): self.verify(path)

    def test_unbound_metadata_byte_change_fails(self):
        path = self.copy_package()
        target = path / "readiness.json"
        target.write_bytes(target.read_bytes() + b" ")
        with self.assertRaises(GameplayContractError): self.verify(path)

    def test_rebound_metadata_cannot_invent_projection_authority(self):
        for name, field, value in (("readiness.json", "projection_authorized", True),
                                  ("readiness.json", "all_source_operation_states", "ESTABLISHED"),
                                  ("current-selection.json", "as_of_date", "2026-10-17")):
            path = self.copy_package()
            changed = json.loads((path / name).read_bytes())
            changed[field] = value
            self.rewrite(path, name, changed, rebind=True)
            with self.subTest(field=field), self.assertRaises(GameplayContractError): self.verify(path)

    def test_rebound_correspondence_cannot_invent_raw_source_fields(self):
        path = self.copy_package()
        review = self.load("artifact-correspondence-review.json")
        body = unbound(ArtifactCorrespondenceReview.from_dict(review))
        body["source_body"] = "Original fictional sentinel."
        with self.assertRaises(GameplayContractError): ArtifactCorrespondenceReview.create(body)
        result = self.load("artifact-verification-result.json")
        result["raw_source"] = "Original fictional sentinel."
        self.rewrite(path, "artifact-verification-result.json", result, rebind=True)
        with self.assertRaises(GameplayContractError): self.verify(path)

    def test_manifest_cannot_rebind_historical_packages_or_change_authority(self):
        for field, value in (("source_package_id", OTHER), ("discovery_package_id", OTHER),
                             ("content_retained", True), ("admission_eligible", True),
                             ("source_policy_clearance", "cleared")):
            path = self.copy_package()
            manifest = self.load("manifest.json")
            manifest[field] = value
            manifest.pop("package_id")
            manifest["package_id"] = package_identity(manifest)
            self.rewrite(path, "manifest.json", manifest)
            with self.subTest(field=field), self.assertRaises(GameplayContractError): self.verify(path)


if __name__ == "__main__":
    unittest.main()
