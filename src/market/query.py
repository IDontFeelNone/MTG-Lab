"""Read-only market extension to the canonical query boundary."""
from __future__ import annotations

from typing import Any, Iterable

from .intelligence import MarketAnalytics, MarketObservation, MarketObservationRepository


class MarketQueryService:
    def __init__(self, canonical_service, repository: MarketObservationRepository):
        self.canonical = canonical_service
        self.repository = repository
        self.analytics = MarketAnalytics()

    def _envelope(self, operation: str, identifier: str, observations: Iterable[MarketObservation],
                  *, providers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        values = list(observations); summary = self.analytics.summarize(values)
        return {"schema_version": "market-query-v1", "query": {"operation": operation, "identifier": identifier},
            "status": summary["status"], "answer": summary if providers is None else providers,
            "provider": summary["provider"], "timestamp": summary["timestamp"],
            "confidence": summary["confidence"], "provenance": summary["provenance"],
            "canonical_snapshot_identity": self.canonical.snapshot_identity}

    def printing(self, identifier: str, *, provider: str | None = None) -> dict[str, Any]:
        canonical = self.canonical.printing(identifier)
        canonical_id = canonical.canonical_identifiers[0] if canonical.canonical_identifiers else identifier
        values = self.repository.observations(entity_type="printing", entity_id=canonical_id, provider=provider)
        return self._envelope("printing_summary", identifier, values)

    def card(self, identifier: str, *, provider: str | None = None) -> dict[str, Any]:
        card = self.canonical.cards(identifier=identifier)
        card_ids = set(card.canonical_identifiers)
        printing_ids = set(self.canonical.printings_for_card(identifier).canonical_identifiers) if card_ids else set()
        values = [x for x in self.repository.observations(provider=provider) if
                  (x.entity_type == "card" and x.entity_id in card_ids) or
                  (x.entity_type == "printing" and x.entity_id in printing_ids)]
        return self._envelope("card_summary", identifier, values)

    def product(self, identifier: str, *, provider: str | None = None) -> dict[str, Any]:
        canonical = self.canonical.product(identifier)
        ids = set(canonical.canonical_identifiers)
        values = [x for x in self.repository.observations(provider=provider) if
                  (x.entity_type == "product" and x.entity_id == identifier) or
                  (x.entity_type == "printing" and x.entity_id in ids)]
        return self._envelope("product_summary", identifier, values)

    def history(self, entity_type: str, identifier: str, *, provider: str | None = None) -> dict[str, Any]:
        values = self.repository.observations(entity_type=entity_type, entity_id=identifier, provider=provider)
        points = [{"observation_id": x.observation_id, "price": None if x.price is None else format(x.price, "f"),
            "buylist_price": None if x.buylist_price is None else format(x.buylist_price, "f"), "currency": x.currency,
            "provider": x.provider, "timestamp": x.observed_at.isoformat().replace("+00:00", "Z"),
            "confidence": None if x.provider_confidence is None else format(x.provider_confidence, "f"),
            "provenance": x.to_dict()["provenance"]} for x in values]
        envelope = self._envelope("history", identifier, values, providers=points)
        envelope["status"] = "known" if points else "unknown"
        return envelope

    def provider_comparison(self, entity_type: str, identifier: str) -> dict[str, Any]:
        values = self.repository.observations(entity_type=entity_type, entity_id=identifier)
        comparisons = []
        for provider in sorted({x.provider for x in values}):
            summary = self.analytics.summarize(x for x in values if x.provider == provider)
            comparisons.append(summary)
        return self._envelope("provider_comparison", identifier, values, providers=comparisons)
