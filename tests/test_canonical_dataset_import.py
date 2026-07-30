import json
import tempfile
import unittest
from pathlib import Path

from dataset_import import DatasetImportError, DatasetRegistry, EntityResolver, ImportManager
from mtglab.__main__ import main

MANIFEST = Path("data/fixtures/canonical_import/pilot-manifest.json")
PILOT = Path("data/fixtures/canonical_import/pilot-reviewed-cards.json")
TS = "2026-07-30T16:00:00+00:00"


class CanonicalDatasetImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.registry = DatasetRegistry(self.root / "datasets")
        self.manifest = json.loads(MANIFEST.read_text()); self.dataset = self.registry.register(self.manifest)

    def tearDown(self): self.temp.cleanup()

    def test_registration_is_first_class_and_idempotent(self):
        self.assertEqual(self.dataset, self.registry.register(self.manifest))
        self.assertEqual(len(self.registry.list()), 1)
        self.assertTrue(self.dataset["canonical_import_id"].startswith("dataset-import-"))
        changed = dict(self.manifest, provider="different")
        with self.assertRaisesRegex(DatasetImportError, "already registered differently"):
            self.registry.register(changed)

    def test_resolution_priority_duplicates_collisions_and_unresolved(self):
        rows = json.loads(PILOT.read_text())["records"]
        result = EntityResolver().resolve(rows)
        self.assertEqual(len(result["resolved"]), 35)
        self.assertEqual(len(result["unresolved"]), 1)
        self.assertEqual({x["reason"] for x in result["rejected"]},
                         {"conflicting_identity", "identifier_collision"})
        generated = EntityResolver().resolve([{"id":"x", "entity_type":"card",
            "identifiers":{"provider_identifier":"provider-x"}, "normalized":{"name":"X"}}])
        self.assertEqual(generated, EntityResolver().resolve([{"id":"x", "entity_type":"card",
            "identifiers":{"provider_identifier":"provider-x"}, "normalized":{"name":"X"}}]))

    def test_complete_governed_partial_import_report_and_audit(self):
        report = ImportManager(self.root, self.registry).run(
            self.manifest["logical_dataset_identity"], "1.0.0", PILOT, actor="reviewer", timestamp=TS)
        self.assertEqual(report["import_summary"]["status"], "partial")
        self.assertEqual(report["completeness_metrics"],
                         {"total":39,"imported":35,"rejected":3,"unresolved":1,"import_ratio":35/39})
        session = ImportManager(self.root, self.registry).status(report["import_summary"]["session_id"])
        self.assertTrue(session["validation_results"]["valid"])
        self.assertTrue((self.root / "audit/knowledge-promotions" / f"{session['promotion_id']}.json").exists())
        self.assertTrue((self.root / "canonical/knowledge/state.json").exists())

    def test_repeated_import_is_deterministic_and_idempotent(self):
        manager = ImportManager(self.root, self.registry)
        first = manager.run("mtg-lab-pilot-cards", "1.0.0", PILOT, actor="reviewer", timestamp=TS)
        second = manager.run("mtg-lab-pilot-cards", "1.0.0", PILOT, actor="reviewer", timestamp=TS)
        self.assertEqual(first, second)
        self.assertEqual(len(self.registry.get("mtg-lab-pilot-cards", "1.0.0")["import_history"]), 1)

    def test_partial_import_can_fail_closed(self):
        with self.assertRaisesRegex(DatasetImportError, "partial import"):
            ImportManager(self.root, self.registry).run("mtg-lab-pilot-cards", "1.0.0", PILOT,
                actor="reviewer", timestamp=TS, allow_partial=False)
        self.assertFalse((self.root / "canonical").exists())

    def test_cli_registration_listing_import_status_and_report(self):
        self.temp.cleanup(); self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.assertEqual(main(["--data-root", str(self.root), "dataset", "register", str(MANIFEST)]), 0)
        self.assertEqual(main(["--data-root", str(self.root), "dataset", "list"]), 0)
        self.assertEqual(main(["--data-root", str(self.root), "import", "mtg-lab-pilot-cards", "--version", "1.0.0",
            "--source", str(PILOT), "--actor", "reviewer", "--timestamp", TS]), 0)
        session = next((self.root / "import-sessions").iterdir()).name
        self.assertEqual(main(["--data-root", str(self.root), "import", "status", session]), 0)
        self.assertEqual(main(["--data-root", str(self.root), "import", "report", session]), 0)


if __name__ == "__main__": unittest.main()
