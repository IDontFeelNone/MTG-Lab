"""Phase 116 deterministic MB2 identifier-resolution overlay coverage."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from production_evidence.identifier_resolution import (
    ALLOWED_DISPOSITIONS, BATCH_ID, classify_collision,
    resolve_first_mb2_identifiers, write_identifier_resolution_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "data/reviews/phase-116" / BATCH_ID
PHASE_115_DIGESTS = {
    "candidate-review-ledger.json": "e4600093a5f460657014d2e8053f10f1f1850fc4035eec75e75b4f5a131f6311",
    "dependency-closure-verification.json": "2e2c874237ecc265b2850b74a22086d78c1cc471798f99a25e89dd000d96b874",
    "findings-report.json": "72ee2b6db74cb4b59a841840a8b690e507813a8a1ae898f75dc018f1a20efa76",
    "pending-review-decision.json": "325270e3d20e0552a42e54d98af19e9bd77c357a1a125592e90f9cd185487a85",
    "promotion-readiness-report.json": "7135173aa95132d277f13ee376d35b6b0691b61af04fba03380fb13651cae769",
}


class Phase116IdentifierResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = resolve_first_mb2_identifiers(ROOT / "data")
        cls.artifacts = cls.result["artifacts"]

    def test_exact_phase_115_scope_and_deterministic_collision_grouping(self):
        ledger = self.artifacts["identifier-resolution-ledger.json"]["resolutions"]
        groups = self.artifacts["collision-analysis-report.json"]["collision_groups"]
        self.assertEqual(len(ledger), 21)
        self.assertEqual(len({row["candidate_id"] for row in ledger}), 21)
        self.assertEqual({row["conflict_group_id"] for row in ledger},
                         {"scryfallCardBackId:0aeebaf5-8c7d-4636-9e82-8c27447861f7"})
        self.assertEqual(groups[0]["collision_count"], 820)
        self.assertEqual(groups[0]["distinct_source_uuids"], 820)

    def test_namespace_policy_and_distinct_printing_alias_resolution(self):
        rows = self.artifacts["identifier-resolution-ledger.json"]["resolutions"]
        self.assertEqual({row["selected_classification"] for row in rows},
                         {"non_unique_provider_identifier_alias"})
        self.assertEqual({row["disposition"] for row in rows},
                         {"approved_after_resolution"})
        self.assertEqual({row["coordinates_agree"] for row in rows}, {False})
        self.assertTrue(all(row["relationship_evidence"]["printing_candidate_present"]
                            and row["relationship_evidence"]["card_candidate_present"]
                            for row in rows))

    def test_fail_closed_duplicate_unresolved_quarantine_and_fatal_handling(self):
        self.assertEqual(classify_collision(uniqueness="not-guaranteed", same_coordinates=True,
            byte_identical=True, same_source_uuid=True, proven_non_unique_alias=False),
            "excluded_duplicate")
        self.assertEqual(classify_collision(uniqueness="not-guaranteed", same_coordinates=False,
            byte_identical=None, same_source_uuid=False, proven_non_unique_alias=False),
            "remains_additional_evidence")
        self.assertEqual(classify_collision(uniqueness="strict", same_coordinates=True,
            byte_identical=False, same_source_uuid=False, proven_non_unique_alias=False),
            "quarantined")
        self.assertEqual(classify_collision(uniqueness="strict", same_coordinates=False,
            byte_identical=False, same_source_uuid=False, proven_non_unique_alias=False),
            "fatal_conflict")
        self.assertIn("excluded_source_defect", ALLOWED_DISPOSITIONS)

    def test_classifications_reconcile_to_1000(self):
        self.assertEqual(self.result["summary"], {
            "unchanged_approved": 979, "newly_approved": 21, "excluded": 0,
            "requires_additional_evidence": 0, "quarantined": 0,
            "fatal_conflicts": 0, "final_classifications": {"approved": 1000},
            "total": 1000,
        })

    def test_dependency_closure_has_no_orphans_or_nonapproved_candidates(self):
        closure = self.artifacts["dependency-closure-verification.json"]
        self.assertTrue(closure["valid"])
        self.assertTrue(closure["no_msh_candidates"])
        self.assertEqual(closure["orphaned_printing_candidate_ids"], [])
        self.assertEqual(len(closure["approved_candidate_ids"]), 1000)
        self.assertEqual(closure["excluded_candidate_ids"], [])
        self.assertEqual(closure["remaining_additional_evidence_candidate_ids"], [])
        self.assertEqual(closure["quarantined_candidate_ids"], [])

    def test_phase_115_artifacts_are_immutable(self):
        root = ROOT / "data/reviews/phase-115" / BATCH_ID
        actual = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in root.iterdir()}
        self.assertEqual(actual, PHASE_115_DIGESTS)

    def test_outputs_are_exactly_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            write_identifier_resolution_artifacts(ROOT / "data", temporary)
            generated = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in Path(temporary).iterdir()}
            retained = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in ARTIFACTS.iterdir()}
            self.assertEqual(generated, retained)
        self.assertEqual(resolve_first_mb2_identifiers(ROOT / "data")["decision_digest"],
                         self.result["decision_digest"])

    def test_pending_signature_no_msh_review_write_or_promotion(self):
        decision = self.artifacts["pending-review-decision.json"]
        readiness = self.artifacts["promotion-readiness-report.json"]
        self.assertEqual(decision["status"], "pending_operator_signature")
        for key in ("reviewer_identity", "review_reference", "reviewed_timestamp",
                    "operator_signature"):
            self.assertIsNone(decision[key])
        self.assertFalse(decision["batch_approved"])
        self.assertFalse(decision["canonical_write"])
        self.assertFalse(decision["promotion_authorized"])
        self.assertTrue(readiness["operator_signature_ready"])
        self.assertFalse(readiness["promotion_ready"])
        self.assertFalse(readiness["promotion_performed"])
        self.assertFalse(readiness["canonical_write"])
        self.assertEqual(decision["review_scope"]["marvel_candidates_reviewed"], 0)
        self.assertEqual(decision["review_scope"]["other_mb2_batches_reviewed"], 0)


if __name__ == "__main__":
    unittest.main()
