"""Read-only card-value evidence explanation CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .explanation import (CardValueExplanationEngine, ERROR_VERSION, ExplanationError,
                          render_historical_explanation)
from .mechanics import MechanicalCardIntelligence
from .roles import FunctionalRolePilot
from .comparison import ContextualCardComparisonPilot, comparison_explanation


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
    mechanical = commands.add_parser("mechanical", help="literal retained production Card mechanics")
    mechanical.add_argument("--card-id", required=True)
    mechanical.add_argument("--reasoning-context", action="store_true",
                            help="existing-contract manual handoff; no model execution")
    commands.add_parser("mechanical-cohort", help="descriptive canonical-cohort statistics, not full-set analysis")
    roles = commands.add_parser("roles", help="pending functional-role proposals for the exact bounded pilot")
    roles.add_argument("--card-id", required=True)
    roles.add_argument("--reasoning-context", action="store_true", help="manual review handoff; no model execution")
    commands.add_parser("roles-pilot", help="15-Card candidate census and human-review material")
    commands.add_parser("roles-comparison", help="three-Card functional comparison; no ranking")
    comparison = commands.add_parser("contextual-comparison", help="one hypothetical comparison; pending roles, no winner")
    output = comparison.add_mutually_exclusive_group()
    output.add_argument("--reasoning-context", action="store_true", help="bounded manual handoff; no live model")
    output.add_argument("--human-readable", action="store_true", help="evidence-grounded manual explanation example")
    args = parser.parse_args(argv)
    try:
        if args.command == "contextual-comparison":
            pilot = ContextualCardComparisonPilot(args.data_root)
            if args.human_readable:
                print(comparison_explanation(pilot.dossier()), end="")
            else:
                result = pilot.reasoning_context() if args.reasoning_context else pilot.dossier().to_dict()
                print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
            return 0
        if args.command in {"roles", "roles-pilot", "roles-comparison"}:
            pilot = FunctionalRolePilot(args.data_root)
            if args.command == "roles-pilot":
                result = pilot.report()
            elif args.command == "roles-comparison":
                result = pilot.comparison()
            elif args.reasoning_context:
                result = pilot.reasoning_context(args.card_id).to_dict()
            else:
                result = pilot.dossier(args.card_id)
            print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
            return 0
        if args.command in {"mechanical", "mechanical-cohort"}:
            engine = MechanicalCardIntelligence(args.data_root)
            if args.command == "mechanical-cohort":
                result = engine.cohort_report()
            elif args.reasoning_context:
                result = engine.reasoning_context(args.card_id).to_dict()
            else:
                result = engine.dossier(args.card_id).to_dict()
            print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
            return 0
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
