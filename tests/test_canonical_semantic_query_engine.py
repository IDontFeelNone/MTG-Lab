import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from types import MappingProxyType

from analytics import CanonicalAnalyticsEngine
from mtglab.__main__ import main
from query import QueryError, QueryResult, QuerySnapshot
from semantic import (CanonicalSemanticQueryEngine, SemanticQueryError, SemanticRequest,
                      SemanticResponse)


def item(identifier, kind="card", *, name=None, sources=(), datasets=(), confidence=None,
         uncertainty="known"):
    return QueryResult(identifier, kind, {"name": name or identifier}, {
        "source_ids": list(sources), "evidence_assertions": [{"source_id": x} for x in sources],
        "dataset_identity": [{"dataset_id": x} for x in datasets]}, confidence, uncertainty, "current")


class FakeQuery:
    game = "test"

    def __init__(self, entities=()):
        self.value = QuerySnapshot("sha256:" + "a" * 64, self.game,
                                   tuple(sorted(entities, key=lambda x: (x.entity_type, x.canonical_identity))))

    def snapshot(self): return self.value
    def entity(self, identifier, *, entity_type=None):
        found = [x for x in self.value.entities if x.canonical_identity == identifier and (not entity_type or x.entity_type == entity_type)]
        if len(found) != 1: raise QueryError(f"expected one entity for {identifier}, found {len(found)}")
        return found[0]
    def search(self, text, *, mode="exact"):
        return tuple(x for x in self.value.entities if str(x.canonical_values.get("name", "")).casefold() == text.casefold())
    def entities(self, *, entity_type=None):
        return tuple(x for x in self.value.entities if x.entity_type == entity_type.casefold())
    def related(self, identifier, relationship):
        return tuple(x for x in self.value.entities if any(y.get("dataset_id") == identifier for y in x.provenance_summary.get("dataset_identity", ())))
    def validation(self, state):
        allowed = {"unknown", "conflicting", "unresolved", "rejected", "validation_failure", "superseded"}
        if state not in allowed: raise QueryError("unsupported validation state")
        return tuple(x for x in self.value.entities if x.uncertainty.startswith(state))


class CanonicalSemanticQueryEngineTests(unittest.TestCase):
    def setUp(self):
        self.query = FakeQuery((
            item("b", name="Beta", sources=("source-2",), datasets=("dataset-1",), confidence=.8),
            item("a", name="Alpha", sources=("source-1",), datasets=("dataset-1",), confidence=.4,
                 uncertainty="unknowns_reviewed"),
            item("p", "printing", sources=("source-1",), confidence=1.0),
        ))
        self.engine = CanonicalSemanticQueryEngine(self.query, CanonicalAnalyticsEngine(self.query))

    def execute(self, operation, **parameters):
        return self.engine.execute(SemanticRequest(operation, parameters))

    def test_deterministic_repeated_execution_and_order(self):
        first = self.execute("list_type", entity_type="card")
        second = self.execute("list_type", entity_type="card")
        self.assertEqual(first, second)
        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual([x["canonical_identity"] for x in first.to_dict()["result"]], ["a", "b"])
        self.assertIsInstance(first.provenance_references, MappingProxyType)

    def test_find_list_filters_and_provenance_preservation(self):
        self.assertEqual(self.execute("find_identifier", identifier="a").to_dict()["result"][0]["canonical_identity"], "a")
        self.assertEqual(self.execute("find_name", name="ALPHA").to_dict()["result"][0]["canonical_identity"], "a")
        dataset = self.execute("list_dataset", dataset="dataset-1")
        self.assertEqual(set(dataset.provenance_references), {"a", "b"})
        self.assertEqual(dataset.to_dict()["provenance_references"]["a"]["source_ids"], ["source-1"])
        self.assertEqual([x["canonical_identity"] for x in self.execute("list_provenance", source_id="source-1").to_dict()["result"]], ["a", "p"])
        self.assertEqual([x["canonical_identity"] for x in self.execute("list_validation", state="unknown").to_dict()["result"]], ["a"])
        self.assertEqual([x["canonical_identity"] for x in self.execute("list_confidence", minimum=.5, maximum=1).to_dict()["result"]], ["b", "p"])

    def test_invalid_unknown_and_schema_requests(self):
        for operation, parameters in (("missing", {}), ("find_identifier", {}),
                ("list_confidence", {"minimum": .9, "maximum": .1}),
                ("find_identifier", {"identifier": "absent"}),
                ("list_dataset", {"dataset": "absent"})):
            with self.subTest(operation=operation), self.assertRaises(SemanticQueryError):
                self.engine.execute(SemanticRequest(operation, parameters))
        with self.assertRaises(ValueError): SemanticRequest("find_identifier", {}, schema_version="v2")

    def test_analytics_delegation_and_snapshot_identifiers(self):
        for operation in ("analytics_summary", "dataset_statistics", "provenance_statistics", "validation_statistics"):
            response = self.execute(operation)
            self.assertEqual(response.canonical_snapshot_id, self.query.value.snapshot_id)
            self.assertTrue(response.analytics_snapshot_id.startswith("sha256:"))
            self.assertEqual(response.to_dict()["result"]["schema_version"], "canonical-analytics-v1")

    def test_empty_repository(self):
        response = CanonicalSemanticQueryEngine(FakeQuery()).execute(SemanticRequest("analytics_summary", {}))
        self.assertEqual(response.to_dict()["result"]["data"]["entity_counts_by_type"], {})
        self.assertEqual(response.to_dict()["provenance_references"], {})

    def test_response_contract_rejects_non_content_identity(self):
        with self.assertRaises(ValueError): SemanticResponse("x", "not-a-hash", [], {})

    def test_cli_json_behavior(self):
        commands = (["semantic", "find", "--identifier", "magic.lightning-bolt"],
                    ["semantic", "list", "--type", "card"],
                    ["semantic", "analytics"],
                    ["semantic", "dataset", "--statistics"],
                    ["semantic", "provenance", "gatherer-lightning-bolt-lea"])
        for command in commands:
            with self.subTest(command=command):
                output = StringIO()
                with redirect_stdout(output): self.assertEqual(main(list(command)), 0)
                payload = json.loads(output.getvalue())
                self.assertEqual(payload["schema_version"], "canonical-semantic-query-v1")
                self.assertTrue(payload["canonical_snapshot_id"].startswith("sha256:"))


if __name__ == "__main__": unittest.main()
