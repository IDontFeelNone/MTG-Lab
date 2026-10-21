"""Independent preservation of the complete PR #200 canonical baseline.

The fixture was derived from exact Git tree bytes, separately from the new
review package and its source fingerprints. No TXT is needed for these checks.
"""
import hashlib
import json
from pathlib import Path
import unittest

from activated_ability_projection_preservation import historical_inventory_before_projection_append
from shared_casting_stage_preservation import (
    DOCUMENT_APPENDICES, NEW_REVIEW_PATHS, NEW_TOOL_PATHS,
    historical_document_before_shared_casting_append,
    is_shared_casting_design_addition,
)
from shared_target_declaration_preservation import is_target_declaration_addition

ROOT = Path(__file__).resolve().parents[1]
BASE = "8c2a79ecce9ae7e6ff8e7959c57271e02bf1a4cb"
FIXTURE = ROOT / "tests/fixtures/shared-casting-stage-protected-state.json"
FIXTURE_SHA256 = "2b5510fa32594ef6e7eb4271aa0837f34ef32a576a588afe91deaad0f11d5140"


def fixture():
    raw = FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise AssertionError("Independent current-baseline preservation fixture changed")
    return json.loads(raw)


def regular_paths(directory):
    return {p.relative_to(ROOT).as_posix() for p in directory.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
            and not is_target_declaration_addition(p)}


