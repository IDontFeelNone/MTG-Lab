"""Historical non-data dependencies are explicit, frozen and independently bound."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import historical_catalog as history
from card_intelligence.mechanics import content_identity
from scripts import build_card_acquisition_pilot as pilot
from scripts import build_collection_audit_pilot as collection_pilot


FIXTURE = "card-acquisition-pilot"
ARCHITECTURE = "docs/ARCHITECTURE.md"
ARCHITECTURE_SHA256 = "53b2818c428901b9dcb46f0eee54017527bc6088fd08fe7aa47aab010afa00f5"
PROTECTED_IDENTITY = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"


class HistoricalReplayAuxiliaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        history.bind_replay_builder(cls, pilot, auxiliary_fixture=FIXTURE)
        cls.root = pilot.ROOT
        cls.artifacts = pilot.build_artifacts()

    def isolated_auxiliary(self, directory):
        root = Path(directory) / "historical-replay"
        shutil.copytree(history.AUXILIARY_ROOT / FIXTURE, root / FIXTURE)
        return root

    def test_exact_pilot_replay_after_current_architecture_proposal(self):
        original = (self.root / ARCHITECTURE).read_bytes()
        self.assertEqual(len(original), 3430)
        self.assertEqual(hashlib.sha256(original).hexdigest(), ARCHITECTURE_SHA256)
        self.assertEqual((history.REPOSITORY / ARCHITECTURE).read_bytes(),
                         (history.historical_repository() / ARCHITECTURE).read_bytes())
        self.assertEqual(content_identity(pilot.protected_inventory()), PROTECTED_IDENTITY)
        retained = {path.name: path.read_bytes() for path in pilot.REVIEW.iterdir()
                    if path.is_file() and path.name not in {"plan.json", "synthetic-inputs.json"}}
        self.assertEqual(self.artifacts, retained)
        self.assertEqual(len(retained), 9)

    def test_tampered_auxiliary_is_rejected_even_with_cached_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = self.isolated_auxiliary(directory)
            path = fixture_root / FIXTURE / ARCHITECTURE
            path.write_bytes(path.read_bytes() + b"\nchanged historical bytes\n")
            with patch.object(history, "AUXILIARY_ROOT", fixture_root):
                with self.assertRaisesRegex(ValueError, "historical fixture integrity mismatch"):
                    history.historical_repository(auxiliary_fixture=FIXTURE)

    def test_missing_auxiliary_never_falls_back_to_current_docs(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = self.isolated_auxiliary(directory)
            (fixture_root / FIXTURE / ARCHITECTURE).unlink()
            with patch.object(history, "AUXILIARY_ROOT", fixture_root):
                with self.assertRaises(FileNotFoundError):
                    history.historical_repository(auxiliary_fixture=FIXTURE)

    def test_current_architecture_cannot_replace_original_auxiliary(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = self.isolated_auxiliary(directory)
            current = (history.REPOSITORY / ARCHITECTURE).read_bytes()
            self.assertNotEqual(hashlib.sha256(current).hexdigest(), ARCHITECTURE_SHA256)
            (fixture_root / FIXTURE / ARCHITECTURE).write_bytes(current)
            with patch.object(history, "AUXILIARY_ROOT", fixture_root):
                with self.assertRaisesRegex(ValueError, "historical fixture integrity mismatch"):
                    history.historical_repository(auxiliary_fixture=FIXTURE)

    def test_auxiliary_manifest_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = self.isolated_auxiliary(directory)
            manifest = fixture_root / FIXTURE / "manifest.json"
            manifest.write_bytes(manifest.read_bytes() + b"\n")
            with patch.object(history, "AUXILIARY_ROOT", fixture_root):
                with self.assertRaisesRegex(ValueError, "auxiliary manifest integrity mismatch"):
                    history.historical_repository(auxiliary_fixture=FIXTURE)

    def test_paths_and_symlink_substitution_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = self.isolated_auxiliary(directory)
            for name in ("../docs/ARCHITECTURE.md", "/docs/ARCHITECTURE.md",
                         "docs\\ARCHITECTURE.md", "docs/../ARCHITECTURE.md",
                         "data/canonical/state.json", "docs//ARCHITECTURE.md"):
                with self.assertRaisesRegex(ValueError, "auxiliary path escape"):
                    history._auxiliary_path(fixture_root, name)
            path = fixture_root / FIXTURE / ARCHITECTURE
            original = Path(directory) / "original.md"
            original.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(original)
            with patch.object(history, "AUXILIARY_ROOT", fixture_root):
                with self.assertRaisesRegex(ValueError, "auxiliary symlink"):
                    history.historical_repository(auxiliary_fixture=FIXTURE)

    def test_unknown_auxiliary_does_not_install_another_root(self):
        with self.assertRaisesRegex(ValueError, "unknown historical auxiliary fixture"):
            history.historical_repository(auxiliary_fixture="../current-docs")

    def test_other_replay_builder_keeps_its_existing_root_and_docs(self):
        cleanup = []
        class BindingOwner:
            addClassCleanup = staticmethod(cleanup.append)
        original_root = collection_pilot.ROOT
        try:
            history.bind_replay_builder(BindingOwner, collection_pilot)
            self.assertEqual(collection_pilot.ROOT, history.historical_repository())
            self.assertNotEqual(collection_pilot.ROOT, self.root)
            self.assertEqual((collection_pilot.ROOT / ARCHITECTURE).read_bytes(),
                             (history.REPOSITORY / ARCHITECTURE).read_bytes())
        finally:
            for restore in reversed(cleanup):
                restore()
        self.assertEqual(collection_pilot.ROOT, original_root)

    def test_fixture_selection_has_no_live_git_dependency(self):
        with patch.object(subprocess, "run", side_effect=AssertionError("no live Git")), \
                patch.object(subprocess, "check_output", side_effect=AssertionError("no live Git")):
            root = history.historical_repository(auxiliary_fixture=FIXTURE)
        self.assertEqual(hashlib.sha256((root / ARCHITECTURE).read_bytes()).hexdigest(), ARCHITECTURE_SHA256)

    def test_historical_canonical_archive_tampering_still_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = Path(directory)
            for name in ("manifest.json", "canonical-3bf4cc27.zip"):
                shutil.copyfile(history.FIXTURE / name, fixture_root / name)
            archive = fixture_root / "canonical-3bf4cc27.zip"
            archive.write_bytes(archive.read_bytes() + b"altered archive")
            with patch.object(history, "FIXTURE", fixture_root):
                # Exercise ordinary cold materialization without evicting any
                # other replay's cached root or changing historical source bytes.
                with self.assertRaisesRegex(ValueError, "historical canonical archive integrity mismatch"):
                    history._materialize_repository.__wrapped__(())

    def test_retained_data_manifest_tampering_rejects_auxiliary_binding(self):
        target = history.REPOSITORY / "data/review/card-acquisition-pilot/manifest.json"
        original_read = Path.read_bytes
        def altered(path):
            raw = original_read(path)
            return raw + b"\n" if path == target else raw
        with patch.object(Path, "read_bytes", altered):
            with self.assertRaisesRegex(ValueError, "auxiliary artifact binding mismatch"):
                history.historical_repository(auxiliary_fixture=FIXTURE)


if __name__ == "__main__":
    unittest.main()
