import json
import os
from pathlib import Path
import subprocess
import unittest
from datetime import datetime, timezone
from decimal import Decimal

from jsonschema import Draft202012Validator, FormatChecker
from card_intelligence import CardValueExplanationEngine, explanation_bytes
from market.intelligence import MarketObservation

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def observation(*, printing="printing-a", provider="provider-a", finish="nonfoil",
                language="en", currency="USD", price_type="market", price="1.00",
                observed="2026-01-01T00:00:00+00:00", record="record-a"):
    return MarketObservation(entity_type="printing", entity_id=printing, provider=provider,
        observed_at=datetime.fromisoformat(observed),
        recorded_at=datetime(2026, 1, 2, tzinfo=timezone.utc), price=price,
        currency=currency, price_type=price_type, finish=finish,
        provenance={"language": language, "acquisition_run_id": "run-a",
            "source_provider_identifier": record, "source_url": "provider:source",
            "source_sha256": "a" * 64, "normalized_sha256": "b" * 64})


class Phase138ObservedPriceEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = CardValueExplanationEngine(DATA)

    def test_v1_is_default_and_v2_is_opt_in_and_schema_valid(self):
        v1 = self.engine.explain(name="Sol Ring")
        v2 = self.engine.explain(name="Sol Ring", include_observed_prices=True)
        self.assertEqual("card-value-explanation-v1", v1["schema_version"])
        self.assertNotIn("observed_price_evidence", v1["evidence_sections"])
        self.assertEqual("card-value-explanation-v2", v2["schema_version"])
        schema = json.loads((ROOT / "src/schemas/v1/card-value-explanation-v2.schema.json").read_text())
        self.assertEqual([], list(Draft202012Validator(schema,
            format_checker=FormatChecker()).iter_errors(v2)))

    def test_actual_sol_ring_prices_exact_printing_and_provenance(self):
        report = self.engine.explain(name="Sol Ring", include_observed_prices=True)
        evidence = report["evidence_sections"]["observed_price_evidence"]
        self.assertEqual(["3.98", "64.18"], sorted(x["price"]["amount"] for x in evidence["observations"]))
        self.assertEqual(["b43c646f-797d-5b5f-8ade-142486708c88"],
                         evidence["summary"]["covered_printing_ids"])
        self.assertEqual(135, evidence["summary"]["uncovered_retained_printing_count"])
        for item in evidence["observations"]:
            self.assertEqual("6ad8011d-3471-4369-9d68-b264cc027487", item["canonical_card_id"])
            self.assertEqual("scryfall-mb2-30754638264-1", item["acquisition_run_id"])
            self.assertTrue(item["observation_id"] and item["provider_record_id"])
            self.assertTrue(item["provenance"]["source_sha256"])
            self.assertEqual({"first": True, "latest": True, "only": True}, item["history_position"])

    def test_dimensions_are_isolated_missing_is_explicit_and_statistics_are_decimal(self):
        values = [observation(price="1.00", record="one"),
                  observation(price="3.00", observed="2026-01-02T00:00:00+00:00", record="two"),
                  observation(finish="foil", price="10.00"),
                  observation(language="fr", price="20.00"),
                  observation(currency="EUR", price="30.00"),
                  observation(price_type="retail", price="40.00"),
                  observation(provider="provider-b", price=None)]
        printings = [{"values": {"uuid": "printing-a", "card_id": "card-a",
                                  "set_id": "mb2", "collector_number": "1"}}]
        result = self.engine._observed_price_evidence("card-a", printings, values)
        self.assertEqual(6, len(result["compatible_dimension_summaries"]))
        base = next(x for x in result["compatible_dimension_summaries"]
                    if x["dimension"] == {"canonical_printing_id": "printing-a",
                    "provider": "provider-a", "finish": "nonfoil", "language": "en",
                    "currency": "USD", "price_type": "market"})
        self.assertEqual(("1.00", "3.00", "2.00", 2),
            (base["minimum_amount"], base["maximum_amount"], base["median_amount"],
             base["statistic_observation_count"]))
        missing = next(x for x in result["observations"] if x["provider"] == "provider-b")
        self.assertEqual({"state": "explicitly_unavailable", "amount": None}, missing["price"])

    def test_empty_determinism_limitations_and_no_prohibited_outputs(self):
        empty = self.engine._observed_price_evidence("card-a", [], [])
        self.assertEqual(0, empty["summary"]["total_observation_count"])
        self.assertEqual([], empty["observations"])
        first = explanation_bytes(self.engine.explain(name="Brainstorm", include_observed_prices=True))
        self.assertEqual(first, explanation_bytes(self.engine.explain(
            name="Brainstorm", include_observed_prices=True)))
        report = json.loads(first)
        self.assertIn("One retained snapshot does not establish a price trend.", report["limitations"])
        text = first.decode().lower()
        for key in ('"value_score":', '"prediction":', '"ranking":', '"recommendation":'):
            self.assertNotIn(key, text)

    def test_cli_name_and_card_id_v2_are_identical(self):
        env = {**os.environ, "PYTHONPATH": "src:."}
        command = ["python", "-m", "card_intelligence.cli", "explain"]
        named = subprocess.run(command + ["Sol Ring", "--include-observed-prices"], cwd=ROOT,
            env=env, check=True, capture_output=True, text=True)
        card_id = json.loads(named.stdout)["card_identity"]["card_id"]
        identified = subprocess.run(command + ["--card-id", card_id, "--include-observed-prices"],
            cwd=ROOT, env=env, check=True, capture_output=True, text=True)
        self.assertEqual(named.stdout, identified.stdout)


if __name__ == "__main__":
    unittest.main()
