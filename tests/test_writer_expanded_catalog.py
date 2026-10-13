"""Whole supported-writer workflow over the retained pending recommendation.

All current-catalog state is writer output in live disposable storage. Historical
source and expected snapshot remain unchanged; no personal inventory is published.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from catalog_admission_helpers import (PACKET, PACKET_DIGEST, RECOMMENDED_DIGEST,
                                       prepare_reference_rehearsal)
from production_evidence.automatic_updates import AutomaticCanonicalUpdate
from production_evidence.repository import EvidenceError


class PendingReferenceAuthorizationTests(unittest.TestCase):
    def test_retained_pending_recommendations_alone_cannot_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config, _ = prepare_reference_rehearsal(root)
            original = (root / "data/canonical/state.json").read_bytes()
            with self.assertRaises(EvidenceError):
                AutomaticCanonicalUpdate(root, config).execute(
                    stop_after="query_and_analytics_smoke_tests")
            self.assertEqual((root / "data/canonical/state.json").read_bytes(), original)
            self.assertFalse((root / "data/audit/bounded_promotions/isolated-reference-810-writer-rehearsal.json").exists())


class WriterExpandedCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from production_evidence.automatic_updates import IsolatedAdmissionTestBoundary
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.config, cls.selected = prepare_reference_rehearsal(cls.root)
        cls.before = json.loads((cls.root / "data/canonical/state.json").read_bytes())
        cls.engine = AutomaticCanonicalUpdate(cls.root, cls.config,
            review_boundary=IsolatedAdmissionTestBoundary(cls.temporary))
        cls.status = cls.engine.execute(stop_after="query_and_analytics_smoke_tests")
        cls.state = json.loads((cls.root / "data/canonical/state.json").read_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_exact_whole_writer_delta_and_held_packet_preservation(self):
        self.assertEqual({k: len(v) for k, v in self.state.items()},
            {"card": 654, "printing": 1183, "identifier": 505, "finish": 2})
        self.assertEqual(Counter(c["entity_type"] for c in self.selected),
            {"card": 270, "printing": 270, "identifier": 270})
        for kind, old_records in self.before.items():
            for identifier, record in old_records.items():
                self.assertEqual(self.state[kind][identifier], record)
        self.assertEqual(hashlib.sha256((PACKET / "candidate-preparation.json").read_bytes()).hexdigest(), PACKET_DIGEST)
        self.assertEqual(self.engine.descriptor.candidate_digest, RECOMMENDED_DIGEST)
        self.assertEqual(self.status["next_stage"], "branch_and_pull_request_persistence")

    def test_writer_retains_native_identity_original_values_and_lineage(self):
        for candidate in self.selected:
            row = candidate["payload"]
            kind = row["entity_type"]
            identifier = row["mapped_fields"].get({"card": "card_reference", "printing": "uuid"}.get(kind, ""),
                row["candidate_identifier"].rsplit(":", 1)[-1]).casefold()
            record = self.state[kind][identifier]
            self.assertEqual(record["source_values"], row["mapped_fields"])
            self.assertEqual(record["provenance"], row["provenance"])
            self.assertEqual(record["unknown_values"], row["unknown_fields"])
            self.assertEqual(record["confidence"], row["confidence"])
            self.assertEqual(record["acquisition_lineage"], [row["acquisition_metadata"]])
            self.assertEqual(record["candidate_context"]["field_provenance"], candidate["field_provenance"])
            self.assertTrue(record["parsed_record_references"])
            if kind == "printing":
                v = record["values"]
                self.assertEqual(v["card_id"], row["mapped_fields"]["card_reference"])
                self.assertEqual(v["finish_ids"], ["nonfoil"])
                self.assertEqual(v["language"], {"English": "en", "Japanese": "ja"}[row["mapped_fields"]["language"]])

    def test_actual_query_collection_projection_and_new_calculation(self):
        from query import CanonicalQueryEngine
        from collection.intelligence import CanonicalCollectionResolver
        from projection.engine import TypedCanonicalProjectionEngine
        q = CanonicalQueryEngine("magic", data_root=self.root / "data",
            games_root=self.root / "data/canonical/games")
        resolver = CanonicalCollectionResolver("magic", self.root / "data")
        self.assertEqual(len(resolver.production_printing_ids), 1183)
        self.assertNotEqual(q.snapshot().snapshot_id,
            "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7")
        for row in [c["payload"] for c in self.selected if c["entity_type"] == "printing"]:
            cid, pid = row["mapped_fields"]["card_reference"], row["mapped_fields"]["uuid"]
            self.assertIn(pid, [x.canonical_identity for x in q.related(cid, "card_printings")])
            self.assertEqual(q.related(pid, "printing_card")[0].canonical_identity, cid)
            self.assertEqual(q.related(pid, "printing_set")[0]["canonical_identity"], "plst")
        validation = TypedCanonicalProjectionEngine(self.root / "data/canonical",
            self.root / "data/canonical/games", self.root / "data/projection-audit").validate()
        self.assertTrue(validation["valid"], validation)

    def test_writer_consumer_reports_all_retained_historical_finish_gaps(self):
        from projection.engine import TypedCanonicalProjectionEngine
        projection = TypedCanonicalProjectionEngine(self.root / "data/canonical",
            self.root / "data/canonical/games", self.root / "data/projection-audit").validate()
        expected = projection["historical_unresolved_finish_references"]
        self.assertEqual(len(expected), 30)
        self.assertEqual(Counter(label for gap in expected for label in gap["provider_finish_labels"]),
                         {"signed": 21, "etched": 9})
        for stage in ("bounded_canonical_promotion", "query_and_analytics_smoke_tests"):
            with self.subTest(stage=stage):
                checkpoint = json.loads(self.engine._checkpoint(stage).read_bytes())
                consumer = checkpoint["details"]["consumer_validation"]
                self.assertEqual(consumer["historical_finish_gaps"], expected)
                self.assertFalse(consumer["typed_materialization_ready"])

    def test_missing_mechanical_coverage_and_acquisition_abstain_after_writer(self):
        from card_intelligence.mechanics import MechanicalCardIntelligence
        from card_intelligence.acquisition import CardAcquisitionAdapter, CardAcquisitionDossier
        m = MechanicalCardIntelligence(self.root / "data")
        self.assertEqual(m.reconciliation["production_card_count"], 654)
        self.assertEqual(m.reconciliation["uniquely_mapped_card_count"], 384)
        self.assertEqual(len(m.reconciliation["missing_canonical_card_ids"]), 270)
        rows = [c["payload"] for c in self.selected if c["entity_type"] == "printing"][:2]
        packet = {"schema_version": "card-acquisition-input-v1", "mode": "synthetic_demonstration",
            "as_of": "2026-10-13T00:00:00Z", "canonical_snapshot_id": m.snapshot_id,
            "sources": [], "candidates": [{"card_id": r["mapped_fields"]["card_reference"],
                "printing_id": r["mapped_fields"]["uuid"],
                "acceptable_printing_ids": [r["mapped_fields"]["uuid"]], "desired_quantity": 1,
                "preferred_dimensions": {"language": "en", "finish": "nonfoil", "treatment": None}} for r in rows]}
        adapter = CardAcquisitionAdapter(self.root / "data")
        dossier = adapter.evaluate(packet, source_root=self.root).to_dict()
        self.assertEqual(dossier["decision"]["recommendation"]["outcome"], "abstain")
        self.assertFalse(dossier["actual_purchase_advice"])
        self.assertTrue(any("source_binding_missing" in x for x in dossier["blockers"]))

    def test_bounded_repeat_preserves_state_and_original_pending_packet(self):
        before = (self.root / "data/canonical/state.json").read_bytes()
        stages = {p.name: p.read_bytes() for p in (self.engine.run_root / "stages").glob("*.json")}
        self.engine.execute(stop_after="query_and_analytics_smoke_tests")
        self.assertEqual(before, (self.root / "data/canonical/state.json").read_bytes())
        self.assertEqual(stages, {p.name: p.read_bytes() for p in (self.engine.run_root / "stages").glob("*.json")})


if __name__ == "__main__":
    unittest.main()
