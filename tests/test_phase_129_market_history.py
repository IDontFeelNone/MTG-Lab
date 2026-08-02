"""Focused Phase 129 append-only market history tests."""

from datetime import date, datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from market.intelligence import MarketObservation, MarketObservationRepository
from scripts.import_market_observations import import_acquisition


ROOT = Path(__file__).parents[1]
RUN = "scryfall-mb2-30754638264-1"
UTC = timezone.utc


def observation(run, day, price="1.00"):
    stamp = datetime(2026, 7, day, 12, tzinfo=UTC)
    return MarketObservation(entity_type="printing", entity_id="phase129-printing",
        provider="fixture", observed_at=stamp, recorded_at=stamp, price=price,
        finish="nonfoil", provenance={"acquisition_run_id": run,
        "provider_identifier": run, "language": "en", "source_timestamp": stamp.isoformat()})


class Phase129MarketHistoryTests(unittest.TestCase):
    def copy_data(self, temporary):
        target = Path(temporary) / "data"
        (target / "canonical").mkdir(parents=True)
        shutil.copy2(ROOT / "data/canonical/state.json", target / "canonical/state.json")
        shutil.copytree(ROOT / "data/market/acquisitions", target / "market/acquisitions")
        return target

    def test_history_queries_are_deterministic_and_acquisition_aware(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = MarketObservationRepository(Path(temporary))
            later, earlier = observation("run-b", 2, "2.00"), observation("run-a", 1)
            repository.append(later); repository.append(earlier)
            self.assertEqual([x.price for x in repository.observations()], [earlier.price, later.price])
            self.assertEqual(repository.first(), earlier)
            self.assertEqual(repository.latest(), later)
            self.assertEqual(repository.count(acquisition_run_id="run-a"), 1)
            self.assertEqual(repository.count(observed_on=date(2026, 7, 2)), 1)
            self.assertEqual(repository.latest(observed_at_or_before=earlier.observed_at), earlier)

    def test_import_appends_to_existing_history_and_preserves_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary)
            repository = MarketObservationRepository(data / "market/observations")
            seed = observation("older-run", 1); seed_path = repository.append(seed)
            seed_bytes = seed_path.read_bytes()
            report = import_acquisition(data, RUN)
            self.assertEqual(report["observation_growth"], {"before": 1, "appended": 478, "after": 479})
            self.assertEqual(repository.count(), 479)
            self.assertEqual(seed_path.read_bytes(), seed_bytes)
            self.assertFalse(report["canonical_write"]); self.assertFalse(report["promotion_performed"])
            self.assertEqual(import_acquisition(data, RUN), report)

    def test_partial_append_rolls_back_without_touching_existing_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary)
            repository = MarketObservationRepository(data / "market/observations")
            seed_path = repository.append(observation("older-run", 1)); before = seed_path.read_bytes()
            with self.assertRaises(OSError): import_acquisition(data, RUN, fail_after=2)
            self.assertEqual(repository.count(), 1)
            self.assertEqual(seed_path.read_bytes(), before)
            self.assertFalse((data / "market/imports" / RUN).exists())

    def test_conflicting_replay_report_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = self.copy_data(temporary); import_acquisition(data, RUN)
            path = data / "market/imports" / RUN / "import-report.json"
            value = json.loads(path.read_text()); value["source_sha256"] = "0" * 64
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(Exception, "conflicting replay"):
                import_acquisition(data, RUN)


if __name__ == "__main__":
    unittest.main()
