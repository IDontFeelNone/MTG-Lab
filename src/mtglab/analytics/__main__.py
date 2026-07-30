"""Compute deterministic analytics reports from local snapshot files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from analytics import AnalyticsService
from collection import CollectionRepository


def _arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-file", type=Path, default=Path("data/collections/default.json"))
    parser.add_argument("--observations-dir", type=Path, default=Path("data/observations"))
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("collection", "duplicates", "acquisitions", "inventory", "observations"):
        commands.add_parser(command)
    report = commands.add_parser("report", help="emit all collection reports")
    report.add_argument("--output", choices=("json",), default="json")
    return parser


def _observations(root: Path) -> list[dict[str, Any]]:
    records = []
    if not root.exists():
        return records
    for path in sorted(root.rglob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict) and "observation_id" in value and isinstance(value.get("cards"), list):
            records.append(value)
    return records


def main(argv: list[str] | None = None) -> int:
    args = _arguments().parse_args(argv)
    analytics = AnalyticsService()
    collection = CollectionRepository(args.collection_file).load()
    operations = {
        "collection": analytics.collection_summary,
        "duplicates": analytics.duplicate_report,
        "acquisitions": analytics.acquisition_report,
        "inventory": analytics.inventory_report,
    }
    if args.command == "observations":
        output: Any = analytics.observation_report(_observations(args.observations_dir)).to_dict()
    elif args.command == "report":
        output = {name: operation(collection).to_dict() for name, operation in operations.items()}
    else:
        output = operations[args.command](collection).to_dict()
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
