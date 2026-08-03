"""Focused Phase 130 read-only historical market reporting tests."""
from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from market.cli import main
from market.intelligence import MarketObservation, MarketObservationRepository
from market.reporting import MAX_LIMIT, MarketHistoryReports

ROOT = Path(__file__).parents[1]
RUN = "scryfall-mb2-30754638264-1"


class Phase130MarketCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = MarketHistoryReports(ROOT / "data")
        cls.printing = cls.reports.all_observations[0].entity_id

    def invoke(self, *arguments):
        output = StringIO()
        with redirect_stdout(output): status = main(["--data-root", str(ROOT / "data"), *arguments])
        return status, json.loads(output.getvalue()), output.getvalue()

    def test_listing_and_exact_dimension_filters_are_deterministic(self):
        args = ("observations", "list", "--printing-id", self.printing, "--provider", "scryfall",
                "--acquisition-run-id", RUN, "--finish", "nonfoil", "--language", "en",
                "--currency", "usd", "--price-type", "market")
        first = self.invoke(*args); second = self.invoke(*args)
        self.assertEqual(first, second); self.assertEqual(first[0], 0)
        self.assertEqual(first[1]["ordering"], ["observed_at", "recorded_at", "provider", "observation_id"])
        for value in first[1]["data"]:
            self.assertEqual((value["entity_id"], value["provider"], value["currency"], value["price_type"]),
                             (self.printing, "scryfall", "USD", "market"))

    def test_first_latest_count_date_range_and_as_of(self):
        source = self.reports.all_observations[0].observed_at.isoformat()
        for operation in ("first", "latest", "count"):
            status, result, _ = self.invoke("observations", operation, "--acquisition-run-id", RUN,
                "--observed-from", source, "--observed-to", source, "--as-of", source)
            self.assertEqual(status, 0); self.assertFalse(result["empty_result"])
        self.assertEqual(self.invoke("observations", "count", "--finish", "foil")[1]["data"]["count"], 121)

    def test_history_snapshot_coverage_and_acquisition_summary(self):
        history = self.invoke("printing-history", self.printing)[1]
        self.assertTrue(history["data"]); self.assertEqual(history["report_type"], "printing-history")
        snapshot = self.invoke("snapshot", "--as-of", "2026-08-02T09:09:45.851000Z")[1]
        self.assertEqual(snapshot["result_count"], 478)
        self.assertTrue(all(x["observed_at"] <= "2026-08-02T09:09:45.851000Z" for x in snapshot["data"]))
        coverage = self.invoke("coverage", "--product", "mystery-booster-2")[1]["data"]
        self.assertEqual((coverage["covered_printing_count"], coverage["uncovered_printing_count"],
                          coverage["total_canonical_printing_count"]), (379, 0, 379))
        summary = self.invoke("acquisition-summary", RUN)[1]["data"]
        self.assertEqual(summary["observation_count"], 478); self.assertEqual(summary["distinct_printing_count"], 379)
        self.assertEqual(summary["known_price_count"] + summary["explicit_missing_price_count"], 478)

    def test_empty_unknown_and_invalid_inputs(self):
        early = self.invoke("observations", "list", "--as-of", "2020-01-01T00:00:00Z")[1]
        self.assertTrue(early["empty_result"]); self.assertEqual(early["data"], [])
        invalid = (("--printing-id", "unknown"), ("--currency", "EUR"), ("--price-type", "retail"),
                   ("--as-of", "yesterday"), ("--observed-from", "2026-08-03T00:00:00Z", "--observed-to", "2026-08-02T00:00:00Z"),
                   ("--limit", str(MAX_LIMIT + 1)))
        for arguments in invalid:
            status, result, _ = self.invoke("observations", "list", *arguments)
            self.assertEqual(status, 2); self.assertFalse(result["valid"])

    def test_explicit_missing_price_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary); (data / "canonical").mkdir()
            shutil.copy2(ROOT / "data/canonical/state.json", data / "canonical/state.json")
            stamp = datetime(2026, 8, 2, tzinfo=timezone.utc)
            item = MarketObservation("printing", self.printing, "fixture", stamp, stamp, None,
                provenance={"acquisition_run_id": "fixture-run", "language": "en",
                            "canonical_snapshot_identity": "fixture"})
            MarketObservationRepository(data / "market/observations").append(item)
            report = MarketHistoryReports(data).observations("list", {"printing_id": self.printing})
            self.assertIsNone(report["data"][0]["price"]); self.assertEqual(report["result_count"], 1)

    def test_commands_do_not_write_any_retained_data(self):
        roots = [ROOT / "data/canonical", ROOT / "data/market/acquisitions",
                 ROOT / "data/market/observations", ROOT / "data/market/imports"]
        before = {path: path.read_bytes() for root in roots for path in root.rglob("*") if path.is_file()}
        self.invoke("observations", "list"); self.invoke("coverage", "--product", "mystery-booster-2")
        self.invoke("acquisition-summary", RUN); self.invoke("snapshot", "--as-of", "2026-08-03T00:00:00Z")
        after = {path: path.read_bytes() for root in roots for path in root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__": unittest.main()
