"""Independent preservation of the exact post-PR-201 canonical baseline.

These checks need neither the external TXT nor its source selector. The new
fixture derives directly from the pinned Git tree, independently of projection
records, and remains usable in shallow CI and disposable publication checkouts.
"""
import hashlib
import json
from pathlib import Path
import unittest

from activated_ability_projection_preservation import historical_inventory_before_projection_append
from shared_casting_stage_preservation import historical_document_before_shared_casting_append
from shared_target_declaration_preservation import (
    BASE, TREE, FIXTURE, FIXTURE_SHA256, ROOT, PROTECTED_INVENTORY_SHA256,
    DOCUMENT_APPENDICES, NEW_REVIEW_PATHS, NEW_SOURCE_PATHS, NEW_TOOL_PATHS,
    historical_document_before_target_declaration_append,
    is_target_declaration_addition,
)
from shared_target_allocation_preservation import (
    DOCUMENT_APPENDICES as TARGET_ALLOCATION_APPENDICES,
    historical_document_before_target_allocation_append,
    is_target_allocation_addition,
)
from shared_proposal_legality_preservation import is_proposal_legality_addition


def fixture():
    raw = FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise AssertionError("Independent 479-file baseline fixture changed")
    value = json.loads(raw)
    if (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode() != raw:
        raise AssertionError("Independent fixture must retain canonical JSON bytes")
    return value


def regular_paths(directory):
    return {p.relative_to(ROOT).as_posix() for p in directory.rglob("*")
            if (p.is_file() or p.is_symlink())
            and "__pycache__" not in p.parts and p.suffix != ".pyc"
            and not is_target_allocation_addition(p)
            and not is_proposal_legality_addition(p)}


class SharedTargetDeclarationPreservationTests(unittest.TestCase):
    def assert_retained_row(self, row):
        path = ROOT / row["path"]
        self.assertTrue(path.is_file())
        for ancestor in (path, *path.parents):
            if ancestor == ROOT:
                break
            self.assertFalse(ancestor.is_symlink())
        raw = path.read_bytes()
        self.assertEqual(len(raw), row["bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_independent_fixture_pins_exact_main_tree_and_479_file_authority(self):
        guard = fixture()
        self.assertEqual((guard["canonical_base"], guard["canonical_tree"]), (BASE, TREE))
        self.assertEqual(guard["authority"], "CANONICAL_GIT_STATE")
        self.assertEqual(guard["purpose"], "BYTE_PRESERVATION_GUARD_ONLY")
        for key in ("gameplay_authority", "comprehensive_rules_authority", "supersedes_prior_digests"):
            self.assertIs(guard[key], False)
        self.assertEqual((guard["source_count"], guard["evidence_count"],
                          guard["evidence_directory_count"]), (347, 132, 20))
        rows = guard["protected_files"]
        self.assertEqual((len(rows), len({r["path"] for r in rows})), (479, 479))
        raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PROTECTED_INVENTORY_SHA256)
        self.assertEqual(guard["protected_inventory_sha256"], PROTECTED_INVENTORY_SHA256)

    def test_every_inherited_source_and_evidence_file_remains_byte_identical(self):
        for row in fixture()["protected_files"]:
            with self.subTest(path=row["path"]):
                self.assert_retained_row(row)

    def test_inherited_review_tool_and_prior_preservation_fixtures_remain_identical(self):
        guard = fixture()
        self.assertEqual(guard["inherited_review_tool"], {
            "path": "scripts/shared_casting_stage_gap_design.py", "bytes": 27105,
            "sha256": "d2788448d15a06107c11e9734d4ed82c5a9dca75868cf38a062cb329b5b72f53",
        })
        self.assertEqual(len(guard["prior_guards"]), 4)
        for row in [guard["inherited_review_tool"], *guard["prior_guards"]]:
            with self.subTest(path=row["path"]):
                self.assert_retained_row(row)

    def test_exact_seven_source_and_nine_evidence_successors_are_the_only_additions(self):
        rows = fixture()["protected_files"]
        sources = {r["path"] for r in rows if r["path"].startswith("src/")}
        reviews = {r["path"] for r in rows if r["path"].startswith("reference-reviews/")}
        self.assertEqual((len(sources), len(reviews)), (347, 132))
        self.assertEqual(len({Path(p).parts[1] for p in reviews}), 20)
        self.assertEqual((len(NEW_SOURCE_PATHS), len(NEW_REVIEW_PATHS)), (7, 9))
        self.assertEqual(NEW_TOOL_PATHS, frozenset())
        self.assertEqual(regular_paths(ROOT / "src"), sources | NEW_SOURCE_PATHS)
        actual = set()
        for directory in (ROOT / "reference-reviews").glob("gameplay-rules-*"):
            actual.update(regular_paths(directory))
        self.assertEqual(actual, reviews | NEW_REVIEW_PATHS)
        for name in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS:
            self.assertTrue(is_target_declaration_addition(ROOT / name))
            self.assertFalse((ROOT / name).is_symlink())
        self.assertFalse(any(is_target_declaration_addition(ROOT / row["path"]) for row in rows))

    def test_unknown_future_paths_stay_visible_to_historical_inventory_guards(self):
        for name in (
            "src/gameplay_rules/shared_target_declaration/future.py",
            "src/gameplay_rules/shared_target_declaration/pins.json",
            "src/gameplay_rules/engine.py",
            "reference-reviews/gameplay-rules-bounded-shared-target-declaration/future.json",
            "reference-reviews/gameplay-rules-shared-casting-stage-gap-design/future.json",
            "scripts/shared_target_declaration.py",
            "scripts/automatic_canonical_update.py",
        ):
            self.assertFalse(is_target_declaration_addition(ROOT / name))

    def test_whole_inherited_documents_and_all_earlier_appendices_are_preserved(self):
        rows = fixture()["historical_documents"]
        self.assertEqual(len(rows), 11)
        for row in rows:
            with self.subTest(path=row["path"]):
                raw = (ROOT / row["path"]).read_bytes()
                if row["path"] in TARGET_ALLOCATION_APPENDICES:
                    raw = historical_document_before_target_allocation_append(row["path"], raw)
                if row["path"] in DOCUMENT_APPENDICES:
                    pin = DOCUMENT_APPENDICES[row["path"]]
                    self.assertGreater(pin["appendix_bytes"], 0)
                    self.assertEqual(len(raw), pin["baseline_bytes"] + pin["appendix_bytes"])
                    raw = historical_document_before_target_declaration_append(row["path"], raw)
                self.assertEqual(len(raw), row["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_inventory_retains_exact_69051_3400_1989_segments_before_old_adapters(self):
        raw = historical_document_before_target_declaration_append(
            "PROJECT_INVENTORY.md", (ROOT / "PROJECT_INVENTORY.md").read_bytes())
        self.assertEqual(len(raw), 74440)
        segments = fixture()["inventory_segments"]
        self.assertEqual([r["bytes"] for r in segments], [69051, 3400, 1989])
        offset = 0
        for row in segments:
            self.assertEqual(hashlib.sha256(raw[offset:offset + row["bytes"]]).hexdigest(), row["sha256"])
            offset += row["bytes"]
        before_201 = historical_document_before_shared_casting_append("PROJECT_INVENTORY.md", raw)
        self.assertEqual(len(before_201), 72451)
        before_200 = historical_inventory_before_projection_append(before_201)
        self.assertEqual(len(before_200), 69051)

    def test_exact_document_selector_rejects_arbitrary_suffixes_and_changed_bytes(self):
        for name, pin in DOCUMENT_APPENDICES.items():
            raw = (ROOT / name).read_bytes()
            baseline = historical_document_before_target_declaration_append(name, raw)
            self.assertEqual(historical_document_before_target_declaration_append(name, baseline), baseline)
            for candidate in (raw + b"future appendix\n", raw[:-1], b"X" + raw[1:],
                              raw[:-1] + b"X", bytearray(raw), baseline + b"unapproved\n"):
                with self.subTest(path=name, kind=type(candidate).__name__, length=len(candidate)):
                    with self.assertRaises(AssertionError):
                        historical_document_before_target_declaration_append(name, candidate)
        with self.assertRaises(AssertionError):
            historical_document_before_target_declaration_append("docs/unapproved.md", b"")

    def test_independent_old_88_ten_and_current_89_eleven_coverage(self):
        paths = [r["path"] for r in fixture()["protected_files"] if r["path"].endswith("/projection.json")]
        inherited = [json.loads((ROOT / p).read_bytes()) for p in paths]
        old_rules = [r for p in inherited for r in p["rules"]]
        old_refs = {r["rule_reference"] for r in old_rules}
        self.assertEqual((len(inherited), len(old_rules), len(old_refs)), (10, 88, 88))
        self.assertNotIn("601.2c", old_refs)
        live_paths = [p for p in sorted((ROOT / "reference-reviews").glob("gameplay-rules-*/projection.json"))
                      if not is_target_allocation_addition(p)
                      and not is_proposal_legality_addition(p)]
        projections = [json.loads(p.read_bytes()) for p in live_paths]
        rules = [r for p in projections for r in p["rules"]]
        refs = {r["rule_reference"] for r in rules}
        self.assertEqual((len(projections), len({p["projection_id"] for p in projections})), (11, 11))
        self.assertEqual((len(rules), len(refs)), (89, 89))
        self.assertEqual(refs - old_refs, {"601.2c"})
        self.assertTrue({"601.2a", "601.2d", "601.2e", "601.2i", "733", "701.20a", "603"}.isdisjoint(refs))
        self.assertEqual(len({json.dumps(r["source_anchor"], sort_keys=True) for r in rules}), 89)

    def test_historical_controlled_82_file_inventory_and_digest_are_unchanged(self):
        from test_real_rules_execution_design_boundaries import PROTECTED_GROUPS, controlled_inventory
        roots, count, expected = PROTECTED_GROUPS["writer_admission_evidence_and_transport"]
        self.assertEqual((count, expected),
                         (82, "210a951e39781044205cb25b6551809a2c4c3450086cc4c74be37c83da8320d5"))
        rows = controlled_inventory(roots)
        self.assertEqual(len(rows), 82)
        raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
