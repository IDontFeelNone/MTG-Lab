"""Read-only historical market query and reporting CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import MarketValidationError
from .reporting import DEFAULT_LIMIT, MAX_LIMIT, MarketHistoryReports


def _filters(parser: argparse.ArgumentParser, *, printing: bool = True, as_of: bool = True) -> None:
    if printing: parser.add_argument("--printing-id")
    parser.add_argument("--provider"); parser.add_argument("--acquisition-run-id")
    parser.add_argument("--finish"); parser.add_argument("--language")
    parser.add_argument("--currency"); parser.add_argument("--price-type")
    parser.add_argument("--observed-from"); parser.add_argument("--observed-to")
    if as_of: parser.add_argument("--as-of")


def _values(args) -> dict:
    names = ("printing_id", "provider", "acquisition_run_id", "finish", "language", "currency",
             "price_type", "observed_from", "observed_to", "as_of")
    return {name: getattr(args, name, None) for name in names}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m market.cli", description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    commands = parser.add_subparsers(dest="command", required=True)
    observations = commands.add_parser("observations")
    observation_commands = observations.add_subparsers(dest="operation", required=True)
    for name in ("list", "latest", "first", "count"):
        command = observation_commands.add_parser(name); _filters(command)
        if name == "list": command.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                                                  help=f"result limit (1-{MAX_LIMIT}; default {DEFAULT_LIMIT})")
    history = commands.add_parser("printing-history"); history.add_argument("printing_id"); _filters(history, printing=False)
    coverage = commands.add_parser("coverage"); coverage.add_argument("--product", required=True)
    acquisition = commands.add_parser("acquisition-summary"); acquisition.add_argument("run_id")
    snapshot = commands.add_parser("snapshot"); _filters(snapshot, as_of=False); snapshot.add_argument("--as-of", required=True)
    args = parser.parse_args(argv)
    try:
        reports = MarketHistoryReports(args.data_root)
        if args.command == "observations": result = reports.observations(args.operation, _values(args), getattr(args, "limit", DEFAULT_LIMIT))
        elif args.command == "printing-history": result = reports.printing_history(args.printing_id, _values(args))
        elif args.command == "coverage": result = reports.coverage(args.product)
        elif args.command == "acquisition-summary": result = reports.acquisition_summary(args.run_id)
        else: result = reports.snapshot(_values(args))
    except (MarketValidationError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"schema_version": "market-history-error-v1", "valid": False,
                          "error": str(error)}, indent=2, sort_keys=True)); return 2
    print(json.dumps(result, indent=2, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
