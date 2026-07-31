"""Phase 107 dataset-delivery tests (unittest only)."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from promotion import MTGJSONDatasetDelivery
from scripts.mtgjson_delivery import main


def fixture(path):
    path.write_text(json.dumps({"meta": {"date": "2026-07-31", "version": "5.2.1"},
        "data": {"TST": {"code": "TST", "name": "Test", "cards": [
            {"uuid": "00000000-0000-0000-0000-000000000001", "name": "One",
             "number": "1", "rarity": "common", "language": "English",
             "finishes": ["nonfoil"], "layout": "normal", "colors": []}]}}}))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.source = self.root / "AllPrintings.json"; self.sha = fixture(self.source)
        self.delivery = MTGJSONDatasetDelivery(self.root / "state", batch_size=2)

    def tearDown(self): self.temp.cleanup()

    def test_missing_and_mismatched_checksum_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "required"): self.delivery.verify(self.source, "")
        with self.assertRaisesRegex(ValueError, "mismatch"): self.delivery.verify(self.source, "0" * 64)
        self.assertFalse((self.root / "state/canonical/state.json").exists())

    def test_malformed_source_and_symlink_are_rejected(self):
        bad = self.root / "bad.json"; bad.write_text("{")
        digest = hashlib.sha256(bad.read_bytes()).hexdigest()
        with self.assertRaises((ValueError, json.JSONDecodeError)): self.delivery.plan(bad, digest)
        link = self.root / "link.json"; link.symlink_to(self.source)
        with self.assertRaisesRegex(ValueError, "non-symlink"): self.delivery.verify(link, self.sha)

    def test_plan_is_deterministic_dry_run_and_generates_reports(self):
        first = self.delivery.plan(self.source, self.sha)
        second = self.delivery.plan(self.source, self.sha)
        self.assertEqual(first["manifest"]["batches"], second["manifest"]["batches"])
        self.assertEqual(first["mode"], "dry-run"); self.assertFalse(first["canonical_write"])
        self.assertFalse((self.root / "state/canonical/state.json").exists())
        names = {p.name for p in (self.root / "state/reports/mtgjson-delivery").glob("*.json")}
        self.assertTrue({"acquisition.json", "checksum-verification.json", "batch-plan.json",
                         "dataset-summary.json", "validation-log.json", "rollback.json"} <= names)

    def test_promotion_requires_review_metadata_and_exactly_one_batch(self):
        batch = self.delivery.plan(self.source, self.sha)["manifest"]["batches"][0]["batch_id"]
        with self.assertRaisesRegex(ValueError, "reviewer"):
            self.delivery.promote(self.source, self.sha, batch, reviewer="", review_reference="R-1")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            self.delivery.promote(self.source, self.sha, "all", reviewer="reviewer", review_reference="R-1")

    def test_cli_defaults_to_plan_only_and_errors_are_json(self):
        with patch("builtins.print") as output:
            code = main(["--data-root", str(self.root / "cli"), "plan", "--source",
                         str(self.source), "--sha256", self.sha])
        self.assertEqual(code, 0)
        self.assertIn('"mode": "dry-run"', output.call_args.args[0])
        with patch("builtins.print"):
            self.assertEqual(main(["--data-root", str(self.root / "bad"), "verify", "--source",
                                  str(self.source), "--sha256", "bad"]), 2)


if __name__ == "__main__": unittest.main()
