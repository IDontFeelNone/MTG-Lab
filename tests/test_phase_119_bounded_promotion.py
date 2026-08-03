"""Phase 119 exact-batch canonical promotion coverage (unittest only)."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from analytics import CanonicalAnalyticsEngine
from production_evidence.bounded_promotion import (
    ENTITY_COUNTS, EXPECTED_CANDIDATE_DIGEST, PROMOTION_ID, preflight, promote, rollback,
)
from production_evidence.promotion_readiness import canonical_state_digest
from production_evidence.repository import EvidenceError
import production_evidence.bounded_promotion as bounded
from query import CanonicalQueryEngine

ROOT = Path(__file__).resolve().parents[1]


class Phase119BoundedPromotionTests(unittest.TestCase):
    def copied_pre_state(self, temporary):
        root = Path(temporary) / "data"
        shutil.copytree(ROOT / "data", root)
        (root / "canonical/state.json").unlink(missing_ok=True)
        (root / "audit/bounded_promotions" / f"{PROMOTION_ID}.json").unlink(missing_ok=True)
        return root

    def test_retained_promotion_has_exact_deterministic_scope_and_audit(self):
        audit_path = ROOT / "data/audit/bounded_promotions" / f"{PROMOTION_ID}.json"
        audit = json.loads(audit_path.read_text())
        self.assertEqual(audit["candidate_count"], 1000)
        self.assertEqual(audit["candidate_id_digest"], EXPECTED_CANDIDATE_DIGEST)
        self.assertEqual(audit["entity_counts"], ENTITY_COUNTS)
        self.assertEqual(audit["excluded_targets"], ["MSH", "all_other_batches"])
        phase136 = json.loads((ROOT / "data/audit/bounded_promotions/phase-136-mtgjson-pilot-30786023976-1.json").read_text())
        self.assertEqual(phase136["canonical_pre_state_digest"], audit["canonical_post_state_digest"])
        self.assertEqual(canonical_state_digest(ROOT / "data"), phase136["canonical_post_state_digest"])
        self.assertEqual(audit, json.loads(audit_path.read_text()))

    def test_preflight_and_output_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_pre_state(temporary)
            self.assertEqual(preflight(root), preflight(root))
            first = promote(root)
            state = (root / "canonical/state.json").read_bytes()
            self.assertTrue(promote(root)["idempotent"])
            self.assertEqual(state, (root / "canonical/state.json").read_bytes())
            self.assertEqual(first["canonical_post_state_digest"], canonical_state_digest(root))

    def test_drift_evidence_and_review_tampering_fail_closed(self):
        cases = ("drift", "evidence", "review")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = self.copied_pre_state(temporary)
                if case == "drift": (root / "canonical/drift").write_text("x")
                elif case == "evidence":
                    path = root / "production_runs/30663562841-review-payload-v2/metadata.json"
                    path.write_text(path.read_text() + " ")
                else:
                    path = root / "reviews/phase-116/mb2-batch-000001-e32022126c07/updated-findings-report.json"
                    path.write_text(path.read_text() + " ")
                with self.assertRaises(EvidenceError): promote(root)

    def test_atomic_rollback_on_write_or_audit_failure(self):
        for point in ("after_canonical_write", "after_audit_write"):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as temporary:
                root = self.copied_pre_state(temporary); before = canonical_state_digest(root)
                def fail(actual):
                    if actual == point: raise OSError("injected failure")
                with self.assertRaises(OSError): promote(root, failure_hook=fail)
                self.assertEqual(canonical_state_digest(root), before)
                self.assertFalse((root / "audit/bounded_promotions" / f"{PROMOTION_ID}.json").exists())

    def test_rollback_metadata_execution_and_conflicting_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_pre_state(temporary); audit = promote(root)
            self.assertEqual(audit["rollback"]["expected_post_rollback_digest"],
                             audit["canonical_pre_state_digest"])
            result = rollback(root)
            self.assertEqual(result["canonical_state_digest"], audit["canonical_pre_state_digest"])
            # Immutable history makes a rolled-back promotion a conflicting replay, not a new write.
            with self.assertRaisesRegex(EvidenceError, "conflicts with immutable audit"): promote(root)

    def test_duplicate_orphan_and_conflicting_repeat_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_pre_state(temporary); payload = bounded._payload(root)
            duplicate = json.loads(json.dumps(payload))
            cards = [row for row in duplicate["candidate_payloads"] if row["entity_type"] == "card"]
            cards[1]["mapped_fields"]["card_reference"] = cards[0]["mapped_fields"]["card_reference"]
            with patch.object(bounded, "_payload", return_value=duplicate):
                with self.assertRaisesRegex(EvidenceError, "duplicate canonical card identity"):
                    preflight(root)
            orphan = json.loads(json.dumps(payload))
            printing = next(row for row in orphan["candidate_payloads"] if row["entity_type"] == "printing")
            printing["mapped_fields"]["card_reference"] = "00000000-0000-0000-0000-000000000000"
            with patch.object(bounded, "_payload", return_value=orphan):
                with self.assertRaisesRegex(EvidenceError, "dependency orphan"):
                    preflight(root)
            promote(root)
            audit_path = root / "audit/bounded_promotions" / f"{PROMOTION_ID}.json"
            audit = json.loads(audit_path.read_text()); audit["candidate_id_digest"] = "0" * 64
            audit_path.write_text(json.dumps(audit))
            with self.assertRaisesRegex(EvidenceError, "conflicting promotion replay"): promote(root)

    def test_dependency_references_and_query_analytics_compatibility(self):
        state = json.loads((ROOT / "data/canonical/state.json").read_text())
        self.assertEqual({kind: len(rows) for kind, rows in state.items() if kind != "printing"},
                         {kind: count for kind, count in ENTITY_COUNTS.items() if kind != "printing"})
        self.assertEqual(len(state["printing"]), 913)
        cards = set(state["card"])
        self.assertTrue(all(row["values"]["card_id"] in cards for row in state["printing"].values()))
        self.assertEqual(sum(row["values"]["set_id"] == "mb2" for row in state["printing"].values()), 379)
        query = CanonicalQueryEngine(data_root=ROOT / "data")
        summary = CanonicalAnalyticsEngine(query).summary().data
        self.assertGreaterEqual(summary["entity_counts_by_type"]["card"], 384)
        self.assertGreaterEqual(summary["entity_counts_by_type"]["printing"], 379)
        self.assertGreaterEqual(summary["printings_per_set"]["mb2"], 379)


if __name__ == "__main__": unittest.main()
