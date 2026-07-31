"""Phase 97 Stage 2 intake tests; all card names and records are synthetic."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from canonical_import.card_list_package import prepare_reviewed_card_list_package
from canonical_import.evidence_package import EvidencePackageError


def _write(root: Path) -> None:
    source_id = "synthetic-reviewed-source"
    def row(kind, candidate, payload, unknowns):
        return {"candidate_id": candidate, "payload": payload, "explicit_unknowns": unknowns,
                "field_provenance": [{"field_path": field, "source_id": source_id,
                                      "confidence": 1.0} for field in payload]}
    artifact = {"dataset_id": "synthetic-mb2-stage-2", "product_id": "mystery_booster_2",
                "cards": [row("card", "candidate.card.one", {"schema_version": "v3",
                          "id": "magic.synthetic-one", "game": "magic", "name": "Synthetic One"},
                          ["layout", "oracle_text"])],
                "printings": [row("printing", "candidate.printing.one", {"schema_version": "v3",
                              "id": "magic.mb2.synthetic-1.en", "card_id": "magic.synthetic-one",
                              "set_id": "mb2", "collector_number": "S1", "language": "en"},
                              ["rarity", "finish", "treatments"])]}
    artifact_bytes = (json.dumps(artifact, sort_keys=True, indent=2) + "\n").encode()
    (root / "cards.json").write_bytes(artifact_bytes)
    records = {
        "manifest.json": {"id": "synthetic-package", "source_record": "source.json",
                          "dataset_record": "dataset.json", "review_record": "review.json",
                          "card_list_artifact": "cards.json"},
        "source.json": {"id": source_id, "dataset_id": "synthetic-mb2-stage-2",
                        "source_identifier": "synthetic:test-only", "artifact_path": "cards.json",
                        "sha256": hashlib.sha256(artifact_bytes).hexdigest(),
                        "captured_at": "2026-07-31T00:00:00Z", "captured_by": "operator",
                        "license_assessment": {"status": "assessed", "result": "test fixture"},
                        "terms_assessment": {"status": "assessed", "result": "test fixture"}},
        "dataset.json": {"id": "synthetic-mb2-stage-2", "source_ids": [source_id],
                         "declared_counts": {"cards": 1, "printings": 1},
                         "completeness": "complete_for_reviewed_card_membership"},
        "review.json": {"id": "synthetic-review", "decision": "approved", "reviewer": "reviewer",
                        "approved_candidate_ids": ["candidate.card.one", "candidate.printing.one"]},
    }
    for name, value in records.items():
        (root / name).write_text(json.dumps(value), encoding="utf-8")


class MB2Stage2IntakeTests(unittest.TestCase):
    def package(self):
        temporary = tempfile.TemporaryDirectory(); root = Path(temporary.name); _write(root)
        return temporary, root

    def test_complete_reviewed_card_membership_is_repeatable_and_audit_ready(self):
        temporary, root = self.package()
        with temporary:
            first = prepare_reviewed_card_list_package(root)
            second = prepare_reviewed_card_list_package(root)
            self.assertEqual(first, second)
            self.assertEqual(first["entity_counts"], {"cards": 1, "printings": 1})
            self.assertTrue(first["promotion_ready"])
            self.assertFalse(first["promoted"])
            self.assertRegex(first["promotion_plan_id"], r"^mb2-stage-2-plan-[0-9a-f]{24}$")

    def test_field_provenance_explicit_unknowns_and_relationships_are_required(self):
        for mutation, message in (
            (lambda data: data["cards"][0].update(field_provenance=[]), "provenance"),
            (lambda data: data["printings"][0].pop("explicit_unknowns"), "explicit_unknowns"),
            (lambda data: data["printings"][0]["payload"].update(card_id="magic.missing"), "outside"),
        ):
            temporary, root = self.package()
            with temporary:
                data = json.loads((root / "cards.json").read_text()); mutation(data)
                raw = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode(); (root / "cards.json").write_bytes(raw)
                source = json.loads((root / "source.json").read_text()); source["sha256"] = hashlib.sha256(raw).hexdigest()
                (root / "source.json").write_text(json.dumps(source))
                with self.assertRaisesRegex(EvidencePackageError, message):
                    prepare_reviewed_card_list_package(root)

    def test_duplicates_and_dataset_inconsistency_fail_closed(self):
        temporary, root = self.package()
        with temporary:
            data = json.loads((root / "cards.json").read_text()); data["cards"].append(data["cards"][0])
            raw = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode(); (root / "cards.json").write_bytes(raw)
            source = json.loads((root / "source.json").read_text()); source["sha256"] = hashlib.sha256(raw).hexdigest()
            (root / "source.json").write_text(json.dumps(source))
            dataset = json.loads((root / "dataset.json").read_text()); dataset["declared_counts"]["cards"] = 2
            (root / "dataset.json").write_text(json.dumps(dataset))
            with self.assertRaisesRegex(EvidencePackageError, "duplicate card"):
                prepare_reviewed_card_list_package(root)

    def test_review_hash_and_topology_requirements_fail_closed(self):
        cases = (("review.json", lambda value: value.update(decision="pending"), "review"),
                 ("source.json", lambda value: value.update(sha256="0" * 64), "hash"),
                 ("cards.json", lambda value: value.update(slots=[]), "topology"))
        for filename, mutation, message in cases:
            temporary, root = self.package()
            with temporary:
                value = json.loads((root / filename).read_text()); mutation(value)
                (root / filename).write_text(json.dumps(value))
                if filename == "cards.json":
                    source = json.loads((root / "source.json").read_text())
                    source["sha256"] = hashlib.sha256((root / filename).read_bytes()).hexdigest()
                    (root / "source.json").write_text(json.dumps(source))
                with self.assertRaisesRegex(EvidencePackageError, message):
                    prepare_reviewed_card_list_package(root)


if __name__ == "__main__":
    unittest.main()
