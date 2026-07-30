"""Unit tests for the product-agnostic Evidence Review Engine."""
from __future__ import annotations
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from evidence_review import HandoffLoadError, load_handoff, render_json_report, render_markdown_report, review_handoff, validate_report
from validation import SchemaValidationError

class EvidenceReviewTests(unittest.TestCase):
    def make_handoff(self, root: Path, *, extra_artifact: bool = False) -> Path:
        artifacts = root / "artifacts"; artifacts.mkdir()
        content = b"external evidence\n"; (artifacts / "capture.txt").write_bytes(content)
        records = [{"id": "capture", "path": "artifacts/capture.txt", "media_type": "text/plain", "byte_size": len(content), "sha256": hashlib.sha256(content).hexdigest(), "source_ids": ["official-source"]}]
        if extra_artifact:
            (artifacts / "orphan.txt").write_bytes(b"orphan")
            records.append({"id": "orphan", "path": "artifacts/orphan.txt", "media_type": "text/plain", "byte_size": 6, "sha256": hashlib.sha256(b"orphan").hexdigest(), "source_ids": ["official-source"]})
        manifest = {"schema_version": "v1", "id": "generic-handoff", "title": "Generic handoff", "created_at": "2026-07-30T00:00:00Z", "sources": [{"id": "official-source", "reference": "https://example.test/source"}], "required_artifact_ids": ["capture"], "artifacts": records, "claims": [{"id": "claim-a", "topic": "declared-fact", "value": "alpha", "statement": "The source explicitly says alpha.", "artifact_ids": ["capture"], "source_ids": ["official-source"]}]}
        path = root / "manifest.json"; path.write_text(json.dumps(manifest), encoding="utf-8"); return path

    def test_complete_handoff_is_ready_and_reports_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = review_handoff(load_handoff(self.make_handoff(Path(directory))))
            self.assertEqual(report["recommendation"], "Ready for verification"); self.assertEqual(report["completeness_score"], 100); self.assertEqual(report["supported_claims"], ["claim-a"])
            validate_report(report); self.assertEqual(render_json_report(report), render_json_report(report)); self.assertIn("**Recommendation:** Ready for verification", render_markdown_report(report))

    def test_missing_artifact_is_reported_without_aborting_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_handoff(Path(directory)); (Path(directory) / "artifacts/capture.txt").unlink(); report = review_handoff(load_handoff(path))
            self.assertEqual(report["recommendation"], "Reject"); self.assertEqual(report["unsupported_claims"], ["claim-a"]); self.assertEqual(report["missing_evidence"], ["capture"]); self.assertEqual(report["completeness_score"], 0); self.assertEqual(report["validation_findings"][0]["code"], "artifact_unreadable")

    def test_integrity_mismatches_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_handoff(Path(directory)); manifest = json.loads(path.read_text()); manifest["artifacts"][0]["byte_size"] += 1; manifest["artifacts"][0]["sha256"] = "0" * 64; path.write_text(json.dumps(manifest)); report = review_handoff(load_handoff(path))
            self.assertEqual({item["code"] for item in report["validation_findings"]}, {"hash_mismatch", "size_mismatch"}); self.assertEqual(report["recommendation"], "Reject")

    def test_duplicates_conflicts_and_unsupported_claims_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_handoff(Path(directory)); manifest = json.loads(path.read_text()); duplicate = dict(manifest["artifacts"][0]); duplicate["id"] = "capture-copy"; manifest["artifacts"].append(duplicate)
            manifest["claims"].extend([{"id": "claim-b", "topic": "declared-fact", "value": "beta", "statement": "A conflicting explicit value.", "artifact_ids": ["capture"], "source_ids": ["official-source"]}, {"id": "claim-c", "topic": "other", "value": True, "statement": "References absent evidence.", "artifact_ids": ["absent"], "source_ids": ["official-source"]}]); path.write_text(json.dumps(manifest)); report = review_handoff(load_handoff(path))
            self.assertEqual(report["conflicting_claims"][0]["claim_ids"], ["claim-a", "claim-b"]); self.assertEqual(report["unsupported_claims"], ["claim-c"]); self.assertEqual({item["field"] for item in report["duplicate_artifacts"]}, {"path", "sha256"}); self.assertEqual(report["recommendation"], "Reject")

    def test_orphaned_artifact_needs_more_evidence_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = review_handoff(load_handoff(self.make_handoff(Path(directory), extra_artifact=True))); self.assertEqual(report["orphaned_artifacts"], ["orphan"]); self.assertEqual(report["recommendation"], "Needs additional evidence")

    def test_invalid_metadata_and_unknown_source_references_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_handoff(Path(directory)); manifest = json.loads(path.read_text()); del manifest["title"]; manifest["artifacts"][0]["source_ids"] = ["undeclared"]; path.write_text(json.dumps(manifest)); report = review_handoff(load_handoff(path))
            self.assertEqual({item["code"] for item in report["validation_findings"]}, {"invalid_manifest", "unknown_source_reference"}); self.assertEqual(report["recommendation"], "Reject")

    def test_unsafe_paths_and_non_object_manifests_fail_safely(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "manifest.json").write_text("[]")
            with self.assertRaisesRegex(HandoffLoadError, "JSON object"): load_handoff(root)
            (root / "manifest.json").write_text(json.dumps({"artifacts": [{"id": "escape", "path": "../outside"}]})); self.assertIn("escapes the handoff", load_handoff(root).load_errors[0])

    def test_report_schema_rejects_unversioned_or_invalid_reports(self) -> None:
        with self.assertRaises(ValueError): validate_report({})
        with self.assertRaises(SchemaValidationError): validate_report({"schema_version": "v1"})

if __name__ == "__main__": unittest.main()
