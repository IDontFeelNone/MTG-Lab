"""JSON persistence for collection aggregate snapshots."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import Acquisition, Collection, DeckAssignment, InventoryLocation, OwnedCard, thaw


class CollectionRepository:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> Collection:
        if not self.path.exists():
            return Collection("default")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != "collection-v1":
            raise ValueError("unsupported collection schema")
        acquisitions = tuple(Acquisition(acquired_at=datetime.fromisoformat(
            item["acquired_at"].replace("Z", "+00:00")), **{k: v for k, v in item.items()
            if k != "acquired_at"}) for item in data.get("acquisitions", ()))
        return Collection(data["id"], tuple(OwnedCard(**item) for item in data.get("cards", ())),
                          acquisitions, tuple(InventoryLocation(**item) for item in data.get("locations", ())),
                          tuple(DeckAssignment(**item) for item in data.get("deck_assignments", ())))

    def save(self, collection: Collection) -> None:
        payload = {"schema_version": "collection-v1", "id": collection.id,
                   "cards": [vars(item) for item in sorted(collection.cards, key=lambda item: item.id)],
                   "locations": [vars(item) for item in sorted(collection.locations, key=lambda item: item.id)],
                   "deck_assignments": [vars(item) for item in collection.deck_assignments],
                   "acquisitions": [{"id": item.id, "type": item.type,
                                     "acquired_at": item.acquired_at.isoformat().replace("+00:00", "Z"),
                                     "product_id": item.product_id, "metadata": thaw(item.metadata)}
                                    for item in sorted(collection.acquisitions, key=lambda item: item.id)]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)
