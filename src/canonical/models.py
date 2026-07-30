"""Immutable, game-agnostic records used by the canonical repository.

The models deliberately contain no observation, price, analytics, or simulation
state.  JSON remains the interchange format; these types are the stable boundary
presented to callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


def _required(data: Mapping[str, Any], *names: str) -> None:
    missing = sorted(name for name in names if name not in data)
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    for name in names:
        if isinstance(data[name], str) and not data[name].strip():
            raise ValueError(f"required field {name} must not be empty")


@dataclass(frozen=True)
class Entity:
    id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Game(Entity):
    name: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Game":
        _required(data, "id", "name")
        return cls(str(data["id"]), dict(data.get("metadata", {})), str(data["name"]))


@dataclass(frozen=True)
class Product(Entity):
    game_id: str = ""
    name: str = ""
    product_type: str = ""
    version_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProductVersion(Entity):
    product_id: str = ""
    name: str = ""
    pack_definition_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Card(Entity):
    game_id: str = ""
    name: str = ""


@dataclass(frozen=True)
class Printing(Entity):
    card_id: str = ""
    rarity_id: str = ""
    treatment_ids: tuple[str, ...] = ()
    finish_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Treatment(Entity):
    game_id: str = ""
    name: str = ""


@dataclass(frozen=True)
class Finish(Entity):
    game_id: str = ""
    name: str = ""


@dataclass(frozen=True)
class Rarity(Entity):
    game_id: str = ""
    name: str = ""


@dataclass(frozen=True)
class PackDefinition(Entity):
    product_version_id: str = ""
    name: str = ""
    slot_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PackSlot(Entity):
    name: str = ""
    sheet_id: str = ""
    count: int = 1


@dataclass(frozen=True)
class SheetEntry:
    printing_id: str
    weight: int = 1


@dataclass(frozen=True)
class Sheet(Entity):
    name: str = ""
    entries: tuple[SheetEntry, ...] = ()
