import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from types import MappingProxyType

from analytics import CanonicalAnalyticsEngine, CanonicalAnalyticsResult
from mtglab.__main__ import main
from query import QueryResult, QuerySnapshot


def entity(identifier, kind, values, *, sources=(), datasets=(), confidence=None,
           uncertainty="known", supersession="current"):
    return QueryResult(identifier, kind, values, {
        "source_ids": list(sources), "evidence_assertions": ([{"id": "a"}] if sources else []),
        "dataset_identity": [{"dataset_id": value} for value in datasets],
    }, confidence, uncertainty, supersession)


class FakeQuery:
    game = "test"

    def __init__(self, entities=()):
        self.value = QuerySnapshot("sha256:" + "1" * 64, "test", tuple(entities))

    def snapshot(self):
        return self.value

    def validation(self, state):
        if state == "superseded":
            return tuple(x for x in self.value.entities if x.supersession_state == state)
        if state in {"unknown", "unresolved", "conflicting"}:
            return tuple(x for x in self.value.entities if x.uncertainty.startswith(state))
        return ()


class CanonicalAnalyticsEngineTests(unittest.TestCase):
    def setUp(self):
        self.query = FakeQuery((
            entity("card-b", "card", {"name": "B", "colors": ["U"], "layout": "normal"},
                   sources=("s2",), datasets=("two",), confidence=.75),
            entity("printing-b", "printing", {"card_id": "card-b", "set_id": "set-a",
                   "rarity_id": "rare", "language": "en", "finishes": ["foil"]},
                   sources=("s2",), datasets=("two",), confidence=.75, supersession="superseded"),
            entity("card-a", "card", {"name": "A", "colors": [], "layout": None},
                   datasets=("one", "two"), uncertainty="unknowns_reviewed"),
            entity("printing-a", "printing", {"card_id": "card-a", "set_id": "set-a",
                   "rarity_id": None, "language": "unknown", "finishes": ["nonfoil"]},
                   datasets=("one",), uncertainty="unresolved"),
        ))
        self.engine = CanonicalAnalyticsEngine(self.query)

    def test_summary_is_deterministic_ordered_and_reproducible(self):
        first = self.engine.summary()
        second = self.engine.summary()
        self.assertEqual(first, second)
        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual(list(first.data["entity_counts_by_type"]), ["card", "printing"])
        self.assertEqual(first.data["cards_per_set"], {"set-a": 2})
        self.assertEqual(first.data["printings_per_card"], {"card-a": 1, "card-b": 1})
        self.assertEqual(tuple(first.provenance), ("card-a", "card-b", "printing-a", "printing-b"))

    def test_distributions_unknowns_confidence_and_supersession(self):
        data = self.engine.summary().data
        self.assertEqual(data["rarity_distribution"], {"rare": 1, "unknown": 1})
        self.assertEqual(data["language_distribution"], {"en": 1, "unknown": 1})
        self.assertEqual(data["finish_distribution"], {"foil": 1, "nonfoil": 1})
        self.assertEqual(data["confidence_distribution"], {"0.75": 2, "unknown": 2})
        self.assertEqual(data["supersession_statistics"], {"current": 3, "superseded": 1})
        self.assertGreater(data["unknown_value_counts"]["card"], 0)

    def test_mixed_dataset_and_provenance_accounting(self):
        datasets = self.engine.dataset().data
        self.assertEqual(datasets["datasets"], {"one": 2, "two": 3})
        self.assertEqual(datasets["covered_entities"], 4)
        provenance = self.engine.provenance().data
        self.assertEqual(provenance["with_sources"], 2)
        self.assertEqual(provenance["without_sources"], 2)

    def test_validation_statistics_include_superseded_entities(self):
        self.assertEqual(self.engine.validation().data, {
            "conflicting": 0, "rejected": 0, "superseded": 1, "unknown": 1,
            "unresolved": 1, "validation_failure": 0,
        })

    def test_empty_snapshot_and_immutable_versioned_contract(self):
        result = CanonicalAnalyticsEngine(FakeQuery()).summary()
        self.assertIsInstance(result, CanonicalAnalyticsResult)
        self.assertEqual(result.schema_version, "canonical-analytics-v1")
        self.assertEqual(result.data["entity_counts_by_type"], {})
        self.assertEqual(result.data["provenance_coverage"]["total_entities"], 0)
        self.assertIsInstance(result.data, MappingProxyType)
        with self.assertRaises(TypeError):
            result.data["changed"] = True

    def test_cli_commands_emit_json_and_snapshot_identity(self):
        for command in ("summary", "entity", "dataset", "validation", "provenance"):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["analytics", command, "--format", "json"]), 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["analytics_type"], command)
            self.assertTrue(payload["canonical_snapshot_id"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
