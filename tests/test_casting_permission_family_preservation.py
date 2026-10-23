"""Finite successor views preserve complete canonical history and old assertions."""
import hashlib
from pathlib import Path
import unittest

import casting_permission_family_preservation as guard
import casting_stage_family_completion_preservation as previous


class CastingPermissionFamilyPreservationTests(unittest.TestCase):
    def test_exact_named_successor_paths_preserve_closed_pr207_selector(self):
        self.assertEqual((len(guard.NEW_SOURCE_PATHS), len(guard.NEW_REVIEW_PATHS)), (7, 8))
        self.assertEqual((len(previous.NEW_SOURCE_PATHS), len(previous.NEW_REVIEW_PATHS)), (7, 12))
        alternate = Path("/tmp/casting-permission-finite-inventory")
        for name in guard.NEW_SOURCE_PATHS | guard.NEW_REVIEW_PATHS:
            with self.subTest(path=name):
                self.assertTrue(guard.is_casting_permission_family_addition(guard.ROOT / name))
                self.assertTrue(guard.is_casting_permission_family_addition(alternate / name, alternate))
                self.assertFalse(previous.is_casting_stage_family_completion_addition(guard.ROOT / name))
                self.assertFalse(guard.is_casting_permission_family_addition(guard.ROOT / (name + ".future")))
        for name in (*previous.NEW_SOURCE_PATHS, *previous.NEW_REVIEW_PATHS,
                     "src/gameplay_rules/casting_permission_family/future.py",
                     "src/gameplay_rules/casting_permission_family/pins.json",
                     "reference-reviews/gameplay-rules-casting-permission-family/future.json",
                     "reference-reviews/gameplay-rules-casting-permission-family/preservation-readiness.json",
                     "scripts/casting_permission_family.py", "src/query/engine.py"):
            self.assertFalse(guard.is_casting_permission_family_addition(guard.ROOT / name))

    def test_exact_document_appendices_preserve_all_eight_complete_canonical_prefixes(self):
        self.assertEqual(set(guard.DOCUMENT_APPENDICES), set(previous.DOCUMENT_APPENDICES))
        total = 0
        for name, pin in guard.DOCUMENT_APPENDICES.items():
            with self.subTest(path=name):
                raw = (guard.ROOT / name).read_bytes()
                self.assertEqual(len(raw), pin["baseline_bytes"] + pin["appendix_bytes"])
                inherited = guard.historical_document_before_casting_permission_append(name, raw)
                self.assertEqual(len(inherited), pin["baseline_bytes"])
                self.assertEqual(hashlib.sha256(inherited).hexdigest(), pin["baseline_sha256"])
                self.assertEqual(hashlib.sha256(raw[len(inherited):]).hexdigest(), pin["appendix_sha256"])
                self.assertEqual(guard.historical_document_before_casting_permission_append(name, inherited), inherited)
                old = previous.historical_document_before_casting_stage_family_completion_append(name, raw)
                self.assertEqual(old, inherited[:previous.DOCUMENT_APPENDICES[name]["baseline_bytes"]])
                total += pin["appendix_bytes"]
        self.assertEqual(total, 15511)

    def test_document_views_reject_changed_prefix_suffix_unknown_path_and_wrong_types(self):
        for name, pin in guard.DOCUMENT_APPENDICES.items():
            raw = (guard.ROOT / name).read_bytes()
            boundary = pin["baseline_bytes"]
            changed_suffix = raw[:boundary] + bytes([raw[boundary] ^ 1]) + raw[boundary + 1:]
            for changed in (raw + b"future appendix\n", raw[:-1], b"X" + raw[1:], changed_suffix,
                            bytearray(raw), memoryview(raw), True, len(raw)):
                with self.subTest(path=name, kind=type(changed).__name__), self.assertRaises(AssertionError):
                    guard.historical_document_before_casting_permission_append(name, changed)
        for name in ("docs/unapproved.md", Path("README.md"), True):
            with self.subTest(path=name), self.assertRaises(AssertionError):
                guard.historical_document_before_casting_permission_append(name, b"")

    def test_only_exact_finite_test_adapter_edits_reproduce_original_test_bytes(self):
        self.assertEqual(set(guard.ADAPTER_PATCHES), set(guard.ADAPTER_BASE_SHA256))
        self.assertEqual(len(guard.ADAPTER_PATCHES), 9)
        for name in guard.ADAPTER_PATCHES:
            raw = (guard.ROOT / name).read_bytes()
            with self.subTest(path=name):
                old = guard.historical_adapter_bytes(name, raw)
                self.assertEqual(hashlib.sha256(old).hexdigest(), guard.ADAPTER_BASE_SHA256[name])
                for changed in (b"X" + raw[1:], raw + b"future test changes\n", raw[:-1], old,
                                bytearray(raw), True):
                    with self.subTest(kind=type(changed).__name__), self.assertRaises(AssertionError):
                        guard.historical_adapter_bytes(name, changed)
        with self.assertRaises(AssertionError):
            guard.historical_adapter_bytes("tests/unapproved.py", b"")


if __name__ == "__main__":
    unittest.main()
