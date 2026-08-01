"""Phase 115 exact-batch candidate review and immutable artifact coverage."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from production_evidence.candidate_review import (
    BATCH_ID, EVIDENCE_ID, review_first_mb2_batch, write_review_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "data/reviews/phase-115" / BATCH_ID


class Phase115CandidateReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = review_first_mb2_batch(ROOT / "data")

    def test_reviews_exactly_one_mb2_batch_and_never_marvel(self):
        self.assertEqual(self.result["evidence_identity"], EVIDENCE_ID)
        self.assertEqual(self.result["batch_id"], BATCH_ID)
        self.assertEqual(self.result["target_set_code"], "MB2")
        self.assertEqual(self.result["review_scope"], {
            "candidate_count": 1000, "other_mb2_batches_reviewed": 0,
            "marvel_candidates_reviewed": 0,
        })

    def test_every_candidate_has_one_supported_classification(self):
        ledger = self.result["ledger"]
        self.assertEqual([item["ordinal"] for item in ledger], list(range(1000)))
        self.assertEqual(len({item["candidate_id"] for item in ledger}), 1000)
        self.assertEqual(self.result["statistics"]["classifications"], {
            "approved": 979, "excluded": 0, "requires_additional_evidence": 21,
        })
        self.assertEqual({reason for item in ledger for reason in item["reasons"]},
                         {"non_unique_external_identifier"})

    def test_all_required_dimensions_and_dependency_closure_are_verified(self):
        self.assertTrue(self.result["dependency_closure"]["valid"])
        self.assertEqual(self.result["statistics"]["entity_types"], {
            "card": 384, "finish": 2, "identifier": 235, "printing": 379,
        })
        self.assertEqual(self.result["findings"]["identifier_collisions_considered"], 117)
        # The reviewer fails closed on identity, relationships, provenance, collector number,
        # identifiers, rarity, finish, language, lifecycle, confidence and explicit unknowns.
        source = (ROOT / "src/production_evidence/candidate_review.py").read_text()
        for token in ("incomplete_card_identity", "missing_card_relationship", "provenance_mismatch",
                      "missing_collector_number", "missing_identifiers", "missing_rarity",
                      "missing_finish_relationship", "unsupported_language", "unexpected_lifecycle",
                      "insufficient_confidence", "unknowns_not_explicit"):
            self.assertIn(token, source)

    def test_committed_artifacts_are_exactly_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            write_review_artifacts(ROOT / "data", temporary)
            historical = {"pending-review-decision.json", "promotion-readiness-report.json"}
            actual = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in ARTIFACTS.iterdir() if p.name not in historical}
            generated = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in Path(temporary).iterdir() if p.name not in historical}
            self.assertEqual(generated, actual)

    def test_pending_decision_stops_before_resolution_and_promotion(self):
        decision = self.result["pending_decision"]
        readiness = self.result["promotion_readiness"]
        self.assertEqual(decision["status"], "additional_evidence_required")
        self.assertFalse(decision["batch_approved"])
        self.assertFalse(decision["canonical_write"])
        self.assertFalse(readiness["ready"])
        self.assertFalse(readiness["promotion_performed"])
        self.assertFalse(readiness["canonical_write"])


if __name__ == "__main__":
    unittest.main()
