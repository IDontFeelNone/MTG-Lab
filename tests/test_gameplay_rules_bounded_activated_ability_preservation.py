"""Independent exact-main preservation guard for this bounded projection.

The fixture derives from Git at the owner's exact canonical main, rather than
the projection's pins or source metadata. It works in shallow CI and in the
disposable publication repository without requiring that historical Git object.
"""
import hashlib
import json
from pathlib import Path
import unittest

from activated_ability_projection_preservation import (
    NEW_REVIEW_PATHS, NEW_SOURCE_PATHS, is_projection_addition,
    historical_inventory_before_projection_append,
)


from shared_casting_stage_preservation import (
    is_shared_casting_design_addition, historical_document_before_shared_casting_append,
)
from shared_target_declaration_preservation import is_target_declaration_addition
from shared_target_allocation_preservation import is_target_allocation_addition
from shared_proposal_legality_preservation import is_proposal_legality_addition

ROOT = Path(__file__).resolve().parents[1]
BASE = "2aa01764db0cfbcd89bc3a30a4433c4f24ea5893"
FIXTURE = ROOT / "tests/fixtures/bounded-activated-ability-protected-state.json"
FIXTURE_SHA256 = "2505fae1bc886a5e32084a674974b9048b4e0329fa7a4557983bf19c67bfdf3a"
ALLOWLIST = {"602.2", "602.2a", "602.2b"}
PACKAGE = ROOT / "reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection"


def fixture():
    raw = FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise AssertionError("Independent exact-main preservation fixture changed")
    return json.loads(raw)


def files_under(directory):
    return {p.relative_to(ROOT).as_posix() for p in directory.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
            and not is_shared_casting_design_addition(p)
            and not is_target_declaration_addition(p)
            and not is_target_allocation_addition(p)
            and not is_proposal_legality_addition(p)}


