"""Phase 113A state-aware retained-evidence gate tests (unittest only)."""
import hashlib
import json
import unittest
from pathlib import Path

from production_evidence import ProductionEvidenceRepository


ROOT = Path(__file__).resolve().parents[1]
RUN = "30663562841"
EVIDENCE = ROOT / "data" / "production_runs"
RUN_ROOT = EVIDENCE / RUN


def canonical_snapshot():
    base = ROOT / "data" / "canonical"
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(base.rglob("*")) if path.is_file()}


def read_json(path):
    return json.loads(path.read_text())


def retained_json_files():
    return sorted(RUN_ROOT.rglob("*.json"))


class FirstMB2BatchReviewGateTests(unittest.TestCase):
    def test_selected_run_absence_or_verified_pending_evidence(self):
        """Accept the historical fail-closed state and PR #86's retained state."""
        if not RUN_ROOT.exists():
            self.assertFalse((EVIDENCE / "index.json").exists())
            self.assertEqual([path.name for path in EVIDENCE.iterdir()], [".gitkeep"])
            return

        manifest_path = RUN_ROOT / "manifest.json"
        batch_index_path = RUN_ROOT / "batch_index.json"
        repository_index_path = EVIDENCE / "index.json"
        for path in (manifest_path, batch_index_path, repository_index_path):
            self.assertTrue(path.is_file(), f"missing retained evidence file: {path}")

        manifest = read_json(manifest_path)
        metadata = read_json(RUN_ROOT / "metadata.json")
        batch_index = read_json(batch_index_path)
        repository_index = read_json(repository_index_path)
        verification = ProductionEvidenceRepository(ROOT / "data").verify(RUN)
        self.assertTrue(verification["valid"])
        self.assertEqual(str(manifest["workflow"]["run_id"]), RUN)
        self.assertEqual(str(metadata["run_id"]), RUN)
        self.assertIn(RUN, {str(item["run_id"]) for item in repository_index["runs"]})

        batches = batch_index["batches"]
        mb2_batches = [item for item in batches if item["target_product"] == "MB2"]
        self.assertGreaterEqual(len(mb2_batches), 1)
        self.assertIn("MSH", {item["target_product"] for item in batches})
        for item in batches:
            bundle = read_json(RUN_ROOT / item["bundle_path"])
            self.assertEqual(bundle["review_package"]["review_status"], "pending")
            self.assertFalse(bundle["review_package"]["canonical_write"])
            self.assertFalse(bundle["review_package"]["promotion_performed"])
            self.assertEqual(item["target_product"],
                             bundle["review_package"]["target_set_code"])

        for document in (read_json(path) for path in retained_json_files()):
            if "canonical_write" in document:
                self.assertFalse(document["canonical_write"])
            if "promotion_performed" in document:
                self.assertFalse(document["promotion_performed"])

    def test_pending_decision_exists_without_approval_or_promotion_audit(self):
        from production_evidence.candidate_review import review_first_mb2_batch
        decision = review_first_mb2_batch(ROOT / "data")["pending_decision"]
        self.assertEqual(decision["status"], "additional_evidence_required")
        self.assertFalse(decision["batch_approved"])
        self.assertFalse(decision["canonical_write"])

    def test_document_records_phase_115_dimensions_and_counts(self):
        text = (ROOT / "docs" / "FIRST_MB2_BATCH_REVIEW.md").read_text()
        for phrase in ("identity", "relationships", "provenance", "collector",
                       "identifiers", "rarity", "finish", "language", "lifecycle",
                       "confidence", "unknown", "dependency closure"):
            self.assertIn(phrase, text.lower())
        self.assertIn("`approved` | 979", text)
        self.assertIn("`excluded` | 0", text)
        self.assertIn("`requires_additional_evidence` | 21", text)
        self.assertIn("no MSH/Marvel payload or candidate was inspected", text)

    def test_gate_performs_no_canonical_write_or_promotion(self):
        before = canonical_snapshot()
        self.test_selected_run_absence_or_verified_pending_evidence()
        self.assertEqual(canonical_snapshot(), before)


if __name__ == "__main__":
    unittest.main()
