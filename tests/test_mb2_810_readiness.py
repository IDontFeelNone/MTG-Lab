"""Pending readiness evidence checks; no admission or production payload writes."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mb2_readiness_inspection import (ROOT, PACKET, POLICY, READINESS, DIGEST, ROLES,
    PERMISSIONS, build_matrix, encoded, inspect_record, paths, read, selected_candidates, sha)
from acquisition import RawSnapshotStore
from production_evidence.automatic_updates import AutomaticCanonicalUpdate, _check_public_bytes
from production_evidence.repository import EvidenceError
from scripts.verify_mb2_reference_packet import check_manifest
from validation import SchemaValidationError, validate_document


class MB2810ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.basis = read(READINESS / "analysis-basis.json")
        cls.matrix = read(READINESS / "field-admission-matrix.json")
        cls.selected, cls.held = selected_candidates()

    def test_original_34_policy_files_remain_bound_and_public_safe(self):
        self.assertEqual(sha((POLICY / "manifest.json").read_bytes()),
            "f686a1792303adbdcfa0dc15359f4614bc2076cc8896dae7273752f98cf9e8d7")
        check_manifest(POLICY, read(POLICY / "manifest.json"))
        files = [p for p in POLICY.rglob("*") if p.is_file()]
        self.assertEqual(len(files), 34)
        for p in files:
            _check_public_bytes(p.read_bytes())
        receipts = read(POLICY / "source-receipts.json")
        for receipt in receipts.values():
            manifest, raw = RawSnapshotStore(POLICY / "raw").load(POLICY / receipt["path"])
            validate_document(manifest, "raw-snapshot", "v1")
            self.assertEqual(sha(raw), receipt["sha256"])
            self.assertFalse(receipt["upstream_capture"]["upstream_git_retained"])
        for p in (POLICY / "source-records").glob("*.json"):
            validate_document(read(p), "source-record")

    def test_readiness_manifest_is_exact_and_bound(self):
        manifest = read(READINESS / "manifest.json")
        check_manifest(ROOT, manifest)
        packet_files = {p.relative_to(ROOT).as_posix() for p in READINESS.rglob("*")
                        if p.is_file() and p.name != "manifest.json"}
        self.assertTrue(packet_files.issubset(manifest["files"]))
        self.assertEqual(manifest["review_status"], "pending")
        self.assertEqual(manifest["human_approvals"], 0)
        self.assertFalse(manifest["entity_admission_ready"])
        for name in manifest["files"]:
            _check_public_bytes((ROOT / name).read_bytes())

    def test_changed_and_missing_manifest_file_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = b'{"review_state":"pending"}\n'
            target = root / "evidence.json"
            target.write_bytes(raw)
            manifest = {"files": {"evidence.json": {"bytes": len(raw), "sha256": sha(raw)}}}
            check_manifest(root, manifest)
            target.write_bytes(b'{"review_state":"cleared"}\n')
            with self.assertRaisesRegex(ValueError, "integrity mismatch"):
                check_manifest(root, manifest)
            target.unlink()
            with self.assertRaisesRegex(ValueError, "file missing"):
                check_manifest(root, manifest)
            with self.assertRaisesRegex(ValueError, "path escape"):
                check_manifest(root, {"files": {"../evidence.json": manifest["files"]["evidence.json"]}})

    def test_matrix_reproduces_exact_adapter_inspection_without_execution(self):
        def protected():
            roots = [ROOT / "data/canonical", ROOT / "reference-reviews/mb2-reference-coverage",
                     ROOT / "config/automatic_updates"]
            return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for root in roots
                    for p in root.rglob("*") if p.is_file()}
        before = protected()
        with patch.object(AutomaticCanonicalUpdate, "execute", side_effect=AssertionError("no writer execution")), \
             patch.object(AutomaticCanonicalUpdate, "plan", side_effect=AssertionError("no substitute planner")):
            observed = build_matrix(self.basis)
        self.assertEqual(encoded(observed), (READINESS / "field-admission-matrix.json").read_bytes())
        self.assertEqual(protected(), before)

    def test_selection_and_multiface_holds_are_independent_of_config(self):
        self.assertEqual(self.matrix["selection"]["ordered_candidate_digest"], DIGEST)
        ids = [r["payload"]["candidate_identifier"] for r in self.selected]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(set(ids) & set(self.held))
        self.assertEqual(len(self.held), 9)
        parsed = {r["id"]: r for r in read(PACKET / "parsed-records.json")["records"]}
        all_rows = read(PACKET / "candidate-preparation.json")["candidates"]
        independently_held = sorted(r["payload"]["candidate_identifier"] for r in all_rows
            if any(parsed[pid]["raw_fields"].get("otherFaceIds") for pid in r["parsed_record_ids"]))
        self.assertEqual(self.held, independently_held)
        self.assertEqual(self.held, self.matrix["selection"]["held_candidate_ids"])

    def test_every_output_surface_and_leaf_is_reviewed(self):
        expected = {(r["entity_type"], r["path"]) for r in self.matrix["fields"]}
        observed = set()
        for candidate in self.selected:
            kind, _, record = inspect_record(candidate, self.basis)
            observed.update((kind, path) for path, _ in paths(record))
            observed.add((kind, "/$canonical_identity"))
        self.assertEqual(observed, expected)
        for field in self.matrix["fields"]:
            self.assertIn(field["admission_role"], ROLES)
            self.assertIn(field["public_retention_evidence"], PERMISSIONS)
        for surface in ["source_values", "unknown_values", "unknown_fields", "candidate_context",
                        "field_provenance", "acquisition_lineage", "parsed_record_references"]:
            self.assertTrue(any(r["path"].startswith("/" + surface) for r in self.matrix["fields"]), surface)

    def test_required_name_and_oracle_identifiers_are_not_cleared(self):
        fields = {(r["entity_type"], r["path"]): r for r in self.matrix["fields"]}
        for kind, path in [("card", "/$canonical_identity"), ("card", "/values/name"),
                           ("printing", "/values/card_id"), ("identifier", "/values/value")]:
            entry = fields[kind, path]
            self.assertEqual(entry["public_retention_evidence"], "NOT_ESTABLISHED")
            self.assertEqual(entry["proposed_action"], "withhold_and_block_required_field")
        self.assertEqual(fields["printing", "/values/uuid"]["public_retention_evidence"], "ESTABLISHED")
        self.assertEqual(fields["card", "/acquisition_metadata/captured_at"]["public_retention_evidence"], "NOT_APPLICABLE")

    def test_omitting_or_replacing_a_required_name_is_rejected_by_real_adapter(self):
        original = next(r for r in self.selected if r["entity_type"] == "card")
        for replacement in [None, {"status": "unavailable", "reason": "withheld"}]:
            candidate = deepcopy(original)
            if replacement is None:
                del candidate["payload"]["mapped_fields"]["name"]
            else:
                candidate["payload"]["mapped_fields"]["name"] = replacement
            with self.assertRaisesRegex(EvidenceError, "missing its name"):
                inspect_record(candidate, self.basis)

    def test_existing_canonical_schema_cannot_encode_withheld_name(self):
        fictional = {"schema_version": "v1", "id": "fictional-card", "game": "fictional",
                     "name": "Fictional Example", "provenance": [{"source_id": "fictional",
                     "field_paths": ["/name"], "claim": "Fictional test input only"}]}
        validate_document(fictional, "card")
        for name in [None, {"status": "unavailable"}, ""]:
            changed = deepcopy(fictional)
            if name is None: del changed["name"]
            else: changed["name"] = name
            with self.assertRaises(SchemaValidationError):
                validate_document(changed, "card")

    def test_sensitive_prose_cannot_hide_in_an_unreviewed_output_surface(self):
        fields = {(r["entity_type"], r["path"]): r for r in self.matrix["fields"]}
        for kind in ["card", "printing"]:
            for surface in ["unknown_fields", "unknown_values"]:
                for field in ["text", "flavorText", "rulings/[]/text", "foreignData/[]/flavorText",
                              "edhrecRank", "edhrecSaltiness"]:
                    self.assertEqual(fields[kind, "/" + surface + "/" + field]["public_retention_evidence"],
                                     "NOT_ESTABLISHED")

    def test_matrix_retains_hashes_and_field_names_without_source_values(self):
        for binding in self.matrix["record_bindings"]:
            self.assertEqual(set(binding), {"candidate_id", "entity_type", "canonical_identity_sha256", "adapted_record_sha256"})
            for key in ["canonical_identity_sha256", "adapted_record_sha256"]:
                self.assertRegex(binding[key], r"^[0-9a-f]{64}$")
        self.assertTrue(self.matrix["inspection_only"])
        self.assertFalse(self.matrix["workflow_executed"])
        self.assertFalse(self.matrix["permission_clearance"])

    def test_policy_status_remains_operation_specific_and_unresolved(self):
        policy = read(POLICY / "policy-review.json")
        self.assertEqual(len(policy["verdicts"]), 4)
        self.assertTrue(all(v["status"] == "NOT ESTABLISHED" for v in policy["verdicts"].values()))
        self.assertFalse(policy["first_party_scryfall_policy_search"]["permission_inference_from_access_errors"])
        report = read(READINESS / "readiness-status.json")
        self.assertEqual(report["minimum_data_admission"], "MINIMUM-DATA ADMISSION NOT CURRENTLY SAFE")
        self.assertEqual(report["approval_state"], "not_granted")
        for field in ["execution_authorized", "admission_ready", "writer_executed", "plan_generated"]:
            self.assertFalse(report[field])


if __name__ == "__main__":
    unittest.main()
