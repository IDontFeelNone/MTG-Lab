"""Explainable, read-only intelligence queries over canonical facts."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Mapping

from .engine import CanonicalQueryEngine, QueryError, QueryResult, normalize_name


@dataclass(frozen=True)
class CanonicalAnswer:
    """Uniform answer contract.  Empty answers are successful, explicit unknowns."""

    query: Mapping[str, Any]
    answer: Any
    provenance: tuple[Mapping[str, Any], ...]
    confidence: float | None
    canonical_identifiers: tuple[str, ...]
    snapshot_identity: str
    status: str = "known"

    def as_dict(self) -> dict[str, Any]:
        return {"schema_version": "canonical-query-v1", "query": dict(self.query),
                "answer": self.answer, "provenance": list(self.provenance),
                "confidence": self.confidence,
                "canonical_identifiers": list(self.canonical_identifiers),
                "snapshot_identity": self.snapshot_identity, "status": self.status}


class CanonicalQueryService:
    """Generic exact-match query layer; it never guesses or reads provider APIs."""

    CARD_FILTERS = {"name", "type", "color", "rarity", "set", "mana_value",
                    "keyword", "legality", "identifier"}

    def __init__(self, engine: CanonicalQueryEngine, market_repository=None):
        self.engine = engine
        snapshot = engine.snapshot()
        self.snapshot_identity = snapshot.snapshot_id
        self.entities = snapshot.entities
        self.market_repository = market_repository

    def _market(self):
        if self.market_repository is None:
            raise QueryError("market observation repository is not configured")
        from market.query import MarketQueryService
        return MarketQueryService(self, self.market_repository)

    def card_market(self, identifier: str, *, provider: str | None = None) -> Mapping[str, Any]:
        return self._market().card(identifier, provider=provider)

    def printing_market(self, identifier: str, *, provider: str | None = None) -> Mapping[str, Any]:
        return self._market().printing(identifier, provider=provider)

    def product_market(self, identifier: str, *, provider: str | None = None) -> Mapping[str, Any]:
        return self._market().product(identifier, provider=provider)

    def market_history(self, entity_type: str, identifier: str, *, provider: str | None = None) -> Mapping[str, Any]:
        return self._market().history(entity_type, identifier, provider=provider)

    def market_provider_comparison(self, entity_type: str, identifier: str) -> Mapping[str, Any]:
        return self._market().provider_comparison(entity_type, identifier)

    def cards(self, **filters: Any) -> CanonicalAnswer:
        supplied = {key: value for key, value in filters.items() if value is not None}
        invalid = sorted(set(supplied) - self.CARD_FILTERS)
        if invalid or not supplied or any(isinstance(v, str) and not v.strip() for v in supplied.values()):
            raise QueryError("card query requires non-empty supported filters")
        cards = [x for x in self.entities if x.entity_type == "card"]
        printings = [x for x in self.entities if x.entity_type == "printing"]
        identifiers = [x for x in self.entities if x.entity_type == "identifier"]
        printing_by_card: dict[str, list[QueryResult]] = {}
        for printing in printings:
            printing_by_card.setdefault(str(printing.canonical_values.get("card_id")), []).append(printing)
        for key, wanted in supplied.items():
            text = str(wanted)
            if key == "name":
                cards = [x for x in cards if normalize_name(str(x.canonical_values.get("name", ""))) == normalize_name(text)]
            elif key == "identifier":
                printing_ids = {x.canonical_identity for x in printings if
                    x.canonical_identity == text or text in self._identifier_values(x)}
                printing_ids.update(str(x.canonical_values.get("printing_uuid")) for x in identifiers
                    if x.canonical_identity == text or str(x.canonical_values.get("value")) == text)
                cards = [x for x in cards if x.canonical_identity == text or any(
                    p.canonical_identity in printing_ids or str(p.canonical_values.get("uuid")) in printing_ids
                    for p in printing_by_card.get(x.canonical_identity, []))]
            elif key in {"rarity", "set"}:
                field = "set_id" if key == "set" else "rarity"
                cards = [x for x in cards if any(str(p.canonical_values.get(field, "")).casefold() == text.casefold()
                    for p in printing_by_card.get(x.canonical_identity, []))]
            else:
                # Only promoted values participate. Values retained under unknown_values
                # are deliberately invisible to this query boundary.
                field = {"mana_value": "mana_value", "type": "type", "color": "colors",
                         "keyword": "keywords", "legality": "legalities"}[key]
                cards = [x for x in cards if self._matches(x.canonical_values.get(field), text)]
        return self._answer({"entity": "card", **supplied}, cards)

    def printing(self, identifier: str) -> CanonicalAnswer:
        if not identifier.strip(): raise QueryError("printing identifier must not be empty")
        matches = [x for x in self.entities if x.entity_type == "printing" and
                   (x.canonical_identity == identifier or identifier in self._identifier_values(x))]
        return self._answer({"entity": "printing", "identifier": identifier}, matches)

    def printings_for_card(self, identifier: str) -> CanonicalAnswer:
        card = self.cards(identifier=identifier)
        card_ids = set(card.canonical_identifiers)
        matches = [x for x in self.entities if x.entity_type == "printing" and
                   str(x.canonical_values.get("card_id")) in card_ids]
        return self._answer({"entity": "printing", "card_identifier": identifier}, matches)

    def product(self, identifier: str) -> CanonicalAnswer:
        if not identifier.strip(): raise QueryError("product identifier must not be empty")
        products = [x for x in self.entities if x.entity_type == "product" and x.canonical_identity == identifier]
        if not products: return self._answer({"entity": "product", "identifier": identifier}, [])
        product = products[0]
        printings = [x for x in self.entities if x.entity_type == "printing" and
                     identifier in x.canonical_values.get("metadata", {}).get("product_membership", [])]
        card_ids = sorted({str(x.canonical_values.get("card_id")) for x in printings})
        answer = {"product": product.as_dict(), "promoted_status": bool(product.provenance_summary.get("promotion_history")),
                  "validation_status": product.canonical_values.get("lifecycle_status", "unknown"),
                  "printings": [x.as_dict() for x in printings], "cards": card_ids,
                  "statistics": {"printing_count": len(printings), "card_count": len(card_ids)}}
        return self._answer({"entity": "product", "identifier": identifier}, products + printings, answer)

    def collection(self, snapshot: Mapping[str, Any], operation: str) -> CanonicalAnswer:
        if operation not in {"owned", "duplicates", "missing", "unique", "unresolved", "acquisitions"}:
            raise QueryError("unsupported collection query")
        holdings = snapshot.get("resolved_holdings", [])
        quantities = Counter(x["printing_id"] for x in holdings for _ in range(int(x["row"]["quantity"])))
        owned_cards = Counter(x["card_id"] for x in holdings for _ in range(int(x["row"]["quantity"])))
        if operation == "owned": answer = sorted(({"printing_id": k, "quantity": v} for k,v in quantities.items()), key=lambda x:x["printing_id"])
        elif operation == "duplicates": answer = [{"printing_id":k,"quantity":v,"duplicate_copies":v-1} for k,v in sorted(quantities.items()) if v>1]
        elif operation == "missing": answer = sorted(x.canonical_identity for x in self.entities if x.entity_type=="card" and x.canonical_identity not in owned_cards)
        elif operation == "unique": answer = {"cards":sorted(owned_cards), "printings":sorted(quantities)}
        elif operation == "unresolved": answer = snapshot.get("unresolved_holdings", [])
        else: answer = [{"printing_id":x["printing_id"], "quantity":x["row"]["quantity"],
                          "acquisition_price":x["row"].get("acquisition_price"),
                          "acquisition_date":x["row"].get("acquisition_date"),
                          "provenance":x["row"].get("provenance")} for x in holdings]
        ids = sorted(set(owned_cards) | set(quantities))
        return CanonicalAnswer({"collection": operation}, answer,
            ({"snapshot_id": snapshot.get("snapshot_id"), "snapshot_digest": snapshot.get("snapshot_digest")},),
            1.0, tuple(ids), self.snapshot_identity,
            "known" if answer else "not_found")

    def _answer(self, query: Mapping[str, Any], matches: list[QueryResult], answer: Any = None) -> CanonicalAnswer:
        matches.sort(key=lambda x: x.canonical_identity)
        confidences = [x.confidence for x in matches if x.confidence is not None]
        rendered = [self._render(x) for x in matches]
        return CanonicalAnswer(query, rendered if answer is None else answer,
            tuple({"canonical_identity":x.canonical_identity, **dict(x.provenance_summary)} for x in matches),
            min(confidences) if confidences else None, tuple(x.canonical_identity for x in matches),
            self.snapshot_identity, "known" if matches else "not_found")

    @staticmethod
    def _render(item: QueryResult) -> dict[str, Any]:
        rendered = item.as_dict()
        if item.entity_type == "printing":
            values = rendered["canonical_values"]
            values["finish"] = values.get("finish_ids")
            values["rarity"] = values.get("rarity", values.get("rarity_id"))
            values["product"] = values.get("metadata", {}).get("product_membership")
            # Explicit nulls communicate that the canonical contract has no fact.
            values.setdefault("release", None)
            values.setdefault("identifiers", {})
        return rendered

    @staticmethod
    def _identifier_values(item: QueryResult) -> set[str]:
        values = item.canonical_values.get("identifiers", {})
        return {str(x) for x in values.values()} if isinstance(values, Mapping) else set()

    @staticmethod
    def _matches(value: Any, wanted: str) -> bool:
        if isinstance(value, Mapping): return wanted.casefold() in {str(k).casefold() for k,v in value.items() if v}
        if isinstance(value, (list, tuple)): return wanted.casefold() in {str(x).casefold() for x in value}
        return value is not None and str(value).casefold() == wanted.casefold()
