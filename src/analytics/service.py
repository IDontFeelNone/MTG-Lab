"""Game-agnostic, side-effect-free analytics computations."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping

from collection.models import Collection

from .models import AnalyticsReport


class AnalyticsService:
    """Compute facts from supplied snapshots without fetching or persisting data."""

    def __init__(self, clock: Callable[[], datetime] | None = None):
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _report(self, kind: str, inputs: Mapping[str, Any], data: Mapping[str, Any]) -> AnalyticsReport:
        return AnalyticsReport(kind, self._clock(), inputs, data)

    def collection_summary(self, collection: Collection) -> AnalyticsReport:
        quantities = self._printing_quantities(collection)
        finishes = self._card_counter(collection, "finish")
        return self._report("collection_summary", {"collection_id": collection.id}, {
            "total_cards": sum(quantities.values()),
            "unique_printings": len(quantities),
            "duplicate_copies": sum(max(0, count - 1) for count in quantities.values()),
            "finish_distribution": dict(sorted(finishes.items())),
            "card_frequency": self._frequency(quantities),
        })

    def duplicate_report(self, collection: Collection) -> AnalyticsReport:
        quantities = self._printing_quantities(collection)
        duplicates = [{"printing_id": key, "quantity": count, "extra_copies": count - 1}
                      for key, count in sorted(quantities.items()) if count > 1]
        return self._report("duplicate_report", {"collection_id": collection.id}, {
            "duplicate_printings": len(duplicates),
            "duplicate_copies": sum(item["extra_copies"] for item in duplicates),
            "items": duplicates,
        })

    def acquisition_report(self, collection: Collection) -> AnalyticsReport:
        acquisitions = {item.id: item for item in collection.acquisitions}
        by_type: Counter[str] = Counter()
        by_product: Counter[str] = Counter()
        growth: Counter[str] = Counter()
        for card in collection.cards:
            acquisition = acquisitions[card.acquisition_id]
            by_type[acquisition.type] += card.quantity
            by_product[acquisition.product_id or "unattributed"] += card.quantity
            growth[acquisition.acquired_at.date().isoformat()] += card.quantity
        running = 0
        timeline = []
        for date, quantity in sorted(growth.items()):
            running += quantity
            timeline.append({"date": date, "acquired": quantity, "cumulative": running})
        return self._report("acquisition_report", {"collection_id": collection.id}, {
            "acquisition_count": len(collection.acquisitions),
            "cards_by_type": dict(sorted(by_type.items())),
            "cards_by_product": dict(sorted(by_product.items())),
            "collection_growth": timeline,
        })

    def inventory_report(self, collection: Collection) -> AnalyticsReport:
        location_names = {item.id: item.name for item in collection.locations}
        by_location: Counter[str] = Counter()
        assigned: Counter[str] = Counter()
        owned_by_id = {item.id: item.quantity for item in collection.cards}
        for card in collection.cards:
            by_location[location_names[card.location_id]] += card.quantity
        for assignment in collection.deck_assignments:
            assigned[assignment.owned_card_id] += assignment.quantity
        assigned_total = sum(min(quantity, owned_by_id.get(identifier, 0))
                             for identifier, quantity in assigned.items())
        total = sum(owned_by_id.values())
        return self._report("inventory_report", {"collection_id": collection.id}, {
            "total_cards": total,
            "assigned_cards": assigned_total,
            "unassigned_cards": total - assigned_total,
            "utilization_ratio": assigned_total / total if total else 0.0,
            "cards_by_location": dict(sorted(by_location.items())),
        })

    def observation_report(self, observations: Iterable[Mapping[str, Any]]) -> AnalyticsReport:
        records = tuple(observations)
        frequency: Counter[str] = Counter()
        finishes: Counter[str] = Counter()
        product_openings: Counter[str] = Counter()
        card_count = 0
        for record in records:
            product_openings[str(record.get("product_id") or "unattributed")] += 1
            for card in record.get("cards", ()):
                identifier = (card.get("canonical_printing_id") or card.get("printing_id") or
                              card.get("reported_name") or "unidentified")
                frequency[str(identifier).strip().casefold()] += 1
                finishes[str(card.get("finish") or card.get("reported_treatment") or "unreported")] += 1
                card_count += 1
        identifiers = sorted(str(item.get("observation_id", "")) for item in records)
        return self._report("observation_report", {"observation_ids": identifiers}, {
            "observation_count": len(records),
            "card_count": card_count,
            "product_openings": dict(sorted(product_openings.items())),
            "finish_distribution": dict(sorted(finishes.items())),
            "card_frequency": self._frequency(frequency),
        })

    @staticmethod
    def _printing_quantities(collection: Collection) -> Counter[str]:
        result: Counter[str] = Counter()
        for card in collection.cards:
            result[card.printing_id] += card.quantity
        return result

    @staticmethod
    def _card_counter(collection: Collection, attribute: str) -> Counter[str]:
        result: Counter[str] = Counter()
        for card in collection.cards:
            result[getattr(card, attribute)] += card.quantity
        return result

    @staticmethod
    def _frequency(counts: Mapping[str, int]) -> list[dict[str, Any]]:
        return [{"id": key, "count": count}
                for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
