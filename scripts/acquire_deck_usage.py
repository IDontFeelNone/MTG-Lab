#!/usr/bin/env python3
"""Acquire MTGJSON's deck snapshot and retain only the ten-card projection."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

from card_intelligence.deck_usage import canonical_bytes, decode_deck_archive, project_decks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-timestamp", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", default="https://mtgjson.com/api/v5/AllDeckFiles.zip")
    parser.add_argument("--canonical", type=Path, default=Path("data/canonical/state.json"))
    args = parser.parse_args()
    if not args.dataset_timestamp.endswith("Z") or not args.retrieved_at.endswith("Z"):
        parser.error("timestamps must be UTC RFC 3339 values ending in Z")
    if args.source.startswith(("http://", "https://")):
        with urlopen(Request(args.source, headers={"User-Agent": "MTG-Lab/phase-143"}), timeout=120) as response:
            payload = response.read()
    else:
        payload = Path(args.source).read_bytes()
    decks = decode_deck_archive(payload)
    canonical = json.loads(args.canonical.read_text())
    mapping = {v["values"]["name"]: k for k, v in canonical["card"].items()
               if v["values"]["name"] in __import__("card_intelligence.deck_usage", fromlist=["PILOT_NAMES"]).PILOT_NAMES}
    document = project_decks(decks, mapping, dataset_timestamp=args.dataset_timestamp,
                             retrieved_at=args.retrieved_at,
                             source_sha256=hashlib.sha256(payload).hexdigest(),
                             source_byte_count=len(payload))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(document))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
