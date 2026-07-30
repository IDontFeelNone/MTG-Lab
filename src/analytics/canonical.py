"""Deterministic analytics over Canonical Query Engine results."""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from query import CanonicalQueryEngine, QueryResult, QuerySnapshot

from .models import CanonicalAnalyticsResult

UNKNOWN = {"", "unknown", "unresolved", "not_known", "none", "null"}


def _distribution(values: Iterable[Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for value in values:
        items = value if isinstance(value, (list, tuple)) else (value,)
        for item in items:
            key = "unknown" if item is None or str(item).casefold() in UNKNOWN else str(item)
            counts[key] += 1
    return dict(sorted(counts.items()))


def _unknowns(value: Any) -> int:
    if isinstance(value, Mapping):
        return sum(_unknowns(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return sum(_unknowns(item) for item in value)
    return int(value is None or (isinstance(value, str) and value.casefold() in UNKNOWN))


class CanonicalAnalyticsEngine:
    """Read-only aggregation facade whose sole input is a query snapshot."""

    def __init__(self, query: CanonicalQueryEngine) -> None:
        self._query = query

    @staticmethod
    def _result(kind: str, snapshot: QuerySnapshot, data: Mapping[str, Any]) -> CanonicalAnalyticsResult:
        provenance = {item.canonical_identity: item.provenance_summary
                      for item in sorted(snapshot.entities, key=lambda value: value.canonical_identity)}
        return CanonicalAnalyticsResult(kind, snapshot.snapshot_id, snapshot.game, data,
                                        provenance)

    def summary(self) -> CanonicalAnalyticsResult:
        snapshot = self._query.snapshot()
        entities = snapshot.entities
        types = Counter(item.entity_type for item in entities)
        printings = tuple(item for item in entities if item.entity_type == "printing")
        cards = tuple(item for item in entities if item.entity_type == "card")
        data = {
            "entity_counts_by_type": dict(sorted(types.items())),
            "cards_per_set": self._cards_per_set(printings),
            "printings_per_card": dict(sorted(Counter(str(x.canonical_values.get("card_id", "unknown")) for x in printings).items())),
            "printings_per_set": dict(sorted(Counter(str(x.canonical_values.get("set_id", "unknown")) for x in printings).items())),
            "rarity_distribution": _distribution(x.canonical_values.get("rarity_id") for x in printings),
            "color_distribution": _distribution(x.canonical_values.get("colors", x.canonical_values.get("color_identity")) for x in cards),
            "layout_distribution": _distribution(x.canonical_values.get("layout") for x in cards),
            "language_distribution": _distribution(x.canonical_values.get("language") for x in printings),
            "finish_distribution": _distribution(x.canonical_values.get("finishes") for x in printings),
            "unknown_value_counts": dict(sorted((kind, sum(_unknowns(x.canonical_values) for x in entities if x.entity_type == kind)) for kind in types)),
        }
        data.update(self._quality(entities))
        return self._result("summary", snapshot, data)

    def entity(self) -> CanonicalAnalyticsResult:
        snapshot = self._query.snapshot()
        types = sorted({x.entity_type for x in snapshot.entities})
        data = {kind: {"count": sum(x.entity_type == kind for x in snapshot.entities),
                       "unknown_values": sum(_unknowns(x.canonical_values) for x in snapshot.entities if x.entity_type == kind)}
                for kind in types}
        return self._result("entity", snapshot, data)

    def dataset(self) -> CanonicalAnalyticsResult:
        snapshot = self._query.snapshot()
        grouped: dict[str, set[str]] = {}
        uncovered = 0
        for item in snapshot.entities:
            ids = self._dataset_ids(item.provenance_summary.get("dataset_identity"))
            if not ids: uncovered += 1
            for identifier in ids:
                grouped.setdefault(identifier, set()).add(item.canonical_identity)
        return self._result("dataset", snapshot, {"datasets": {key: len(grouped[key]) for key in sorted(grouped)},
            "covered_entities": len(snapshot.entities) - uncovered, "uncovered_entities": uncovered,
            "total_entities": len(snapshot.entities)})

    def validation(self) -> CanonicalAnalyticsResult:
        snapshot = self._query.snapshot()
        data = {state: len(self._query.validation(state)) for state in
                ("conflicting", "rejected", "superseded", "unknown", "unresolved", "validation_failure")}
        return self._result("validation", snapshot, data)

    def provenance(self) -> CanonicalAnalyticsResult:
        snapshot = self._query.snapshot()
        return self._result("provenance", snapshot, self._quality(snapshot.entities)["provenance_coverage"])

    @staticmethod
    def _cards_per_set(printings: Iterable[QueryResult]) -> dict[str, int]:
        grouped: dict[str, set[str]] = {}
        for item in printings:
            grouped.setdefault(str(item.canonical_values.get("set_id", "unknown")), set()).add(str(item.canonical_values.get("card_id", "unknown")))
        return {key: len(grouped[key]) for key in sorted(grouped)}

    @staticmethod
    def _dataset_ids(value: Any) -> tuple[str, ...]:
        found: set[str] = set()
        def walk(item: Any) -> None:
            if isinstance(item, Mapping):
                if item.get("dataset_id"): found.add(str(item["dataset_id"]))
                for child in item.values(): walk(child)
            elif isinstance(item, (list, tuple)):
                for child in item: walk(child)
            elif item: found.add(str(item))
        walk(value)
        return tuple(sorted(found))

    @staticmethod
    def _quality(entities: Iterable[QueryResult]) -> dict[str, Any]:
        values = tuple(entities)
        with_sources = sum(bool(x.provenance_summary.get("source_ids")) for x in values)
        with_assertions = sum(bool(x.provenance_summary.get("evidence_assertions")) for x in values)
        return {"confidence_distribution": _distribution(x.confidence for x in values),
            "provenance_coverage": {"total_entities": len(values), "with_sources": with_sources,
                "without_sources": len(values) - with_sources, "with_evidence_assertions": with_assertions,
                "without_evidence_assertions": len(values) - with_assertions},
            "supersession_statistics": _distribution(x.supersession_state for x in values),
            "validation_state_statistics": _distribution(x.uncertainty for x in values)}
