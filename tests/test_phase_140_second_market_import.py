"""Focused Phase 140 second production MB2 market snapshot import tests."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from card_intelligence.explanation import CardValueExplanationEngine
from market.intelligence import MarketObservationRepository
from market.reporting import MarketHistoryReports, history_readiness
from market.models import MarketValidationError
from scripts.import_market_observations import import_acquisition

ROOT = Path(__file__).parents[1]
FIRST_RUN = "scryfall-mb2-30754638264-1"
SECOND_RUN = "scryfall-mb2-30959813191-1"


class Phase140SecondMarketImportTests(unittest.TestCase):
    def copy_data(self, temporary):
        target = Path(temporary) / "data"
        (target / "canonical").mkdir(parents=True)
        shutil.copy2(ROOT / "data/canonical/state.json", target / "canonical/state.json")
        shutil.copytree(ROOT / "data/market/acquisitions", target / "market/acquisitions")
        shutil.copytree(ROOT / "data/market/observations", target / "market/observations")
        shutil.copytree(ROOT / "data/market/imports", target / "market/imports")
        second_report = target / "market/imports" / SECOND_RUN / "import-report.json"
        if second_report.exists():
            changed = json.loads(second_report.read_text()).get("changed_files", [])
            shutil.rmtree(second_report.parent)
            for item in changed:
                if item.endswith("/import-report.json"):
                    continue
                (target.parent / item).unlink(missing_ok=True)
        shutil.copytree(ROOT / "data/knowledge", target / "knowledge")
        return target

    @staticmethod
    def observation_bytes(data):
        return {p.relative_to(data): p.read_bytes() for p in (data / "market/observations").rglob("*.json")}

    def test_successful_second_import_append_only_and_readiness(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary)
            first_bytes = self.observation_bytes(data)
            canonical_before = (data / "canonical/state.json").read_bytes()
            knowledge_before = {p.relative_to(data): p.read_bytes() for p in (data / "knowledge").rglob("*.json")}
            report = import_acquisition(data, SECOND_RUN)
            self.assertEqual(478, report["observations_written_for_this_acquisition"])
            self.assertEqual((478, 956), (report["total_historical_observations_before"], report["total_historical_observations_after"]))
            self.assertEqual((1, 2), (report["acquisition_count_before"], report["acquisition_count_after"]))
            self.assertEqual((1, 2), (report["distinct_source_timestamp_count_before"], report["distinct_source_timestamp_count_after"]))
            self.assertEqual("single_snapshot_only", report["readiness_state_before"])
            self.assertEqual("multiple_snapshots_descriptive_only", report["readiness_state_after"])
            self.assertEqual(478, report["comparable_exact_dimension_count"])
            self.assertEqual(478, report["multi_snapshot_dimension_count"])
            self.assertEqual(0, report["single_snapshot_dimension_count"])
            self.assertEqual(0, report["explicit_missing_dimension_count"])
            after_bytes = self.observation_bytes(data)
            for path, content in first_bytes.items():
                self.assertEqual(content, after_bytes[path])
            values = MarketObservationRepository(data / "market/observations").observations()
            self.assertEqual(956, len(values))
            self.assertEqual({FIRST_RUN, SECOND_RUN}, {x.provenance["acquisition_run_id"] for x in values})
            self.assertTrue(all(x.entity_type == "printing" and x.provider == "scryfall" for x in values))
            self.assertEqual(canonical_before, (data / "canonical/state.json").read_bytes())
            self.assertEqual(knowledge_before, {p.relative_to(data): p.read_bytes() for p in (data / "knowledge").rglob("*.json")})
            self.assertFalse(report["canonical_write"])
            self.assertFalse(report["promotion_performed"])

    def test_replay_conflict_rollback_and_tampering_boundaries(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary)
            report = import_acquisition(data, SECOND_RUN)
            before = self.observation_bytes(data)
            self.assertEqual(report, import_acquisition(data, SECOND_RUN))
            self.assertEqual(before, self.observation_bytes(data))
            path = data / "market/imports" / SECOND_RUN / "import-report.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(MarketValidationError, "conflicting replay"):
                import_acquisition(data, SECOND_RUN)
        for case in ("source", "manifest", "extra", "missing", "non_mb2", "canonical"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                data = self.copy_data(temporary)
                evidence = data / "market/acquisitions" / SECOND_RUN
                if case == "source":
                    (evidence / "source-mb2.json").write_bytes(b"[]\n")
                elif case == "manifest":
                    manifest = json.loads((evidence / "manifest.json").read_text())
                    manifest["provider"] = "other"
                    (evidence / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
                elif case == "extra":
                    (evidence / "extra.json").write_text("{}")
                elif case == "missing":
                    (evidence / "dry-run-report.json").unlink()
                elif case == "non_mb2":
                    records = json.loads((evidence / "source-mb2.json").read_text())
                    records[0]["set"] = "abc"
                    (evidence / "source-mb2.json").write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")
                elif case == "canonical":
                    state = json.loads((data / "canonical/state.json").read_text())
                    state["printing"].pop(next(iter(state["printing"])))
                    (data / "canonical/state.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
                with self.assertRaises(MarketValidationError):
                    import_acquisition(data, SECOND_RUN)
                self.assertFalse((data / "market/imports" / SECOND_RUN).exists())
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary)
            with self.assertRaisesRegex(OSError, "partial write"):
                import_acquisition(data, SECOND_RUN, fail_after=2)
            self.assertFalse((data / "market/imports" / SECOND_RUN).exists())
            self.assertEqual(478, MarketObservationRepository(data / "market/observations").count())

    def test_exact_dimension_isolation_cli_and_explanation_compatibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary)
            import_acquisition(data, SECOND_RUN)
            reports = MarketHistoryReports(data)
            coverage = reports.coverage("mystery-booster-2")["data"]
            self.assertEqual((379, 956, 2), (coverage["covered_printing_count"], coverage["observation_count"], coverage["acquisition_count"]))
            summary = reports.acquisition_summary(SECOND_RUN)["data"]
            self.assertEqual((478, 379, 478, 0), (summary["observation_count"], summary["distinct_printing_count"], summary["known_price_count"], summary["explicit_missing_price_count"]))
            readiness = history_readiness(MarketObservationRepository(data / "market/observations").observations())
            movement = readiness["descriptive_historical_movements"][0]
            self.assertEqual("descriptive_historical_movement", movement["label"])
            self.assertIn("not a prediction", movement["statement"])
            dimensions = {tuple(m["dimension"][k] for k in ("canonical_printing_id", "provider", "finish", "language", "currency", "price_type")) for m in readiness["descriptive_historical_movements"]}
            self.assertEqual(478, len(dimensions))
            explanation = CardValueExplanationEngine(data).explain(name="Sol Ring", include_observed_prices=True)
            self.assertEqual("card-value-explanation-v2", explanation["schema_version"])


if __name__ == "__main__":
    unittest.main()
