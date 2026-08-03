from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from card_intelligence import CardKnowledgeQuery, KnowledgeRepository, KnowledgeValidationError
from card_intelligence.repository import serialize_fact

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "data" / "knowledge"
REPORT = ROOT / "data" / "reviews" / "phase-133" / "pilot-review.json"
PROTECTED_DIGESTS = {
    "data/canonical": "38c48952c8d751da1d8d215548b522130f9cd09f59faca121bd28a1417c971e5",
    "data/market/acquisitions": "33b69201a0be62104911f098f38211ed7c6d7b4d6945b06075fb5e8d8371de35",
    "data/market/observations": "7ecc2c6064856e4921802813e186d34ccafb0ca6daf6a59b0b6c1dd11ad999f8",
    "data/market/imports": "72dd8d9f45d1d252aa5de9ecf4d5b52f87651a1a4346c79e863cb5fe50bd0bd8",
}
PHASE132_DIGEST = "2be71f5dddc86bb63868fc556ea683d45ca43c085826fdde9f7df99017f67b62"


def digest_files(paths, base=ROOT):
    digest = hashlib.sha256()
    for item in sorted(paths):
        digest.update(item.relative_to(base).as_posix().encode() + b"\0")
        digest.update(item.read_bytes())
    return digest.hexdigest()


def tree_digest(relative):
    root = ROOT / relative
    return digest_files((x for x in root.rglob("*") if x.is_file()), root)


class Phase133PrintingHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = KnowledgeRepository(KNOWLEDGE)
        cls.facts = cls.repo.validate()
        cls.report_bytes = REPORT.read_bytes()
        cls.report = json.loads(cls.report_bytes)
        cls.new = [x for x in cls.facts if x.fact_id.startswith("phase133-")]

    def test_exact_pilot_scope_and_deterministic_aggregation(self):
        self.assertEqual(len(self.new), 10)
        self.assertEqual({x.card_id for x in self.new},
                         {x["card_id"] for x in self.report["selected_cards"]})
        for fact in self.new:
            value = fact.to_dict()["value"]["data"]
            self.assertEqual(value["total_known_canonical_printings"], 1)
            self.assertEqual(len(value["canonical_printing_ids"]), 1)
            self.assertEqual(value["distinct_canonical_set_codes"], ["MB2"])
            self.assertEqual(value["reprint_count"], 0)
            self.assertEqual(value["reprint_count_definition"],
                             "max(total distinct canonical printings - 1, 0)")

    def test_dates_finishes_treatments_and_evidence_states(self):
        for fact in self.new:
            value = fact.to_dict()["value"]["data"]
            self.assertEqual(value["earliest_known_canonical_printing_date"], "2024-08-02")
            self.assertEqual(value["latest_known_canonical_printing_date"], "2024-08-02")
            self.assertEqual(value["years_between_known_date_boundaries"], 0)
            self.assertTrue(value["known_finishes"])
            self.assertEqual(value["known_languages"], ["en"])
            self.assertEqual(value["coverage_state"], "incomplete")
            self.assertIn("frames", value["known_treatments"])
            self.assertIsNone(fact.confidence)

    def test_supersession_active_and_full_history_queries(self):
        query = CardKnowledgeQuery(self.repo)
        for card in self.report["selected_cards"]:
            active = query.printing_history("magic", card["card_id"])
            history = query.printing_history("magic", card["card_id"], include_superseded=True)
            self.assertEqual(active["count"], 1)
            self.assertEqual(active["facts"][0]["value"]["status"], "known")
            self.assertEqual(history["count"], 2)
            self.assertEqual(Counter(x["value"]["status"] for x in history["facts"]),
                             {"unknown": 1, "known": 1})
            self.assertEqual(active["evidence_sources"],
                             ["phase-119-canonical-state", "scryfall-mb2-30754638264-1"])

    def test_invalid_supersession_duplicate_and_replay_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "knowledge"
            shutil.copytree(KNOWLEDGE, copy)
            replay = KnowledgeRepository(copy)
            self.assertEqual(tuple(serialize_fact(x) for x in replay.validate()),
                             tuple(serialize_fact(x) for x in self.facts))
            with self.assertRaisesRegex(KnowledgeValidationError, "duplicate fact_id"):
                replay.append(self.new[0])
            target = copy / "facts" / "magic" / self.new[0].card_id / f"{self.new[0].fact_id}.json"
            document = json.loads(target.read_text())
            document["subject"]["card_id"] = self.new[1].card_id
            target.unlink()
            wrong = copy / "facts" / "magic" / self.new[1].card_id / target.name
            wrong.write_text(json.dumps(document, indent=2, sort_keys=True, separators=(",", ": ")) + "\n")
            with self.assertRaisesRegex(KnowledgeValidationError, "subject and predicate"):
                replay.validate()

    def test_serialized_bytes_fact_ids_report_and_exclusions_are_deterministic(self):
        for fact in self.new:
            path = KNOWLEDGE / "facts" / fact.game_id / fact.card_id / f"{fact.fact_id}.json"
            self.assertEqual(path.read_bytes(), serialize_fact(fact))
        expected = (json.dumps(self.report, indent=2, sort_keys=True,
                               separators=(",", ": ")) + "\n").encode()
        self.assertEqual(self.report_bytes, expected)
        self.assertEqual(self.report["total_new_facts"], 10)
        self.assertEqual(self.report["superseded_unknown_fact_count"], 10)
        self.assertEqual(len(self.report["cards_with_incomplete_printing_history_evidence"]), 10)
        forbidden = {"scarcity", "demand", "value", "supply_quantity", "investment_quality"}
        self.assertTrue(forbidden <= set(self.report["unsupported_assertions_excluded"]))
        self.assertFalse(any(x.kind in forbidden for x in self.new))

    def test_phase132_facts_and_protected_data_are_immutable(self):
        old = list((KNOWLEDGE / "facts").glob("*/*/phase132-*.json"))
        self.assertEqual(len(old), 90)
        self.assertEqual(digest_files(old), PHASE132_DIGEST)
        for path, expected in PROTECTED_DIGESTS.items():
            self.assertEqual(tree_digest(path), expected, path)
        for flag in ("canonical_write", "promotion_performed", "inference_performed",
                     "external_acquisition_performed"):
            self.assertFalse(self.report[flag])

    def test_explicit_empty_unsupported_dimensions(self):
        query = CardKnowledgeQuery(self.repo)
        for card in self.report["selected_cards"]:
            self.assertTrue(query.archetypes("magic", card["card_id"])["empty"])
            self.assertTrue(query.market_catalysts("magic", card["card_id"])["empty"])


if __name__ == "__main__":
    unittest.main()
