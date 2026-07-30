"""Manage an offline personal card collection using canonical printing IDs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from collection import (Acquisition, CollectionError, CollectionRepository, CollectionService,
                        InventoryLocation)
from repository.canonical import CanonicalRepository


def _arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", default="magic")
    parser.add_argument("--file", type=Path, default=Path("data/collections/default.json"))
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add")
    add.add_argument("printing_id"); add.add_argument("--quantity", type=int, default=1)
    add.add_argument("--finish", default="nonfoil"); add.add_argument("--condition", default="near_mint")
    add.add_argument("--language", default="en"); add.add_argument("--observation")
    add.add_argument("--acquisition", choices=("pack_opening", "single_purchase", "trade", "gift", "manual_entry"), default="manual_entry")
    add.add_argument("--product"); add.add_argument("--location", default="unknown")
    move = commands.add_parser("move"); move.add_argument("card_id"); move.add_argument("location")
    move.add_argument("--quantity", type=int)
    commands.add_parser("summary")
    imp = commands.add_parser("import"); imp.add_argument("path", type=Path,
        help="JSON array of objects accepted by the add command")
    return parser


def main(argv=None) -> int:
    parser = _arguments(); args = parser.parse_args(argv)
    repository = CollectionRepository(args.file)
    try:
        collection = repository.load()
        service = CollectionService(CanonicalRepository(args.game))
        if args.command == "summary":
            output = service.summary(collection)
        elif args.command == "move":
            location = InventoryLocation(args.location, args.location.replace("_", " ").title(), args.location)
            collection = service.move(collection, args.card_id, location, args.quantity)
            repository.save(collection); output = service.summary(collection)
        else:
            records = json.loads(args.path.read_text(encoding="utf-8")) if args.command == "import" else [vars(args)]
            if not isinstance(records, list):
                raise CollectionError("import document must be a JSON array")
            for record in records:
                location_id = record.get("location", "unknown")
                location = InventoryLocation(location_id, location_id.replace("_", " ").title(), location_id)
                identifier = service.id_factory()
                acquisition = Acquisition(identifier, record.get("acquisition", "manual_entry"),
                                          datetime.now(timezone.utc), record.get("product"))
                collection = service.add(collection, record["printing_id"], int(record.get("quantity", 1)),
                    acquisition, location, finish=record.get("finish", "nonfoil"),
                    condition=record.get("condition", "near_mint"), language=record.get("language", "en"),
                    observation_id=record.get("observation"))
            repository.save(collection); output = service.summary(collection)
    except (CollectionError, KeyError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
