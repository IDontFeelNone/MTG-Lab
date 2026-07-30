"""Immutable domain values for owned card inventory."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


class CollectionError(ValueError):
    """A collection operation or value is invalid."""


def _text(value: str, label: str) -> str:
    value = str(value).strip()
    if not value:
        raise CollectionError(f"{label} is required")
    return value


def _metadata(value: Mapping[str, Any]) -> Mapping[str, Any]:
    def freeze(item: Any) -> Any:
        if isinstance(item, Mapping):
            return MappingProxyType({str(k): freeze(v) for k, v in item.items()})
        if isinstance(item, (list, tuple)):
            return tuple(freeze(v) for v in item)
        if isinstance(item, (str, int, float, bool, type(None))):
            return item
        raise CollectionError(f"unsupported metadata value: {type(item).__name__}")
    return freeze(value)


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class Acquisition:
    id: str
    type: str
    acquired_at: datetime
    product_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "acquisition id"))
        kind = _text(self.type, "acquisition type").lower().replace(" ", "_")
        if kind not in {"pack_opening", "single_purchase", "trade", "gift", "manual_entry"}:
            raise CollectionError(f"unsupported acquisition type: {kind}")
        object.__setattr__(self, "type", kind)
        if not isinstance(self.acquired_at, datetime) or self.acquired_at.tzinfo is None:
            raise CollectionError("acquired_at must be timezone-aware")
        object.__setattr__(self, "acquired_at", self.acquired_at.astimezone(timezone.utc))
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True)
class InventoryLocation:
    id: str
    name: str
    kind: str = "unknown"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "location id"))
        object.__setattr__(self, "name", _text(self.name, "location name"))
        object.__setattr__(self, "kind", _text(self.kind, "location kind").lower().replace(" ", "_"))


@dataclass(frozen=True)
class DeckAssignment:
    """Reserved ownership allocation; deck rules are deliberately out of scope."""
    deck_id: str
    owned_card_id: str
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise CollectionError("deck assignment quantity must be positive")


@dataclass(frozen=True)
class OwnedCard:
    id: str
    printing_id: str
    acquisition_id: str
    location_id: str
    quantity: int = 1
    observation_id: str | None = None
    condition: str = "near_mint"
    language: str = "en"
    finish: str = "nonfoil"

    def __post_init__(self) -> None:
        for field_name in ("id", "printing_id", "acquisition_id", "location_id", "condition", "language", "finish"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int) or self.quantity < 1:
            raise CollectionError("quantity must be a positive integer")

    def with_quantity(self, quantity: int) -> "OwnedCard":
        return replace(self, quantity=quantity)


@dataclass(frozen=True)
class Collection:
    id: str
    cards: tuple[OwnedCard, ...] = ()
    acquisitions: tuple[Acquisition, ...] = ()
    locations: tuple[InventoryLocation, ...] = ()
    deck_assignments: tuple[DeckAssignment, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id, "collection id"))
        for values, label in ((self.cards, "card"), (self.acquisitions, "acquisition"), (self.locations, "location")):
            identifiers = [item.id for item in values]
            if len(identifiers) != len(set(identifiers)):
                raise CollectionError(f"duplicate {label} id")
        acquisition_ids = {item.id for item in self.acquisitions}
        location_ids = {item.id for item in self.locations}
        for card in self.cards:
            if card.acquisition_id not in acquisition_ids:
                raise CollectionError(f"unknown acquisition: {card.acquisition_id}")
            if card.location_id not in location_ids:
                raise CollectionError(f"unknown location: {card.location_id}")
