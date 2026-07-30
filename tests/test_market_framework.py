import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from market import (ManualMarketProvider, MarketProvider, MarketService, MarketSnapshot,
                    MarketSnapshotRepository, MarketValidationError, PriceValues,
                    ProviderResponse)


NOW = datetime(2026, 7, 30, 12, tzinfo=timezone.utc)


class CanonicalStub:
    def __init__(self, identifiers=("printing.one",)):
        self.identifiers = set(identifiers)

    def get_printing(self, identifier):
        if identifier not in self.identifiers:
            raise KeyError(identifier)
        return identifier


class CountingProvider(MarketProvider):
    name = "sample"

    def __init__(self):
        self.calls = 0

    def fetch(self, printing_id):
        self.calls += 1
        return ProviderResponse(printing_id, self.name, NOW - timedelta(hours=1),
                                values=PriceValues(low="1.00", market="2.25", high="3.50"),
                                variants={"foil": PriceValues(latest="4.00")},
                                metadata={"request": {"sequence": self.calls}})


class BadIdentityProvider(CountingProvider):
    def fetch(self, printing_id):
        return ProviderResponse("different", self.name, NOW, values=PriceValues(latest=1))


class MarketFrameworkTests(unittest.TestCase):
    def test_provider_interface_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            MarketProvider()

    def test_partial_values_and_variants_are_supported_and_immutable(self):
        response = ProviderResponse("p", "source", NOW, variants={
            "nonfoil": PriceValues(market="1.20"), "foil": PriceValues(low=2)
        }, metadata={"nested": {"value": 1}})
        self.assertEqual(response.variants["nonfoil"].to_dict(), {"market": "1.20"})
        with self.assertRaises(TypeError):
            response.metadata["nested"]["value"] = 2

    def test_market_service_normalizes_and_caches(self):
        provider = CountingProvider()
        service = MarketService(CanonicalStub(), [provider], clock=lambda: NOW)
        first = service.get("printing.one", provider="sample")
        second = service.get("printing.one", provider="sample")
        self.assertIs(first, second)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(first.currency, "USD")
        self.assertEqual(first.provenance["retrieval"]["framework"], "market-provider-v1")

    def test_refresh_bypasses_cache(self):
        provider = CountingProvider()
        service = MarketService(CanonicalStub(), [provider], clock=lambda: NOW)
        service.get("printing.one", provider="sample")
        service.get("printing.one", provider="sample", refresh=True)
        self.assertEqual(provider.calls, 2)

    def test_cache_expires(self):
        provider = CountingProvider()
        times = iter((NOW, NOW + timedelta(minutes=6)))
        service = MarketService(CanonicalStub(), [provider], cache_ttl=timedelta(minutes=5),
                                clock=lambda: next(times))
        service.get("printing.one", provider="sample")
        service.get("printing.one", provider="sample")
        self.assertEqual(provider.calls, 2)

    def test_service_rejects_unknown_printing_provider_and_bad_response(self):
        service = MarketService(CanonicalStub(), [CountingProvider()], clock=lambda: NOW)
        with self.assertRaisesRegex(MarketValidationError, "unknown canonical printing"):
            service.get("missing", provider="sample")
        with self.assertRaisesRegex(MarketValidationError, "unknown market provider"):
            service.get("printing.one", provider="missing")
        bad = MarketService(CanonicalStub(), [BadIdentityProvider()], clock=lambda: NOW)
        with self.assertRaisesRegex(MarketValidationError, "printing identifier mismatch"):
            bad.get("printing.one", provider="sample")

    def test_validation_rejects_invalid_prices_and_timestamps(self):
        with self.assertRaisesRegex(MarketValidationError, "at least one"):
            PriceValues()
        with self.assertRaisesRegex(MarketValidationError, "non-negative"):
            PriceValues(low="-0.01")
        with self.assertRaisesRegex(MarketValidationError, "timezone-aware"):
            ProviderResponse("p", "provider", datetime(2026, 1, 1),
                             values=PriceValues(latest=1))
        with self.assertRaisesRegex(MarketValidationError, "stable lowercase identifier"):
            ProviderResponse("../printing", "provider", NOW, values=PriceValues(latest=1))
        future = CountingProvider()
        future.fetch = lambda printing_id: ProviderResponse(
            printing_id, future.name, NOW + timedelta(seconds=1), values=PriceValues(latest=1))
        with self.assertRaisesRegex(MarketValidationError, "in the future"):
            MarketService(CanonicalStub(), [future], clock=lambda: NOW).get(
                "printing.one", provider="sample")

    def test_snapshot_append_load_and_append_only_behavior(self):
        snapshot = MarketSnapshot("printing.one", "sample", NOW - timedelta(hours=1), NOW,
                                  "usd", values=PriceValues(market="2.00"),
                                  provenance={"source": "fixture"})
        with tempfile.TemporaryDirectory() as directory:
            repository = MarketSnapshotRepository(Path(directory))
            path = repository.append(snapshot)
            self.assertEqual(repository.load(path), snapshot)
            with self.assertRaisesRegex(MarketValidationError, "already exists"):
                repository.append(snapshot)
            self.assertEqual(repository.list(), (snapshot,))

    def test_snapshot_integrity_detects_tampering(self):
        snapshot = MarketSnapshot("printing.one", "sample", NOW, NOW, "USD",
                                  values=PriceValues(latest="2.00"))
        with tempfile.TemporaryDirectory() as directory:
            repository = MarketSnapshotRepository(Path(directory))
            path = repository.append(snapshot)
            data = json.loads(path.read_text())
            data["snapshot_id"] = "tampered"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(MarketValidationError, "snapshot_id"):
                repository.load(path)

    def test_service_can_persist_snapshot_without_mutating_canonical_data(self):
        canonical = CanonicalStub()
        with tempfile.TemporaryDirectory() as directory:
            repository = MarketSnapshotRepository(Path(directory))
            service = MarketService(canonical, [CountingProvider()], snapshots=repository,
                                    clock=lambda: NOW)
            snapshot = service.refresh("printing.one", provider="sample")
            self.assertEqual(repository.list(), (snapshot,))
            self.assertEqual(canonical.identifiers, {"printing.one"})

    def test_cached_retrieval_can_be_persisted_later(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = MarketSnapshotRepository(Path(directory))
            service = MarketService(CanonicalStub(), [CountingProvider()], snapshots=repository,
                                    clock=lambda: NOW)
            cached = service.get("printing.one", provider="sample")
            persisted = service.get("printing.one", provider="sample", persist=True)
            self.assertIs(cached, persisted)
            self.assertEqual(repository.list(), (cached,))

    def test_manual_provider_output_is_deterministic_and_offline(self):
        first = ManualMarketProvider().fetch("printing.one")
        second = ManualMarketProvider().fetch("printing.one")
        self.assertEqual(first, second)
        self.assertFalse(first.metadata["network_access"])


if __name__ == "__main__":
    unittest.main()
