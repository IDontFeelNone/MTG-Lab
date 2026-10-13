"""Read-only validation of production records against their retained admissions."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from projection import ProjectionValidationError, TypedCanonicalProjectionEngine


ROOT = Path(__file__).parents[1]
TIME = "2026-10-13T12:00:00+00:00"


class ProductionProjectionBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        shutil.copytree(ROOT / "data/canonical", self.data / "canonical")
        shutil.copytree(ROOT / "data/audit/bounded_promotions",
                        self.data / "audit/bounded_promotions")
        shutil.copytree(ROOT / "data/reviews/phase-115", self.data / "reviews/phase-115")
        shutil.copytree(ROOT / "data/reviews/phase-116", self.data / "reviews/phase-116")
        shutil.copytree(ROOT / "data/evidence/phase-135", self.data / "evidence/phase-135")
        source = ROOT / "data/production_runs/30663562841-review-payload-v2"
        target = self.data / "production_runs/30663562841-review-payload-v2"
        for relative in ("lineage/source.json",
                         "review_payloads/mb2/mb2-batch-000001-e32022126c07.json"):
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, destination)
        self.engine = TypedCanonicalProjectionEngine(self.data / "canonical",
            self.root / "typed", self.root / "projection-audits")

    def tearDown(self):
        self.temp.cleanup()

    def test_real_historical_admissions_validate_without_mutating_records(self):
        state = (self.data / "canonical/state.json").read_bytes()
        audits = {p.name: p.read_bytes() for p in
                  (self.data / "audit/bounded_promotions").glob("*.json")}
        result = self.engine.validate()
        self.assertTrue(result["valid"], [c for c in result["checks"] if not c["valid"]][:4])
        self.assertEqual(result["entity_count"], 1534)
        self.assertEqual(result["typed_entity_count"], 1299)
        self.assertEqual(result["identifier_alias_count"], 235)
        self.assertEqual(result["validation_scope"], "production-read-and-admission-integrity")
        self.assertFalse(result["fully_dependency_closed"])
        self.assertFalse(result["typed_materialization_ready"])
        gaps = result["historical_unresolved_finish_references"]
        self.assertEqual(len(gaps), 30)
        self.assertEqual({finish for row in gaps for finish in row["provider_finish_labels"]},
                         {"etched", "signed"})
        self.assertEqual(state, (self.data / "canonical/state.json").read_bytes())
        self.assertEqual(audits, {p.name: p.read_bytes() for p in
                  (self.data / "audit/bounded_promotions").glob("*.json")})

    def test_production_projection_does_not_manufacture_v3_assertions(self):
        with self.assertRaisesRegex(ProjectionValidationError,
                                    "production.*materialization"):
            self.engine.project(TIME)
        self.assertFalse(self.root.joinpath("typed").exists())

    def test_state_change_is_not_grandfathered_by_a_real_promotion_identifier(self):
        path = self.data / "canonical/state.json"
        state = json.loads(path.read_text())
        identifier = next(iter(state["card"]))
        state["card"][identifier]["values"]["name"] = "Changed but schema-valid title"
        path.write_text(json.dumps(state))
        result = self.engine.validate()
        self.assertFalse(result["valid"])
        self.assertTrue(any(c["name"] == "admission_evidence" and not c["valid"]
                            for c in result["checks"]))

    def test_altered_or_missing_retained_admission_inputs_are_rejected(self):
        path = self.data / "production_runs/30663562841-review-payload-v2/review_payloads/mb2/mb2-batch-000001-e32022126c07.json"
        original = path.read_bytes()
        document = json.loads(original)
        document["candidate_payloads"][0]["unknown_fields"]["unreviewed"] = "tampered"
        path.write_text(json.dumps(document))
        self.assertFalse(self.engine.validate()["valid"])
        path.write_bytes(original)
        self.assertTrue(self.engine.validate()["valid"])
        path.unlink()
        self.assertFalse(self.engine.validate()["valid"])

    def test_identifiers_are_validated_and_counted_as_existing_query_aliases(self):
        path = self.data / "canonical/state.json"
        state = json.loads(path.read_text())
        identifier = next(iter(state["identifier"]))
        state["identifier"][identifier]["values"]["printing_uuid"] = "missing-printing"
        path.write_text(json.dumps(state))
        result = self.engine.validate()
        self.assertFalse(result["valid"])
        self.assertEqual(result["identifier_alias_count"], 235)
        self.assertTrue(any(c["name"] == "dependency_integrity" and not c["valid"]
                            for c in result["checks"]))
        state["identifier"][identifier]["values"] = {}
        path.write_text(json.dumps(state))
        result = self.engine.validate()
        self.assertFalse(result["valid"])
        self.assertEqual(result["entity_count"], 1534)
        self.assertEqual(result["identifier_alias_count"], 235)

    def test_corrupt_historical_audit_cannot_authorize_production_shape(self):
        path = next((self.data / "audit/bounded_promotions").glob("*phase-119*.json"))
        audit = json.loads(path.read_text())
        audit["result"] = "pending"
        path.write_text(json.dumps(audit))
        self.assertFalse(self.engine.validate()["valid"])

    def test_configured_audit_locations_are_resolved_without_duplicate_fallback(self):
        source = next((self.data / "audit/bounded_promotions").glob("*phase-119*.json"))
        relocated = self.data / "audit/configured/retained-first-admission.json"
        relocated.parent.mkdir(parents=True)
        source.rename(relocated)
        self.assertTrue(self.engine.validate()["valid"])
        shutil.copy2(relocated, source)
        self.assertFalse(self.engine.validate()["valid"])

    def test_schema_invalid_production_values_return_failed_validation(self):
        path = self.data / "canonical/state.json"
        state = json.loads(path.read_text())
        record = next(iter(state["printing"].values()))
        record["values"]["card_id"] = ["wrong-type"]
        record["values"]["finish_ids"] = [{"invalid": "finish-reference"}]
        record["evidence_references"] = [{"invalid": "evidence-reference"}]
        path.write_text(json.dumps(state))
        self.assertFalse(self.engine.validate()["valid"])

    def test_original_pilot_projection_tampering_is_rejected(self):
        path = self.data / "evidence/phase-135/mtgjson-pilot-30786023976-1/source-pilot-printings.json"
        source = json.loads(path.read_text())
        source["pilot_printings"][0]["collector_number"] = "changed"
        path.write_text(json.dumps(source))
        result = self.engine.validate()
        self.assertFalse(result["valid"])
        self.assertTrue(any(c["name"] == "admission_evidence" and not c["valid"]
                            for c in result["checks"]))


if __name__ == "__main__":
    unittest.main()