class BoundedActivatedAbilityPreservationTests(unittest.TestCase):
    def test_fixture_authority_exact_main_and_all_454_baseline_files(self):
        guard = fixture()
        self.assertEqual(guard["canonical_base"], BASE)
        self.assertEqual(guard["authority"], "CANONICAL_GIT_STATE")
        self.assertEqual(guard["purpose"], "BYTE_PRESERVATION_GUARD_ONLY")
        self.assertIs(guard["gameplay_authority"], False)
        self.assertIs(guard["supersedes_prior_digests"], False)
        self.assertEqual((guard["source_count"], guard["evidence_count"],
                          guard["evidence_directory_count"]), (339, 115, 18))
        rows = guard["protected_files"]
        self.assertEqual(len(rows), 454)
        self.assertEqual(len({r["path"] for r in rows}), 454)
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

    def test_exact_finite_source_and_evidence_extensions(self):
        rows = fixture()["protected_files"]
        old_source = {r["path"] for r in rows if r["path"].startswith("src/")}
        old_reviews = {r["path"] for r in rows if r["path"].startswith("reference-reviews/")}
        self.assertEqual(len(old_source), 339)
        self.assertEqual(len(old_reviews), 115)
        self.assertEqual(len({Path(p).parts[1] for p in old_reviews}), 18)
        self.assertEqual(len(NEW_SOURCE_PATHS), 8)
        self.assertEqual(len(NEW_REVIEW_PATHS), 11)
        self.assertEqual(files_under(ROOT / "src"), old_source | NEW_SOURCE_PATHS)
        actual_reviews = set()
        for directory in (ROOT / "reference-reviews").glob("gameplay-rules-*"):
            actual_reviews.update(files_under(directory))
        self.assertEqual(actual_reviews, old_reviews | NEW_REVIEW_PATHS)
        for path in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS:
            self.assertTrue(is_projection_addition(ROOT / path))
            self.assertFalse((ROOT / path).is_symlink())
        for path in ("src/gameplay_rules/activated_ability_projection/future.py",
                     "reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/future.json",
                     "src/gameplay_rules/engine.py"):
            self.assertFalse(is_projection_addition(ROOT / path))

    def test_package_preservation_pins_match_independent_canonical_inventory(self):
        pins = json.loads((ROOT / "src/gameplay_rules/activated_ability_projection/pins.json").read_bytes())
        self.assertEqual(pins["canonical_base"], BASE)
        self.assertEqual(pins["inherited_source_count"], 339)
        self.assertEqual(pins["inherited_gameplay_evidence_count"], 115)
        self.assertEqual(pins["inherited_gameplay_evidence_directory_count"], 18)
        self.assertEqual(pins["protected_files"],
                         {r["path"]: r["sha256"] for r in fixture()["protected_files"]})

    def test_all_seven_canonical_document_bodies_retained_byte_for_byte(self):
        rows = fixture()["historical_documents"]
        self.assertEqual(len(rows), 7)
        append_only = {"PROJECT_INVENTORY.md", "docs/HANDOFF.md",
                       "docs/SESSION_STATE.md", "docs/NEXT_TASK.md"}
        for row in rows:
            with self.subTest(path=row["path"]):
                raw = (ROOT / row["path"]).read_bytes()
                original = raw[:row["bytes"]]
                self.assertEqual(len(original), row["bytes"])
                self.assertEqual(hashlib.sha256(original).hexdigest(), row["sha256"])
                if row["path"] not in append_only:
                    self.assertEqual(len(raw), row["bytes"])

    def test_historical_inventory_selector_accepts_only_the_exact_current_appendix(self):
        raw = historical_document_before_shared_casting_append(
            "PROJECT_INVENTORY.md", (ROOT / "PROJECT_INVENTORY.md").read_bytes())
        historical = historical_inventory_before_projection_append(raw)
        row = next(r for r in fixture()["historical_documents"]
                   if r["path"] == "PROJECT_INVENTORY.md")
        self.assertEqual(len(historical), row["bytes"])
        self.assertEqual(hashlib.sha256(historical).hexdigest(), row["sha256"])
        for candidate in (raw + b"future appendix\n", raw[:-1],
                          b"X" + raw[1:], raw[:-1] + b"X", historical,
                          bytearray(raw)):
            with self.subTest(kind=type(candidate).__name__, length=len(candidate)):
                with self.assertRaises(AssertionError):
                    historical_inventory_before_projection_append(candidate)

    def test_historical_85_units_nine_projections_and_exact_three_unit_extension(self):
        old_paths = [r["path"] for r in fixture()["protected_files"]
                     if r["path"].endswith("/projection.json")]
        self.assertEqual(len(old_paths), 9)
        projections = [json.loads((ROOT / p).read_bytes()) for p in old_paths]
        old_ids = {p["projection_id"] for p in projections}
        old_rules = [r for p in projections for r in p["rules"]]
        old_refs = {r["rule_reference"] for r in old_rules}
        self.assertEqual((len(old_ids), len(old_rules), len(old_refs)), (9, 85, 85))
        self.assertTrue(ALLOWLIST.isdisjoint(old_refs))
        new = json.loads((PACKAGE / "projection.json").read_bytes())
        new_rules = new["rules"]
        new_refs = {r["rule_reference"] for r in new_rules}
        self.assertEqual(len(new_rules), 3)
        self.assertEqual(new_refs, ALLOWLIST)
        self.assertEqual(len({r["rule_id"] for r in new_rules}), 3)
        self.assertEqual(len({r["source_anchor"]["anchor_id"] for r in new_rules}), 3)
        self.assertEqual(len(old_refs | new_refs), 88)
        self.assertEqual(len(old_ids | {new["projection_id"]}), 10)
        self.assertTrue({"601.2a", "601.2c", "601.2d", "601.2e", "601.2i",
                         "733", "701.20a", "405.6", "603", "603.7d", "603.7e", "603.7f",
                         "605", "602", "602.3"}.isdisjoint(old_refs | new_refs))

    def test_protected_design_stack_exception_and_acquisition_identities(self):
        for directory, identity in (
            ("gameplay-rules-activated-ability-procedure-design",
             "sha256:cfe499b63d673af2337beac94134d30b1dac2a14097e244e79742670ed2ec1b1"),
            ("gameplay-rules-bounded-mana-stack-exception-projection",
             "sha256:da05752959743ca36c65489c75c50e7f648eee2f2bf6db3d94cecfa827072ff1"),
        ):
            value = json.loads((ROOT / "reference-reviews" / directory / "manifest.json").read_bytes())
            self.assertEqual(value["package_id"], identity)
        stack = json.loads((ROOT / "reference-reviews/gameplay-rules-bounded-mana-stack-exception-projection/projection.json").read_bytes())
        self.assertEqual(stack["projection_id"],
                         "sha256:7ff68d920bd2b846e3fb1616743c48d99e2935b007ccb6943057c47ce74cf87a")
        from gameplay_rules.projection.bounded_mana_package import HISTORICAL_ACQUISITION_ID
        self.assertEqual(HISTORICAL_ACQUISITION_ID,
                         "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53")


if __name__ == "__main__":
    unittest.main()
