"""Evaluate deterministic decisions from local repository snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analytics import AnalyticsService
from collection import CollectionRepository
from decisions import DEFAULT_RULES, DecisionService
from mtglab.analytics.__main__ import _observations


def _arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-file", type=Path, default=Path("data/collections/default.json"))
    parser.add_argument("--observations-dir", type=Path, default=Path("data/observations"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("evaluate", help="emit all matching decisions")
    report = commands.add_parser("report", help="emit the versioned decision report")
    report.add_argument("--format", choices=("json",), default="json")
    commands.add_parser("rules", help="list active rule configuration")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _arguments().parse_args(argv)
    service = DecisionService()
    if args.command == "rules":
        output = [{"rule_id": r.rule_id, "version": r.version, "category": r.category,
                   "report_type": r.report_type, "fact_path": r.fact_path,
                   "operator": r.operator, "threshold": r.threshold,
                   "severity": r.severity, "explanation": r.explanation}
                  for r in DEFAULT_RULES]
    else:
        collection = CollectionRepository(args.collection_file).load()
        observations = _observations(args.observations_dir)
        analytics = AnalyticsService()
        reports = (analytics.collection_summary(collection), analytics.duplicate_report(collection),
                   analytics.acquisition_report(collection), analytics.inventory_report(collection),
                   analytics.observation_report(observations), analytics.product_report(observations))
        if args.command == "evaluate":
            output = [decision.to_dict() for decision in service.evaluate(reports)]
        else:
            output = service.generate_decision_report(reports).to_dict()
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
