#!/usr/bin/env python3
"""Manually record a genuine Phase 117 operator decision from a JSON file."""
import argparse
import json
from pathlib import Path

from production_evidence.operator_authorization import record_authorization
from production_evidence.repository import EvidenceError

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("authorization", type=Path, help="JSON containing all human-entered fields")
parser.add_argument("--data-root", type=Path, default=Path("data"))
args = parser.parse_args()
try:
    result = record_authorization(args.data_root, json.loads(args.authorization.read_text()))
except (OSError, ValueError, EvidenceError) as error:
    print(json.dumps({"valid": False, "error": str(error), "canonical_write": False,
                      "promotion_performed": False}, indent=2, sort_keys=True))
    raise SystemExit(2)
print(json.dumps(result, indent=2, sort_keys=True))
