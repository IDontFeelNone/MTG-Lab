"""Warm attachment reuse preserves current reads and immutable control ownership."""
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from legacy_profile_fixture import CONTROL, build_legacy_fixture, save
from repository import legacy_profile
from repository.legacy_profile import LegacyCompatibilityAttachment, attach_legacy_compatibility
from repository.snapshots import SnapshotError, canonical_json


class LegacyProfilePerformanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.root = self.work / "catalog"
        self.document = build_legacy_fixture(self.root)
        self.prefix = "data/canonical/games/paper-world/"
        self.card = self.prefix + "cards/paper-unit/card.json"

    def attach(self, root=None):
        return attach_legacy_compatibility(root or self.root, control_path=CONTROL,
            game="paper-world", expected_profile_id=self.document["profile_id"])

    def assert_blocked(self, attachment, code):
        with self.assertRaises(SnapshotError) as caught:
            attachment.verify_unchanged()
        self.assertEqual(caught.exception.code, code)

    def replace_preserving_stat(self, path, original, replacement):
        before = path.stat()
        self.assertEqual(len(original), len(replacement))
        path.write_bytes(replacement)
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(path.stat().st_size, before.st_size)
        self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)

    def test_warm_verification_rereads_control_and_every_selected_file(self):
        attached = self.attach()
        attached.verify_unchanged()
        observed = []
        parsed = []
        original_read = legacy_profile._read
        original_parse = legacy_profile.strict_json

        def read(root, name):
            observed.append((root, name))
            return original_read(root, name)

        def parse(raw, name):
            parsed.append(name)
            return original_parse(raw, name)

        with patch.object(legacy_profile, "_read", side_effect=read), \
             patch.object(legacy_profile, "strict_json", side_effect=parse):
            attached.verify_unchanged()
        expected = Counter({CONTROL: 1, **{row["path"]: 1 for row in self.document["files"]}})
        self.assertEqual(Counter(name for _, name in observed), expected)
        self.assertTrue(all(root == self.root for root, _ in observed))
        self.assertTrue(set(parsed) <= {CONTROL})

    def test_warm_content_and_control_changes_with_preserved_size_mtime_block(self):
        for target in ("content", "control"):
            with self.subTest(target=target):
                root = self.work / target
                shutil.copytree(self.root, root)
                attached = self.attach(root)
                attached.verify_unchanged()
                if target == "content":
                    path = root / self.card
                    original = path.read_bytes()
                    replacement = original.replace(b"Paper Voyager", b"Paper VoyagEr")
                    code = "integrity_mismatch"
                else:
                    path = root / CONTROL
                    original = path.read_bytes()
                    replacement = original.replace(b'"game":"paper-world"', b'"game":"paper-worle"')
                    code = "identity_mismatch"
                self.assertNotEqual(original, replacement)
                self.replace_preserving_stat(path, original, replacement)
                self.assert_blocked(attached, code)

    def test_warm_control_accepts_strict_canonical_equivalence(self):
        attached = self.attach()
        for raw in (canonical_json(self.document),
                    json.dumps(self.document, ensure_ascii=True, indent=3).encode() + b"\n"):
            with self.subTest(length=len(raw)):
                (self.root / CONTROL).write_bytes(raw)
                attached.verify_unchanged()
                self.assertEqual(attached.binding, self.document)

    def test_warm_control_equivalence_still_rejects_duplicate_and_nonfinite_json(self):
        attached = self.attach()
        for raw in (b'{"profile":1,"profile":2}', b'{"x":NaN}', b'{"x":1e999}'):
            with self.subTest(raw=raw):
                (self.root / CONTROL).write_bytes(raw)
                self.assert_blocked(attached, "invalid_json")

    def test_identical_control_plans_keep_current_checks_at_each_root(self):
        second_root = self.work / "second"
        shutil.copytree(self.root, second_root)
        first, second = self.attach(), self.attach(second_root)
        first.verify_unchanged()
        second.verify_unchanged()
        self.assertEqual(first.binding, second.binding)
        self.assertEqual(second.paths(second_root / self.prefix / "cards", "*/card.json"),
                         (second_root / self.card,))
        path = second_root / self.card
        original = path.read_bytes()
        self.replace_preserving_stat(path, original, original.replace(b"Paper Voyager", b"Paper VoyagEr"))
        self.assert_blocked(second, "integrity_mismatch")
        first.verify_unchanged()

    def test_mutable_binding_and_constructor_aliases_cannot_change_private_plan(self):
        control_alias = bytearray(canonical_json(self.document))
        attached = LegacyCompatibilityAttachment(self.root, CONTROL, control_alias)
        attached.verify_unchanged()
        control_alias[:] = b"{}"
        binding = attached.binding
        binding["files"][0]["sha256"] = "0" * 64
        binding["files"].clear()
        binding["namespaces"][0]["paths"].clear()
        binding["absent"].clear()
        binding["game_namespaces"].clear()
        binding["entity_counts"].clear()
        binding["permissions"]["LOCAL_PRIVATE_PROCESSING"] = "ESTABLISHED"
        attached.verify_unchanged()
        self.assertEqual(attached.binding, self.document)
        self.assertEqual(attached.game, "paper-world")
        self.assertEqual(attached.read_json(self.root / self.card)["name"], "Paper Voyager")

    def test_warm_relative_plans_reinspect_namespace_absence_game_and_collisions(self):
        cases = (("source", self.prefix + "sources/new.json", "inventory_mismatch"),
                 ("absence", "data/canonical/knowledge/state.json", "scope_mismatch"),
                 ("collision", self.prefix + "cards/paper-unit/CARD.JSON", "duplicate_path"),
                 ("game", "data/canonical/games/new-game", "scope_mismatch"))
        for target, name, code in cases:
            with self.subTest(target=target):
                root = self.work / target
                shutil.copytree(self.root, root)
                attached = self.attach(root)
                attached.verify_unchanged()
                if target == "game":
                    (root / name).mkdir()
                else:
                    save(root / name, {})
                self.assert_blocked(attached, code)


if __name__ == "__main__":
    unittest.main()
