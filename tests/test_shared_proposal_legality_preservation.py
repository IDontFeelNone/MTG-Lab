"""Independent canonical preservation and exact current proposal-legality coverage.

This fixture derives from Git tree bytes, separately from the new package. It
requires no external TXT and supplies byte-preservation evidence only.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from query_attachment_performance_preservation import assert_retained_row
from casting_permission_family_preservation import is_casting_permission_family_addition
from casting_stage_family_completion_preservation import (
    DOCUMENT_APPENDICES as CASTING_STAGE_BATCH_APPENDICES,
    historical_document_before_casting_stage_family_completion_append,
    is_casting_stage_family_completion_addition,
)

from validation_performance_preservation import (
    NEW_SOURCE_PATHS as PERFORMANCE_SOURCE_PATHS,
    historical_document_before_validation_performance_append,
)

from activated_ability_projection_preservation import historical_inventory_before_projection_append
from shared_casting_stage_preservation import historical_document_before_shared_casting_append
from shared_target_declaration_preservation import historical_document_before_target_declaration_append
from shared_target_allocation_preservation import historical_document_before_target_allocation_append
from shared_proposal_legality_preservation import (
    BASE, TREE, ROOT, FIXTURE, FIXTURE_SHA256, PROTECTED_INVENTORY_SHA256,
    DOCUMENT_APPENDICES, NEW_SOURCE_PATHS, NEW_REVIEW_PATHS, NEW_TOOL_PATHS,
    historical_document_before_proposal_legality_append, is_proposal_legality_addition,
)


def fixture():
    raw = FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise AssertionError("Independent 511-file baseline fixture changed")
    value = json.loads(raw)
    if (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode() != raw:
        raise AssertionError("Independent fixture must retain canonical JSON bytes")
    return value


def regular_paths(directory, root=ROOT):
    return {p.relative_to(root).as_posix() for p in directory.rglob("*")
            if (p.is_file() or p.is_symlink())
            and "__pycache__" not in p.parts and p.suffix != ".pyc"
            and not is_casting_permission_family_addition(p, root)
            and not is_casting_stage_family_completion_addition(p, root)}


class SharedProposalLegalityPreservationTests(unittest.TestCase):
    def assert_retained_row(self, row, root=ROOT):
        assert_retained_row(row, root)

    def assert_exact_current_inventory(self, root=ROOT):
        rows = fixture()["protected_files"]
        sources = {r["path"] for r in rows if r["path"].startswith("src/")}
        reviews = {r["path"] for r in rows if r["path"].startswith("reference-reviews/")}
        self.assertEqual(regular_paths(root / "src", root), sources | NEW_SOURCE_PATHS | PERFORMANCE_SOURCE_PATHS)
        actual = set()
        for directory in (root / "reference-reviews").glob("gameplay-rules-*"):
            actual.update(regular_paths(directory, root))
        self.assertEqual(actual, reviews | NEW_REVIEW_PATHS)

    def test_canonical_git_fixture_reproduces_511_rows_and_independent_digest(self):
        guard = fixture()
        self.assertEqual((guard["canonical_base"], guard["canonical_tree"]), (BASE, TREE))
        self.assertEqual(guard["authority"], "CANONICAL_GIT_STATE")
        self.assertEqual(guard["purpose"], "BYTE_PRESERVATION_GUARD_ONLY")
        for key in ("gameplay_authority", "comprehensive_rules_authority", "supersedes_prior_digests"):
            self.assertIs(guard[key], False)
        self.assertEqual((guard["source_count"], guard["evidence_count"],
                          guard["evidence_directory_count"]), (361, 150, 22))
        rows = guard["protected_files"]
        self.assertEqual((len(rows), len({r["path"] for r in rows})), (511, 511))
        self.assertEqual(rows, sorted(rows, key=lambda r: r["path"]))
        raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PROTECTED_INVENTORY_SHA256)
        self.assertEqual(guard["protected_inventory_sha256"], PROTECTED_INVENTORY_SHA256)

    def test_historical_rows_and_authorized_current_implementation_match_exact_pins(self):
        for row in fixture()["protected_files"]:
            with self.subTest(path=row["path"]):
                self.assert_retained_row(row)

    def test_changed_historical_bytes_fail_the_current_guard(self):
        row = fixture()["protected_files"][0]
        raw = (ROOT / row["path"]).read_bytes()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / row["path"]
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
            self.assert_retained_row(row, root)
            path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
            with self.assertRaises(AssertionError):
                self.assert_retained_row(row, root)

    def test_all_six_prior_fixtures_and_inherited_review_tool_are_unchanged(self):
        guard = fixture()
        self.assertEqual(guard["inherited_review_tool"], {
            "path": "scripts/shared_casting_stage_gap_design.py", "bytes": 27105,
            "sha256": "d2788448d15a06107c11e9734d4ed82c5a9dca75868cf38a062cb329b5b72f53",
        })
        self.assertEqual(len(guard["prior_guards"]), 6)
        self.assertEqual({Path(r["path"]).name for r in guard["prior_guards"]}, {
            "mana-classification-protected-source.json", "mana-stack-exception-protected-state.json",
            "bounded-activated-ability-protected-state.json", "shared-casting-stage-protected-state.json",
            "shared-target-declaration-protected-state.json", "shared-target-allocation-protected-state.json",
        })
        for row in [guard["inherited_review_tool"], *guard["prior_guards"]]:
            with self.subTest(path=row["path"]):
                self.assert_retained_row(row)

    def test_exact_seven_source_and_ten_evidence_files_account_for_all_additions(self):
        self.assertEqual((len(NEW_SOURCE_PATHS), len(NEW_REVIEW_PATHS)), (7, 10))
        self.assertEqual(NEW_TOOL_PATHS, frozenset())
        self.assert_exact_current_inventory()
        for name in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS:
            self.assertTrue(is_proposal_legality_addition(ROOT / name))
            self.assertFalse((ROOT / name).is_symlink())
        self.assertFalse(any(is_proposal_legality_addition(ROOT / r["path"])
                             for r in fixture()["protected_files"]))

    def test_synthetic_unknown_source_and_evidence_paths_fail_structural_inventory(self):
        # Empty authored files exercise structure only; they establish no real
        # byte-preservation or source authority and never modify the checkout.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            names = {r["path"] for r in fixture()["protected_files"]} | NEW_SOURCE_PATHS | NEW_REVIEW_PATHS | PERFORMANCE_SOURCE_PATHS
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            self.assert_exact_current_inventory(root)
            for name in ("src/gameplay_rules/shared_proposal_legality/unapproved.py",
                         "reference-reviews/gameplay-rules-bounded-shared-proposal-legality/unapproved.json"):
                with self.subTest(path=name):
                    path = root / name
                    path.touch()
                    with self.assertRaises(AssertionError):
                        self.assert_exact_current_inventory(root)
                    path.unlink()
                    self.assert_exact_current_inventory(root)

    def test_unknown_future_paths_are_never_hidden_from_historical_views(self):
        for name in (
            "src/gameplay_rules/shared_proposal_legality/future.py",
            "src/gameplay_rules/shared_proposal_legality/pins.json",
            "src/gameplay_rules/shared_target_declaration/future.py",
            "src/gameplay_rules/shared_target_allocation/future.py",
            "src/gameplay_rules/engine.py",
            "reference-reviews/gameplay-rules-bounded-shared-proposal-legality/future.json",
            "reference-reviews/gameplay-rules-bounded-shared-target-declaration/future.json",
            "reference-reviews/gameplay-rules-bounded-shared-target-allocation/future.json",
            "scripts/shared_proposal_legality.py", "scripts/automatic_canonical_update.py",
        ):
            self.assertFalse(is_proposal_legality_addition(ROOT / name))

    def test_all_thirteen_complete_inherited_documents_and_checkpoints_are_preserved(self):
        rows = fixture()["historical_documents"]
        self.assertEqual(len(rows), 13)
        self.assertIn("docs/GAMEPLAY_RULES_BOUNDED_SHARED_TARGET_ALLOCATION_PROJECTION.md",
                      {r["path"] for r in rows})
        for row in rows:
            with self.subTest(path=row["path"]):
                raw = (ROOT / row["path"]).read_bytes()
                if row["path"] in CASTING_STAGE_BATCH_APPENDICES:
                    raw = historical_document_before_casting_stage_family_completion_append(row["path"], raw)
                if row["path"] == "docs/NEXT_TASK.md":
                    raw = historical_document_before_validation_performance_append(row["path"], raw)
                if row["path"] in DOCUMENT_APPENDICES:
                    pin = DOCUMENT_APPENDICES[row["path"]]
                    self.assertGreater(pin["appendix_bytes"], 0)
                    self.assertEqual(len(raw), pin["baseline_bytes"] + pin["appendix_bytes"])
                    raw = historical_document_before_proposal_legality_append(row["path"], raw)
                self.assertEqual(len(raw), row["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_inventory_preserves_complete_83080_bytes_and_all_five_segments(self):
        raw = historical_document_before_proposal_legality_append(
            "PROJECT_INVENTORY.md", (ROOT / "PROJECT_INVENTORY.md").read_bytes())
        self.assertEqual(len(raw), 83080)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "434a05abdba31305dc8ff917ec530aeb8b08c9fdcfa9054fbaaaf47476ac334d")
        segments = fixture()["inventory_segments"]
        self.assertEqual([r["bytes"] for r in segments], [69051, 3400, 1989, 3400, 5240])
        offset = 0
        for row in segments:
            self.assertEqual(hashlib.sha256(raw[offset:offset + row["bytes"]]).hexdigest(), row["sha256"])
            offset += row["bytes"]
        self.assertEqual(offset, len(raw))
        before_203 = historical_document_before_target_allocation_append("PROJECT_INVENTORY.md", raw)
        self.assertEqual(len(before_203), 77840)
        before_202 = historical_document_before_target_declaration_append("PROJECT_INVENTORY.md", before_203)
        self.assertEqual(len(before_202), 74440)
        before_201 = historical_document_before_shared_casting_append("PROJECT_INVENTORY.md", before_202)
        self.assertEqual(len(before_201), 72451)
        self.assertEqual(len(historical_inventory_before_projection_append(before_201)), 69051)

    def test_exact_document_adapter_rejects_arbitrary_suffixes_and_changed_bytes(self):
        for name in DOCUMENT_APPENDICES:
            raw = (ROOT / name).read_bytes()
            baseline = historical_document_before_proposal_legality_append(name, raw)
            self.assertEqual(historical_document_before_proposal_legality_append(name, baseline), baseline)
            midpoint = len(baseline) // 2
            changed_middle = raw[:midpoint] + bytes([raw[midpoint] ^ 1]) + raw[midpoint + 1:]
            for candidate in (raw + b"future appendix\n", raw[:-1], b"X" + raw[1:],
                              raw[:-1] + b"X", changed_middle, bytearray(raw), baseline + b"unapproved\n"):
                with self.subTest(path=name, kind=type(candidate).__name__, length=len(candidate)):
                    with self.assertRaises(AssertionError):
                        historical_document_before_proposal_legality_append(name, candidate)
        with self.assertRaises(AssertionError):
            historical_document_before_proposal_legality_append("docs/unapproved.md", b"")

    def test_independent_90_twelve_to_91_thirteen_coverage_adds_only_e(self):
        old_paths = [r["path"] for r in fixture()["protected_files"] if r["path"].endswith("/projection.json")]
        inherited = [json.loads((ROOT / p).read_bytes()) for p in old_paths]
        old_rules = [r for p in inherited for r in p["rules"]]
        old_refs = {r["rule_reference"] for r in old_rules}
        self.assertEqual((len(inherited), len(old_rules), len(old_refs)), (12, 90, 90))
        self.assertTrue({"601.2b", "601.2c", "601.2d", "601.2f", "601.2g", "601.2h"}.issubset(old_refs))
        self.assertNotIn("601.2e", old_refs)
        paths = [p for p in sorted((ROOT / "reference-reviews").glob("gameplay-rules-*/projection.json"))
                 if not is_casting_permission_family_addition(p)
                 and not is_casting_stage_family_completion_addition(p)]
        projections = [json.loads(p.read_bytes()) for p in paths]
        rules = [r for p in projections for r in p["rules"]]
        refs = {r["rule_reference"] for r in rules}
        self.assertEqual((len(projections), len({p["projection_id"] for p in projections})), (13, 13))
        self.assertEqual((len(rules), len(refs)), (91, 91))
        self.assertEqual(refs - old_refs, {"601.2e"})
        self.assertTrue({"601.2a", "601.2i", "733", "701.20a", "603"}.isdisjoint(refs))
        self.assertEqual(len({json.dumps(r["source_anchor"], sort_keys=True) for r in rules}), 91)

    def test_explicit_historical_identity_pins_are_unchanged(self):
        old = ROOT / "reference-reviews/gameplay-rules-bounded-shared-target-declaration"
        manifest = json.loads((old / "manifest.json").read_bytes())
        projection = json.loads((old / "projection.json").read_bytes())
        self.assertEqual(manifest["package_id"],
                         "sha256:55b70ae4c7c8fa5f4abadba27a0205f1c433aaff3f6de74f1d42829cf1b999ce")
        self.assertEqual(projection["projection_id"],
                         "sha256:5195b58cb6525dd6fc3a86b5e6511392597e6ea089514df3ab62cdcb21dee016")
        self.assertEqual(projection["rules"][0]["rule_id"],
                         "sha256:d6076ca821f51ee3d694efc7fe38a5c822436d17682889a302e4236c6674506b")
        self.assertEqual(projection["rules"][0]["source_anchor"]["anchor_id"],
                         "sha256:2d8cc88aed759ca45fa2eedec589c2148e6a351e15b1340ffb21927494740b1d")
        d = ROOT / "reference-reviews/gameplay-rules-bounded-shared-target-allocation"
        d_manifest = json.loads((d / "manifest.json").read_bytes())
        d_projection = json.loads((d / "projection.json").read_bytes())
        self.assertEqual(d_manifest["package_id"],
                         "sha256:56ad746cd5c87c0fac1b864289283135b4d4adb10ee441fbaa970a1dcefb1678")
        self.assertEqual(d_projection["projection_id"],
                         "sha256:bd5739a5d9afe5e06d6eb662cbe0b5c4c5b87711f502d039e980c51c6c7f4f66")
        self.assertEqual(d_projection["rules"][0]["rule_id"],
                         "sha256:54b3b3d770276044bb519285cb6f202ce236656bd82a20d4a1fc16ec57e8d1d5")
        self.assertEqual(d_projection["rules"][0]["source_anchor"]["anchor_id"],
                         "sha256:c39fda4f934f1a6d13a863a984a128dee24513bc26d2d2f28b3ea2b3e6aa30c7")
        design = json.loads((ROOT / "reference-reviews/gameplay-rules-shared-casting-stage-gap-design/manifest.json").read_bytes())
        self.assertEqual(design["package_id"],
                         "sha256:4ec995686f7ebb851fae1d6a3b732b1669a9f8cbe7d7ad547f939d928b6c729f")
        from gameplay_rules.projection.bounded_mana_package import HISTORICAL_ACQUISITION_ID
        self.assertEqual(HISTORICAL_ACQUISITION_ID,
                         "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53")

    def test_historical_controlled_82_file_inventory_and_digest_are_unchanged(self):
        from test_real_rules_execution_design_boundaries import PROTECTED_GROUPS, controlled_inventory
        roots, count, expected = PROTECTED_GROUPS["writer_admission_evidence_and_transport"]
        self.assertEqual((count, expected),
                         (82, "210a951e39781044205cb25b6551809a2c4c3450086cc4c74be37c83da8320d5"))
        rows = controlled_inventory(roots)
        self.assertEqual(len(rows), 82)
        raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)

    def test_current_readiness_and_all_ten_responsibilities_remain_blocked(self):
        directory = ROOT / "reference-reviews/gameplay-rules-bounded-shared-proposal-legality"
        semantic = json.loads((directory / "consumer-semantic-boundaries.json").read_bytes())["findings"]
        readiness = json.loads((directory / "preservation-readiness.json").read_bytes())["findings"]
        self.assertEqual(len(semantic["activated_responsibilities"]), 10)
        self.assertTrue(all(row["state"] == "OPEN / EXECUTION_BLOCKED"
                            and row["implementation_available"] is False
                            for row in semantic["activated_responsibilities"]))
        self.assertEqual(readiness["execution_readiness"], "BLOCKED")
        for field in ("runtime_implemented", "real_snapshot_created", "real_execution_profile_activated", "admission_eligible"):
            self.assertIs(readiness[field], False)
        self.assertEqual(readiness["source_policy_clearance"], "not_granted")
        self.assertEqual(set(readiness["permissions"].values()), {"NOT_ESTABLISHED"})


if __name__ == "__main__":
    unittest.main()
