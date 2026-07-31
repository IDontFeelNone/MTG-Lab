"""Phase 96B evidence-package and deterministic Stage 1 import tests."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from canonical_import.evidence_package import EvidencePackageError, import_reviewed_product_package


PACKAGE = Path("data/evidence-packages/magic/mb2-stage-1")
GAMES = Path("data/canonical/games")


class MB2Stage1ImportTests(unittest.TestCase):
    def test_source_hash_capture_registration_provenance_and_unknowns(self):
        source = json.loads((PACKAGE / "source.json").read_text())
        raw = PACKAGE / source["artifact_path"]
        self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(), source["sha256"])
        self.assertEqual(raw.stat().st_size, source["byte_size"])
        dataset = json.loads((PACKAGE / "dataset.json").read_text())
        self.assertEqual(dataset["source_ids"], [source["id"]])
        candidate = json.loads((PACKAGE / "candidate.json").read_text())["candidates"][0]
        self.assertEqual(set(candidate["payload"]),
                         {item["field_path"] for item in candidate["field_provenance"]})
        manifest = json.loads((PACKAGE / "manifest.json").read_text())
        self.assertFalse(manifest["bounded_completeness"]["full_packaging_composition"])
        self.assertEqual(manifest["bounded_completeness"]["pack_topology"], "unresolved")
        self.assertIn("packaging type", manifest["explicit_unknowns"])

    def test_independent_review_validation_promotion_and_duplicate_prevention(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = import_reviewed_product_package(PACKAGE, root, games_seed=GAMES)
            second = import_reviewed_product_package(PACKAGE, root, games_seed=GAMES)
            self.assertEqual(first, second)
            self.assertEqual(first["promotion_outcomes"], ["confirmed"])
            self.assertEqual(len(list((root / "audit/promotions").glob("*.json"))), 1)
            self.assertEqual(len(list((root / "sources").glob("**/*.html"))), 1)

    def test_two_disposable_imports_are_byte_deterministic_and_have_no_topology(self):
        results, trees = [], []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                results.append(import_reviewed_product_package(PACKAGE, root, games_seed=GAMES))
                trees.append({str(path.relative_to(root)): path.read_bytes()
                              for path in sorted(root.glob("**/*")) if path.is_file()})
                product = root / "canonical/games/magic/products/mystery_booster_2"
                self.assertEqual(json.loads((product / "packs.json").read_text())["pack_definition_ids"], [])
                self.assertEqual(json.loads((product / "slots.json").read_text())["slot_ids"], [])
                self.assertFalse(list((root / "canonical/games/magic/product_versions").glob("*.json")))
        self.assertEqual(results[0], results[1])
        self.assertEqual(trees[0], trees[1])

    def test_review_must_be_independent(self):
        with tempfile.TemporaryDirectory() as package_dir, tempfile.TemporaryDirectory() as output:
            copy = Path(package_dir)
            import shutil
            shutil.copytree(PACKAGE, copy, dirs_exist_ok=True)
            source = json.loads((copy / "source.json").read_text())
            review = json.loads((copy / "review.json").read_text())
            review["reviewer"] = source["captured_by"]
            (copy / "review.json").write_text(json.dumps(review))
            with self.assertRaisesRegex(EvidencePackageError, "independent"):
                import_reviewed_product_package(copy, Path(output), games_seed=GAMES)

    def test_immutable_destination_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = import_reviewed_product_package(PACKAGE, root, games_seed=GAMES)
            source = json.loads((PACKAGE / "source.json").read_text())
            retained = next((root / "sources" / source["id"] / result["source_hashes"][0]).iterdir())
            retained.write_bytes(b"changed")
            with self.assertRaisesRegex(EvidencePackageError, "immutable"):
                import_reviewed_product_package(PACKAGE, root, games_seed=GAMES)


if __name__ == "__main__":
    unittest.main()
