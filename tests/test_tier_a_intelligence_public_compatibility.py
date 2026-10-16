"""Existing public bytes in place; compatibility is not permission or activation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from card_intelligence import MechanicalCardIntelligence, CardAcquisitionAdapter
from card_intelligence.mechanics import content_identity
from repository.legacy_profile import attach_legacy_compatibility
from repository.snapshots import SnapshotError

ROOT = Path(__file__).resolve().parents[1]
CONTROL = "config/catalog_profiles/legacy-public-tier-a.json"
EXPECTED_QUERY = "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7"


class TierAIntelligencePublicCompatibilityTests(unittest.TestCase):
    def test_current_public_vertical_parity_in_place_or_explicit_baseline_drift_block(self):
        control = json.loads((ROOT / CONTROL).read_bytes())
        def attach():
            return attach_legacy_compatibility(ROOT, control_path=CONTROL, game="magic",
                                               expected_profile_id=control["profile_id"])
        intact = all(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]
                     for row in control["files"])
        # The real publication regression changes the current catalog through the
        # writer. This exact OLD profile must then block, never substitute history.
        if not intact:
            with self.assertRaises(SnapshotError):
                MechanicalCardIntelligence.from_attachment(attach(), data_root=ROOT / "data",
                    expected_query_snapshot_id=EXPECTED_QUERY)
            return
        protected = {row["path"]: hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest()
                     for row in control["files"]}
        attached = MechanicalCardIntelligence.from_attachment(attach(), data_root=ROOT / "data",
                    expected_query_snapshot_id=EXPECTED_QUERY)
        legacy = MechanicalCardIntelligence(ROOT / "data")
        self.assertEqual(attached.snapshot_id, EXPECTED_QUERY)
        self.assertEqual(attached.snapshot_id, legacy.snapshot_id)
        self.assertEqual(set(attached.cards), set(legacy.cards))
        self.assertEqual(content_identity(attached.reconciliation), content_identity(legacy.reconciliation))
        self.assertEqual(content_identity(attached.source), content_identity(legacy.source))
        identities = sorted(key for key in attached.cards if len(attached.rows[key]) == 1)[:2]
        self.assertEqual(len(identities), 2)
        for identity in identities:
            self.assertEqual(hashlib.sha256(attached.dossier(identity).to_json().encode()).hexdigest(),
                             hashlib.sha256(legacy.dossier(identity).to_json().encode()).hexdigest())
        self.assertEqual(hashlib.sha256(attached.reasoning_context(identities[0]).to_json().encode()).hexdigest(),
                         hashlib.sha256(legacy.reasoning_context(identities[0]).to_json().encode()).hexdigest())
        integrated = CardAcquisitionAdapter.from_mechanical(attached, expected_query_snapshot_id=EXPECTED_QUERY)
        old = CardAcquisitionAdapter(ROOT / "data")
        self.assertEqual(integrated.policy.to_dict(), old.policy.to_dict())
        candidates = []
        for identity in identities:
            printing = next(p for p in integrated.printings.values() if p.canonical_values["card_id"] == identity)
            values = printing.canonical_values
            candidates.append({"card_id":identity,"printing_id":printing.canonical_identity,
                "acceptable_printing_ids":[printing.canonical_identity],"desired_quantity":1,
                "preferred_dimensions":{"language":values["language"],"finish":values["finish_ids"][0],
                                        "treatment":values.get("treatment")},"eligibility":None,"offer":None})
        # Intentionally no buyer, ownership or market evidence: honest abstention.
        packet = {"schema_version":"card-acquisition-input-v1","mode":"synthetic_demonstration",
                  "as_of":"2026-10-15T00:00:00Z","canonical_snapshot_id":EXPECTED_QUERY,
                  "sources":[],"candidates":candidates}
        with tempfile.TemporaryDirectory() as directory:
            result = integrated.evaluate(packet,source_root=Path(directory))
            reference = old.evaluate(packet,source_root=Path(directory))
        self.assertEqual(hashlib.sha256(result.to_json().encode()).hexdigest(),
                         hashlib.sha256(reference.to_json().encode()).hexdigest())
        self.assertEqual(result.to_dict()["decision"]["recommendation"]["outcome"],"abstain")
        self.assertEqual(result.to_dict()["canonical_snapshot_id"], EXPECTED_QUERY)
        self.assertEqual(integrated.catalog_binding, attached.catalog_binding)
        self.assertIs(integrated.query, attached.query)
        self.assertEqual({p:hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in protected},protected)


if __name__ == "__main__": unittest.main()
