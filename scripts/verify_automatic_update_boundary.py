#!/usr/bin/env python3
"""Read-only semantic publication inventory; this never authenticates or publishes."""
import argparse
import json
from pathlib import Path

from production_evidence.automatic_updates import (
    AdmissionDecision, AutomaticCanonicalUpdate, admission_publication_inventory,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="exact reviewed base SHA, not a moving branch")
    parser.add_argument("--config", required=True)
    parser.add_argument("--plan", required=True, help="retained previously reviewed planning JSON")
    parser.add_argument("--repository-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    try:
        engine = AutomaticCanonicalUpdate(args.repository_root, args.config)
        plan = json.loads(Path(args.plan).read_bytes())
        audit = json.loads((engine.data / engine.config["artifacts"]["promotion_audit"]).read_bytes())
        # Content inspection only. This serialized decision is NOT installed as
        # a trusted boundary and cannot be supplied to an execution/publish CLI.
        decision = AdmissionDecision(**audit["admission_decision"])
        result = admission_publication_inventory(engine, plan, args.base, decision)
        print(json.dumps({"status": "verified-content-only", "execution_authorized": False,
                          "inventory": result}, indent=2, sort_keys=True))
        return 0
    except Exception as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
