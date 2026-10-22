"""Current implementation pins and historical fixture integrity stay distinct."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import validation_performance_preservation as guard


class ValidationPerformancePreservationTests(unittest.TestCase):
    def test_current_authorized_implementations_and_operational_appendix_match_exact_pins(self):
        guard.assert_current_implementation()

    def test_original_historical_rows_are_required_before_each_successor_check(self):
        rows = json.loads((guard.ROOT / "tests/fixtures/shared-proposal-legality-protected-state.json").read_bytes())["protected_files"]
        historical = {row["path"]: row for row in rows}
        for item in guard.ledger()["replacements"]:
            original = {"path": item["path"], "bytes": item["original"]["bytes"],
                        "sha256": item["original"]["sha256"]}
            with self.subTest(path=item["path"]):
                if item["path"] in historical:
                    self.assertEqual(historical[item["path"]], original)
                guard.assert_retained_row(original)
                for field, value in (("bytes", original["bytes"] + 1),
                                     ("sha256", "0" * 64)):
                    changed = {**original, field: value}
                    with self.assertRaisesRegex(AssertionError, "exact authorized original"):
                        guard.assert_retained_row(changed)

    def test_each_authorized_replacement_rejects_same_length_tampering_after_success(self):
        for item in guard.ledger()["replacements"]:
            row = {"path": item["path"], "bytes": item["original"]["bytes"],
                   "sha256": item["original"]["sha256"]}
            raw = guard.regular_bytes(item["path"])
            with self.subTest(path=item["path"]), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                path = root / item["path"]
                path.parent.mkdir(parents=True)
                path.write_bytes(raw)
                guard.assert_retained_row(row, root)
                path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
                with self.assertRaisesRegex(AssertionError, "explicit pin"):
                    guard.assert_retained_row(row, root)
                path.unlink()
                with self.assertRaises(AssertionError):
                    guard.assert_retained_row(row, root)

    def test_unrelated_historical_files_continue_requiring_their_original_bytes(self):
        raw = b"invented historical fixture\n"
        row = {"path": "src/unrelated.fixture", "bytes": len(raw),
               "sha256": hashlib.sha256(raw).hexdigest()}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / row["path"]
            path.parent.mkdir()
            path.write_bytes(raw)
            guard.assert_retained_row(row, root)
            path.write_bytes(b"X" + raw[1:])
            with self.assertRaises(AssertionError):
                guard.assert_retained_row(row, root)

    def test_original_git_blob_reproduction_checks_git_identity_hash_and_length(self):
        raw = b"invented canonical original\n"
        pin = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
               "git_blob": hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()}
        guard.assert_original_git_blob(raw, pin)
        for field, changed in (("bytes", len(raw) + 1), ("sha256", "0" * 64),
                               ("git_blob", "0" * 40)):
            with self.subTest(field=field), self.assertRaises(AssertionError):
                guard.assert_original_git_blob(raw, {**pin, field: changed})

    def test_symlinks_directories_and_noncanonical_paths_cannot_replace_protected_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual = root / "actual"
            actual.mkdir()
            (actual / "file").write_bytes(b"fixture")
            (root / "linked").symlink_to(actual, target_is_directory=True)
            (actual / "linked-file").symlink_to(actual / "file")
            for relative in ("linked/file", "actual/linked-file", "actual",
                             "../outside", "/absolute", "actual/../actual/file",
                             "actual//file", "actual/./file"):
                with self.subTest(path=relative), self.assertRaises(AssertionError):
                    guard.regular_bytes(relative, root)

    def test_exact_added_helper_and_tool_leave_unknown_neighboring_paths_visible(self):
        for name in guard.NEW_SOURCE_PATHS | guard.NEW_TOOL_PATHS:
            self.assertTrue(guard.is_validation_performance_addition(guard.ROOT / name))
            self.assertFalse(guard.is_validation_performance_addition(guard.ROOT / (name + ".unexpected")))
        for name in ("src/gameplay_rules/future.py", "scripts/future.py",
                     "src/gameplay_rules/shared_target_declaration/future.py"):
            self.assertFalse(guard.is_validation_performance_addition(guard.ROOT / name))

    def test_each_added_helper_and_tool_rejects_tampering_after_current_validation(self):
        value = guard.ledger()
        names = ({row["path"] for row in value["replacements"]}
                 | {row["path"] for row in value["additions"]}
                 | set(value["document_appendices"]))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(guard.regular_bytes(name))
            guard.assert_current_implementation(root)
            for item in value["additions"]:
                path = root / item["path"]
                raw = path.read_bytes()
                with self.subTest(path=item["path"]):
                    path.write_bytes(b"X" + raw[1:])
                    with self.assertRaisesRegex(AssertionError, "explicit pin"):
                        guard.assert_current_implementation(root)
                    path.write_bytes(raw)
                    guard.assert_current_implementation(root)

    def test_ledger_tampering_cannot_redefine_an_authorized_replacement(self):
        value = deepcopy(guard.ledger())
        value["replacements"][0]["replacement"]["sha256"] = "0" * 64
        changed = json.dumps(value, sort_keys=True).encode()
        with patch.object(guard, "regular_bytes", return_value=changed):
            with self.assertRaisesRegex(AssertionError, "ledger changed"):
                guard.ledger()

    def test_operational_appendix_rejects_changed_prefix_unknown_suffix_and_truncation(self):
        name = "docs/NEXT_TASK.md"
        raw = guard.regular_bytes(name)
        baseline = guard.historical_document_before_validation_performance_append(name, raw)
        self.assertEqual(guard.historical_document_before_validation_performance_append(name, baseline), baseline)
        for changed in (raw + b"future appendix\n", raw[:-1], b"X" + raw[1:],
                        raw[:-1] + b"X", bytearray(raw)):
            with self.subTest(kind=type(changed).__name__), self.assertRaises(AssertionError):
                guard.historical_document_before_validation_performance_append(name, changed)
        with self.assertRaises(AssertionError):
            guard.historical_document_before_validation_performance_append("docs/unknown.md", b"")


if __name__ == "__main__":
    unittest.main()
