import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from evidence import (AcquisitionMetadata, EvidenceArtifact, EvidenceDataset, ReviewMetadata)
from mtglab.__main__ import main
from providers import provider_registry
from providers.mtgjson import (MTGJSONProvider, MTGJSONValidationError, identifier_findings,
                               map_dataset, parse_dataset, validate_document)
from providers.mtgjson.provider import ENTITY_TYPES, LICENSE

FIXTURE = Path(__file__).parent / "fixtures" / "mtgjson" / "AllPrintings.json"
CAPTURE = AcquisitionMetadata("2026-07-31T00:00:00Z", "2026-07-31T00:00:00Z",
                              "local-supplied-file", "mtgjson-fixture")


class MTGJSONProviderTests(unittest.TestCase):
    def test_provider_registration_metadata_and_capabilities(self):
        provider = provider_registry().get("mtgjson")
        self.assertEqual(provider.metadata().category, "reference_dataset")
        self.assertTrue(provider.capabilities().acquisition_planning)

    def test_schema_dataset_and_malformed_validation(self):
        provider = MTGJSONProvider()
        self.assertTrue(provider.validate_local(FIXTURE)["valid"])
        value = json.loads(FIXTURE.read_text())
        value["meta"]["version"] = "6.0.0"
        self.assertEqual(parse_dataset(json.dumps(value).encode())["meta"]["version"], "6.0.0")
        value = json.loads(FIXTURE.read_text())
        del value["data"]["TST"]["cards"][0]["number"]
        with self.assertRaisesRegex(MTGJSONValidationError, "number"):
            parse_dataset(json.dumps(value).encode())

    def test_duplicate_identifiers_are_rejected(self):
        value = json.loads(FIXTURE.read_text())
        duplicate = dict(value["data"]["TST"]["cards"][0])
        duplicate["uuid"] = "00000000-0000-4000-8000-000000000099"
        value["data"]["TST"]["cards"].append(duplicate)
        with self.assertRaisesRegex(MTGJSONValidationError, "globally unique external identifier"):
            parse_dataset(json.dumps(value).encode())

    def test_identifier_scope_policy_and_deckbox_collision_findings(self):
        value = json.loads(FIXTURE.read_text())
        first = value["data"]["TST"]["cards"][0]
        first["identifiers"]["deckboxId"] = "2676"
        duplicate = dict(first)
        duplicate.update({"uuid": "00000000-0000-4000-8000-000000000099", "number": "99",
                          "identifiers": {"deckboxId": "2676",
                                          "scryfallOracleId": first["identifiers"]["scryfallOracleId"]}})
        value["data"]["TWO"] = {"code": "TWO", "name": "Second", "cards": [duplicate]}
        first_findings = validate_document(value)
        second_findings = identifier_findings(value)
        self.assertEqual(first_findings, second_findings)
        self.assertEqual(json.dumps(first_findings, sort_keys=True),
                         json.dumps(identifier_findings(value), sort_keys=True))
        finding = next(item for item in first_findings
                       if item["identifier_namespace"] == "deckboxId")
        self.assertEqual(finding["severity"], "review-required")
        self.assertEqual(finding["scope"], "not-guaranteed")
        self.assertEqual(len(finding["affected_source_records"]), 2)
        self.assertEqual({row["set_code"] for row in finding["affected_source_records"]},
                         {"tst", "two"})
        # Repeated card-scoped Oracle identities are expected across printings.
        self.assertFalse(any(item["identifier_namespace"] == "scryfallOracleId"
                             for item in first_findings))

    def test_globally_unique_external_identifier_duplicate_remains_fatal(self):
        value = json.loads(FIXTURE.read_text())
        duplicate = dict(value["data"]["TST"]["cards"][0])
        duplicate["uuid"] = "00000000-0000-4000-8000-000000000099"
        duplicate["number"] = "99"
        value["data"]["TST"]["cards"].append(duplicate)
        with self.assertRaisesRegex(MTGJSONValidationError, "scryfallId"):
            validate_document(value)
        value = json.loads(FIXTURE.read_text())
        value["data"]["TST"]["cards"].append(dict(value["data"]["TST"]["cards"][0]))
        with self.assertRaisesRegex(MTGJSONValidationError, "duplicate printing identifier"):
            parse_dataset(json.dumps(value).encode())

    def test_parsing_mapping_unknowns_and_identifiers_are_deterministic(self):
        first = map_dataset(parse_dataset(FIXTURE))
        second = map_dataset(parse_dataset(FIXTURE))
        self.assertEqual(first, second)
        self.assertTrue({"card", "printing", "set", "language", "rarity", "identifier"}.issubset(
            {item["entity_type"] for item in first}))
        card = next(item for item in first if item["entity_type"] == "card")
        self.assertIn("text", card["unknown_fields"])
        self.assertEqual(card["candidate_identifier"], next(
            item for item in second if item["entity_type"] == "card")["candidate_identifier"])
        value = json.loads(FIXTURE.read_text())
        value["data"]["TST"]["cards"][0]["finishes"] = ["foil", "nonfoil"]
        mapped = map_dataset(parse_dataset(json.dumps(value).encode()))
        self.assertEqual({item["mapped_fields"]["value"] for item in mapped
                          if item["entity_type"] == "finish"}, {"foil", "nonfoil"})

    def test_artifact_dataset_and_deterministic_hash_validation(self):
        payload = FIXTURE.read_bytes(); digest = hashlib.sha256(payload).hexdigest()
        provider = MTGJSONProvider()
        artifact = EvidenceArtifact("mtgjson", "all-printings", "all-printings-json", digest,
                                    "application/json", len(payload), CAPTURE, LICENSE)
        dataset = EvidenceDataset("mtgjson", "all-printings", "5.2.1",
                                  "2026-07-31T00:00:00Z", LICENSE, (("source", "fixture"),),
                                  ENTITY_TYPES, ("all-printings-json",), ReviewMetadata())
        self.assertEqual(provider.validate_artifact(artifact), ())
        self.assertEqual(provider.validate_dataset(dataset), ())
        self.assertTrue(provider.validate_local(FIXTURE, digest)["valid"])
        self.assertFalse(provider.validate_local(FIXTURE, "0" * 64)["valid"])

    def test_cli_validate_inspect_and_plan_json_without_canonical_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = {}
            for operation in ("validate", "inspect", "plan"):
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    self.assertEqual(main(["--data-root", str(root), "provider", "mtgjson",
                                           operation, str(FIXTURE), "--format", "json"]), 0)
                outputs[operation] = json.loads(stream.getvalue())
            self.assertTrue(outputs["validate"]["valid"])
            self.assertGreater(outputs["inspect"]["record_count"], 0)
            self.assertFalse(outputs["plan"]["canonical_write"])
            self.assertTrue(outputs["plan"]["review_required"])
            self.assertFalse((root / "canonical").exists())


if __name__ == "__main__":
    unittest.main()
