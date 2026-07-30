"""Stable market API, provider selection, normalization, caching, and capture."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable

from .models import (MarketSnapshot, MarketValidationError, ProviderResponse,
                     normalize_timestamp)
from .providers import MarketProvider
from .repository import MarketSnapshotRepository


class MarketService:
    def __init__(self, canonical_repository, providers: Iterable[MarketProvider], *,
                 snapshots: MarketSnapshotRepository | None = None,
                 cache_ttl: timedelta = timedelta(minutes=5),
                 clock: Callable[[], datetime] | None = None):
        self.canonical_repository = canonical_repository
        self.snapshots = snapshots
        self.cache_ttl = cache_ttl
        if cache_ttl < timedelta(0):
            raise MarketValidationError("cache_ttl cannot be negative")
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.providers = {}
        for provider in providers:
            if not isinstance(provider, MarketProvider):
                raise MarketValidationError("providers must implement MarketProvider")
            if provider.name in self.providers:
                raise MarketValidationError(f"duplicate provider: {provider.name}")
            self.providers[provider.name] = provider
        self._cache: dict[tuple[str, str], tuple[datetime, MarketSnapshot]] = {}

    def get(self, printing_id: str, *, provider: str, refresh: bool = False,
            persist: bool = False) -> MarketSnapshot:
        try:
            self.canonical_repository.get_printing(printing_id)
        except KeyError as error:
            raise MarketValidationError(f"unknown canonical printing: {printing_id}") from error
        if provider not in self.providers:
            raise MarketValidationError(f"unknown market provider: {provider}")
        now = normalize_timestamp(self.clock())
        key = (provider, printing_id)
        cached = self._cache.get(key)
        if not refresh and cached and now - cached[0] <= self.cache_ttl:
            if persist:
                if self.snapshots is None:
                    raise MarketValidationError("snapshot repository is not configured")
                self.snapshots.append(cached[1])
            return cached[1]
        response = self.providers[provider].fetch(printing_id)
        self._validate_response(response, provider, printing_id, now)
        provenance = {"provider_metadata": response.metadata,
                      "retrieval": {"provider": provider, "framework": "market-provider-v1"}}
        snapshot = MarketSnapshot(response.printing_id, response.provider, response.timestamp,
                                  now, response.currency, response.values, response.variants,
                                  provenance)
        self._cache[key] = (now, snapshot)
        if persist:
            if self.snapshots is None:
                raise MarketValidationError("snapshot repository is not configured")
            self.snapshots.append(snapshot)
        return snapshot

    def refresh(self, printing_id: str, *, provider: str, persist: bool = True) -> MarketSnapshot:
        return self.get(printing_id, provider=provider, refresh=True, persist=persist)

    @staticmethod
    def _validate_response(response: ProviderResponse, provider: str,
                           printing_id: str, retrieved_at: datetime) -> None:
        if not isinstance(response, ProviderResponse):
            raise MarketValidationError("provider must return ProviderResponse")
        if response.provider != provider:
            raise MarketValidationError("provider response identifier mismatch")
        if response.printing_id != printing_id:
            raise MarketValidationError("provider response printing identifier mismatch")
        if response.timestamp > retrieved_at:
            raise MarketValidationError("provider response timestamp is in the future")
