#!/usr/bin/env python3
"""Validate a local bounded competitive snapshot; never downloads or admits facts."""
import argparse
import json
from pathlib import Path

from card_intelligence.competitive_evidence import validate_competitive_snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--design-review", action="store_true",
                        help="allow unverified licensing for contract review only")
    args = parser.parse_args()
    document = validate_competitive_snapshot(
        args.snapshot, require_acquisition_ready=not args.design_review)
    print(json.dumps({"snapshot_id": document["snapshot_id"], "records": len(document["records"]),
                      "acquisition_ready": document["license_review"]["status"] == "approved"
                      and document["license_review"]["retention_permitted"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
