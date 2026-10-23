"""Exact finite adapters retain historical assertions without widening their view."""
from pathlib import Path
import unittest

import casting_stage_family_completion_preservation as guard
from casting_permission_family_preservation import historical_document_before_casting_permission_append


class CastingStageFamilyCompletionPreservationTests(unittest.TestCase):
    def test_only_seven_modules_and_twelve_named_package_files_are_selected(self):
        self.assertEqual((len(guard.NEW_SOURCE_PATHS), len(guard.NEW_REVIEW_PATHS)), (7, 12))
        for name in guard.NEW_SOURCE_PATHS | guard.NEW_REVIEW_PATHS:
            with self.subTest(path=name):
                self.assertTrue(guard.is_casting_stage_family_completion_addition(guard.ROOT / name))
                self.assertFalse(guard.is_casting_stage_family_completion_addition(guard.ROOT / (name + ".future")))
        for name in (
            "src/gameplay_rules/casting_stage_family_completion/future.py",
            "src/gameplay_rules/casting_stage_family_completion/pins.json",
            "src/gameplay_rules/shared_proposal_legality/package.py",
            "reference-reviews/gameplay-rules-casting-stage-family-completion/future.json",
            "reference-reviews/gameplay-rules-bounded-shared-proposal-legality/projection.json",
            "scripts/casting_stage_family_completion.py",
        ):
            self.assertFalse(guard.is_casting_stage_family_completion_addition(guard.ROOT / name))
        temporary_root = Path("/tmp/finite-casting-stage-view")
        for name in guard.NEW_SOURCE_PATHS | guard.NEW_REVIEW_PATHS:
            self.assertTrue(guard.is_casting_stage_family_completion_addition(temporary_root / name, temporary_root))

    def test_exact_eight_whole_documents_and_appendices_preserve_all_inherited_bytes(self):
        self.assertEqual(set(guard.DOCUMENT_APPENDICES), {
            "README.md", "PROJECT_INVENTORY.md", "CHANGELOG.md",
            "docs/SESSION_STATE.md", "docs/NEXT_TASK.md", "docs/HANDOFF.md",
            "docs/ROADMAP.md", "docs/PROJECT_STATUS.md",
        })
        for name, pin in guard.DOCUMENT_APPENDICES.items():
            with self.subTest(path=name):
                raw = (guard.ROOT / name).read_bytes()
                raw = historical_document_before_casting_permission_append(name, raw)
                self.assertEqual(len(raw), pin["baseline_bytes"] + pin["appendix_bytes"])
                inherited = guard.historical_document_before_casting_stage_family_completion_append(name, raw)
                self.assertEqual(inherited, raw[:pin["baseline_bytes"]])
                self.assertEqual(guard.historical_document_before_casting_stage_family_completion_append(name, inherited), inherited)

    def test_document_adapter_rejects_changed_prefix_suffix_and_json_type_substitutions(self):
        for name, pin in guard.DOCUMENT_APPENDICES.items():
            raw = (guard.ROOT / name).read_bytes()
            boundary = pin["baseline_bytes"]
            changed_boundary = raw[:boundary] + bytes([raw[boundary] ^ 1]) + raw[boundary + 1:]
            for changed in (raw + b"future appendix\n", raw[:-1], b"X" + raw[1:],
                            changed_boundary, bytearray(raw), memoryview(raw), len(raw), True):
                with self.subTest(path=name, kind=type(changed).__name__), self.assertRaises(AssertionError):
                    guard.historical_document_before_casting_stage_family_completion_append(name, changed)
        for name in ("docs/unapproved.md", Path("README.md"), True):
            with self.subTest(path=name), self.assertRaises(AssertionError):
                guard.historical_document_before_casting_stage_family_completion_append(name, b"")


if __name__ == "__main__":
    unittest.main()
