from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from card_intelligence import CardKnowledgeQuery, KnowledgeRepository, KnowledgeValidationError
from card_intelligence.repository import serialize_fact

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "data" / "knowledge"
REPORT = ROOT / "data" / "reviews" / "phase-132" / "pilot-review.json"
PROTECTED = ("data/canonical", "data/market/acquisitions", "data/market/observations", "data/market/imports")
PROTECTED_DIGESTS = {
    "data/canonical": "38c48952c8d751da1d8d215548b522130f9cd09f59faca121bd28a1417c971e5",
    "data/market/acquisitions": "33b69201a0be62104911f098f38211ed7c6d7b4d6945b06075fb5e8d8371de35",
    "data/market/observations": "7ecc2c6064856e4921802813e186d34ccafb0ca6daf6a59b0b6c1dd11ad999f8",
    "data/market/imports": "72dd8d9f45d1d252aa5de9ecf4d5b52f87651a1a4346c79e863cb5fe50bd0bd8",
}

def tree_digest(path):
    digest = hashlib.sha256()
    for item in sorted((ROOT / path).rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(ROOT / path).as_posix().encode() + b"\0")
            digest.update(item.read_bytes())
    return digest.hexdigest()

class Phase132PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = KnowledgeRepository(KNOWLEDGE)
        # Phase-specific assertions remain stable when later phases append facts.
        cls.facts = tuple(x for x in cls.repo.validate() if x.fact_id.startswith("phase132-"))
        cls.report_bytes = REPORT.read_bytes()
        cls.report = json.loads(cls.report_bytes)

    def test_deterministic_selection_exact_count_and_identities(self):
        names = [x["name"] for x in self.report["selected_cards"]]
        self.assertEqual(names, sorted(names))
        self.assertEqual(names, ["Brainstorm", "Command Tower", "Counterspell",
            "Goblin Charbelcher", "Goblin King", "Sol Ring", "Swords to Plowshares",
            "Treasure Cruise", "Walking Ballista", "Wishclaw Talisman"])
        self.assertEqual(len(self.facts), 90)
        self.assertEqual([x.fact_id for x in self.facts], self.report["fact_ids"])

    def test_schema_repository_and_canonical_serialization(self):
        schema = json.loads((ROOT / "src/schemas/v1/card-knowledge-fact.schema.json").read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for fact in self.facts:
            document = fact.to_dict()
            self.assertEqual([], list(validator.iter_errors(document)))
            path = KNOWLEDGE / "facts" / fact.game_id / fact.card_id / f"{fact.fact_id}.json"
            self.assertEqual(path.read_bytes(), serialize_fact(fact))

    def test_provenance_known_unknown_and_excluded_assertions(self):
        self.assertEqual(Counter(x.value_status for x in self.facts), {"known": 70, "unknown": 20})
        self.assertTrue(all(x.evidence and x.confidence is None for x in self.facts))
        self.assertEqual({e.source_id for x in self.facts for e in x.evidence},
            {"phase-119-canonical-state", "phase-128-market-observations",
             "scryfall-mb2-30754638264-1"})
        forbidden = {"popularity", "scarcity", "supply", "staple", "market_catalyst",
                     "archetype_usage", "combo", "infinite_combo", "reserved_status"}
        self.assertFalse(forbidden & {x.kind for x in self.facts})

    def test_every_card_query_projection_and_explicit_empty_categories(self):
        query = CardKnowledgeQuery(self.repo)
        for selected in self.report["selected_cards"]:
            card_id = selected["card_id"]
            all_facts = query.explain("magic", card_id)
            all_facts["facts"] = [x for x in all_facts["facts"]
                                  if x["fact_id"].startswith("phase132-")]
            all_facts["count"] = len(all_facts["facts"])
            self.assertEqual(all_facts["count"], 9)
            self.assertFalse(all_facts["empty"])
            self.assertTrue(all_facts["evidence_sources"])
            self.assertEqual(sum(x["fact_id"].startswith("phase132-")
                                 for x in all_facts["confidence_values"]), 9)
            value_drivers = query.value_drivers("magic", card_id)["facts"]
            self.assertEqual(sum(x["fact_id"].startswith("phase132-") for x in value_drivers), 2)
            self.assertEqual(query.competitive_formats("magic", card_id)["count"], 1)
            for empty in (query.archetypes("magic", card_id), query.market_catalysts("magic", card_id)):
                self.assertEqual(empty["facts"], [])
                self.assertEqual(empty["evidence_sources"], [])
                self.assertEqual(empty["confidence_values"], [])
                self.assertTrue(empty["empty"])

    def test_duplicate_rejection_and_byte_identical_replay_loading(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "knowledge"
            shutil.copytree(KNOWLEDGE, copy)
            replay = KnowledgeRepository(copy)
            replay_facts = (x for x in replay.validate() if x.fact_id.startswith("phase132-"))
            self.assertEqual(tuple(serialize_fact(x) for x in replay_facts),
                             tuple(serialize_fact(x) for x in self.facts))
            with self.assertRaisesRegex(KnowledgeValidationError, "duplicate fact_id"):
                replay.append(self.facts[0])

    def test_review_report_is_canonical_and_matches_repository(self):
        expected = (json.dumps(self.report, indent=2, sort_keys=True,
                               separators=(",", ": ")) + "\n").encode()
        self.assertEqual(self.report_bytes, expected)
        self.assertEqual(self.report["total_facts_created"], 90)
        self.assertEqual(self.report["known_fact_count"], 70)
        self.assertEqual(self.report["explicit_unknown_count"], 20)
        self.assertFalse(self.report["canonical_write"])
        self.assertFalse(self.report["promotion_performed"])
        self.assertFalse(self.report["inference_performed"])

    def test_protected_production_data_digests(self):
        for path, expected in PROTECTED_DIGESTS.items():
            self.assertEqual(tree_digest(path), expected, path)

if __name__ == "__main__":
    unittest.main()
