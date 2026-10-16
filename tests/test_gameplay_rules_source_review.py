"""Retained metadata closure, never a real rules corpus or release approval."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from evidence.contracts import deterministic_json
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.source_evidence.contracts import EvidenceIndex, PERMISSION_OPERATIONS
from gameplay_rules.source_evidence.review import package_identity, verify_review_package
from gameplay_rules.source_evidence.selection import select_version
from gameplay_rules_source_fixture import (AS_OF, designation, evidence_index,
    release_candidate, reviewed_fixture, source_reference)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reference-reviews/gameplay-rules-source-versioning"


class GameplayRulesSourceReviewTests(unittest.TestCase):
    def test_repeated_identical_artifact_observation_is_not_a_release_conflict(self):
        fixture = reviewed_fixture()
        second = source_reference(observed_at="2032-01-06T13:00:00Z")
        repeated = release_candidate(second)
        self.assertNotEqual(second.identity, fixture["artifact"].identity)
        self.assertEqual(second.artifact_hash, fixture["artifact"].artifact_hash)
        index = evidence_index([fixture["artifact"], second, fixture["page"]],
            [fixture["candidate"], repeated], [fixture["review"]],
            [designation(fixture["page"], fixture["artifact"])])
        selection = select_version(index, scope="current_designation", as_of_date=AS_OF,
                                   review_id=fixture["review"].identity)
        self.assertEqual(selection.status, "READY_FOR_RULE_PROJECTION")
        self.assertFalse(selection.projection_authorized)

    def copy_package(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "metadata"
        shutil.copytree(PACKAGE, root)
        return root

    def rewrite(self, root, name, mutate, *, rebind=False):
        path = root / name
        value = json.loads(path.read_bytes())
        mutate(value)
        path.write_text(deterministic_json(value) + "\n")
        if rebind:
            manifest = json.loads((root / "manifest.json").read_bytes())
            manifest["files"][name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                       "bytes": path.stat().st_size}
            manifest.pop("package_id")
            manifest["package_id"] = package_identity(manifest)
            (root / "manifest.json").write_text(deterministic_json(manifest) + "\n")

    def test_retained_package_verifies_without_source_access_and_is_deterministic(self):
        with patch("gameplay_rules.source_evidence.intake.UrllibMetadataTransport.fetch",
                   side_effect=AssertionError("no network during retained review")):
            first = verify_review_package(PACKAGE)
            self.assertEqual(first, verify_review_package(PACKAGE))
        self.assertTrue(first["integrity_verified"])
        self.assertFalse(first["projection_authorized"])
        self.assertEqual(first["status"], "NOT_READY_FOR_RULE_PROJECTION")

    def test_metadata_relocation_keeps_exact_package_and_selection_identities(self):
        self.assertEqual(verify_review_package(PACKAGE), verify_review_package(self.copy_package()))

    def test_changed_metadata_fails_without_hash_refresh(self):
        root = self.copy_package()
        self.rewrite(root, "readiness.json", lambda value: value.update(currentness_status="VERIFIED"))
        with self.assertRaises(GameplayContractError): verify_review_package(root)

    def test_raw_content_fields_cannot_hide_under_rehashed_authored_metadata(self):
        for name in ("source-authority.json", "release-candidates.json", "release-lineage.json",
                     "permission-matrix.json", "readiness.json"):
            root = self.copy_package()
            self.rewrite(root, name, lambda value: value.update(raw_rules_text="Unretained source body"), rebind=True)
            with self.subTest(name=name), self.assertRaises(GameplayContractError):
                verify_review_package(root)

    def test_nested_component_cannot_hide_source_body_even_after_rehash(self):
        root = self.copy_package()
        self.rewrite(root, "permission-matrix.json", lambda value:
                     value["components"][0].update(source_body="Forbidden source body"), rebind=True)
        with self.assertRaises(GameplayContractError): verify_review_package(root)

    def test_unknown_schema_stays_blocked_after_rehash(self):
        root = self.copy_package()
        self.rewrite(root, "source-authority.json", lambda value:
                     value.update(schema_version="unsupported-v99"), rebind=True)
        with self.assertRaises(GameplayContractError): verify_review_package(root)

    def test_missing_extra_symlink_and_pdf_artifacts_block(self):
        for mode in ("missing", "extra", "symlink", "pdf"):
            root = self.copy_package()
            if mode == "missing": (root / "readiness.json").unlink()
            elif mode == "symlink":
                (root / "readiness.json").unlink()
                (root / "readiness.json").symlink_to(PACKAGE / "readiness.json")
            else: (root / ("official.pdf" if mode == "pdf" else "extra.json")).write_bytes(b"not a permitted dependency")
            with self.subTest(mode=mode), self.assertRaises(GameplayContractError):
                verify_review_package(root)

    def test_duplicate_json_keys_are_rejected(self):
        root = self.copy_package()
        (root / "readiness.json").write_text('{"status":"one","status":"two"}')
        with self.assertRaises(GameplayContractError): verify_review_package(root)

    def test_unavailable_first_party_chain_does_not_invent_artifact_or_currentness(self):
        index = EvidenceIndex.from_json((PACKAGE / "source-inventory.json").read_bytes())
        self.assertEqual(list(index.release_candidates), [])
        self.assertEqual(list(index.relations), [])
        source = index.to_dict()["source_references"][0]
        self.assertEqual(source["access_outcome"], "ACCESS_UNAVAILABLE")
        self.assertIsNone(source["http_status"])
        for key in ("resolved_reference", "artifact_hash", "byte_length", "media_type", "rules_version", "effective_date"):
            self.assertIsNone(source[key], key)
        readiness = json.loads((PACKAGE / "readiness.json").read_bytes())
        self.assertEqual(readiness["currentness_status"], "CURRENT_RULES_RELEASE_NOT_VERIFIED")
        self.assertIn("REALITY_FRACTURE_INCORPORATION_UNVERIFIED", readiness["blocking_reasons"])
        self.assertFalse(readiness["full_source_retained"])

    def test_all_required_permission_components_and_operations_are_explicit(self):
        permissions = json.loads((PACKAGE / "permission-matrix.json").read_bytes())
        self.assertEqual(set(permissions["operations"]), set(PERMISSION_OPERATIONS))
        self.assertEqual(len(permissions["components"]), 5)
        for row in permissions["components"]:
            self.assertEqual(set(row["permission_status"]), set(PERMISSION_OPERATIONS))
            self.assertEqual({entry["status"] for entry in row["permission_status"].values()}, {"NOT_ESTABLISHED"})
        self.assertEqual(permissions["project_authored_metadata"]["status"], "NOT_APPLICABLE")

    def test_unavailable_evidence_cannot_establish_another_components_permission(self):
        root = self.copy_package()
        matrix = json.loads((root / "permission-matrix.json").read_bytes())
        reference = matrix["components"][0]["source_reference_id"]
        def promote(value):
            value["components"][1]["permission_status"]["private_raw_retention"].update(
                status="ESTABLISHED", evidence_references=[reference])
        self.rewrite(root, "permission-matrix.json", promote, rebind=True)
        with self.assertRaises(GameplayContractError): verify_review_package(root)

    def test_blocked_selection_cannot_claim_verified_currentness_after_rehash(self):
        root = self.copy_package()
        self.rewrite(root, "readiness.json", lambda value:
                     value.update(currentness_status="VERIFIED_CURRENT_RELEASE_REFERENCE"), rebind=True)
        with self.assertRaises(GameplayContractError): verify_review_package(root)

    def test_unavailable_reference_cannot_verify_update_incorporation_after_rehash(self):
        root = self.copy_package()
        reference = json.loads((root / "source-inventory.json").read_bytes())["source_references"][0]["source_reference_id"]
        self.rewrite(root, "release-lineage.json", lambda value:
                     value["reality_fracture_check"].update(status="VERIFIED", evidence_reference_ids=[reference]), rebind=True)
        with self.assertRaises(GameplayContractError): verify_review_package(root)

    def test_public_package_is_small_metadata_and_contains_no_body_fields(self):
        self.assertEqual(len(list(PACKAGE.iterdir())), 8)
        self.assertLess(sum(path.stat().st_size for path in PACKAGE.iterdir()), 20_000)
        forbidden = {"body", "payload", "raw_rules_text", "oracle_text", "full_text",
                     "headers", "cookies", "authorization", "token"}
        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(set(value) & forbidden)
                for child in value.values(): inspect(child)
            elif isinstance(value, list):
                for child in value: inspect(child)
        for path in PACKAGE.iterdir(): inspect(json.loads(path.read_bytes()))


if __name__ == "__main__":
    unittest.main()
