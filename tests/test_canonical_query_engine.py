import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from mtglab.__main__ import main
from query import CanonicalQueryEngine, QueryError


ROOT = Path(__file__).parents[1]


class CanonicalQueryEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = CanonicalQueryEngine()

    def test_entity_and_identifier_lookups(self):
        card = self.engine.entity("magic.lightning-bolt")
        self.assertEqual(card.entity_type, "card")
        self.assertEqual(card.canonical_values["name"], "Lightning Bolt")
        self.assertEqual(card.provenance_summary["source_ids"], ["gatherer-lightning-bolt-lea"])
        self.assertEqual(card.confidence, 1.0)
        self.assertEqual(card.uncertainty, "known")
        self.assertEqual(self.engine.entities(printing_id="magic.lea.161.en")[0].canonical_identity, "magic.lea.161.en")
        self.assertEqual(len(self.engine.entities(set_id="mb2")), 4)
        self.assertEqual(len(self.engine.entities(entity_type="card")), 15)

    def test_relationships_and_provenance(self):
        printings = self.engine.related("magic.lightning-bolt", "card_printings")
        self.assertEqual([x.canonical_identity for x in printings], ["magic.lea.161.en"])
        self.assertEqual(self.engine.related("magic.lea.161.en", "printing_card")[0].canonical_identity, "magic.lightning-bolt")
        self.assertEqual(self.engine.related("magic.lea.161.en", "printing_set"), ({
        "canonical_identity": "lea", "entity_type": "set",
        "printing_ids": ["magic.lea.161.en", "magic.lea.232.en", "magic.lea.262.en",
                         "magic.lea.263.en", "magic.lea.264.en", "magic.lea.265.en",
                         "magic.lea.266.en", "magic.lea.270.en", "magic.lea.47.en",
                         "magic.lea.83.en", "magic.lea.85.en"]},))
        provenance = self.engine.provenance("magic.lightning-bolt")
        self.assertEqual(provenance["canonical_identity"], "magic.lightning-bolt")
        self.assertEqual(provenance["evidence_assertions"][0]["source_id"], "gatherer-lightning-bolt-lea")

    def test_search_is_deterministic_and_repeatable(self):
        self.assertEqual([x.canonical_identity for x in self.engine.search("Lightning Bolt")], ["magic.lightning-bolt"])
        self.assertEqual(self.engine.search("lightning bolt", mode="normalized"), self.engine.search("LIGHTNING BOLT", case_insensitive=True))
        first = self.engine.search("mox", mode="prefix", case_insensitive=True)
        self.assertEqual(first, self.engine.search("mox", mode="prefix", case_insensitive=True))
        self.assertEqual([x.canonical_identity for x in first], sorted(x.canonical_identity for x in first))
        with self.assertRaises(QueryError):
            self.engine.search("bolt", mode="fuzzy")

    def test_promoted_dataset_review_audit_and_validation_states(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            games = ROOT / "data/canonical/games"
            state = {"card": {
                "magic.query-test": {"entity_type": "card", "values": {"name": "Query Test", "provider_id": "p-1", "external_id": "e-1"},
                 "promotion_id": "promotion-test", "review_package_id": "review-test",
                 "dataset_identity": [{"dataset_id": "dataset-test"}], "acquisition_lineage": {"run_id": "run-test"},
                 "evidence_references": ["assertion-test"], "confidence": .75,
                 "uncertainty_state": "unknowns_reviewed", "superseded_status": True}}}
            canonical = tmp_path / "canonical"
            canonical.mkdir()
            (canonical / "state.json").write_text(json.dumps(state))
            audit = {"promotion_id": "promotion-test", "promoted_entities": ["magic.query-test"], "rejected_entities": [],
                     "validation_results": {"valid": True}, "review_package": {"review_package_id": "review-test",
                     "provider": {"provider_id": "provider-test"}, "candidate_assertions": [{"id": "assertion-test",
                     "source_id": "provider-test", "status": "candidate", "evidence_class": "unknown"}]}}
            audit_root = tmp_path / "audit"
            audit_root.mkdir()
            (audit_root / "promotion-test.json").write_text(json.dumps(audit))
            query = CanonicalQueryEngine(games_root=games, data_root=tmp_path)
            result = query.entity("magic.query-test")
            self.assertEqual(query.entities(provider_id="p-1"), (result,))
            self.assertEqual(query.entities(external_id="e-1"), (result,))
            self.assertEqual(query.dataset("dataset-test")["promoted_entities"][0]["canonical_identity"], result.canonical_identity)
            self.assertEqual(query.related("review-test", "review_package_entities"), (result,))
            self.assertEqual(query.related("promotion-test", "promotion_audits")[0]["promotion_id"], "promotion-test")
            self.assertEqual(query.validation("unknown"), (result,))
            self.assertEqual(query.validation("superseded"), (result,))

    def test_rejected_and_validation_failure_audits(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            audit = tmp_path / "audit"
            audit.mkdir()
            value = {"promotion_id": "failed", "promoted_entities": [], "rejected_entities": ["bad"],
                     "validation_results": {"valid": False}}
            (audit / "failed.json").write_text(json.dumps(value))
            query = CanonicalQueryEngine(games_root=ROOT / "data/canonical/games", data_root=tmp_path)
            self.assertEqual(query.validation("rejected")[0]["rejected_entities"], ["bad"])
            self.assertEqual(query.validation("validation_failure")[0]["promotion_id"], "failed")

    def _run_cli(self, arguments):
        output = StringIO()
        with redirect_stdout(output):
            result = main(arguments)
        self.assertEqual(result, 0)
        return json.loads(output.getvalue())

    def test_cli_query_operations(self):
        prefix = ["--data-root", str(ROOT / "data"), "query"]
        self.assertEqual(self._run_cli(prefix + ["entity", "magic.lightning-bolt"])[0]["canonical_identity"], "magic.lightning-bolt")
        self.assertEqual(self._run_cli(prefix + ["search", "light", "--mode", "prefix", "--case-insensitive"])[0]["canonical_identity"], "magic.lightning-bolt")
        self.assertEqual(self._run_cli(prefix + ["provenance", "magic.lightning-bolt"])["source_ids"], ["gatherer-lightning-bolt-lea"])
        self.assertEqual(self._run_cli(prefix + ["validation", "superseded"]), [])
        self.assertEqual(self._run_cli(prefix + ["dataset", "missing-dataset"])["promoted_entities"], [])


if __name__ == "__main__":
    unittest.main()
