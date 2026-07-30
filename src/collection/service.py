"""Pure collection operations and deterministic inventory analytics."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import Callable
from uuid import uuid4

from .models import Acquisition, Collection, CollectionError, InventoryLocation, OwnedCard


class CollectionService:
    def __init__(self, canonical_repository, id_factory: Callable[[], str] | None = None):
        self.canonical = canonical_repository
        self.id_factory = id_factory or (lambda: uuid4().hex)

    def _printing(self, printing_id: str) -> None:
        try:
            self.canonical.get_printing(printing_id)
        except KeyError as error:
            raise CollectionError(f"unknown canonical printing: {printing_id}") from error

    def add(self, collection: Collection, printing_id: str, quantity: int,
            acquisition: Acquisition, location: InventoryLocation, **attributes) -> Collection:
        self._printing(printing_id)
        card = OwnedCard(self.id_factory(), printing_id, acquisition.id, location.id,
                         quantity=quantity, **attributes)
        acquisitions = collection.acquisitions
        existing_acquisition = next((a for a in acquisitions if a.id == acquisition.id), None)
        if existing_acquisition and existing_acquisition != acquisition:
            raise CollectionError(f"acquisition id already has different data: {acquisition.id}")
        if not existing_acquisition:
            acquisitions += (acquisition,)
        locations = collection.locations
        existing_location = next((item for item in locations if item.id == location.id), None)
        if existing_location and existing_location != location:
            raise CollectionError(f"location id already has different data: {location.id}")
        if not existing_location:
            locations += (location,)
        return replace(collection, cards=collection.cards + (card,), acquisitions=acquisitions,
                       locations=locations)

    def remove(self, collection: Collection, card_id: str, quantity: int | None = None) -> Collection:
        card = self._card(collection, card_id)
        amount = card.quantity if quantity is None else quantity
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 1 or amount > card.quantity:
            raise CollectionError("remove quantity must be positive and no greater than owned quantity")
        cards = tuple(item for item in collection.cards if item.id != card_id)
        if amount < card.quantity:
            cards += (card.with_quantity(card.quantity - amount),)
        return replace(collection, cards=cards)

    def move(self, collection: Collection, card_id: str, location: InventoryLocation,
             quantity: int | None = None) -> Collection:
        card = self._card(collection, card_id)
        amount = card.quantity if quantity is None else quantity
        if not isinstance(amount, int) or isinstance(amount, bool) or not 1 <= amount <= card.quantity:
            raise CollectionError("move quantity must be positive and no greater than owned quantity")
        locations = collection.locations
        known = next((item for item in locations if item.id == location.id), None)
        if known and known != location:
            raise CollectionError(f"location id already has different data: {location.id}")
        if not known:
            locations += (location,)
        cards = tuple(item for item in collection.cards if item.id != card_id)
        if amount < card.quantity:
            cards += (card.with_quantity(card.quantity - amount),)
        cards += (replace(card, id=self.id_factory() if amount < card.quantity else card.id,
                          quantity=amount, location_id=location.id),)
        return replace(collection, cards=cards, locations=locations)

    def split(self, collection: Collection, card_id: str, quantity: int) -> Collection:
        card = self._card(collection, card_id)
        if not isinstance(quantity, int) or isinstance(quantity, bool) or not 1 <= quantity < card.quantity:
            raise CollectionError("split quantity must be less than owned quantity")
        cards = tuple(item for item in collection.cards if item.id != card_id)
        cards += (card.with_quantity(card.quantity - quantity),
                  replace(card, id=self.id_factory(), quantity=quantity))
        return replace(collection, cards=cards)

    def merge(self, collection: Collection, card_ids: tuple[str, ...]) -> Collection:
        if len(set(card_ids)) < 2:
            raise CollectionError("merge requires at least two different cards")
        cards = [self._card(collection, identifier) for identifier in card_ids]
        comparable = lambda card: (card.printing_id, card.acquisition_id, card.location_id,
                                   card.observation_id, card.condition, card.language, card.finish)
        if len({comparable(card) for card in cards}) != 1:
            raise CollectionError("only cards with identical ownership attributes can be merged")
        merged = cards[0].with_quantity(sum(card.quantity for card in cards))
        remaining = tuple(card for card in collection.cards if card.id not in set(card_ids))
        return replace(collection, cards=remaining + (merged,))

    @staticmethod
    def _card(collection: Collection, card_id: str) -> OwnedCard:
        try:
            return next(card for card in collection.cards if card.id == card_id)
        except StopIteration as error:
            raise CollectionError(f"unknown owned card: {card_id}") from error

    @staticmethod
    def owned(collection: Collection, printing_id: str) -> tuple[OwnedCard, ...]:
        return tuple(sorted((card for card in collection.cards if card.printing_id == printing_id),
                            key=lambda card: card.id))

    @staticmethod
    def summary(collection: Collection) -> dict:
        quantities = Counter()
        finish = Counter()
        acquisition = Counter()
        locations = Counter()
        acquisition_by_id = {item.id: item.type for item in collection.acquisitions}
        location_by_id = {item.id: item.name for item in collection.locations}
        for card in collection.cards:
            quantities[card.printing_id] += card.quantity
            finish[card.finish] += card.quantity
            acquisition[acquisition_by_id[card.acquisition_id]] += card.quantity
            locations[location_by_id[card.location_id]] += card.quantity
        return {"total_cards": sum(quantities.values()), "unique_printings": len(quantities),
                "duplicate_count": sum(max(0, number - 1) for number in quantities.values()),
                "finish_breakdown": dict(sorted(finish.items())),
                "acquisition_breakdown": dict(sorted(acquisition.items())),
                "inventory_locations": dict(sorted(locations.items()))}
