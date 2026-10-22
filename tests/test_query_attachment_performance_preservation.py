"""Historical evidence is immutable; authorized current implementations are checked."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import query_attachment_performance_preservation as guard


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


class QueryAttachmentPerformancePreservationTests(unittest.TestCase):
    def test_exact_current_successors_tool_historical_fixtures_and_prior_ledger(self):
        guard.assert_current_implementation()
        for item in guard.ledger()["replacements"]:
            with self.subTest(path=item["path"]):
                self.assertNotEqual(item["original"]["sha256"], item["replacement"]["sha256"])

    def test_all_retained_fixture_rows_keep_original_schemas_values_and_counts(self):
        expected_counts = {
            "mana-classification-protected-source.json": (None, 325),
            "mana-stack-exception-protected-state.json": ("canonical_source_files", 329),
            "bounded-activated-ability-protected-state.json": ("protected_files", 454),
            "shared-casting-stage-protected-state.json": ("protected_files", 473),
            "shared-target-declaration-protected-state.json": ("protected_files", 479),
            "shared-target-allocation-protected-state.json": ("protected_files", 495),
            "shared-proposal-legality-protected-state.json": ("protected_files", 511),
        }
        replacements = {item["path"]: item for item in guard.ledger()["replacements"]}
        for fixture in guard.ledger()["historical_fixtures"]:
            value = json.loads(guard.regular_bytes(fixture["path"]))
            key, count = expected_counts[Path(fixture["path"]).name]
            rows = value[key] if key else value
            with self.subTest(fixture=fixture["path"]):
                self.assertEqual((len(rows), len({row["path"] for row in rows})), (count, count))
                selected = {row["path"]: row for row in rows if row["path"] in replacements}
                self.assertEqual(set(selected), guard.REPLACEMENT_PATHS)
                for name, row in selected.items():
                    item = replacements[name]
                    expected = {"path": name, "sha256": item["original"]["sha256"]}
                    if key:
                        expected["bytes"] = item["original"]["bytes"]
                    self.assertEqual(row, expected)
                    (guard.assert_retained_row if key else guard.assert_hash_row)(row)

    def test_each_schema_requires_exact_original_before_selecting_current_bytes(self):
        for item in guard.ledger()["replacements"]:
            for with_length in (False, True):
                row = {"path": item["path"], "sha256": item["original"]["sha256"]}
                operation = guard.assert_hash_row
                if with_length:
                    row["bytes"] = item["original"]["bytes"]
                    operation = guard.assert_retained_row
                with self.subTest(path=item["path"], with_length=with_length):
                    operation(row)
                    changed_rows = [{**row, "sha256": "0" * 64},
                                    {**row, "sha256": item["replacement"]["sha256"]}]
                    if with_length:
                        changed_rows.append({**row, "bytes": row["bytes"] + 1})
                    for changed in changed_rows:
                        with self.assertRaisesRegex(AssertionError, "exact authorized original"):
                            operation(changed)
                    for malformed in ({**row, "unexpected": None}, list(row.items())):
                        with self.assertRaisesRegex(AssertionError, "schema required"):
                            operation(malformed)
                    if with_length:
                        for malformed_length in (True, float(row["bytes"]), str(row["bytes"])):
                            with self.assertRaisesRegex(AssertionError, "schema required"):
                                operation({**row, "bytes": malformed_length})

    def test_each_successor_rechecks_disk_after_warmup_and_rejects_retargeting(self):
        for item in guard.ledger()["replacements"]:
            row = {"path": item["path"], "bytes": item["original"]["bytes"],
                   "sha256": item["original"]["sha256"]}
            raw = guard.regular_bytes(item["path"])
            with self.subTest(path=item["path"]), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                target = root / item["path"]
                target.parent.mkdir(parents=True)
                target.write_bytes(raw)
                guard.assert_retained_row(row, root)
                target.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                with self.assertRaisesRegex(AssertionError, "exact authorized pin"):
                    guard.assert_retained_row(row, root)
                target.unlink()
                target.symlink_to(guard.ROOT / item["path"])
                with self.assertRaisesRegex(AssertionError, "symlink"):
                    guard.assert_retained_row(row, root)
                target.unlink()
                target.mkdir()
                with self.assertRaisesRegex(AssertionError, "regular file"):
                    guard.assert_retained_row(row, root)

    def test_current_mode_rejects_original_implementation_for_both_historical_schemas(self):
        # Authored finite old/new bytes exercise current-mode selection without
        # relying on unavailable historical Git objects in shallow hosted trees.
        original, replacement = b"historical implementation\n", b"authorized implementation\n"
        name = "src/query/engine.py"
        value = {"replacements": [{"path": name, "original": pin(original),
                                    "replacement": pin(replacement)}]}
        with tempfile.TemporaryDirectory() as temporary, patch.object(guard, "ledger", return_value=value):
            root = Path(temporary)
            target = root / name
            target.parent.mkdir(parents=True)
            for with_length in (False, True):
                row = {"path": name, "sha256": pin(original)["sha256"]}
                operation = guard.assert_hash_row
                if with_length:
                    row["bytes"] = len(original)
                    operation = guard.assert_retained_row
                target.write_bytes(replacement)
                operation(row, root)
                target.write_bytes(original)
                with self.subTest(with_length=with_length), self.assertRaisesRegex(AssertionError, "exact authorized pin"):
                    operation(row, root)

    def test_unrelated_rows_keep_original_checks_and_previous_successors_still_apply(self):
        raw = b"unrelated retained bytes\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "unrelated.fixture"
            target.write_bytes(raw)
            length_row = {"path": target.name, **pin(raw)}
            hash_row = {key: length_row[key] for key in ("path", "sha256")}
            guard.assert_hash_row(hash_row, root)
            guard.assert_retained_row(length_row, root)
            target.write_bytes(b"X" + raw[1:])
            for operation, row in ((guard.assert_hash_row, hash_row),
                                   (guard.assert_retained_row, length_row)):
                with self.assertRaises(AssertionError):
                    operation(row, root)
        for item in guard.previous.ledger()["replacements"]:
            guard.assert_retained_row({"path": item["path"],
                                       "bytes": item["original"]["bytes"],
                                       "sha256": item["original"]["sha256"]})

    def test_ledger_cannot_be_redefined_and_unknown_neighboring_additions_stay_visible(self):
        value = deepcopy(guard.ledger())
        value["replacements"][0]["replacement"]["sha256"] = "0" * 64
        with patch.object(guard, "regular_bytes", return_value=json.dumps(value).encode()):
            with self.assertRaisesRegex(AssertionError, "ledger changed"):
                guard.ledger()
        for name in guard.NEW_SOURCE_PATHS | guard.NEW_TOOL_PATHS:
            self.assertTrue(guard.is_query_attachment_performance_addition(guard.ROOT / name))
            self.assertFalse(guard.is_query_attachment_performance_addition(guard.ROOT / (name + ".unexpected")))
        for name in ("src/query/future.py", "src/repository/future.py", "scripts/future.py"):
            self.assertFalse(guard.is_query_attachment_performance_addition(guard.ROOT / name))

    def test_current_and_aggregate_guards_recheck_tool_source_and_retained_bytes(self):
        value = guard.ledger()
        selected = [*value["additions"], value["prior_implementation_ledger"],
                    *value["historical_fixtures"]]
        names = {item["path"] for item in [*value["replacements"], *selected]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in names:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(guard.regular_bytes(name))
            guard.assert_current_implementation(root)
            import test_real_rules_execution_design_boundaries as aggregate
            with (patch.object(aggregate, "ROOT", root),
                  patch.object(aggregate, "is_shared_casting_design_addition", return_value=False),
                  patch.object(aggregate, "is_validation_performance_addition", return_value=False)):
                legacy = next(item for item in value["replacements"]
                              if item["path"] == "src/repository/legacy_profile.py")
                original = {"path": legacy["path"], "bytes": legacy["original"]["bytes"],
                            "sha256": legacy["original"]["sha256"]}
                roots = ("src/repository", "scripts")
                self.assertEqual(aggregate.controlled_inventory(roots), [original])
                for name in (legacy["path"], next(iter(guard.NEW_TOOL_PATHS))):
                    target = root / name
                    raw = target.read_bytes()
                    target.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                    with self.subTest(aggregate_tampering=name), self.assertRaises(AssertionError):
                        aggregate.controlled_inventory(roots)
                    target.write_bytes(raw)
                unknown = root / "scripts/future.py"
                unknown.write_bytes(b"unapproved neighboring tool\n")
                self.assertEqual({row["path"] for row in aggregate.controlled_inventory(roots)},
                                 {legacy["path"], "scripts/future.py"})
                unknown.unlink()
            for row in selected:
                target = root / row["path"]
                raw = target.read_bytes()
                target.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                with self.subTest(path=row["path"]), self.assertRaisesRegex(AssertionError, "exact authorized pin"):
                    guard.assert_current_implementation(root)
                target.write_bytes(raw)


if __name__ == "__main__":
    unittest.main()
