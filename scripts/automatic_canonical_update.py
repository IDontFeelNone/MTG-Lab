#!/usr/bin/env python3
"""JSON CLI for automatic canonical updates; default to read-only planning."""
import argparse
import json
from pathlib import Path
import sys

from production_evidence.automatic_updates import AutomaticCanonicalUpdate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="plan",
                        choices=("plan", "verify", "execute", "status", "replay", "rollback-plan"),
                        help="operation to perform (default: read-only plan)")
    parser.add_argument("--config", required=True)
    parser.add_argument("--repository-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    try:
        engine = AutomaticCanonicalUpdate(args.repository_root, args.config)
        method = getattr(engine, args.command.replace("-", "_"))
        result = method()
    except BaseException as error:
        print(json.dumps({"status": "blocked", "error": f"{type(error).__name__}: {error}"}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True)); return 0


if __name__ == "__main__": sys.exit(main())
