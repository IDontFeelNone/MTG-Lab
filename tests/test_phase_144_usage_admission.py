import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout

from jsonschema import Draft202012Validator, FormatChecker

from card_intelligence.cli import main as cli_main
from card_intelligence.deck_usage import load_deck_usage
from card_intelligence.explanation import CardValueExplanationEngine
from card_intelligence.repository import KnowledgeRepository
from card_intelligence.usage_review import admit_usage_facts, build_usage_facts

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/card_intelligence/demand/phase-143/mtgjson-decks.json"


def tree_digest(relative):
    base = ROOT / relative; digest = hashlib.sha256()
    for path in sorted(x for x in base.rglob("*") if x.is_file()):
        digest.update(path.relative_to(base).as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


class Phase144UsageAdmissionTests(unittest.TestCase):
    def test_exact_production_evidence_and_semantics(self):
        document = load_deck_usage(EVIDENCE)
        self.assertEqual(document["schema_version"], "card-deck-usage-evidence-v1")
        self.assertEqual((document["provider"], document["provider_dataset"]),
                         ("mtgjson", "AllDeckFiles.zip"))
        self.assertEqual({r["denominator"] for r in document["records"]}, {3004})
        self.assertEqual([r["numerator"] for r in document["records"]],
                         [23, 205, 63, 4, 17, 241, 78, 15, 8, 3])
        self.assertTrue(all(len(r["deck_associations"]) == r["numerator"]
                            for r in document["records"]))
        identities = [a["provider_deck_identity"] for r in document["records"]
                      for a in r["deck_associations"]]
        self.assertTrue(all(a["source_record_identity"] and a["retained_record_id"]
                            for r in document["records"] for a in r["deck_associations"]))
        self.assertLess(len(set(x for x in identities if x)), len([x for x in identities if x]))

    def test_literal_provider_isolated_facts_and_no_supersession(self):
        facts = build_usage_facts(EVIDENCE)
        self.assertEqual(len(facts), 20)
        self.assertEqual({f.predicate for f in facts}, {"demand.deck_inclusion", "format.usage"})
        self.assertTrue(all(not f.supersedes and f.value_status == "known" for f in facts))
        serialized = json.dumps([f.to_dict() for f in facts], sort_keys=True).lower()
        for prohibited in ("demand_score", "popularity_class", "valuation", "recommendation",
                           "scarcity_conclusion", "price_target", "inferred_archetype"):
            self.assertNotIn(prohibited, serialized)

    def test_byte_identical_replay_and_conflicting_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = KnowledgeRepository(Path(temporary) / "knowledge")
            self.assertEqual(admit_usage_facts(EVIDENCE, repo)["facts_added"], 20)
            self.assertEqual(admit_usage_facts(EVIDENCE, repo)["facts_replayed"], 20)
            path = next((Path(temporary) / "knowledge/facts").rglob("*deck_inclusion.json"))
            path.write_text(path.read_text().replace('"numerator": ', '"numerator": 999', 1))
            with self.assertRaisesRegex(ValueError, "conflicting Phase 144 replay"):
                admit_usage_facts(EVIDENCE, repo)

    def test_production_facts_and_phase142_provider_isolation(self):
        facts = KnowledgeRepository(ROOT / "data/knowledge").validate()
        self.assertEqual(sum(f.fact_id.startswith("phase144-") for f in facts), 20)
        self.assertEqual(sum(f.fact_id.startswith("phase142-") for f in facts), 10)
        self.assertEqual({f.to_dict()["value"]["data"]["provider"] for f in facts
                          if f.fact_id.startswith(("phase142-", "phase144-"))},
                         {"scryfall", "mtgjson"})

    def test_v4_schema_determinism_and_name_id_cli_parity(self):
        engine = CardValueExplanationEngine(ROOT / "data")
        by_name = engine.explain(name="Sol Ring", include_demand_evidence=True)
        card_id = by_name["card_identity"]["card_id"]
        by_id = engine.explain(card_id=card_id, include_demand_evidence=True)
        self.assertEqual(by_name, by_id)
        self.assertEqual(by_name, engine.explain(name="Sol Ring", include_demand_evidence=True))
        schema = json.loads((ROOT / "src/schemas/v1/card-value-explanation-v4.schema.json").read_text())
        self.assertEqual([], list(Draft202012Validator(
            schema, format_checker=FormatChecker()).iter_errors(by_name)))
        self.assertIn("historical_price_evidence", by_name["evidence_sections"])
        self.assertIn("literal_deck_associations", by_name["evidence_sections"]["deck_usage_evidence"])
        self.assertNotIn("archetype_associations", by_name["evidence_sections"]["deck_usage_evidence"])
        outputs = []
        for args in (["explain", "Sol Ring", "--include-demand-evidence"],
                     ["explain", "--card-id", card_id, "--include-demand-evidence"]):
            stream = io.StringIO()
            with redirect_stdout(stream): self.assertEqual(cli_main(args), 0)
            outputs.append(json.loads(stream.getvalue()))
        self.assertEqual(outputs[0], outputs[1])

    def test_protected_production_digests(self):
        expected = {
            "data/canonical": "e3fa0240c17516cfd64e92e17cefcab92a55be8a5d27edb2df439c21a0068e19",
            "data/market/observations": "34c880d24b3eb6251ce513ad53d682ee5ee1ed11554ce3f2ba8cf7287a5269c9",
            "data/market/imports": "7daaeb8a031a10c1f4143026a0f57c3873ef3cbbd1500674b6e0b7fdb7a3e0df",
        }
        for path, digest in expected.items(): self.assertEqual(tree_digest(path), digest)
        self.assertEqual(len(list((ROOT / "data/market/observations").rglob("*.json"))), 956)


if __name__ == "__main__": unittest.main()
