"""Read-only card-value evidence explanation CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .explanation import (CardValueExplanationEngine, ERROR_VERSION, ExplanationError,
                          render_historical_explanation)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m card_intelligence.cli", description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    commands = parser.add_subparsers(dest="command", required=True)
    explain = commands.add_parser("explain")
    explain.add_argument("name", nargs="?")
    explain.add_argument("--card-id")
    explain.add_argument("--include-observed-prices", action="store_true",
                         help="opt in to card-value-explanation-v2 retained price evidence")
    explain.add_argument("--include-historical-movement", action="store_true",
                         help="opt in to exact-dimension history (automatically enables observed prices)")
    explain.add_argument("--include-demand-evidence", action="store_true",
                         help="opt in to card-value-explanation-v3 reviewed demand evidence")
    explain.add_argument("--human-readable", action="store_true",
                         help="render the historical JSON contract as text instead of authoritative JSON")
    args = parser.parse_args(argv)
    try:
        result = CardValueExplanationEngine(args.data_root).explain(
            name=args.name, card_id=args.card_id,
            include_observed_prices=args.include_observed_prices,
            include_historical_movement=args.include_historical_movement,
            include_demand_evidence=args.include_demand_evidence)
        if args.human_readable:
            print(render_historical_explanation(result), end="")
            return 0
    except (ExplanationError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"schema_version": ERROR_VERSION, "valid": False,
                          "error": str(error)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
