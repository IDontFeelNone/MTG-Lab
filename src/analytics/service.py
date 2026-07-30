"""Game-agnostic, side-effect-free analytics computations."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
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
        return self._report("collection_summary", self._collection_inputs(collection), {
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
        return self._report("duplicate_report", self._collection_inputs(collection), {
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
        return self._report("acquisition_report", self._collection_inputs(collection), {
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
        return self._report("inventory_report", self._collection_inputs(collection), {
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
        sources: Counter[str] = Counter()
        statuses: Counter[str] = Counter()
        card_count = 0
        for record in records:
            product_openings[self._product_id(record)] += 1
            observation = record.get("observation", {})
            if isinstance(observation, Mapping):
                sources[str(observation.get("source_type") or "unreported")] += 1
                statuses[str(observation.get("verification_status") or "unreported")] += 1
            for card in record.get("cards", ()):
                identifier = (card.get("canonical_printing_id") or card.get("printing_id") or
                              card.get("reported_name") or "unidentified")
                frequency[str(identifier).strip().casefold()] += 1
                finishes[str(card.get("finish") or card.get("reported_treatment") or "unreported")] += 1
                card_count += 1
        inputs = self._observation_inputs(records)
        return self._report("observation_report", inputs, {
            "observation_count": len(records),
            "card_count": card_count,
            "product_openings": dict(sorted(product_openings.items())),
            "finish_distribution": dict(sorted(finishes.items())),
            "source_distribution": dict(sorted(sources.items())),
            "verification_distribution": dict(sorted(statuses.items())),
            "card_frequency": self._frequency(frequency),
        })

    def distribution_report(self, collection: Collection, canonical: Any | None = None) -> AnalyticsReport:
        """Describe owned-card dimensions, enriched by a canonical snapshot when supplied."""
        language = self._card_counter(collection, "language")
        finish = self._card_counter(collection, "finish")
        rarity: Counter[str] = Counter()
        treatment: Counter[str] = Counter()
        printing_by_id = {item.id: item for item in canonical.printings} if canonical is not None else {}
        for card in collection.cards:
            if canonical is None:
                continue
            if card.printing_id not in printing_by_id:
                raise ValueError(f"collection references unknown canonical printing: {card.printing_id}")
            printing = printing_by_id[card.printing_id]
            rarity[printing.rarity_id or "unreported"] += card.quantity
            values = printing.treatment_ids or ("none",)
            for value in values:
                treatment[value] += card.quantity
        inputs = dict(self._collection_inputs(collection))
        inputs["canonical_game"] = getattr(canonical, "game_id", None)
        return self._report("distribution_report", inputs, {
            "finish": dict(sorted(finish.items())),
            "language": dict(sorted(language.items())),
            "rarity": dict(sorted(rarity.items())),
            "treatment": dict(sorted(treatment.items())),
        })

    def product_report(self, observations: Iterable[Mapping[str, Any]]) -> AnalyticsReport:
        """Summarize recorded product openings without inferring product rules."""
        records = tuple(observations)
        openings: Counter[str] = Counter()
        cards: Counter[str] = Counter()
        for record in records:
            product = self._product_id(record)
            openings[product] += 1
            value = record.get("cards", ())
            if not isinstance(value, (list, tuple)):
                raise ValueError("observation cards must be a sequence")
            cards[product] += len(value)
        items = []
        for product in sorted(openings):
            count = openings[product]
            items.append({"product_id": product, "openings": count, "cards_observed": cards[product],
                          "cards_per_opening": cards[product] / count})
        return self._report("product_report", self._observation_inputs(records), {"products": items})

    @staticmethod
    def _collection_inputs(collection: Collection) -> dict[str, Any]:
        snapshot = {
            "cards": sorted((item.id, item.printing_id, item.quantity, item.acquisition_id,
                             item.location_id, item.finish, item.language) for item in collection.cards),
            "acquisitions": sorted((item.id, item.type, item.acquired_at.isoformat(), item.product_id)
                                   for item in collection.acquisitions),
            "locations": sorted((item.id, item.name, item.kind) for item in collection.locations),
            "assignments": sorted((item.deck_id, item.owned_card_id, item.quantity)
                                  for item in collection.deck_assignments),
        }
        digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        return {"collection_id": collection.id, "collection_sha256": digest}

    @staticmethod
    def _observation_inputs(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        values = sorted((str(item.get("observation_id", "")),
                         hashlib.sha256(json.dumps(item, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest())
                        for item in records)
        return {"observation_ids": [item[0] for item in values], "observation_sha256": [item[1] for item in values]}

    @staticmethod
    def _product_id(record: Mapping[str, Any]) -> str:
        product = record.get("product")
        if isinstance(product, Mapping):
            return str(product.get("slug") or product.get("id") or product.get("name") or "unattributed")
        return str(record.get("product_id") or product or "unattributed")

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
