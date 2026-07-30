import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from market import (ExternalIdentifierMapping, ExternalMappingRepository, MappingSet,
                    MappedMarketProvider, MarketValidationError, PriceValues,
                    ProviderResponse)


NOW = datetime(2026, 7, 30, tzinfo=timezone.utc)


class CanonicalStub:
    def get_printing(self, identifier):
        if identifier not in {"printing.one", "printing.two"}:
            raise KeyError(identifier)
        return identifier


def record(printing="printing.one", **changes):
    values = {
        "canonical_printing_id": printing,
        "provider_name": "example",
        "provider_product_id": "Product-123",
        "provider_sku_id": "SKU-foil-en",
        "finish": "Foil",
        "language": "EN",
        "mapping_status": "active",
        "provenance": {"source": "reviewed fixture", "record": 7},
    }
    values.update(changes)
    return ExternalIdentifierMapping(**values)


class FixtureProvider(MappedMarketProvider):
    name = "example"

    def fetch_mapped(self, printing_id, mapping):
        return ProviderResponse(printing_id, self.name, NOW,
                                values=PriceValues(market="1.25"),
                                metadata={"provider_product_id": mapping.provider_product_id})


class ExternalMappingTests(unittest.TestCase):
    def test_mapping_normalizes_dimensions_and_is_immutable(self):
        mapping = record()
        self.assertEqual((mapping.finish, mapping.language), ("foil", "en"))
        self.assertEqual(mapping.provider_product_id, "Product-123")
        with self.assertRaises(TypeError):
            mapping.provenance["source"] = "changed"

    def test_validation_requires_status_identifiers_and_provenance(self):
        with self.assertRaisesRegex(MarketValidationError, "mapping_status"):
            record(mapping_status="guessed")
        with self.assertRaisesRegex(MarketValidationError, "provenance"):
            record(provenance={})
        with self.assertRaisesRegex(MarketValidationError, "provider_product_id"):
            record(provider_product_id="")

    def test_mapping_set_rejects_duplicate_exact_dimensions(self):
        with self.assertRaisesRegex(MarketValidationError, "duplicate"):
            MappingSet("2026.07.30", (record(), record(provider_sku_id="another")),
                       {"import": "fixture"})

    def test_import_is_canonical_deterministic_and_append_only(self):
        mapping_set = MappingSet("2026.07.30", (record("printing.two"), record()),
                                 {"import": "fixture"})
        with tempfile.TemporaryDirectory() as directory:
            repository = ExternalMappingRepository(Path(directory), CanonicalStub())
            path = repository.import_document(mapping_set.to_dict())
            first = path.read_bytes()
            self.assertEqual(json.loads(first)["mappings"][0]["canonical_printing_id"],
                             "printing.one")
            self.assertEqual(repository.load("example", "2026.07.30"), mapping_set)
            with self.assertRaisesRegex(MarketValidationError, "already exists"):
                repository.import_document(mapping_set.to_dict())

    def test_import_rejects_unknown_canonical_printing_and_multiple_providers(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = ExternalMappingRepository(Path(directory), CanonicalStub())
            unknown = MappingSet("v1", (record("printing.unknown"),), {"import": "fixture"})
            with self.assertRaisesRegex(MarketValidationError, "unknown canonical"):
                repository.import_document(unknown.to_dict())
            mixed = MappingSet("v2", (record(), record(
                "printing.two", provider_name="second")), {"import": "fixture"})
            with self.assertRaisesRegex(MarketValidationError, "exactly one provider"):
                repository.import_document(mixed.to_dict())

    def test_resolve_requires_exact_active_finish_and_language(self):
        mapping_set = MappingSet("v1", (
            record(),
            record(finish=None, language=None, provider_sku_id=None),
            record("printing.two", finish=None, language=None, mapping_status="pending"),
        ), {"import": "fixture"})
        with tempfile.TemporaryDirectory() as directory:
            repository = ExternalMappingRepository(Path(directory), CanonicalStub())
            repository.import_document(mapping_set.to_dict())
            exact = repository.resolve("printing.one", "example", version="v1",
                                       finish="FOIL", language="en")
            self.assertEqual(exact.provider_sku_id, "SKU-foil-en")
            generic = repository.resolve("printing.one", "example", version="v1")
            self.assertIsNone(generic.finish)
            with self.assertRaisesRegex(MarketValidationError, "no exact active"):
                repository.resolve("printing.two", "example", version="v1")
            self.assertEqual(repository.validate("example", "v1"),
                             ("printing.two: mapping is pending",))

    def test_mapped_provider_resolves_before_adapter_fetch(self):
        mapping_set = MappingSet("v1", (record(finish=None, language=None),),
                                 {"import": "fixture"})
        with tempfile.TemporaryDirectory() as directory:
            repository = ExternalMappingRepository(Path(directory), CanonicalStub())
            repository.import_document(mapping_set.to_dict())
            response = FixtureProvider(repository, "v1").fetch("printing.one")
            self.assertEqual(response.metadata["provider_product_id"], "Product-123")


if __name__ == "__main__":
    unittest.main()
