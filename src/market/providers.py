"""Provider interface and deterministic offline reference provider."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone

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
