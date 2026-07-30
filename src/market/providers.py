"""Provider interface and deterministic offline reference provider."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from .mappings import ExternalIdentifierMapping, ExternalMappingRepository
from .models import PriceValues, ProviderResponse, validate_identifier


class MarketProvider(ABC):
    """Interchangeable source boundary; only MarketService calls providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider's stable identifier."""

    @abstractmethod
    def fetch(self, printing_id: str) -> ProviderResponse:
        """Retrieve partial market information for a canonical printing."""


class MappedMarketProvider(MarketProvider):
    """Base for future adapters that require an exact external identifier mapping."""

    def __init__(self, mappings: ExternalMappingRepository, mapping_version: str):
        self.mappings = mappings
        self.mapping_version = validate_identifier(mapping_version, "mapping_version")

    def fetch(self, printing_id: str) -> ProviderResponse:
        mapping = self.mappings.resolve(printing_id, self.name, version=self.mapping_version)
        return self.fetch_mapped(printing_id, mapping)

    @abstractmethod
    def fetch_mapped(self, printing_id: str,
                     mapping: ExternalIdentifierMapping) -> ProviderResponse:
        """Retrieve data using a mapping selected by the shared mapping layer."""


class ManualMarketProvider(MarketProvider):
    """Deterministic, network-free sample provider for framework validation."""

    name = "manual"
    _timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def fetch(self, printing_id: str) -> ProviderResponse:
        printing_id = validate_identifier(printing_id, "printing_id")
        cents = int(hashlib.sha256(printing_id.encode("utf-8")).hexdigest()[:8], 16) % 10000 + 100
        market = f"{cents / 100:.2f}"
        return ProviderResponse(
            printing_id=printing_id, provider=self.name, timestamp=self._timestamp,
            variants={"nonfoil": PriceValues(latest=market, market=market)},
            metadata={"mode": "deterministic-sample", "network_access": False},
        )
