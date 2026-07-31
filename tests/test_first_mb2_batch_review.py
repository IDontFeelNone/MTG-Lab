"""Phase 113 retained-evidence review gate tests (unittest only)."""
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = "30663562841"
EVIDENCE = ROOT / "data" / "production_runs"


def canonical_snapshot():
    base = ROOT / "data" / "canonical"
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(base.rglob("*")) if path.is_file()}


class FirstMB2BatchReviewGateTests(unittest.TestCase):
    def test_selected_run_is_not_in_production_evidence_repository(self):
        self.assertFalse((EVIDENCE / RUN).exists())
        self.assertFalse((EVIDENCE / "index.json").exists())
        self.assertEqual([path.name for path in EVIDENCE.iterdir()], [".gitkeep"])

    def test_no_immutable_decision_was_fabricated(self):
        decisions = [path for path in (ROOT / "data").rglob("*.json")
                     if RUN in path.read_text(errors="ignore") and "review_decision" in path.name]
        self.assertEqual(decisions, [])

    def test_document_records_all_verification_dimensions_and_unknown_counts(self):
        text = (ROOT / "docs" / "FIRST_MB2_BATCH_REVIEW.md").read_text()
        for phrase in ("Candidate payloads", "Candidate IDs", "Dependency closure", "Provenance",
                       "Confidence", "Validation state", "Identifiers", "Explicit unknowns",
                       "Review package integrity"):
            self.assertIn(phrase, text)
        self.assertIn("each **undetermined**", text)
        self.assertIn("No Marvel batch or candidate was inspected", text)

    def test_gate_performs_no_canonical_write_or_promotion(self):
        before = canonical_snapshot()
        self.test_selected_run_is_not_in_production_evidence_repository()
        self.assertEqual(canonical_snapshot(), before)


if __name__ == "__main__":
    unittest.main()
