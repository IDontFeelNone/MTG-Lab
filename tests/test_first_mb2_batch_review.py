"""Phase 110B fail-closed repository evidence tests (unittest only)."""
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = "30663562841"
BATCH = "mb2-batch-000001-e32022126c07"


def canonical_snapshot():
    base = ROOT / "data" / "canonical"
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(base.rglob("*")) if path.is_file()}


class FirstMB2BatchReviewGateTests(unittest.TestCase):
    def test_retained_batch_integrity_fails_closed_when_run_is_absent(self):
        matches = [path for path in (ROOT / "data").rglob("*")
                   if path.is_file() and (RUN in str(path) or BATCH in str(path))]
        self.assertEqual(matches, [])

    def test_no_review_decision_or_promotion_was_manufactured(self):
        decision_files = [path for path in (ROOT / "data").rglob("*.json")
                          if BATCH in path.read_text(errors="ignore")]
        self.assertEqual(decision_files, [])

    def test_documented_gate_is_deterministic_and_pending_operator_evidence(self):
        text = (ROOT / "docs" / "FIRST_MB2_BATCH_REVIEW.md").read_text()
        self.assertIn(RUN, text)
        self.assertIn(BATCH, text)
        self.assertIn("pre-decision artifact-gate failure", text)
        self.assertIn("not ready", text)

    def test_gate_check_performs_no_canonical_writes_or_promotion(self):
        before = canonical_snapshot()
        self.test_retained_batch_integrity_fails_closed_when_run_is_absent()
        self.assertEqual(canonical_snapshot(), before)


if __name__ == "__main__":
    unittest.main()
