"""Focused Phase 128 production market observation import tests."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from market.intelligence import MarketAnalytics, MarketObservationRepository
from market.models import MarketValidationError
from scripts.import_market_observations import import_acquisition


ROOT = Path(__file__).parents[1]
RUN = "scryfall-mb2-30754638264-1"


class Phase128MarketImportTests(unittest.TestCase):
    def copy_data(self, temporary):
        target = Path(temporary) / "data"
        (target / "canonical").mkdir(parents=True)
        shutil.copy2(ROOT / "data/canonical/state.json", target / "canonical/state.json")
        shutil.copytree(ROOT / "data/market/acquisitions", target / "market/acquisitions")
        return target

    def test_verified_import_exact_resolution_census_and_query_analytics_compatibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary); canonical_before = (data / "canonical/state.json").read_bytes()
            report = import_acquisition(data, RUN)
            self.assertEqual(report["matched_printing_count"], 379)
            self.assertEqual(report["total_observations_written"], 478)
            self.assertEqual(report["production_mb2_printing_coverage_before"], {"covered": 0, "total": 379})
            self.assertEqual(report["production_mb2_printing_coverage_after"], {"covered": 379, "total": 379})
            values = MarketObservationRepository(data / "market/observations").observations()
            self.assertEqual(len(values), 478)
            self.assertTrue(all(x.entity_type == "printing" and x.price is not None for x in values))
            self.assertTrue(all(x.provenance["acquisition_run_id"] == RUN for x in values))
            self.assertEqual(MarketAnalytics().summarize(values)["status"], "known")
            self.assertEqual((data / "canonical/state.json").read_bytes(), canonical_before)
            self.assertFalse(report["canonical_write"]); self.assertFalse(report["promotion_performed"])

    def test_byte_identical_replay_and_conflicting_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary); first = import_acquisition(data, RUN)
            before = {p.relative_to(data): p.read_bytes() for p in (data / "market/observations").rglob("*.json")}
            self.assertEqual(first, import_acquisition(data, RUN))
            self.assertEqual(before, {p.relative_to(data): p.read_bytes() for p in (data / "market/observations").rglob("*.json")})
            path = data / "market/imports" / RUN / "import-report.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(MarketValidationError, "conflicting replay"):
                import_acquisition(data, RUN)

    def test_manifest_payload_tampering_extra_missing_files_and_canonical_drift(self):
        cases = ("tamper", "extra", "missing", "drift")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                data = self.copy_data(temporary); evidence = data / "market/acquisitions" / RUN
                if case == "tamper": (evidence / "source-mb2.json").write_bytes(b"[]\n")
                if case == "extra": (evidence / "extra.json").write_text("{}")
                if case == "missing": (evidence / "dry-run-report.json").unlink()
                if case == "drift": (data / "canonical/state.json").write_bytes(b"{}\n")
                with self.assertRaises(MarketValidationError): import_acquisition(data, RUN)
                self.assertFalse((data / "market/observations").exists())

    def test_symlink_rejected_and_atomic_rollback_after_partial_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary); evidence = data / "market/acquisitions" / RUN
            source = evidence / "source-mb2.json"; real = evidence / "real-source.json"
            source.rename(real); source.symlink_to(real.name)
            with self.assertRaisesRegex(MarketValidationError, "extra or missing|regular"):
                import_acquisition(data, RUN)
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary)
            with self.assertRaisesRegex(OSError, "partial write"):
                import_acquisition(data, RUN, fail_after=3)
            self.assertFalse((data / "market/observations").exists())
            self.assertFalse((data / "market/imports" / RUN / "import-report.json").exists())

    def test_production_report_is_deterministic_and_explicit(self):
        report = json.loads((ROOT / "data/market/imports" / RUN / "import-report.json").read_text())
        self.assertEqual(report["unmatched_count"], 6)
        self.assertEqual(report["ambiguous_count"], 0)
        self.assertEqual(report["rejected_count"], 0)
        self.assertEqual(report["explicit_missing_price_observation_count"], 0)
        self.assertEqual(report["duplicate_count"], 0)
        self.assertTrue(report["observations_persisted"])
        self.assertEqual(len(report["changed_files"]), 479)


if __name__ == "__main__":
    unittest.main()
