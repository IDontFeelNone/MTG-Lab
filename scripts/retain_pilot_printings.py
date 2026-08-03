#!/usr/bin/env python3
"""Acquire and immutably retain the bounded Phase 135 MTGJSON projection."""
import argparse
import json
from pathlib import Path
import shutil
from urllib.request import Request, urlopen

from production_evidence.pilot_printings import PilotPrintingRetention


def download(url: str, target: Path) -> dict:
    request = Request(url, headers={"Accept": "application/gzip"})
    with urlopen(request, timeout=120) as response, target.open("xb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)
        return {"status": response.status, "content_type": response.headers.get_content_type()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--canonical-snapshot", required=True)
    parser.add_argument("--acquired-at", required=True)
    parser.add_argument("--repository", type=Path, default=Path("data/evidence/phase-135"))
    parser.add_argument("--source-url", default="https://mtgjson.com/api/v5/AllPrintings.json.gz")
    args = parser.parse_args()
    args.repository.mkdir(parents=True, exist_ok=True)
    result = PilotPrintingRetention(args.repository, download).acquire(
        run_id=args.run_id, source_url=args.source_url,
        canonical_snapshot=args.canonical_snapshot, acquired_at=args.acquired_at)
    print(json.dumps(result["report"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
