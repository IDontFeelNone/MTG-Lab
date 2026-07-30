import json
import unittest
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError
from io import StringIO
from types import MappingProxyType

from analytics import CanonicalAnalyticsEngine
from mtglab.__main__ import main
from query import QueryResult, QuerySnapshot
from reasoning import (InvalidReasoningRequest, ReasoningContextBuilder,
                       ReasoningContextRequest, ReasoningContextResult,
                       ReasoningSnapshotError)
from semantic import CanonicalSemanticQueryEngine, SemanticRequest
from tests.test_canonical_semantic_query_engine import FakeQuery, item


class CountingSemantic(CanonicalSemanticQueryEngine):
    def __init__(self, query): super().__init__(query, CanonicalAnalyticsEngine(query)); self.calls=[]
    def execute(self, request): self.calls.append(request.operation); return super().execute(request)


class ReasoningContextTests(unittest.TestCase):
    def setUp(self):
        entities=(item("b", name="Beta", sources=("s2",), datasets=("d",), confidence=.8),
                  item("a", name="Alpha", sources=("s1",), datasets=("d",), confidence=.4, uncertainty="unknowns_reviewed"),
                  QueryResult("p", "printing", {"card_id":"a", "finish":None}, {"source_ids":[], "evidence_assertions":[], "dataset_identity":[]}, None, "incomplete", "superseded"))
        self.semantic=CountingSemantic(FakeQuery(entities)); self.builder=ReasoningContextBuilder(self.semantic)

    def request(self, **kwargs): return ReasoningContextRequest(SemanticRequest("find_name", {"name":"Alpha"}), **kwargs)
    def all_request(self, **kwargs): return ReasoningContextRequest(SemanticRequest("list_type", {"entity_type":kwargs.pop("kind", "card")}), **kwargs)

    def test_immutable_request_and_recursive_result(self):
        request=self.request(requested_entity_types=("card",))
        with self.assertRaises(FrozenInstanceError): request.maximum_entities=2
        result=self.builder.build(request)
        self.assertIsInstance(result.normalized_request, MappingProxyType)
        with self.assertRaises(TypeError): result.normalized_request["x"]=1
        with self.assertRaises(FrozenInstanceError): result.context_id="x"

    def test_stable_serialization_identifier_order_and_repetition(self):
        first=self.builder.build(self.all_request()); second=self.builder.build(self.all_request())
        self.assertEqual(first.context_id, second.context_id); self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual([x["canonical_identity"] for x in first.entities], ["a","b"])
        self.assertEqual(first.to_json(), json.dumps(first.to_dict(), sort_keys=True, ensure_ascii=False, separators=(",",":")))

    def test_semantic_delegation_analytics_and_snapshot(self):
        result=self.builder.build(self.all_request(include_analytics=True))
        self.assertEqual(self.semantic.calls, ["list_type", "analytics_summary"])
        self.assertTrue(result.analytics_snapshot_id.startswith("sha256:")); self.assertEqual(len(result.analytics_results),1)

    def test_provenance_evidence_unknown_and_incomplete_preserved(self):
        result=self.builder.build(self.all_request())
        self.assertEqual(result.provenance_references["a"]["source_ids"], ("s1",))
        self.assertEqual(result.evidence_references["a#0"]["validation_state"], "unknowns_reviewed")
        printing=self.builder.build(self.all_request(kind="printing"))
        self.assertEqual(printing.entities[0]["canonical_values"]["finish"], None)
        self.assertEqual(printing.validation_information["p"], "incomplete")
        self.assertEqual(printing.confidence_information["p"], None)
        self.assertEqual(printing.relationships[0]["target"], "a")

    def test_filters_and_empty_results(self):
        self.assertEqual(len(self.builder.build(self.all_request(minimum_confidence=.5)).entities),1)
        self.assertEqual(len(self.builder.build(self.all_request(validation_states=("unknown",))).entities),1)
        self.assertEqual(len(self.builder.build(self.all_request(requested_datasets=("missing",))).entities),0)
        empty=ReasoningContextBuilder(CountingSemantic(FakeQuery())).build(self.all_request())
        self.assertEqual(empty.entities, ()); self.assertEqual(empty.evidence_references, {})

    def test_limits_truncation_and_omitted_accounting(self):
        result=self.builder.build(self.all_request(maximum_entities=1, maximum_evidence_items=0))
        self.assertTrue(result.truncation["occurred"]); self.assertEqual(result.omitted_item_counts["entities"],1)
        self.assertEqual(result.omitted_item_counts["evidence"],2); self.assertEqual(result.entities[0]["canonical_identity"],"a")
        printing=self.builder.build(self.all_request(kind="printing", maximum_relationships=0))
        self.assertEqual(printing.omitted_item_counts["relationships"],1)

    def test_invalid_requests_schema_limits_confidence_and_operations(self):
        invalid=(dict(maximum_entities=-1), dict(maximum_relationships=True), dict(minimum_confidence=.9,maximum_confidence=.1),
                 dict(truncation_policy="random"), dict(include_analytics=True,analytics_operation="other"))
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(InvalidReasoningRequest): self.builder.build(self.all_request(**values))
        with self.assertRaises(ValueError): ReasoningContextRequest(SemanticRequest("list_type",{"entity_type":"card"}),schema_version="v2")
        with self.assertRaises(InvalidReasoningRequest): self.builder.build(ReasoningContextRequest(SemanticRequest("analytics_summary",{})))

    def test_result_rejects_bad_identifiers(self):
        with self.assertRaises(ValueError): ReasoningContextResult("bad","bad",{},(),(),(),{},{},{},{},{},{},())

    def test_cli_json_output_and_structured_failure(self):
        out=StringIO()
        with redirect_stdout(out): self.assertEqual(main(["reasoning","entity","magic.lightning-bolt"]),0)
        payload=json.loads(out.getvalue()); self.assertEqual(payload["schema_version"],"canonical-reasoning-context-v1")
        self.assertIn("context_id",payload); self.assertIn("omitted_item_counts",payload); self.assertIn("provenance_references",payload)
        out=StringIO()
        with redirect_stdout(out): self.assertEqual(main(["reasoning","entity","absent"]),2)
        self.assertEqual(json.loads(out.getvalue())["error"]["code"],"invalid_reasoning_request")


if __name__ == "__main__": unittest.main()
