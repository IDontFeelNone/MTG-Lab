"""Phase 102 deterministic validation of the complete governed platform path."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from acquisition import (AcquisitionEngine, CanonicalPromotionEngine, FixtureProvider,
    PromotionDecision, PromotionError, ProviderPolicy, ProviderTrustPolicy,
    RawSnapshotStore, assertions_from_normalized, build_review_package,
    normalize_snapshot)
from ai import AIModelRequest
from analytics import CanonicalAnalyticsEngine
from query import CanonicalQueryEngine
from reasoning import ReasoningContextBuilder, ReasoningContextRequest
from semantic import CanonicalSemanticQueryEngine, SemanticRequest


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests/fixtures/representative_corpus/corpus.json"
POLICY = ProviderPolicy("fixture", "authoritative_structured", .9,
    ("test-only",), "Deterministic Phase 102 corpus", ("card", "printing"))
TIMESTAMP = "2026-07-31T12:00:00+00:00"


class RepresentativeCorpusValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.provider = FixtureProvider({"phase-102": CORPUS.read_bytes()})

    def tearDown(self): self.temp.cleanup()

    def acquire(self, destination=None):
        root = destination or self.root
        store = RawSnapshotStore(root / "raw")
        engine = AcquisitionEngine(store, root / "runs"); engine.register(self.provider)
        run = engine.acquire("fixture", "phase-102", started_at=TIMESTAMP,
                             run_id="phase-102-representative")
        snapshot_path = Path(run["downloaded_snapshots"][0]["path"])
        snapshot = json.loads((snapshot_path / "manifest.json").read_text())
        normalized = normalize_snapshot(self.provider, store, snapshot_path,
                                        root / "normalized.json")
        assertions = assertions_from_normalized(normalized,
            ProviderTrustPolicy("authoritative_structured", .9, "verified"), TIMESTAMP)
        package = build_review_package(run, [snapshot], [normalized], assertions, POLICY,
                                       "phase-102-v1")
        return run, snapshot, normalized, assertions, package

    def promote(self, package, timestamp=TIMESTAMP):
        engine = CanonicalPromotionEngine(self.root / "canonical", self.root / "audit")
        decision = PromotionDecision("independent-phase-102-reviewer", timestamp,
                                     allow_unknowns=True, reason="corpus validation")
        return engine, engine.promote(package, POLICY, decision)

    def test_complete_pipeline_is_deterministic_and_preserves_governance(self):
        run, snapshot, normalized, assertions, package = self.acquire()
        self.assertEqual(len(normalized["records"]), 5)
        self.assertEqual(package["promotion_recommendation"], "hold")
        self.assertGreater(package["unknown_values"]["count"], 0)
        self.assertTrue(package["reports"]["validation_report"]["valid"])
        engine, audit = self.promote(package)
        self.assertEqual(audit, engine.promote(package, POLICY,
            PromotionDecision("independent-phase-102-reviewer", TIMESTAMP,
                              allow_unknowns=True, reason="corpus validation")))

        query = CanonicalQueryEngine(games_root=ROOT / "data/canonical/games",
                                     data_root=self.root)
        self.assertEqual(query.entity("card-alpha").canonical_values["/name"], "Alpha Adept")
        self.assertEqual(query.snapshot(), query.snapshot())
        promoted = query.entity("printing-alpha-ja")
        self.assertEqual(promoted.canonical_values["/artist"], None)
        self.assertEqual(promoted.confidence, .9)
        self.assertEqual(promoted.uncertainty, "unknowns_reviewed")
        self.assertEqual(promoted.provenance_summary["review_package_id"],
                         package["review_package_id"])
        self.assertEqual(promoted.provenance_summary["dataset_identity"],
                         package["snapshot_lineage"])

        analytics = CanonicalAnalyticsEngine(query)
        summary = analytics.summary()
        self.assertEqual(summary.to_json(), analytics.summary().to_json())
        self.assertGreaterEqual(summary.data["entity_counts_by_type"]["card"], 2)
        self.assertGreaterEqual(summary.data["entity_counts_by_type"]["printing"], 3)
        self.assertEqual(summary.canonical_snapshot_id, query.snapshot().snapshot_id)
        semantic = CanonicalSemanticQueryEngine(query, analytics)
        semantic_result = semantic.execute(SemanticRequest("find_identifier", {"identifier": "card-alpha"}))
        self.assertEqual(semantic_result.to_json(), semantic.execute(
            SemanticRequest("find_identifier", {"identifier": "card-alpha"})).to_json())
        self.assertEqual(semantic_result.to_dict()["result"][0]["canonical_identity"], "card-alpha")
        context = ReasoningContextBuilder(semantic).build(ReasoningContextRequest(
            SemanticRequest("list_dataset", {"dataset": package["snapshot_lineage"][0]["logical_dataset_identity"]}),
            include_analytics=True))
        repeated_context = ReasoningContextBuilder(semantic).build(ReasoningContextRequest(
            SemanticRequest("list_dataset", {"dataset": package["snapshot_lineage"][0]["logical_dataset_identity"]}),
            include_analytics=True))
        self.assertEqual(context.to_json(), repeated_context.to_json())
        request = AIModelRequest("validation-provider", "1.0.0", "validation-model",
            context.context_id, "phase-102-no-execution", TIMESTAMP,
            required_capabilities=("structured-response",))
        self.assertEqual(request.reasoning_context_identifier, context.context_id)
        self.assertEqual(request.to_json(), request.to_json())
        self.assertNotIn("response", request.to_dict())

    def test_byte_identical_replay_conflicts_failures_supersession_and_rollback(self):
        first_root, second_root = self.root / "first", self.root / "second"
        first = self.acquire(first_root); second = self.acquire(second_root)
        self.assertEqual(first[1]["snapshot_id"], second[1]["snapshot_id"])
        first_payload = Path(first[0]["downloaded_snapshots"][0]["path"]) / "payload.bin"
        second_payload = Path(second[0]["downloaded_snapshots"][0]["path"]) / "payload.bin"
        self.assertEqual(first_payload.read_bytes(), second_payload.read_bytes())
        self.assertEqual(first_payload.read_bytes(), CORPUS.read_bytes())
        self.assertEqual([x["id"] for x in first[2]["records"]],
                         [x["id"] for x in second[2]["records"]])

        package = first[4]
        conflicting_assertions = copy.deepcopy(first[3])
        conflict = copy.deepcopy(conflicting_assertions[0]); conflict["id"] += "-conflict"
        conflict["asserted_value"] = "contradictory value"
        conflicting_assertions.append(conflict)
        conflict_package = build_review_package(first[0], [first[1]], [first[2]],
            conflicting_assertions, POLICY, "phase-102-v1")
        self.assertEqual(conflict_package["promotion_recommendation"], "hold")
        self.assertEqual(conflict_package["detected_conflicts"]["count"], 1)
        rejected_engine = CanonicalPromotionEngine(self.root / "rejected/canonical",
                                                   self.root / "rejected/audit")
        decision = PromotionDecision("independent-phase-102-reviewer", TIMESTAMP,
                                     allow_unknowns=True, reason="negative validation")
        with self.assertRaisesRegex(PromotionError, "conflicts"):
            rejected_engine.promote(conflict_package, POLICY, decision)
        self.assertFalse((self.root / "canonical/state.json").exists())

        invalid = copy.deepcopy(package); invalid["candidate_assertions"].append(
            invalid["candidate_assertions"][0])
        with self.assertRaisesRegex(PromotionError, "review_package"):
            CanonicalPromotionEngine(self.root / "invalid/canonical",
                self.root / "invalid/audit").promote(invalid, POLICY, decision)

        engine, original = self.promote(package)
        changed = copy.deepcopy(first[2]); changed["records"][0]["source_values"]["name"] = "Alpha Adept Revised"
        changed_assertions = assertions_from_normalized(changed,
            ProviderTrustPolicy("authoritative_structured", .9, "verified"), TIMESTAMP)
        changed_package = build_review_package(first[0], [first[1]], [changed],
            changed_assertions, POLICY, "phase-102-v2", first[3])
        replacement = engine.promote(changed_package, POLICY,
            PromotionDecision("independent-phase-102-reviewer", "2026-07-31T13:00:00+00:00",
                              allow_unknowns=True, reason="supersession validation"))
        self.assertEqual(engine.current("card", "card-alpha")["values"]["/name"],
                         "Alpha Adept Revised")
        engine.rollback(replacement["promotion_id"], PromotionDecision(
            "independent-phase-102-reviewer", "2026-07-31T14:00:00+00:00",
            allow_unknowns=True, reason="rollback validation"))
        self.assertEqual(engine.current("card", "card-alpha")["values"]["/name"], "Alpha Adept")
        self.assertEqual(engine.replay(), json.loads((self.root / "canonical/state.json").read_text()))
        self.assertNotEqual(original["promotion_id"], replacement["promotion_id"])


if __name__ == "__main__": unittest.main()