class SharedCastingStagePreservationTests(unittest.TestCase):
    def test_independent_fixture_names_exact_473_file_canonical_authority(self):
        guard = fixture()
        self.assertEqual(guard["canonical_base"], BASE)
        self.assertEqual(guard["authority"], "CANONICAL_GIT_STATE")
        self.assertEqual(guard["purpose"], "BYTE_PRESERVATION_GUARD_ONLY")
        for key in ("gameplay_authority", "comprehensive_rules_authority", "supersedes_prior_digests"):
            self.assertIs(guard[key], False)
        self.assertEqual((guard["source_count"], guard["evidence_count"],
                          guard["evidence_directory_count"]), (347, 126, 19))
        rows = guard["protected_files"]
        self.assertEqual(len(rows), 473)
        self.assertEqual(len({row["path"] for row in rows}), 473)
        for row in rows:
            with self.subTest(path=row["path"]):
                path = ROOT / row["path"]
                self.assertTrue(path.is_file())
                for parent in (path, *path.parents):
                    if parent == ROOT:
                        break
                    self.assertFalse(parent.is_symlink())
                raw = path.read_bytes()
                self.assertEqual(len(raw), row["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_no_new_source_files_and_only_finitely_enumerated_review_additions(self):
        rows = fixture()["protected_files"]
        source = {r["path"] for r in rows if r["path"].startswith("src/")}
        reviews = {r["path"] for r in rows if r["path"].startswith("reference-reviews/")}
        self.assertEqual((len(source), len(reviews)), (347, 126))
        self.assertEqual(len({Path(p).parts[1] for p in reviews}), 19)
        self.assertEqual(regular_paths(ROOT / "src"), source)
        actual = set()
        for directory in (ROOT / "reference-reviews").glob("gameplay-rules-*"):
            actual.update(regular_paths(directory))
        self.assertEqual(actual, reviews | NEW_REVIEW_PATHS)
        for name in NEW_REVIEW_PATHS:
            self.assertTrue(is_shared_casting_design_addition(ROOT / name))
        self.assertEqual(NEW_TOOL_PATHS, {"scripts/shared_casting_stage_gap_design.py"})
        for name in NEW_TOOL_PATHS:
            self.assertTrue((ROOT / name).is_file())
            self.assertFalse((ROOT / name).is_symlink())
            self.assertTrue(is_shared_casting_design_addition(ROOT / name))
        self.assertEqual({name for name in regular_paths(ROOT / "scripts")
                          if is_shared_casting_design_addition(ROOT / name)}, NEW_TOOL_PATHS)
        # No canonical source/evidence member may disappear from older guards.
        self.assertFalse(any(is_shared_casting_design_addition(ROOT / row["path"])
                             for row in rows))
        for name in (
            "src/gameplay_rules/engine.py",
            "src/gameplay_rules/shared_casting_design/future.py",
            "scripts/shared_casting_stage_gap_design_future.py",
            "scripts/future.py",
            "scripts/automatic_canonical_update.py",
            "reference-reviews/gameplay-rules-shared-casting-stage-gap-design/future.json",
            "reference-reviews/gameplay-rules-shared-casting-stage-gap-design/projection.json",
        ):
            self.assertFalse(is_shared_casting_design_addition(ROOT / name))

    def test_prior_preservation_fixtures_remain_byte_identical(self):
        rows = fixture()["prior_guards"]
        self.assertEqual(len(rows), 3)
        for row in rows:
            with self.subTest(path=row["path"]):
                raw = (ROOT / row["path"]).read_bytes()
                self.assertEqual(len(raw), row["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_historical_documents_and_complete_prior_appendices_are_preserved(self):
        rows = fixture()["historical_documents"]
        self.assertEqual(len(rows), 10)
        for row in rows:
            with self.subTest(path=row["path"]):
                raw = (ROOT / row["path"]).read_bytes()
                if row["path"] in DOCUMENT_APPENDICES:
                    raw = historical_document_before_shared_casting_append(row["path"], raw)
                self.assertEqual(len(raw), row["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_each_document_successor_adapter_rejects_unknown_or_changed_suffixes(self):
        for name, pin in DOCUMENT_APPENDICES.items():
            raw = (ROOT / name).read_bytes()
            invalid = [raw + b"future appendix\n", raw[:-1], b"X" + raw[1:],
                       raw[:-1] + b"X", bytearray(raw)]
            if pin["appendix_bytes"]:
                invalid.append(raw[:pin["baseline_bytes"]])
            for candidate in invalid:
                with self.subTest(path=name, kind=type(candidate).__name__, length=len(candidate)):
                    with self.assertRaises(AssertionError):
                        historical_document_before_shared_casting_append(name, candidate)
        with self.assertRaises(AssertionError):
            historical_document_before_shared_casting_append("docs/unapproved.md", b"")

    def test_inventory_successor_adapter_preserves_original_69051_plus_3400_assertion(self):
        raw = (ROOT / "PROJECT_INVENTORY.md").read_bytes()
        canonical = historical_document_before_shared_casting_append("PROJECT_INVENTORY.md", raw)
        self.assertEqual(len(canonical), 69051 + 3400)
        historical = historical_inventory_before_projection_append(canonical)
        self.assertEqual(len(historical), 69051)
        self.assertEqual(hashlib.sha256(historical).hexdigest(),
                         "ebf315219fda9317f99431cea4564d6a364aabb2de0618f30795c1e665a570d5")
        self.assertEqual(hashlib.sha256(canonical[69051:]).hexdigest(),
                         "fd7d6c5e65d4bdabba1676972ac693329e8bbfa2d11f2b98f21e1eabd3bb1497")

    def test_all_88_units_ten_projections_rule_and_anchor_identities_remain(self):
        paths = [r["path"] for r in fixture()["protected_files"]
                 if r["path"].endswith("/projection.json")]
        self.assertEqual(len(paths), 10)
        projections = [json.loads((ROOT / p).read_bytes()) for p in paths]
        rules = [r for p in projections for r in p["rules"]]
        self.assertEqual(len({p["projection_id"] for p in projections}), 10)
        self.assertEqual((len(rules), len({r["rule_reference"] for r in rules})), (88, 88))
        # Earlier contracts have no per-rule ID or registered anchor ID. Preserve
        # those schemas too; do not invent identities for historical rows.
        own_rule_ids = [r["rule_id"] for r in rules if "rule_id" in r]
        self.assertEqual((len(own_rule_ids), len(set(own_rule_ids))), (56, 56))
        self.assertEqual(len({json.dumps(r["source_anchor"], sort_keys=True) for r in rules}), 88)
        registered = [r["source_anchor"]["anchor_id"] for r in rules
                      if "anchor_id" in r["source_anchor"]]
        self.assertEqual((len(registered), len(set(registered))), (3, 3))
        refs = {r["rule_reference"] for r in rules}
        self.assertTrue({"601.2c", "601.2d", "601.2e", "601.2i", "601.2a",
                         "601.3", "733", "701.20a", "603"}.isdisjoint(refs))

    def test_required_protected_identities_and_historical_validators_still_agree(self):
        from gameplay_rules.activated_ability_design import package as design
        from gameplay_rules.activated_ability_projection import package as projected
        from gameplay_rules.projection.bounded_mana_package import HISTORICAL_ACQUISITION_ID
        review_root = ROOT / "reference-reviews"
        old_design = json.loads((review_root / design.PACKAGE_NAME / "manifest.json").read_bytes())
        old_projection = json.loads((review_root / projected.PACKAGE_NAME / "manifest.json").read_bytes())
        self.assertEqual(old_design["package_id"],
                         "sha256:cfe499b63d673af2337beac94134d30b1dac2a14097e244e79742670ed2ec1b1")
        self.assertEqual(old_projection["package_id"],
                         "sha256:02667e58da72701b7464275184de452a1ec53f34b7dedc80ca3cde8c595a7ff4")
        self.assertEqual(old_projection["projection_id"],
                         "sha256:adaeae6e9da7956facbbe8db13c3f1a597328d184071bd6b6d61780c15957553")
        self.assertEqual(old_projection["canonical_base_preservation_pins_identity"],
                         "sha256:9cc186e74977b66142109faf244fccfe640005041c1b21c1e007a5e751275f2b")
        self.assertEqual(HISTORICAL_ACQUISITION_ID,
                         "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53")
        design.load_package(review_root / design.PACKAGE_NAME, review_root=review_root)
        projected.load_package(review_root / projected.PACKAGE_NAME, review_root=review_root)


if __name__ == "__main__":
    unittest.main()
