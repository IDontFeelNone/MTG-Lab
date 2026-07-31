"""Phase 103 typed canonical projection guarantees and consumer compatibility."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from acquisition import (AcquisitionEngine, CanonicalPromotionEngine, FixtureProvider,
    PromotionDecision, ProviderPolicy, ProviderTrustPolicy, RawSnapshotStore,
    assertions_from_normalized, build_review_package, normalize_snapshot)
from analytics import CanonicalAnalyticsEngine
from projection import ProjectionValidationError, TypedCanonicalProjectionEngine
from query import CanonicalQueryEngine
from reasoning import ReasoningContextBuilder, ReasoningContextRequest
from semantic import CanonicalSemanticQueryEngine, SemanticRequest

ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests/fixtures/representative_corpus/corpus.json"
TIME = "2026-07-31T12:00:00+00:00"
POLICY = ProviderPolicy("fixture", "authoritative_structured", .9, ("test-only",),
                        "projection corpus", ("card", "printing"))


class TypedCanonicalProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        store = RawSnapshotStore(self.root / "raw")
        provider = FixtureProvider({"phase-103": CORPUS.read_bytes()})
        run = AcquisitionEngine(store, self.root / "runs")
        run.register(provider); acquired = run.acquire("fixture", "phase-103", started_at=TIME)
        snapshot_path = Path(acquired["downloaded_snapshots"][0]["path"])
        snapshot = json.loads((snapshot_path / "manifest.json").read_text())
        normalized = normalize_snapshot(provider, store, snapshot_path, self.root / "normalized.json")
        assertions = assertions_from_normalized(normalized,
            ProviderTrustPolicy("authoritative_structured", .9, "verified"), TIME)
        package = build_review_package(acquired, [snapshot], [normalized], assertions,
                                       POLICY, "phase-103-v1")
        CanonicalPromotionEngine(self.root / "canonical", self.root / "audit").promote(
            package, POLICY, PromotionDecision("independent-reviewer", TIME,
            allow_unknowns=True, reason="approved projection input"))
        self.engine = TypedCanonicalProjectionEngine(self.root / "canonical",
            self.root / "canonical/games", self.root / "projection-audit")

    def tearDown(self): self.temp.cleanup()

    def test_projection_is_deterministic_idempotent_audited_and_repeatable(self):
        validation = self.engine.validate(); self.assertTrue(validation["valid"])
        first = self.engine.project(TIME)
        before = {str(path.relative_to(self.root / "canonical/games")): path.read_bytes()
                  for path in (self.root / "canonical/games").rglob("*.json")}
        second = self.engine.project("2099-01-01T00:00:00+00:00")
        after = {str(path.relative_to(self.root / "canonical/games")): path.read_bytes()
                 for path in (self.root / "canonical/games").rglob("*.json")}
        self.assertEqual(first, second); self.assertEqual(before, after)
        self.assertEqual(first, self.engine.inspect(first["projection_id"]))
        self.assertEqual(first["schema_version"], "typed-canonical-projection-v1")
        self.assertEqual(len(first["source_assertion_ids"]), 27)
        self.assertEqual(len(first["projected_entity_ids"]), 5)

    def test_projection_is_compatible_with_all_read_layers(self):
        self.engine.project(TIME)
        query = CanonicalQueryEngine(games_root=self.root / "canonical/games", data_root=self.root)
        card = query.entity("card-alpha")
        self.assertEqual(card.canonical_values["name"], "Alpha Adept")
        self.assertEqual(query.entities(set_id="set-one")[0].canonical_values["set_id"], "set-one")
        analytics = CanonicalAnalyticsEngine(query)
        self.assertEqual(analytics.summary().data["entity_counts_by_type"],
                         {"card": 2, "game": 1, "printing": 3})
        semantic = CanonicalSemanticQueryEngine(query, analytics)
        self.assertEqual(semantic.execute(SemanticRequest("find_identifier",
            {"identifier": "card-alpha"})).to_dict()["result"][0]["canonical_identity"], "card-alpha")
        context = ReasoningContextBuilder(semantic).build(ReasoningContextRequest(
            SemanticRequest("list_type", {"entity_type": "printing"})))
        self.assertEqual(len(context.entities), 3)

    def test_validation_prevents_missing_conflicting_duplicate_and_bad_lifecycle(self):
        state_path = self.root / "canonical/state.json"; original = json.loads(state_path.read_text())
        cases = []
        missing = copy.deepcopy(original); missing["card"]["card-alpha"]["values"].pop("/name"); cases.append(missing)
        duplicate = copy.deepcopy(original); duplicate["card"]["card-beta"]["evidence_references"][0] = \
            duplicate["card"]["card-alpha"]["evidence_references"][0]; cases.append(duplicate)
        lifecycle = copy.deepcopy(original); lifecycle["card"]["card-alpha"]["superseded_status"] = True; cases.append(lifecycle)
        unsupported = copy.deepcopy(original); unsupported["set"] = {"set-one": {}}; cases.append(unsupported)
        for state in cases:
            state_path.write_text(json.dumps(state))
            self.assertFalse(self.engine.validate()["valid"])
            with self.assertRaises(ProjectionValidationError): self.engine.project(TIME)
        state_path.write_text(json.dumps(original))


if __name__ == "__main__": unittest.main()
