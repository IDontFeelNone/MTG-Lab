"""Offline CLI for refreshing and inspecting market snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from market import ManualMarketProvider, MarketService, MarketSnapshotRepository, MarketValidationError
from repository.canonical import CanonicalRepository


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", default="magic")
    parser.add_argument("--root", type=Path, default=Path("data/market/snapshots"))
    commands = parser.add_subparsers(dest="command", required=True)
    refresh = commands.add_parser("refresh", help="retrieve and append sample market data")
    refresh.add_argument("--provider", default="manual", choices=("manual",))
    refresh.add_argument("--printing", action="append", dest="printings")
    commands.add_parser("snapshot", help="list immutable snapshots")
    args = parser.parse_args(argv)
    snapshots = MarketSnapshotRepository(args.root)
    try:
        if args.command == "snapshot":
            output = [snapshot.to_dict() for snapshot in snapshots.list()]
        else:
            canonical = CanonicalRepository(args.game)
            identifiers = sorted(args.printings or (item.id for item in canonical.printings))
            service = MarketService(canonical, [ManualMarketProvider()], snapshots=snapshots)
            output = [service.refresh(identifier, provider=args.provider).to_dict()
                      for identifier in identifiers]
    except MarketValidationError as error:
        parser.error(str(error))
    print(json.dumps(output, indent=2, sort_keys=True) + "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
