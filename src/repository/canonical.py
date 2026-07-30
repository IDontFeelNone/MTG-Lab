"""Read-only, deterministic access to Canonical Product Repository v1."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from canonical import (Card, Finish, Game, PackDefinition, PackSlot, Printing,
                       Product, ProductVersion, Rarity, Sheet, SheetEntry, Treatment)
from repository.cards import load_card_repository
from repository.products import load_product

_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data/canonical/games"


class CanonicalRepositoryError(ValueError):
    """Canonical data is malformed or has inconsistent relationships."""


class CanonicalRepository:
    """Validated in-memory view; this service never writes canonical files."""

    def __init__(self, game: str, *, games_root: Path | None = None):
        if not _ID.fullmatch(game):
            raise CanonicalRepositoryError("game must be a stable lowercase identifier")
        self.game_id = game
        self.root = Path(games_root) if games_root is not None else _DEFAULT_ROOT
        self.game = self._load_game()
        self.cards, self.printings = self._load_cards()
        self.products = self._load_products()
        self.product_versions = self._load("product_versions", ProductVersion)
        self.treatments = self._load("treatments", Treatment)
        self.finishes = self._load("finishes", Finish)
        self.rarities = self._load("rarities", Rarity)
        self.pack_definitions = self._load("packs", PackDefinition)
        self.pack_slots = self._load("slots", PackSlot)
        self.sheets = self._load("sheets", Sheet)
        self._validate_relationships()

    def get_card(self, identifier: str) -> Card:
        return self._get(self.cards, "Card", identifier)

    def get_printing(self, identifier: str) -> Printing:
        return self._get(self.printings, "Printing", identifier)

    def get_product(self, identifier: str) -> Product:
        return self._get(self.products, "Product", identifier)

    def get_pack_definition(self, identifier: str) -> PackDefinition:
        return self._get(self.pack_definitions, "PackDefinition", identifier)

    def _load_game(self) -> Game:
        path = self.root / self.game_id / "game.json"
        if not path.exists():
            return Game(self.game_id, {}, self.game_id.replace("_", " ").title())
        data = self._read(path)
        try:
            game = Game.from_dict(data)
        except (TypeError, ValueError) as error:
            raise CanonicalRepositoryError(f"Invalid Game {path}: {error}") from error
        if game.id != self.game_id:
            raise CanonicalRepositoryError(f"Game identifier does not match path: {path}")
        return game

    def _load_cards(self) -> tuple[tuple[Card, ...], tuple[Printing, ...]]:
        try:
            cards, printings = load_card_repository(self.game_id, games_root=self.root)
        except ValueError as error:
            raise CanonicalRepositoryError(str(error)) from error
        return (
            tuple(Card(str(x["id"]), dict(x.get("metadata", {})), str(x["game"]), str(x["name"])) for x in cards),
            tuple(Printing(str(x["id"]), dict(x.get("metadata", {})), str(x["card_id"]),
                           str(x["rarity"]), tuple(map(str, x.get("treatments", ()))),
                           tuple(map(str, x.get("finishes", ())))) for x in printings),
        )

    def _load_products(self) -> tuple[Product, ...]:
        result = []
        for path in sorted((self.root / self.game_id / "products").glob("*/product.json")):
            try:
                item = load_product(self.game_id, path.parent.name, games_root=self.root)
            except ValueError as error:
                raise CanonicalRepositoryError(str(error)) from error
            result.append(Product(str(item["id"]), {}, str(item["game"]), str(item["name"]),
                                  str(item["product_type"]), tuple(map(str, item.get("version_ids", ())))))
        return self._unique(result, "Product")

    def _load(self, directory: str, model: type) -> tuple:
        records = []
        for path in sorted((self.root / self.game_id / directory).glob("*.json")):
            data = self._read(path)
            try:
                records.append(self._construct(model, data))
            except (KeyError, TypeError, ValueError) as error:
                raise CanonicalRepositoryError(f"Invalid {model.__name__} {path}: {error}") from error
        return self._unique(records, model.__name__)

    @staticmethod
    def _construct(model: type, data: Mapping[str, Any]):
        required = {
            ProductVersion: ("id", "product_id", "name", "pack_definition_ids"),
            Treatment: ("id", "game_id", "name"), Finish: ("id", "game_id", "name"),
            Rarity: ("id", "game_id", "name"),
            PackDefinition: ("id", "product_version_id", "name", "slot_ids"),
            PackSlot: ("id", "name", "sheet_id", "count"),
            Sheet: ("id", "name", "entries"),
        }[model]
        missing = sorted(key for key in required if key not in data)
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        meta = dict(data.get("metadata", {}))
        if model is Sheet:
            entries = tuple(SheetEntry(str(x["printing_id"]), int(x.get("weight", 1))) for x in data["entries"])
            if not entries or any(x.weight < 1 for x in entries):
                raise ValueError("entries must be non-empty with positive weights")
            return Sheet(str(data["id"]), meta, str(data["name"]), entries)
        if model is PackSlot:
            count = int(data["count"])
            if count < 1: raise ValueError("count must be positive")
            return PackSlot(str(data["id"]), meta, str(data["name"]), str(data["sheet_id"]), count)
        values = [str(data[key]) for key in required]
        for index, key in enumerate(required):
            if key.endswith("_ids"): values[index] = tuple(map(str, data[key]))
        return model(values[0], meta, *values[1:])

    def _validate_relationships(self) -> None:
        for label, records in (("Treatment", self.treatments), ("Finish", self.finishes),
                               ("Rarity", self.rarities)):
            for record in records:
                if record.game_id != self.game_id:
                    raise CanonicalRepositoryError(
                        f"{label} {record.id} references missing Game {record.game_id}"
                    )
        self._refs(self.printings, "card_id", self.cards, "Printing", "Card")
        self._refs(self.product_versions, "product_id", self.products, "ProductVersion", "Product")
        self._refs_many(self.products, "version_ids", self.product_versions, "Product", "ProductVersion")
        self._refs_many(self.product_versions, "pack_definition_ids", self.pack_definitions, "ProductVersion", "PackDefinition")
        self._refs_many(self.pack_definitions, "slot_ids", self.pack_slots, "PackDefinition", "PackSlot")
        self._refs(self.pack_slots, "sheet_id", self.sheets, "PackSlot", "Sheet")
        if self.rarities:
            self._refs(self.printings, "rarity_id", self.rarities, "Printing", "Rarity")
        if self.treatments:
            self._refs_many(self.printings, "treatment_ids", self.treatments,
                            "Printing", "Treatment")
        if self.finishes:
            self._refs_many(self.printings, "finish_ids", self.finishes, "Printing", "Finish")
        ids = {x.id for x in self.printings}
        for sheet in self.sheets:
            for entry in sheet.entries:
                if entry.printing_id not in ids:
                    raise CanonicalRepositoryError(f"Sheet {sheet.id} references missing Printing {entry.printing_id}")

    @staticmethod
    def _read(path: Path) -> Mapping[str, Any]:
        try: data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error: raise CanonicalRepositoryError(f"Invalid JSON: {path}") from error
        if not isinstance(data, dict): raise CanonicalRepositoryError(f"Canonical record must be an object: {path}")
        return data

    @staticmethod
    def _unique(items: Iterable, label: str) -> tuple:
        values = tuple(items); seen = set()
        for item in values:
            if not _ID.fullmatch(item.id): raise CanonicalRepositoryError(f"Invalid {label} identifier: {item.id}")
            if item.id in seen: raise CanonicalRepositoryError(f"Duplicate {label} identifier: {item.id}")
            seen.add(item.id)
        return values

    @staticmethod
    def _get(items: Iterable, label: str, identifier: str):
        for item in items:
            if item.id == identifier: return item
        raise KeyError(f"{label} not found: {identifier}")

    def _refs(self, sources, attr, targets, source_label, target_label):
        ids = {x.id for x in targets}
        for source in sources:
            value = getattr(source, attr)
            if value not in ids: raise CanonicalRepositoryError(f"{source_label} {source.id} references missing {target_label} {value}")

    def _refs_many(self, sources, attr, targets, source_label, target_label):
        ids = {x.id for x in targets}
        for source in sources:
            for value in getattr(source, attr):
                if value not in ids: raise CanonicalRepositoryError(f"{source_label} {source.id} references missing {target_label} {value}")


def load_canonical_repository(game: str, *, games_root: Path | None = None) -> CanonicalRepository:
    return CanonicalRepository(game, games_root=games_root)


__all__ = ["CanonicalRepository", "CanonicalRepositoryError", "load_canonical_repository"]
