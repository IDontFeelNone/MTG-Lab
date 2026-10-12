"""Pending identity preparation preserves evidence and never promotes it."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from decision_intelligence import EvidenceReference
from product_intelligence import FixedContentProductManifest, GuaranteedComponent
from scripts.verify_identity_review_bundle import verify_bundle

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "data/reviews/fixed-content-identity/commander-collection-black-non-premium-2026-10-12"


def load(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


class IdentityPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        self.data = self.root / "data"
        shutil.copytree(BUNDLE, self.bundle)
        (self.data / "canonical").mkdir(parents=True)
        shutil.copyfile(ROOT / "data/canonical/state.json", self.data / "canonical/state.json")
        for reference in load(self.bundle / "bundle.json")["research_references"]:
            destination = self.data / reference["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "data" / reference["path"], destination)

    def tearDown(self):
        self.temp.cleanup()

    def verify(self):
        return verify_bundle(self.bundle, self.data)

    def repin(self):
        """Permit structural tests to reach native validators beyond integrity pins."""
        config = load(self.bundle / "bundle.json")
        paths = {config[key] for key in ("manifest_path", "unresolved_path", "existing_references_path")}
        for entry in config["parsed_artifacts"]:
            paths.add(entry["path"])
            paths.update(entry["candidate_artifacts"])
        config["artifact_sha256"] = {path: hashlib.sha256((self.bundle / path).read_bytes()).hexdigest()
                                    for path in set(config["artifact_sha256"]) | paths}
        write(self.bundle / "bundle.json", config)

    def manifest(self, document):
        values = {key: value for key, value in document.items()
                  if key not in {"manifest_id", "components", "evidence"}}
        if values["release_date"]:
            values["release_date"] = date.fromisoformat(values["release_date"])
        value = FixedContentProductManifest(**values,
            components=tuple(GuaranteedComponent(**item) for item in document["components"]),
            evidence=tuple(EvidenceReference(**item) for item in document["evidence"]))
        write(self.bundle / "manifest.json", value.to_dict())

    def add_pair(self):
        """Synthetic future pair exercises schema/relationship gates, never real evidence."""
        card = {"schema_version": "v3", "id": "synthetic-card", "game": "magic", "name": "Synthetic",
                "normalized_name": "synthetic", "layout": "normal", "assertions": []}
        printing = {"schema_version": "v3", "id": "synthetic-printing", "card_id": card["id"],
                    "set_id": "synthetic", "collector_number": "1", "language": "en", "assertions": []}
        config = load(self.bundle / "bundle.json")
        original = load(self.bundle / "candidates/product.json")
        for kind, payload in (("card", card), ("printing", printing)):
            artifact = deepcopy(original)
            artifact.update(id=f"synthetic-{kind}-artifact", candidate_type=kind)
            candidate = artifact["candidates"][0]
            candidate.update(id=f"synthetic-{kind}-candidate", entity_type=kind, payload=payload)
            exemplar = candidate["field_provenance"][0]
            candidate["field_provenance"] = [dict(exemplar, field_path=key, value_origin="computed",
                notes="Explicit synthetic test fixture; pending and not source-admissible.")
                for key in payload if key != "schema_version"]
            path = f"candidates/{kind}.json"
            write(self.bundle / path, artifact)
            config["parsed_artifacts"][0]["candidate_artifacts"].append(path)
        write(self.bundle / "bundle.json", config)
        document = load(self.bundle / "manifest.json")
        document["components"][0]["printing_id"] = printing["id"]
        self.manifest(document)
        unresolved = load(self.bundle / "unresolved-identities.json")
        write(self.bundle / "unresolved-identities.json", unresolved[1:])
        self.repin()

    def mutate_candidate(self, kind, field, value):
        path = self.bundle / f"candidates/{kind}.json"
        artifact = load(path)
        artifact["candidates"][0]["payload"][field] = value
        # Include full provenance so the regression reaches the intended native check.
        exemplar = artifact["candidates"][0]["field_provenance"][0]
        if not any(item["field_path"] == field for item in artifact["candidates"][0]["field_provenance"]):
            artifact["candidates"][0]["field_provenance"].append(dict(exemplar, field_path=field))
        write(path, artifact)
        self.repin()

    def test_real_bundle_replays_deterministically_without_writers(self):
        protected = [ROOT / "data/canonical", ROOT / "data/market", ROOT / "data/knowledge"]
        files = [path for directory in protected for path in directory.rglob("*") if path.is_file()]
        files += list(ROOT.glob("**/ARCHITECTURE.md"))
        before = {path: hashlib.sha256(path.read_bytes()).digest() for path in files}
        with patch("acquisition.RawSnapshotStore.store", side_effect=AssertionError("write forbidden")), \
             patch("acquisition.CanonicalPromotionEngine.promote", side_effect=AssertionError("promotion forbidden")), \
             patch("repository.promotion.CandidatePromotionService.review", side_effect=AssertionError("review forbidden")), \
             patch("repository.canonical.CanonicalRepository.apply_import", side_effect=AssertionError("import forbidden")):
            report = verify_bundle(BUNDLE, ROOT / "data")
            self.assertEqual(report, verify_bundle(BUNDLE / "bundle.json", ROOT / "data"))
        self.assertEqual(report, load(BUNDLE / "review-report.json"))
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).digest() for path in files})
        self.assertEqual(report["candidate_counts"], {"card": 0, "printing": 0, "product": 1})
        self.assertEqual(report["unresolved_identity_count"], 7)
        self.assertEqual(report["reused_printing_count"], 2)
        self.assertFalse(report["human_approved"])
        self.assertFalse(report["source_extraction_semantically_approved"])
        self.assertFalse(report["promotion_performed"])
        self.assertEqual(report["readiness"], "NOT_READY_FOR_EVALUATION")

    def test_retained_source_bytes_cannot_be_changed(self):
        entry = load(self.bundle / "bundle.json")["raw_sources"][0]
        payload = self.bundle / entry["snapshot_directory"] / "payload.bin"
        payload.write_bytes(payload.read_bytes() + b"altered")
        self.repin()
        with self.assertRaisesRegex(ValueError, "checksum|hash|length"):
            self.verify()

    def test_coordinated_name_metadata_and_identity_changes_break_prepared_pins(self):
        for field, value in (("name", "Invented Product"), ("id", "invented-product"),
                             ("metadata", {"provider_identifiers": {"tcgplayerProductId": "invented"},
                                           "release_date": "1900-01-01", "reported_physical_card_count": 99})):
            with self.subTest(field=field):
                path = self.bundle / "candidates/product.json"
                original = path.read_bytes()
                candidate = load(path)
                candidate["candidates"][0]["payload"][field] = value
                write(path, candidate)
                parsed_path = self.bundle / "parsed/product.json"
                old_parsed = parsed_path.read_bytes()
                parsed = load(parsed_path)
                parsed["records"][0]["raw_fields"]["product_name"] = "Invented Product"
                write(parsed_path, parsed)
                with self.assertRaisesRegex(ValueError, "prepared artifact integrity"):
                    self.verify()
                path.write_bytes(original)
                parsed_path.write_bytes(old_parsed)

    def test_field_provenance_must_bind_original_source(self):
        path = self.bundle / "candidates/product.json"
        candidate = load(path)
        candidate["candidates"][0]["field_provenance"][0]["raw_evidence_hash"] = "0" * 64
        write(path, candidate)
        self.repin()
        with self.assertRaisesRegex(ValueError, "field provenance source"):
            self.verify()

    def test_source_excerpt_and_json_selection_must_match_bytes(self):
        for relative in ("parsed/product.json", "parsed/token-pairing.json"):
            with self.subTest(relative=relative):
                path = self.bundle / relative
                original = path.read_bytes()
                parsed = load(path)
                if parsed["input_content_type"] == "text/plain":
                    parsed["records"][0]["source_excerpt"]["raw_text"] = "not in retained source"
                else:
                    parsed["records"][0]["raw_fields"] = {"token_product_records": [{"invented": True}]}
                write(path, parsed)
                self.repin()
                with self.assertRaisesRegex(ValueError, "excerpt|JSON record"):
                    self.verify()
                path.write_bytes(original)
                self.repin()

    def test_reused_state_record_mutation_is_detected(self):
        reference = load(self.bundle / "existing-references.json")[0]
        state = load(self.data / "canonical/state.json")
        state[reference["entity_type"]][reference["entity_id"]]["values"]["name"] = "Changed"
        write(self.data / "canonical/state.json", state)
        with self.assertRaisesRegex(ValueError, "reused canonical reference"):
            self.verify()

    def test_native_and_state_identities_cannot_be_recreated(self):
        payload = load(self.bundle / "candidates/product.json")["candidates"][0]["payload"]
        path = self.data / "canonical/games/magic/products" / payload["id"] / "product.json"
        write(path, payload)
        with self.assertRaisesRegex(ValueError, "recreates canonical"):
            self.verify()
        path.unlink()
        self.add_pair()
        existing = load(self.bundle / "existing-references.json")[0]["entity_id"]
        self.mutate_candidate("card", "id", existing)
        with self.assertRaisesRegex(ValueError, "recreates canonical"):
            self.verify()

    def test_pending_synthetic_pair_relationship_and_face_schema(self):
        self.add_pair()
        self.assertEqual(self.verify()["candidate_counts"], {"card": 1, "printing": 1, "product": 1})
        self.mutate_candidate("printing", "card_id", "missing-card")
        with self.assertRaisesRegex(ValueError, "missing Card"):
            self.verify()
        self.mutate_candidate("printing", "card_id", "synthetic-card")
        self.mutate_candidate("card", "layout", "double_faced_token")
        self.mutate_candidate("card", "faces", [{"name": "Only one face"}])
        with self.assertRaisesRegex(ValueError, "too short"):
            self.verify()

    def test_existing_collector_coordinates_and_provider_identifiers_are_protected(self):
        self.add_pair()
        self.mutate_candidate("printing", "set_id", "cc2")
        self.mutate_candidate("printing", "collector_number", "7")
        with self.assertRaisesRegex(ValueError, "collector coordinate collision"):
            self.verify()
        self.mutate_candidate("printing", "set_id", "synthetic")
        self.mutate_candidate("printing", "external_identifiers", {"scryfallId": "collision"})
        native = {"id": "native-existing", "card_id": "synthetic-card", "set_id": "other",
                  "collector_number": "99", "language": "en", "external_identifiers": {"scryfallId": "collision"}}
        write(self.data / "canonical/games/magic/printings/native-existing/printing.json", native)
        with self.assertRaisesRegex(ValueError, "provider identifier collision"):
            self.verify()

    def test_card_scoped_oracle_identity_is_unique_among_card_candidates(self):
        self.add_pair()
        existing = next(reference["entity_id"] for reference in load(self.bundle / "existing-references.json")
                        if reference["entity_type"] == "card")
        self.mutate_candidate("card", "metadata", {"provider_identifiers": {"scryfallOracleId": existing}})
        with self.assertRaisesRegex(ValueError, "provider identifier collision"):
            self.verify()

    def test_reused_printing_census_and_unique_reference_inventory_are_enforced(self):
        path = self.bundle / "existing-references.json"
        original = load(path)
        write(path, [reference for reference in original
                     if reference["entity_id"] != original[1]["entity_id"]])
        self.repin()
        with self.assertRaisesRegex(ValueError, "scope census"):
            self.verify()
        write(path, original + [original[1]])
        self.repin()
        with self.assertRaisesRegex(ValueError, "duplicate reused"):
            self.verify()

    def test_unresolved_inventory_and_manifest_cannot_claim_completeness(self):
        document = load(self.bundle / "manifest.json")
        document["completeness"] = "complete"
        self.manifest(document)
        self.repin()
        with self.assertRaisesRegex(ValueError, "claims completeness"):
            self.verify()

    def test_manifest_digest_source_binding_and_path_traversal_fail_closed(self):
        document = load(self.bundle / "manifest.json")
        document["evidence"][0]["content_digest"] = "sha256:" + "0" * 64
        self.manifest(document)
        self.repin()
        with self.assertRaisesRegex(ValueError, "manifest source provenance"):
            self.verify()
        config = load(self.bundle / "bundle.json")
        config["artifact_sha256"]["../outside"] = "0" * 64
        write(self.bundle / "bundle.json", config)
        with self.assertRaisesRegex(ValueError, "unsafe bundle path"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
