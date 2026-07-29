"""Tests for content-identified archived evidence bundles."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from repository import EvidenceRepositoryError, evidence_manifest_path, load_evidence_bundle
from validation import SchemaValidationError, validate_document

ROOT = Path(__file__).parents[1]
EVIDENCE_ROOT = ROOT / "data/sources"
GAMES_ROOT = ROOT / "data/canonical/games"


class EvidenceRepositoryTests(unittest.TestCase):
    def copy_repository(self, directory: str) -> tuple[Path, Path]:
        evidence_root = Path(directory) / "sources"
        games_root = Path(directory) / "games"
        shutil.copytree(EVIDENCE_ROOT, evidence_root)
        shutil.copytree(GAMES_ROOT, games_root)
        return evidence_root, games_root

    def test_wave_1_archive_loads_verified_bytes_and_provenance(self) -> None:
        bundle = load_evidence_bundle("magic", "mb2-wave-1")
        self.assertEqual(bundle.manifest["product_id"], "mystery_booster_2")
        self.assertEqual(len(bundle.artifacts), 1)
        artifact = bundle.artifacts[0]
        self.assertEqual(artifact.id, "mb2-wave-1-card-printing-evidence")
        self.assertEqual(artifact.media_type, "application/json")
        self.assertEqual(
            json.loads(artifact.content),
            json.loads(
                (ROOT / "data/raw/magic/mystery_booster_2/wave_1/card-printing-evidence.json")
                .read_bytes()
            ),
        )
        self.assertEqual(
            {entry["source_id"] for entry in artifact.provenance},
            set(bundle.manifest["source_ids"]),
        )
        with self.assertRaises(TypeError):
            bundle.manifest["title"] = "changed"

    def test_manifest_path_requires_stable_identifiers(self) -> None:
        with self.assertRaises(ValueError):
            evidence_manifest_path("magic", "../escape")

    def test_schema_rejects_unbounded_archive_paths_and_bad_hashes(self) -> None:
        manifest = json.loads(
            (EVIDENCE_ROOT / "magic/mb2-wave-1/manifest.json").read_text()
        )
        for unsafe_path in ("../outside.json", "files/../outside.json"):
            manifest["artifacts"][0]["path"] = unsafe_path
            with self.assertRaises(SchemaValidationError):
                validate_document(manifest, "evidence-manifest")
        manifest["artifacts"][0]["path"] = "files/evidence.json"
        manifest["artifacts"][0]["sha256"] = "not-a-sha256"
        with self.assertRaises(SchemaValidationError):
            validate_document(manifest, "evidence-manifest")

    def test_changed_or_missing_archived_bytes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence_root, games_root = self.copy_repository(directory)
            archive = evidence_root / "magic/mb2-wave-1/files/card-printing-evidence.json"
            archive.write_bytes(b"changed")
            with self.assertRaisesRegex(EvidenceRepositoryError, "size mismatch"):
                load_evidence_bundle(
                    "magic", "mb2-wave-1", evidence_root=evidence_root, games_root=games_root
                )
            archive.unlink()
            with self.assertRaisesRegex(EvidenceRepositoryError, "Cannot read"):
                load_evidence_bundle(
                    "magic", "mb2-wave-1", evidence_root=evidence_root, games_root=games_root
                )

    def test_duplicate_and_incomplete_provenance_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence_root, games_root = self.copy_repository(directory)
            manifest_path = evidence_root / "magic/mb2-wave-1/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["source_ids"].append("unused-source")
            source = games_root / "magic/sources/unused-source.json"
            source.write_text(json.dumps({
                "schema_version": "v1", "id": "unused-source", "title": "Unused",
                "source_classification": "internal", "provider": "test",
                "source_location": "fixture", "access_date": "2026-07-29",
                "verification_status": "unverified", "claims": ["fixture"],
                "record_version": "1"
            }))
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(EvidenceRepositoryError, "unused sources"):
                load_evidence_bundle(
                    "magic", "mb2-wave-1", evidence_root=evidence_root, games_root=games_root
                )

            manifest["source_ids"].remove("unused-source")
            manifest["artifacts"].append(dict(manifest["artifacts"][0]))
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(EvidenceRepositoryError, "Duplicate evidence artifact id"):
                load_evidence_bundle(
                    "magic", "mb2-wave-1", evidence_root=evidence_root, games_root=games_root
                )

    def test_unknown_source_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence_root, games_root = self.copy_repository(directory)
            manifest_path = evidence_root / "magic/mb2-wave-1/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["source_ids"][0] = "missing-source"
            manifest["artifacts"][0]["provenance"][0]["source_id"] = "missing-source"
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(EvidenceRepositoryError, "invalid source"):
                load_evidence_bundle(
                    "magic", "mb2-wave-1", evidence_root=evidence_root, games_root=games_root
                )


if __name__ == "__main__":
    unittest.main()
