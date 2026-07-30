import hashlib
import json
import unittest
from pathlib import Path

from external_ingestion import MTGJSONAdapter


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/mtgjson/AllPrintings.json"
REPORT = ROOT / "data/validation/mystery_booster_2/phase_90_mtgjson_evidence_gap.json"


class Phase90MTGJSONEvidenceGapTests(unittest.TestCase):
    def test_report_deterministically_matches_supplied_non_mb2_fixture(self):
        payload = FIXTURE.read_bytes()
        source = json.loads(payload)
        report = json.loads(REPORT.read_text())
        rows = list(MTGJSONAdapter().records(payload))

        self.assertEqual(hashlib.sha256(payload).hexdigest(), report["dataset"]["sha256"])
        self.assertEqual(sorted(source["data"]), report["observed"]["set_codes"])
        self.assertNotIn("MB2", source["data"])
        self.assertEqual(
            report["observed"],
            {"cards": 10, "normalized_records": len(rows), "printings": 10,
             "set_codes": ["TST"], "sets": 1},
        )
        self.assertEqual(report["status"], "stopped_after_validation_evidence_gap")
        self.assertTrue(all(value == 0 for value in report["result"].values()))


if __name__ == "__main__":
    unittest.main()
