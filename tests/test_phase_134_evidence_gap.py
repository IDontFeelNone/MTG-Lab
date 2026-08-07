import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/reviews/phase-134/evidence-gap-report.json"


class Phase134EvidenceGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_bytes())

    def test_exact_retained_boundary_and_checksums(self):
        self.assertEqual(self.report["dataset"]["dataset_id"],
                         "mtgjson-allprintings-5.3.0+20260731-b47cc8360034")
        self.assertEqual(self.report["evidence_boundary"]["retained_set_codes"], ["MB2", "MSH"])
        self.assertEqual(len(self.report["source_artifacts"]), 12)
        for artifact in self.report["source_artifacts"]:
            self.assertEqual(hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest(),
                             artifact["sha256"])

    def test_exact_pilot_scope_has_no_supported_non_mb2_printings(self):
        cards = self.report["coverage_by_card"]
        self.assertEqual(len(cards), 10)
        self.assertEqual(len({x["card_id"] for x in cards}), 10)
        self.assertEqual(self.report["evidence_boundary"]["pilot_mb2_printing_records"], 10)
        self.assertEqual(self.report["evidence_boundary"]["pilot_non_mb2_printing_records"], 0)
        self.assertTrue(all(x["printing_count_before"] == x["printing_count_after"] == 1 for x in cards))
        self.assertTrue(all(x["coverage_state"] == "incomplete" for x in cards))

    def test_fail_closed_without_promotion_or_new_facts(self):
        self.assertEqual(self.report["status"], "blocked_retained_evidence_gap")
        self.assertEqual(self.report["promoted_printing_ids"], [])
        self.assertEqual(list((ROOT / "data/knowledge/facts").glob("*/*/phase134-*.json")), [])
        for flag in ("canonical_write", "promotion_performed", "inference_performed",
                     "external_acquisition_performed"):
            self.assertFalse(self.report[flag])
        self.assertEqual(self.report["canonical_digest_before"],
                         self.report["canonical_digest_after"])

    def test_prior_facts_and_market_boundary_remain_intact(self):
        facts = ROOT / "data/knowledge/facts"
        self.assertEqual(len(list(facts.glob("*/*/phase132-*.json"))), 90)
        phase133 = list(facts.glob("*/*/phase133-*.json"))
        self.assertEqual(len(phase133), 10)
        for path in phase133:
            self.assertEqual(json.loads(path.read_bytes())["value"]["data"]["coverage_state"],
                             "incomplete")
        self.assertEqual(len(list((ROOT / "data/market/observations").glob("*/*/*/*.json"))), 956)

    def test_deterministic_report_and_unsupported_claim_exclusion(self):
        expected = (json.dumps(self.report, indent=2, sort_keys=True,
                               separators=(",", ": ")) + "\n").encode()
        self.assertEqual(REPORT.read_bytes(), expected)
        self.assertIn("supply_quantity", self.report["unsupported_claims_excluded"])
        self.assertEqual(self.report["candidate_census"]["accepted_non_mb2_printing_candidates"], 0)


if __name__ == "__main__":
    unittest.main()
