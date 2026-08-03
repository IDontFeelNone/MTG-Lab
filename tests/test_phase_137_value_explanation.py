import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from card_intelligence import CardValueExplanationEngine, ExplanationError, explanation_bytes

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PILOT = ["Brainstorm", "Command Tower", "Counterspell", "Goblin Charbelcher",
         "Goblin King", "Sol Ring", "Swords to Plowshares", "Treasure Cruise",
         "Walking Ballista", "Wishclaw Talisman"]
PROTECTED = ("data/canonical", "data/market/observations", "data/market/acquisitions")


def digest_tree(relative):
    digest = hashlib.sha256()
    root = ROOT / relative
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode() + b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


class Phase137ValueExplanationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = CardValueExplanationEngine(DATA)
        cls.before = {path: digest_tree(path) for path in PROTECTED}

    def test_exact_pilot_determinism_repeatability_and_no_value_output(self):
        for name in PILOT:
            first = explanation_bytes(self.engine.explain(name=name))
            second = explanation_bytes(self.engine.explain(name=name))
            self.assertEqual(first, second)
            text = first.decode().lower()
            for forbidden in ('"recommendation":', '"value_score":', '"ranking":', '"price":'):
                self.assertNotIn(forbidden, text)
        with self.assertRaisesRegex(ExplanationError, "ten-card pilot"):
            self.engine.explain(name="Black Lotus")

    def test_known_unknown_incomplete_unsupported_and_provenance(self):
        report = self.engine.explain(name="Sol Ring")
        quality = report["evidence_sections"]["evidence_quality"]
        self.assertIn("value_driver.demand", quality["unknown"])
        self.assertTrue(quality["known"] and quality["incomplete"] and quality["unsupported"])
        self.assertTrue(report["provenance"]["input_only"])
        self.assertTrue(report["provenance"]["knowledge_fact_ids"])
        self.assertTrue(report["provenance"]["market_observation_ids"])
        self.assertEqual(report["canonical_snapshot"]["identity"],
                         "sha256:881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077")

    def test_empty_market_evidence_section_is_explicit(self):
        self.assertEqual(CardValueExplanationEngine._market([]), {
            "observation_count": 0, "first_observation": None, "latest_observation": None,
            "provider_coverage": [], "supported_currencies": [], "observation_span": None})

    def test_json_schema_all_pilot_cards(self):
        schema = json.loads((ROOT / "src/schemas/v1/card-value-explanation.schema.json").read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for name in PILOT:
            self.assertEqual([], list(validator.iter_errors(self.engine.explain(name=name))), name)

    def test_cli_name_card_id_and_error(self):
        env = {**os.environ, "PYTHONPATH": "src:."}
        named = subprocess.run(["python", "-m", "card_intelligence.cli", "explain", "Sol Ring"],
                               cwd=ROOT, env=env, check=True, capture_output=True, text=True)
        report = json.loads(named.stdout)
        identified = subprocess.run(["python", "-m", "card_intelligence.cli", "explain",
                                     "--card-id", report["card_identity"]["card_id"]], cwd=ROOT,
                                    env=env, check=True, capture_output=True, text=True)
        self.assertEqual(named.stdout, identified.stdout)
        failed = subprocess.run(["python", "-m", "card_intelligence.cli", "explain", "Black Lotus"],
                                cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(json.loads(failed.stdout)["schema_version"],
                         "card-value-explanation-error-v1")

    def test_protected_inputs_unchanged(self):
        self.assertEqual(self.before, {path: digest_tree(path) for path in PROTECTED})


if __name__ == "__main__":
    unittest.main()
