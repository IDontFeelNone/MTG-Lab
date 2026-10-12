"""Regressions for production-shaped bounded promotion lineage projections."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from query import CanonicalQueryEngine
from reasoning import ReasoningContextBuilder, ReasoningContextRequest
from semantic import CanonicalSemanticQueryEngine, SemanticRequest


ROOT = Path(__file__).parents[1]
DATA = ROOT / "data"
SOL_RING = "6ad8011d-3471-4369-9d68-b264cc027487"
COUNTERSPELL = "cc187110-1148-4090-bbb8-e205694a39f5"
SOL_RING_PRINTING = "006bd15a-3949-51a7-9c11-06142f3bcc41"


class PromotedQueryLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        state = json.loads((DATA / "canonical/state.json").read_bytes())
        cls.state = {"card": {identity: state["card"][identity]
                              for identity in (SOL_RING, COUNTERSPELL)},
                     "printing": {SOL_RING_PRINTING: state["printing"][SOL_RING_PRINTING]}}
        cls.audit_files = {path.relative_to(DATA).as_posix(): path.read_bytes()
                           for path in (DATA / "audit/bounded_promotions").glob("*.json")}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self._write_fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def _write_fixture(self, root):
        (root / "canonical").mkdir(parents=True)
        (root / "canonical/state.json").write_text(json.dumps(self.state, sort_keys=True))
        for locator, content in self.audit_files.items():
            path = root / locator
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def _engine(self, root=None):
        return CanonicalQueryEngine(games_root=DATA / "canonical/games", data_root=root or self.root)

    @staticmethod
    def _context(engine, identity):
        return ReasoningContextBuilder(CanonicalSemanticQueryEngine(engine)).build(
            ReasoningContextRequest(SemanticRequest("find_identifier", {"identifier": identity}),
                                    maximum_entities=1, maximum_evidence_items=10))

    def test_exact_production_identity_and_retained_card_reference_bindings(self):
        engine = self._engine()
        for identity, name in ((SOL_RING, "Sol Ring"), (COUNTERSPELL, "Counterspell")):
            with self.subTest(identity=identity):
                result = engine.entity(identity, entity_type="card")
                retained = self.state["card"][identity]
                provenance = result.provenance_summary
                self.assertEqual(result.canonical_values, retained["values"])
                self.assertEqual(result.canonical_values["name"], name)
                self.assertEqual(provenance["record_provenance"], retained["provenance"])
                self.assertEqual(provenance["acquisition_lineage"], retained["acquisition_lineage"])
                self.assertEqual(provenance["dataset_identity"], retained["dataset_identity"])
                self.assertEqual(provenance["source_ids"], [retained["provenance"]["artifact_identifier"]])
                self.assertEqual([item["id"] for item in provenance["evidence_assertions"]],
                                 retained["evidence_references"])
                reference = provenance["evidence_assertions"][0]
                self.assertEqual(reference["canonical_identity"], identity)
                self.assertEqual(reference["provenance"], retained["provenance"])
                self.assertEqual(reference["acquisition_lineage"], retained["acquisition_lineage"])
                self.assertNotIn("value", reference)
                self.assertNotIn("verified", reference)
                if name == "Sol Ring":
                    self.assertEqual({item.canonical_identity for item in engine.search(name)},
                                     {SOL_RING, "magic.sol-ring"})
                self.assertNotEqual(identity, "magic.sol-ring" if name == "Sol Ring" else "magic.counterspell")

    def test_bounded_audit_reference_preserves_digests_and_exact_membership(self):
        engine = self._engine()
        for identity in (SOL_RING, COUNTERSPELL):
            history = engine.entity(identity).provenance_summary["promotion_history"]
            self.assertEqual(len(history), 1)
            summary = history[0]
            locator = summary["audit_reference"]["relative_path"]
            content = self.audit_files[locator]
            audit = json.loads(content)
            self.assertEqual(summary["audit_reference"]["sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(summary["audit_digest"], audit["audit_digest"])
            self.assertEqual(summary["source_lineage_digest"], audit["source_lineage_digest"])
            self.assertEqual(summary["review_artifact_digests"], audit["review_artifact_digests"])
            self.assertEqual(summary["entity_binding"]["canonical_identity"], identity)
            self.assertEqual(summary["entity_binding"]["matched_promoted_references"],
                             self.state["card"][identity]["evidence_references"])
            self.assertEqual(summary["omitted_promoted_entity_count"], 999)
            self.assertNotIn("promoted_entities", summary)
            self.assertNotIn("review_package", summary)
            self.assertLess(len(json.dumps(summary).encode()), 6000)
            # Full audit retrieval is still available through its explicit query.
            self.assertEqual(engine.related(summary["promotion_id"], "promotion_audits")[0], audit)

    def test_printing_lineage_preserves_original_and_projection_source_digests(self):
        engine = self._engine()
        result = engine.entity(SOL_RING_PRINTING, entity_type="printing")
        retained = self.state["printing"][SOL_RING_PRINTING]
        self.assertEqual(result.canonical_values["card_id"], SOL_RING)
        self.assertEqual(result.provenance_summary["record_provenance"], retained["provenance"])
        reference = result.provenance_summary["evidence_assertions"][0]
        self.assertEqual(reference["id"], retained["evidence_references"][0])
        self.assertEqual(reference["acquisition_lineage"], retained["acquisition_lineage"])
        self.assertEqual(set(reference["acquisition_lineage"][0]),
                         {"acquisition_run_id", "source_sha256", "normalized_projection_sha256"})
        # A source record identity is not fabricated into a registry Source ID.
        self.assertNotIn("source_id", reference)
        history = result.provenance_summary["promotion_history"]
        self.assertEqual(history[0]["entity_binding"]["matched_promoted_references"], [SOL_RING_PRINTING])
        self.assertEqual(history[0]["omitted_promoted_entity_count"], 533)
        audit = engine.related(retained["promotion_id"], "promotion_audits")[0]
        self.assertEqual(history[0]["evidence_files"], audit["evidence_files"])
        self.assertNotIn("promoted_printing_ids", history[0])
        self.assertLess(len(json.dumps(history).encode()), 3000)

    def test_generic_review_package_assertions_remain_exact_and_reference_filtered(self):
        retained = copy.deepcopy(self.state["card"][SOL_RING])
        retained["evidence_references"] = ["assertion-sol-ring"]
        retained["promotion_id"] = "generic-review-promotion"
        (self.root / "canonical/state.json").write_text(json.dumps({"card": {SOL_RING: retained}}))
        assertion = {"id": "assertion-sol-ring", "source_id": "existing-source-id",
                     "value": "Sol Ring", "status": "candidate", "evidence_class": "supported"}
        audit = {"promotion_id": retained["promotion_id"], "promoted_entities": [SOL_RING],
                 "review_package": {"provider": {"provider_id": "legacy-provider"},
                                    "candidate_assertions": [assertion, {"id": "unrelated"}]}}
        (self.root / "audit/generic.json").write_text(json.dumps(audit))
        result = self._engine().entity(SOL_RING)
        self.assertEqual(result.provenance_summary["evidence_assertions"], [assertion])
        self.assertEqual(result.provenance_summary["source_ids"], ["existing-source-id"])
        self.assertEqual(result.provenance_summary["provider_policy"], {"provider_id": "legacy-provider"})

    def test_context_replay_is_bounded_has_evidence_and_survives_root_relocation(self):
        engine = self._engine()
        with tempfile.TemporaryDirectory() as relocated:
            other_root = Path(relocated)
            self._write_fixture(other_root)
            other_engine = self._engine(other_root)
            self.assertEqual(engine.snapshot().snapshot_id, other_engine.snapshot().snapshot_id)
            for identity in (SOL_RING, COUNTERSPELL):
                with self.subTest(identity=identity):
                    first = self._context(engine, identity)
                    second = self._context(other_engine, identity)
                    self.assertEqual(first.to_json(), second.to_json())
                    self.assertEqual(first.to_json(), self._context(engine, identity).to_json())
                    self.assertEqual(len(first.evidence_references), 1)
                    evidence = first.evidence_references[identity + "#0"]
                    self.assertEqual(evidence["canonical_snapshot_id"], first.canonical_snapshot_id)
                    self.assertEqual(evidence["provenance"]["id"],
                                     self.state["card"][identity]["evidence_references"][0])
                    self.assertEqual(dict(first.omitted_item_counts), {"entities": 0, "evidence": 0, "relationships": 0})
                    self.assertLess(len(first.to_json().encode()), 20000)

    def test_raw_audit_byte_change_changes_snapshot_binding(self):
        first = self._engine()
        locator = first.entity(SOL_RING).provenance_summary["promotion_history"][0]["audit_reference"]["relative_path"]
        path = self.root / locator
        path.write_bytes(path.read_bytes() + b"\n")
        second = self._engine()
        self.assertNotEqual(first.snapshot().snapshot_id, second.snapshot().snapshot_id)
        self.assertNotEqual(self._context(first, SOL_RING).context_id, self._context(second, SOL_RING).context_id)
        self.assertEqual(first.entity(SOL_RING).canonical_values, second.entity(SOL_RING).canonical_values)

    def test_read_only_projection_cannot_write_or_promote(self):
        protected = {path: path.read_bytes() for path in
                     [DATA / "canonical/state.json", *sorted((DATA / "audit/bounded_promotions").glob("*.json"))]}
        with patch.object(Path, "write_text", side_effect=AssertionError("unexpected write")), \
                patch.object(Path, "write_bytes", side_effect=AssertionError("unexpected write")), \
                patch("production_evidence.bounded_promotion.promote", side_effect=AssertionError("unexpected promotion")), \
                patch("production_evidence.phase136_promotion.promote", side_effect=AssertionError("unexpected promotion")):
            engine = self._engine()
            self._context(engine, SOL_RING)
            self._context(engine, COUNTERSPELL)
        self.assertEqual(protected, {path: path.read_bytes() for path in protected})


if __name__ == "__main__":
    unittest.main()
