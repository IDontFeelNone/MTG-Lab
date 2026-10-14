"""Historical replay uses its explicit catalog; current calculations get new IDs.

The current-root copy below deliberately changes a historical value solely to
exercise snapshot rejection. Writer-expanded catalog coverage is tested by the
admission workflow regressions, never by constructing a replacement store here.
"""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from card_intelligence.roles import FunctionalRoleError, FunctionalRolePilot
from collection.audit import CollectionAudit, CollectionAuditError
from collection.intelligence import CanonicalCollectionResolver, build_snapshot, read_import


from historical_catalog import historical_repository

# This module replays the retained original catalog, not the current catalog.
ROOT = historical_repository()
HISTORICAL_DATA = ROOT / "data"
IMPORT = ROOT / "data/collections/imports/fictional-collection-audit-pilot.json"
SNAPSHOT = ROOT / "data/collections/snapshots/4a8072970571a357780a6d24.json"
PONDER = "02090581-61aa-4348-ad57-451be8ee91c2"


class HistoricalCatalogSeparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.current_data = Path(self.temporary.name) / "data"
        shutil.copytree(HISTORICAL_DATA / "canonical", self.current_data / "canonical")
        shutil.copytree(HISTORICAL_DATA / "audit", self.current_data / "audit")
        # The mechanical source is copied unchanged so missing coverage cannot
        # be confused with the intentionally changed canonical binding.
        shutil.copytree(HISTORICAL_DATA / "market/acquisitions",
                        self.current_data / "market/acquisitions")
        self.original_snapshot_bytes = SNAPSHOT.read_bytes()
        self.historical_snapshot = json.loads(self.original_snapshot_bytes)
        self.historical = CanonicalCollectionResolver("magic", HISTORICAL_DATA)

    def tearDown(self):
        self.assertEqual(SNAPSHOT.read_bytes(), self.original_snapshot_bytes)
        self.temporary.cleanup()

    def change_current_catalog(self):
        path = self.current_data / "canonical/state.json"
        state = json.loads(path.read_bytes())
        state["card"][PONDER]["values"]["name"] = "Deliberately changed snapshot test value"
        path.write_text(json.dumps(state, sort_keys=True) + "\n")
        return CanonicalCollectionResolver("magic", self.current_data)

    def test_explicit_original_fixture_replays_without_repinning_history(self):
        self.assertEqual(hashlib.sha256(self.original_snapshot_bytes).hexdigest(),
                         "870fed09a14ddf58fa775084ae787c474a4555a0076934f9d619bf29835d56ad")
        replay = CollectionAudit(self.historical).verify_source_snapshot(
            self.historical_snapshot, source_path=IMPORT, source_root=ROOT)
        self.assertEqual(replay, self.historical_snapshot)
        relocated = CanonicalCollectionResolver("magic", self.current_data)
        self.assertEqual(relocated.canonical_snapshot_id, self.historical.canonical_snapshot_id)
        self.assertEqual(CollectionAudit(relocated).verify_source_snapshot(
            self.historical_snapshot, source_path=IMPORT, source_root=ROOT), replay)

    def test_changed_current_root_rejects_history_and_never_falls_back(self):
        current = self.change_current_catalog()
        self.assertNotEqual(current.canonical_snapshot_id, self.historical.canonical_snapshot_id)
        with self.assertRaisesRegex(CollectionAuditError, "canonical snapshot changed"):
            CollectionAudit(current).verify_source_snapshot(
                self.historical_snapshot, source_path=IMPORT, source_root=ROOT)
        with self.assertRaisesRegex(FunctionalRoleError, "snapshot"):
            FunctionalRolePilot(self.current_data)
        # A correct historical rejection does not make the original fixture
        # unusable or silently rewrite its retained binding.
        self.assertEqual(CollectionAudit(self.historical).verify_source_snapshot(
            self.historical_snapshot, source_path=IMPORT, source_root=ROOT),
            self.historical_snapshot)

    def test_new_current_calculation_has_distinct_snapshot_and_audit_identity(self):
        current = self.change_current_catalog()
        imported = read_import(IMPORT)
        new_snapshot = build_snapshot(imported, current.resolve(imported), None)
        self.assertNotEqual(new_snapshot["snapshot_id"], self.historical_snapshot["snapshot_id"])
        self.assertNotEqual(new_snapshot["snapshot_digest"], self.historical_snapshot["snapshot_digest"])
        self.assertEqual(new_snapshot["canonical_snapshot_id"], current.canonical_snapshot_id)
        historical_audit = CollectionAudit(self.historical).build(
            self.historical_snapshot, source_path=IMPORT, source_root=ROOT, expected_total=360)
        current_audit = CollectionAudit(current).build(
            new_snapshot, source_path=IMPORT, source_root=ROOT, expected_total=360)
        self.assertNotEqual(current_audit["audit_id"], historical_audit["audit_id"])
        self.assertEqual(current_audit["quantity_census"]["confirmed_total_quantity"], 360)
        self.assertEqual(new_snapshot["source_import_digest"], self.historical_snapshot["source_import_digest"])


if __name__ == "__main__":
    unittest.main()
