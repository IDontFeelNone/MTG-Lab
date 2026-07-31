import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from evidence import (
    AcquisitionMetadata, AcquisitionRequest, EvidenceArtifact, EvidenceDataset,
    EvidenceProvider, EvidenceProviderAdapter, LicensingMetadata, ProviderCapabilities,
    ProviderRegistry, ReferenceDatasetRegistry, RegistryValidationError, ReviewMetadata,
    sha256_identity,
)


LICENSE = LicensingMetadata("credit source", "metadata only", "approved", "legal-review", "2026-07-31T00:00:00Z")
CAPTURE = AcquisitionMetadata("2026-07-31T00:00:00Z", "2026-07-30T00:00:00Z", "manual", "https://example.test/source")


class FixtureProvider(EvidenceProviderAdapter):
    def metadata(self):
        return EvidenceProvider("official-fixture", "Official Fixture", "official", "https://example.test", LICENSE)

    def capabilities(self):
        return ProviderCapabilities()

    def register_artifact(self, value):
        return value

    def register_dataset(self, value):
        return value

    def plan(self, request):
        return tuple(sorted(request.requested_artifacts))

    def validate_artifact(self, artifact):
        return ()

    def validate_dataset(self, dataset):
        return ()


def artifact(identifier="artifact-1"):
    content = b"immutable evidence"
    return EvidenceArtifact("official-fixture", "dataset-1", identifier, sha256_identity(content),
                            "application/json", len(content), CAPTURE, LICENSE)


def dataset(artifacts=("artifact-1",)):
    return EvidenceDataset("official-fixture", "dataset-1", "2026.07", "2026-07-31T00:00:00Z",
                           LICENSE, (("source", "fixture"),), ("card", "printing"), artifacts,
                           ReviewMetadata("pending"))


class MultiSourceEvidenceTests(unittest.TestCase):
    def test_provider_registration_capabilities_and_duplicate_detection(self):
        registry = ProviderRegistry(); provider = FixtureProvider(); registry.register(provider)
        self.assertTrue(registry.get("official-fixture").capabilities().artifact_validation)
        with self.assertRaisesRegex(ValueError, "duplicate provider"):
            registry.register(provider)

    def test_dataset_and_artifact_registration_are_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = ReferenceDatasetRegistry(directory)
            self.assertEqual(registry.register_artifact(artifact()), registry.register_artifact(artifact()))
            self.assertEqual(registry.register_dataset(dataset()), registry.register_dataset(dataset()))
            self.assertTrue(registry.validate()["valid"])
            serialized = (Path(directory) / "datasets" / "dataset-1.json").read_text()
            self.assertEqual(serialized, dataset().serialize() + "\n")

    def test_content_hash_is_deterministic(self):
        self.assertEqual(sha256_identity(b"a"), sha256_identity(b"a"))
        self.assertNotEqual(sha256_identity(b"a"), sha256_identity(b"b"))
        self.assertEqual(dataset().identity_sha256, dataset().identity_sha256)

    def test_duplicate_identifier_with_different_content_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = ReferenceDatasetRegistry(directory); registry.register_artifact(artifact())
            with self.assertRaisesRegex(RegistryValidationError, "different content"):
                registry.register_artifact(artifact("artifact-1").__class__(
                    "official-fixture", "dataset-1", "artifact-1", "0" * 64,
                    "application/json", 1, CAPTURE, LICENSE))

    def test_unknown_licensing_fails_closed(self):
        unknown = LicensingMetadata("", "unknown", "unknown", "", "")
        invalid = EvidenceArtifact("p", "d", "a", "0" * 64, "text/plain", 0, CAPTURE, unknown)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RegistryValidationError, "licensing"):
                ReferenceDatasetRegistry(directory).register_artifact(invalid)

    def test_contracts_are_immutable_and_serialization_is_stable(self):
        request = AcquisitionRequest("official-fixture", "dataset-1", ("b", "a"))
        with self.assertRaises(FrozenInstanceError):
            request.dataset_identifier = "other"
        self.assertEqual(request.serialize(), request.serialize())
        self.assertEqual(json.loads(request.serialize())["schema_version"], "1.0.0")

    def test_cli_lists_and_validates_empty_registry_as_json(self):
        with tempfile.TemporaryDirectory() as directory:
            for operation, key in (("providers", "providers"), ("datasets", "datasets"),
                                   ("artifacts", "artifacts")):
                command = [sys.executable, "-m", "mtglab", "--data-root", directory,
                           "evidence", operation, "--format", "json"]
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                self.assertEqual(json.loads(result.stdout)[key], [])
            command = [sys.executable, "-m", "mtglab", "--data-root", directory,
                       "evidence", "validate", "--format", "json"]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertTrue(json.loads(result.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
