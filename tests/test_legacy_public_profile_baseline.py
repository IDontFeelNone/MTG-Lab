"""In-place compatibility characterization, never data permission or activation."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch
import unittest

from collection.intelligence import CanonicalCollectionResolver
from query.engine import CanonicalQueryEngine
from repository.legacy_profile import attach_legacy_compatibility, AUTHORITY, OPERATIONS
from repository.snapshots import SnapshotError, attach_legacy_public

ROOT = Path(__file__).resolve().parents[1]
CONTROL = "config/catalog_profiles/legacy-public-tier-a.json"
CONTRACT = ROOT / "reference-reviews/v13-legacy-profile-permission-closure"
QUERY = "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7"
BARE = "sha256:e580c987f4e7cae0c0a69e22dc025e468ceacef078a4ff907935c1d54998fa6e"


class LegacyPublicProfileBaselineTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((ROOT / CONTROL).read_bytes())

    def attach(self):
        return attach_legacy_compatibility(ROOT, control_path=CONTROL, game="magic", expected_profile_id=self.doc["profile_id"])

    def unchanged_baseline(self):
        return all(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"] for row in self.doc["files"])

    def test_control_reuses_exact_reviewed_forty_file_closure_not_provider_values(self):
        closure = json.loads((CONTRACT / "dependency-closure.json").read_bytes())
        expected = [{k: row[k] for k in ("path", "sha256", "byte_length", "placement")} for row in closure["tiers"]["A"]["files"]]
        self.assertEqual(self.doc["files"], expected)
        self.assertEqual(Counter(row["placement"] for row in expected), {
            "CORE_CATALOG_CONTENT": 33, "SOURCE_EVIDENCE_REFERENCE": 5, "AUDIT_CONTEXT": 2})
        self.assertEqual(self.doc["query_snapshot_id"], QUERY)
        self.assertEqual(self.doc["entity_counts"], {"card":399,"printing":928,"identifier":235,"finish":2,"game":1,"product":1})
        self.assertEqual(self.doc["historical_prestate_reference"], "881c4ddf1dd5f3dc8004aef001277407e359b165cba6d9f5e8d442e9eef48077")
        for key, value in AUTHORITY.items(): self.assertEqual(self.doc[key], value)
        self.assertEqual(self.doc["permissions"], dict.fromkeys(OPERATIONS, "NOT_ESTABLISHED"))
        self.assertEqual(self.doc["incompleteness"]["finish_references"], {"status":"incomplete","unresolved_by_identifier":{"signed":21,"etched":9}})
        self.assertEqual(self.doc["incompleteness"]["product_slots"], 0)
        self.assertNotEqual(self.doc["profile_id"], self.doc["closure_id"])
        self.assertNotEqual(self.doc["profile_id"], QUERY)
        self.assertNotEqual(self.doc["profile_id"].removeprefix("sha256:"), self.doc["historical_prestate_reference"])

    def test_current_catalog_in_place_parity_or_explicit_drift_rejection(self):
        # The publication gate legitimately tests a changed current catalog. It
        # must reject this OLD exact profile, not secretly substitute old data.
        if not self.unchanged_baseline():
            with self.assertRaises(SnapshotError) as caught: self.attach()
            self.assertIn(caught.exception.code, {"integrity_mismatch", "inventory_mismatch", "scope_mismatch"})
            return
        before = {row["path"]: (ROOT / row["path"]).read_bytes() for row in self.doc["files"]}
        query = CanonicalQueryEngine.from_attachment(self.attach())
        snapshot = query.snapshot()
        self.assertEqual(snapshot.snapshot_id, QUERY)
        self.assertEqual(Counter(item.entity_type for item in snapshot.entities), self.doc["entity_counts"])
        self.assertEqual(len(snapshot.entities), 1566)
        reference = CanonicalQueryEngine("magic", data_root=ROOT/"data", games_root=ROOT/"data/canonical/games")
        self.assertEqual(snapshot.as_dict(), reference.snapshot().as_dict())
        resolver = CanonicalCollectionResolver.from_attachment(self.attach())
        printing = next(item for item in snapshot.entities if item.entity_type == "printing")
        fictional_input = {"entries":[{"printing_id": printing.canonical_identity, "quantity":1}]}
        resolved = resolver.resolve(fictional_input)
        self.assertEqual(resolved["catalog_attachment"]["profile_id"], self.doc["profile_id"])
        legacy = CanonicalCollectionResolver("magic",ROOT/"data",games_root=ROOT/"data/canonical/games").resolve(fictional_input)
        resolved.pop("catalog_attachment")
        self.assertEqual(resolved,legacy)
        self.assertEqual({p:(ROOT/p).read_bytes() for p in before},before)

    def test_bare_and_unrestricted_legacy_remain_separate(self):
        bare = CanonicalQueryEngine().snapshot()
        self.assertEqual(len(bare.entities),32)
        self.assertEqual(bare.snapshot_id,BARE)
        legacy = attach_legacy_public(game="magic",data_root=ROOT/"data")
        self.assertEqual(CanonicalQueryEngine.from_attachment(legacy).snapshot().as_dict(),
            CanonicalQueryEngine("magic",data_root=ROOT/"data",games_root=ROOT/"data/canonical/games").snapshot().as_dict())

    def test_selected_audits_and_sources_only_in_place_no_excluded_file_opens(self):
        if not self.unchanged_baseline():
            with self.assertRaises(SnapshotError): self.attach()
            return
        allowed = {ROOT/row["path"] for row in self.doc["files"]}
        opened = set()
        original = os.open
        def guard(path,*args,**kwargs):
            if isinstance(path,(str,bytes,os.PathLike)):
                p=Path(path)
                if p.is_relative_to(ROOT/"data/audit") or (p.is_relative_to(ROOT/"data/canonical/games/magic") and "sources" in p.parts):
                    self.assertIn(p,allowed,"excluded dependency opened")
                    opened.add(p)
            return original(path,*args,**kwargs)
        with patch("os.open",side_effect=guard):
            q=CanonicalQueryEngine.from_attachment(self.attach())
            q.snapshot()
            q.provenance(q.entities(entity_type="printing")[0].canonical_identity)
        self.assertEqual(len([p for p in opened if p.is_relative_to(ROOT/"data/audit")]),2)
        self.assertEqual(len([p for p in opened if (p.is_relative_to(ROOT/"data/canonical/games/magic") and "sources" in p.parts)]),5)


if __name__ == "__main__": unittest.main()
