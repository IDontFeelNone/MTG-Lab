"""Phase 117 governed operator authorization tests (unittest only)."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from production_evidence.operator_authorization import (
    BATCH_ID, build_signature_request, canonical_state_digest, record_authorization,
    verify_review_chain, write_phase117_artifacts,
)
from production_evidence.repository import EvidenceError

ROOT = Path(__file__).resolve().parents[1]
RETAINED = ROOT / "data/reviews/phase-117" / BATCH_ID


class Phase117AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request, cls.chain, cls.contract, cls.readiness = build_signature_request(ROOT / "data")

    def valid_fields(self, decision="authorize_for_promotion"):
        return {"operator_identity": "Jane Example", "operator_role": "Release manager",
            "review_reference": "ticket:MTGLAB-117", "reviewed_at": "2026-08-01T12:00:00Z",
            "authorization_decision": decision, "operator_notes": "Reviewed retained artifacts.",
            "signature_request_digest": self.request["signature_request_digest"],
            "authorized_batch_id": BATCH_ID,
            "authorized_candidate_digest": self.request["final_candidate_id_digest"]}

    def copied_data(self, temporary):
        root = Path(temporary) / "data"
        shutil.copytree(ROOT / "data", root, copy_function=lambda s, d: shutil.copy2(s, d))
        return root

    def test_complete_chain_exact_membership_scope_and_counts(self):
        chain = verify_review_chain(ROOT / "data")
        self.assertEqual(chain["candidate_count"], 1000)
        self.assertEqual(len(chain["final_candidate_ids"]), 1000)
        self.assertEqual(chain["approved_entity_counts"],
                         {"card": 384, "finish": 2, "identifier": 235, "printing": 379})
        self.assertEqual(chain["target_isolation_status"], "MB2_only")
        self.assertEqual(self.request["exact_promotion_scope"]["batch_ids"], [BATCH_ID])
        self.assertEqual(len(self.request["exact_promotion_scope"]["candidate_ids"]), 1000)

    def test_request_and_retained_outputs_are_deterministic(self):
        self.assertEqual(build_signature_request(ROOT / "data")[0], self.request)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out"
            write_phase117_artifacts(ROOT / "data", output)
            for path in output.iterdir():
                self.assertEqual(path.read_bytes(), (RETAINED / path.name).read_bytes())

    def test_missing_authorization_reports_no_write_or_promotion(self):
        self.assertFalse(self.readiness["operator_authorization_present"])
        self.assertFalse(self.readiness["eligible_for_promotion"])
        self.assertFalse(self.readiness["canonical_write"])
        self.assertFalse(self.readiness["promotion_performed"])
        self.assertFalse((RETAINED / "operator-authorization.json").exists())

    def test_blank_placeholder_and_ai_identity_rejected(self):
        for identity in ("", "placeholder", "Codex", "ChatGPT operator", "OpenAI", "AI"):
            with self.subTest(identity=identity), tempfile.TemporaryDirectory() as tmp:
                root = self.copied_data(tmp); fields = self.valid_fields(); fields["operator_identity"] = identity
                with self.assertRaises(EvidenceError): record_authorization(root, fields)

    def test_invalid_reference_timestamp_and_decision_rejected(self):
        for key, value in (("review_reference", "temporary note"), ("reviewed_at", "yesterday"),
                           ("reviewed_at", "2026-08-01T12:00:00"), ("authorization_decision", "approve")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = self.copied_data(tmp); fields = self.valid_fields(); fields[key] = value
                with self.assertRaises(EvidenceError): record_authorization(root, fields)

    def test_mismatched_batch_request_and_candidate_digest_rejected(self):
        for key in ("authorized_batch_id", "signature_request_digest", "authorized_candidate_digest"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = self.copied_data(tmp); fields = self.valid_fields(); fields[key] = "0" * 64
                with self.assertRaises(EvidenceError): record_authorization(root, fields)

    def test_valid_authorization_is_verified_idempotent_immutable_and_nonpromoting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.copied_data(tmp); before = canonical_state_digest(root)
            first = record_authorization(root, self.valid_fields())
            second = record_authorization(root, self.valid_fields())
            self.assertEqual(first, second)
            self.assertEqual(first["status"], "authorized_for_later_promotion")
            self.assertFalse(first["canonical_write"]); self.assertFalse(first["promotion_performed"])
            self.assertEqual(before, canonical_state_digest(root))
            conflicting = self.valid_fields(); conflicting["operator_notes"] = "Different"
            with self.assertRaises(EvidenceError): record_authorization(root, conflicting)

    def test_rejection_and_return_block_later_promotion(self):
        for decision, status in (("reject", "rejected"),
                                 ("return_for_additional_review", "returned_for_additional_review")):
            with self.subTest(decision=decision), tempfile.TemporaryDirectory() as tmp:
                artifact = record_authorization(self.copied_data(tmp), self.valid_fields(decision))
                self.assertEqual(artifact["status"], status)
                self.assertFalse(artifact["promotion_performed"])

    def test_digest_mismatch_and_canonical_drift_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.copied_data(tmp)
            ledger = root / "reviews/phase-116" / BATCH_ID / "updated-findings-report.json"
            ledger.write_text(ledger.read_text() + " ")
            with self.assertRaises(EvidenceError): verify_review_chain(root)
        with tempfile.TemporaryDirectory() as tmp:
            root = self.copied_data(tmp)
            (root / "canonical/drift").write_text("drift")
            with self.assertRaises(EvidenceError): record_authorization(root, self.valid_fields())


if __name__ == "__main__":
    unittest.main()
