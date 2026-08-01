import json
import subprocess
import sys
import unittest
from pathlib import Path

from query import CanonicalQueryEngine, CanonicalQueryService, QueryError


ROOT = Path(__file__).parents[1]


class CanonicalQueryServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = CanonicalQueryService(CanonicalQueryEngine(
            "magic", games_root=ROOT / "data/canonical/games", data_root=ROOT / "data"))

    def test_name_query_is_repeatable_and_explainable(self):
        first = self.service.cards(name="  SOL ring ").as_dict()
        second = self.service.cards(name="  SOL ring ").as_dict()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "known")
        self.assertTrue(first["answer"])
        self.assertTrue(first["canonical_identifiers"])
        self.assertTrue(first["snapshot_identity"].startswith("sha256:"))
        self.assertEqual(len(first["provenance"]), len(first["answer"]))

    def test_identifier_and_every_printing_lookup(self):
        printing = self.service.printing("magic.mb2.1.en").as_dict()
        self.assertEqual(printing["canonical_identifiers"], ["magic.mb2.1.en"])
        card = self.service.printings_for_card("magic.abzan-falconer").as_dict()
        self.assertIn("magic.mb2.1.en", card["canonical_identifiers"])
        values = card["answer"][0]["canonical_values"]
        for field in ("language", "rarity", "collector_number"):
            self.assertIn(field, values)

    def test_unknown_and_missing_are_not_inferred(self):
        unknown = self.service.cards(type="definitely-not-canonical").as_dict()
        missing = self.service.product("not-a-product").as_dict()
        self.assertEqual(unknown["status"], "not_found")
        self.assertEqual(unknown["answer"], [])
        self.assertIsNone(unknown["confidence"])
        self.assertEqual(missing["status"], "not_found")

    def test_product_summary_uses_canonical_membership(self):
        result = self.service.product("mystery_booster_2").as_dict()
        self.assertEqual(result["status"], "known")
        self.assertEqual(result["answer"]["validation_status"], "foundation")
        self.assertEqual(result["answer"]["statistics"]["printing_count"], 4)
        self.assertFalse(result["answer"]["promoted_status"])

    def test_malformed_queries_fail(self):
        with self.assertRaises(QueryError): self.service.cards()
        with self.assertRaises(QueryError): self.service.cards(name=" ")
        with self.assertRaises(QueryError): self.service.collection({}, "prices")

    def test_cli_json_and_error_behavior(self):
        base = [sys.executable, "-m", "mtglab", "--data-root", "data", "query"]
        run = subprocess.run(base + ["card", "Sol Ring"], cwd=ROOT,
            env={"PYTHONPATH": "src"}, text=True, capture_output=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["schema_version"], "canonical-query-v1")
        bad = subprocess.run(base + ["card"], cwd=ROOT, env={"PYTHONPATH": "src"},
            text=True, capture_output=True, check=False)
        self.assertEqual(bad.returncode, 2)
        self.assertFalse(json.loads(bad.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
