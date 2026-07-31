"""Phase 104 bounded MTGJSON canonical promotion acceptance tests."""
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from mtglab.__main__ import main
from promotion import BoundedCorpusPromotion

ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "data/reference/mtgjson/bounded-canonical-promotion-v1.json"


class BoundedCanonicalPromotionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.workflow = BoundedCorpusPromotion(self.root, CORPUS)

    def tearDown(self): self.temporary.cleanup()

    def test_reviewed_promotion_projection_consumers_replay_and_rollback(self):
        first = self.workflow.promote()
        second = self.workflow.promote()
        self.assertEqual(first, second)
        self.assertEqual(first["promoted_entity_count"], 5)
        self.assertEqual(first["rejected_candidate_count"], 1)
        self.assertTrue(first["replay_matches"])
        self.assertNotEqual(first["superseding_promotion_id"], first["rollback_id"])

        report = self.workflow.verify()
        self.assertTrue(report["valid"], report)
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["ai_model_request"]["provider_identifier"], "not-invoked")
        state = json.loads((self.root / "canonical/state.json").read_text())
        self.assertEqual(state["card"]["card-alpha"]["values"]["/name"],
                         "Alpha Adept, Reviewed")
        self.assertEqual(state["printing"]["printing-alpha-ja"]["values"]["/artist"], None)
        self.assertEqual(state["printing"]["printing-alpha-ja"]["confidence"], .9)
        self.assertEqual(state["printing"]["printing-alpha-ja"]["uncertainty_state"],
                         "unknowns_reviewed")
        failed = [event for event in self.workflow.inspect()["audits"]
                  if not event["validation_results"]["valid"]]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["promoted_entities"], [])
        self.assertTrue(failed[0]["rejected_entities"])

    def test_cli_corpus_inspect_and_verify_are_json(self):
        for command in ("corpus", "inspect", "verify"):
            output = StringIO()
            with redirect_stdout(output):
                code = main(["--data-root", str(self.root), "promote", command,
                             "--format", "json"])
            self.assertEqual(code, 0, output.getvalue())
            value = json.loads(output.getvalue())
            self.assertEqual(value["schema_version"], "bounded-canonical-promotion-v1")
        self.assertTrue(value["valid"])


if __name__ == "__main__": unittest.main()
