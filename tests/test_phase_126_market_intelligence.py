import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from market import (MarketAnalytics, MarketObservation, MarketObservationRepository,
                    MarketQueryService, MarketValidationError)
from query import CanonicalQueryEngine, CanonicalQueryService

ROOT = Path(__file__).parents[1]
NOW = datetime(2026, 8, 1, 12, tzinfo=timezone.utc)


def observation(day, price, provider="alpha", **changes):
    values = dict(entity_type="printing", entity_id="magic.lea.161.en", provider=provider,
        observed_at=NOW - timedelta(days=day), recorded_at=NOW, price=price,
        listing_count=50, sales_count=15, spread="0.10", provider_confidence="0.80",
        provenance={"source_record": f"fixture-{provider}-{day}"})
    values.update(changes)
    return MarketObservation(**values)


class Phase126MarketIntelligenceTests(unittest.TestCase):
    def test_deterministic_analytics_and_metrics(self):
        values = [observation(30, "10"), observation(7, "12"), observation(1, "15"), observation(0, "20")]
        analytics = MarketAnalytics()
        self.assertEqual(analytics.summarize(values), analytics.summarize(reversed(values)))
        result = analytics.summarize(values)
        self.assertEqual(result["current_market_value"], "20.000000")
        self.assertEqual(result["average_market_value"], "14.250000")
        self.assertEqual(result["daily_change"], "0.333333")
        self.assertEqual(result["weekly_change"], "0.666667")
        self.assertEqual(result["monthly_change"], "1.000000")
        self.assertIsNotNone(result["price_volatility"])
        self.assertEqual(result["liquidity_score"], "0.633333")
        self.assertEqual(result["confidence"], "0.840000")

    def test_append_only_immutable_history_integrity_and_provider_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = MarketObservationRepository(Path(directory)); first = observation(1, "2")
            path = repo.append(first); original = path.read_bytes()
            self.assertEqual(repo.append(first), path)  # byte-identical replay is safe
            repo.append(observation(0, "7", provider="beta"))
            self.assertEqual(len(repo.observations(provider="alpha")), 1)
            self.assertEqual(len(repo.observations(provider="beta")), 1)
            value = json.loads(original); value["price"] = "999"; path.write_text(json.dumps(value))
            with self.assertRaisesRegex(MarketValidationError, "integrity"): repo.load(path)

    def test_query_unknown_provenance_confidence_and_comparison(self):
        engine = CanonicalQueryEngine("magic", games_root=ROOT/"data/canonical/games", data_root=ROOT/"data")
        with tempfile.TemporaryDirectory() as directory:
            repo = MarketObservationRepository(Path(directory)); service = MarketQueryService(CanonicalQueryService(engine), repo)
            unknown = service.printing("magic.lea.161.en")
            self.assertEqual(unknown["status"], "unknown"); self.assertIsNone(unknown["answer"]["current_market_value"])
            repo.append(observation(0, "4")); repo.append(observation(0, "5", provider="beta"))
            answer = service.printing("magic.lea.161.en", provider="alpha")
            self.assertEqual(answer["provider"], "alpha"); self.assertTrue(answer["provenance"])
            comparison = service.provider_comparison("printing", "magic.lea.161.en")
            self.assertEqual([x["provider"] for x in comparison["answer"]], ["alpha", "beta"])

    def test_cli_json_and_no_canonical_writes(self):
        before = hashlib.sha256((ROOT/"data/canonical/state.json").read_bytes()).hexdigest()
        run = subprocess.run([sys.executable, "-m", "mtglab", "--data-root", "data", "market", "printing",
            "magic.lea.161.en"], cwd=ROOT, env={**os.environ, "PYTHONPATH":"src"}, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout); self.assertEqual(result["schema_version"], "market-query-v1")
        self.assertEqual(result["status"], "unknown"); self.assertIsNone(result["provider"])
        after = hashlib.sha256((ROOT/"data/canonical/state.json").read_bytes()).hexdigest()
        self.assertEqual(before, after)


if __name__ == "__main__": unittest.main()
