from datetime import datetime, timezone
from decimal import Decimal
import unittest

from market.intelligence import MarketObservation
from market.reporting import history_readiness


def item(stamp, price, *, finish="nonfoil", run="run-1", language="en"):
    return MarketObservation(entity_type="printing", entity_id="printing-1", provider="scryfall",
        observed_at=datetime.fromisoformat(stamp), recorded_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        price=price, currency="USD", price_type="market", finish=finish,
        provenance={"language": language, "acquisition_run_id": run})


class Phase139MarketReadinessTests(unittest.TestCase):
    def test_zero_and_one_snapshot_states(self):
        self.assertEqual("no_observations", history_readiness([])["readiness_state"])
        report = history_readiness([item("2026-01-01T00:00:00+00:00", "1.00")])
        self.assertEqual("single_snapshot_only", report["readiness_state"])
        self.assertFalse(report["supports_descriptive_movement"])

    def test_exact_dimension_decimal_descriptive_movement(self):
        report = history_readiness([
            item("2026-01-01T00:00:00+00:00", "1.20"),
            item("2026-01-03T00:00:00+00:00", "1.50", run="run-2"),
            item("2026-01-03T00:00:00+00:00", "9.00", finish="foil", run="run-2")])
        self.assertEqual("multiple_snapshots_descriptive_only", report["readiness_state"])
        self.assertEqual(1, report["comparable_dimension_count"])
        movement = report["descriptive_historical_movements"][0]
        self.assertEqual(("1.20", "1.50", "0.30", "25.000000", 172800),
            (movement["first_amount"], movement["latest_amount"], movement["absolute_change"],
             movement["percentage_change"], movement["elapsed_seconds"]))

    def test_incompatible_and_missing_are_not_comparable(self):
        report = history_readiness([
            item("2026-01-01T00:00:00+00:00", "1.00"),
            item("2026-01-02T00:00:00+00:00", None, run="run-2"),
            item("2026-01-02T00:00:00+00:00", "2.00", finish="foil", run="run-2")])
        self.assertEqual("insufficient_comparable_dimensions", report["readiness_state"])
        self.assertEqual([], report["descriptive_historical_movements"])
        self.assertEqual(1, len(report["dimensions_with_missing_observations"]))


if __name__ == "__main__": unittest.main()
