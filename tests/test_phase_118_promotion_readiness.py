"""Phase 118 trusted-source promotion-readiness coverage (unittest only)."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from production_evidence.candidate_review import BATCH_ID, EVIDENCE_ID
from production_evidence.promotion_readiness import (
    EXPECTED_CANONICAL_PRE_STATE, build_promotion_plan, canonical_state_digest,
    evaluate_review_gate,
)
from production_evidence.repository import EvidenceError

ROOT = Path(__file__).resolve().parents[1]


class Phase118PromotionReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = build_promotion_plan(ROOT / "data")

    def copied_data(self, temporary):
        root = Path(temporary) / "data"
        shutil.copytree(ROOT / "data", root)
        return root

    def test_mb2_batch_is_validation_gated_and_promotion_ready(self):
        self.assertTrue(self.plan["promotion_ready"])
        self.assertEqual(self.plan["evidence_identity"], EVIDENCE_ID)
        self.assertEqual(self.plan["batch_id"], BATCH_ID)
        self.assertEqual(self.plan["candidate_count"], 1000)
        self.assertEqual(self.plan["unresolved_count"], 0)
        self.assertEqual(self.plan["dependency_closure"], "valid")

    def test_scope_is_exactly_one_mb2_batch_and_excludes_msh(self):
        self.assertEqual(self.plan["target"], {"code": "MB2", "name": "Mystery Booster 2"})
        self.assertEqual(self.plan["target_isolation"], "MB2_only")
        self.assertEqual(self.plan["entity_counts"],
                         {"card": 384, "finish": 2, "identifier": 235, "printing": 379})

    def test_trusted_provider_and_explicit_invocation_boundary(self):
        self.assertEqual(self.plan["trusted_providers"], ["mtgjson"])
        self.assertTrue(self.plan["explicit_invocation_required"])
        self.assertFalse(self.plan["promotion_performed"])
        self.assertFalse(self.plan["canonical_write"])

    def test_plan_is_deterministic_and_requires_audit_and_rollback(self):
        self.assertEqual(build_promotion_plan(ROOT / "data"), self.plan)
        self.assertIn("pre_and_post_state_digests", self.plan["audit_requirements"])
        self.assertIn("audit_replay_verification", self.plan["rollback_requirements"])

    def test_unresolved_quarantined_conflicting_and_incomplete_reviews_block(self):
        cases = ({"approved": 999}, {"unresolved": 1}, {"quarantined": 1},
                 {"fatal_conflicts": 1}, {"orphaned": 1}, {"target_isolated": False})
        defaults = dict(approved=1000, unresolved=0, quarantined=0,
                        fatal_conflicts=0, orphaned=0, target_isolated=True)
        for changed in cases:
            with self.subTest(changed=changed):
                self.assertTrue(evaluate_review_gate(**{**defaults, **changed}))

    def test_canonical_pre_state_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_data(temporary)
            (root / "canonical/drift").write_text("drift")
            with self.assertRaisesRegex(EvidenceError, "canonical pre-state drift"):
                build_promotion_plan(root)
        audit = json.loads((ROOT / "data/audit/bounded_promotions/phase-119-mb2-batch-000001-e32022126c07.json").read_text())
        self.assertEqual(canonical_state_digest(ROOT / "data"), audit["canonical_post_state_digest"])
        self.assertEqual(audit["canonical_pre_state_digest"], EXPECTED_CANONICAL_PRE_STATE)

    def test_checksum_and_review_artifact_tampering_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_data(temporary)
            payload = (root / "production_runs" / EVIDENCE_ID /
                       "review_payloads/mb2/mb2-batch-000001-e32022126c07.json")
            payload.write_text(payload.read_text() + " ")
            with self.assertRaises(EvidenceError): build_promotion_plan(root)
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_data(temporary)
            report = root / "reviews/phase-116" / BATCH_ID / "updated-findings-report.json"
            value = json.loads(report.read_text()); value["summary"]["quarantined"] = 1
            report.write_text(json.dumps(value))
            with self.assertRaisesRegex(EvidenceError, "Phase 116 artifact mismatch"):
                build_promotion_plan(root)


if __name__ == "__main__": unittest.main()
