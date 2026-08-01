#!/usr/bin/env python3
"""Bounded, replay-safe Scryfall acquisition for promoted MB2 printings."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.error
import urllib.request

from market import MarketObservationRepository
from market.scryfall import (PROVIDER, SOURCE_DATASET, ProviderAcquisitionError,
    ProviderRateLimitError, ScryfallMarketAdapter, canonical_json, load_payload, sha256_bytes)

METADATA_URL = "https://api.scryfall.com/bulk-data/default-cards"
USER_AGENT = "MTG-Lab/127 (+https://github.com/IDontFeelNone/MTG-Lab)"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise ProviderRateLimitError("Scryfall rate limit (HTTP 429)") from error
        raise ProviderAcquisitionError(f"Scryfall request failed with HTTP {error.code}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        # Deliberately omit request headers and URL query strings from diagnostics.
        raise ProviderAcquisitionError("Scryfall request failed before a response was available") from error


def run(data_root: Path, *, payload_path: Path | None, retrieved_at: datetime,
        persist: bool, run_id: str, retain_payload: Path | None = None,
        observed_at_override: datetime | None = None,
        source_url_override: str | None = None) -> dict:
    canonical_path = data_root / "canonical" / "state.json"
    canonical_bytes = canonical_path.read_bytes()
    canonical_identity = "sha256:" + sha256_bytes(canonical_bytes)
    if payload_path:
        payload = payload_path.read_bytes()
        source_url = source_url_override or f"file:{payload_path.name}"
        observed_at = observed_at_override or retrieved_at
    else:
        metadata_bytes = fetch(METADATA_URL)
        metadata = json.loads(metadata_bytes)
        if metadata.get("object") != "bulk_data" or metadata.get("type") != "default_cards":
            raise ProviderAcquisitionError("unexpected Scryfall bulk metadata")
        source_url = str(metadata["download_uri"])
        payload = fetch(source_url)
        observed_at = datetime.fromisoformat(str(metadata["updated_at"]).replace("Z", "+00:00"))
        if retain_payload:
            retain_payload.write_bytes(payload)
    source_digest = sha256_bytes(payload)
    records = load_payload(payload)
    adapter = ScryfallMarketAdapter(json.loads(canonical_bytes), canonical_identity)
    observations, mappings = adapter.normalize(records, observed_at=observed_at,
        retrieved_at=retrieved_at, source_url=source_url, source_digest=source_digest)
    normalized = canonical_json([item.to_dict() for item in observations])
    counts = {status: sum(item["status"] == status for item in mappings)
              for status in ("matched", "unmatched", "ambiguous", "rejected")}
    result = {"schema_version": "market-acquisition-run-v1", "run_id": run_id,
        "provider": PROVIDER, "source_dataset": SOURCE_DATASET, "source_url": source_url,
        "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
        "source_observed_at": observed_at.isoformat().replace("+00:00", "Z"),
        "currency": "USD", "target": {"set": "MB2", "promoted_only": True},
        "source_sha256": source_digest, "normalized_sha256": sha256_bytes(normalized),
        "canonical_snapshot_identity": canonical_identity, "mapping_counts": counts,
        "observation_count": len(observations), "canonical_write": False,
        "promotion_performed": False, "persisted": persist}
    if persist:
        run_root = data_root / "market" / "acquisitions" / run_id
        run_root.mkdir(parents=True, exist_ok=False)
        # Retain only the bounded MB2 source subset; the workflow artifact retains
        # the fetched source for diagnostics without growing Git indefinitely.
        bounded = [item for item in records if str(item.get("set", "")).lower() == "mb2"]
        (run_root / "source-mb2.json").write_bytes(canonical_json(bounded))
        (run_root / "normalized.json").write_bytes(normalized)
        (run_root / "mappings.json").write_bytes(canonical_json(list(mappings)))
        repository = MarketObservationRepository(data_root / "market" / "observations")
        for observation in observations:
            repository.load(repository.append(observation))
        (run_root / "manifest.json").write_bytes(canonical_json(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--retain-payload", type=Path)
    parser.add_argument("--observed-at")
    parser.add_argument("--source-url")
    args = parser.parse_args()
    try:
        retrieved = datetime.fromisoformat(args.retrieved_at.replace("Z", "+00:00")).astimezone(timezone.utc)
        observed = (datetime.fromisoformat(args.observed_at.replace("Z", "+00:00")).astimezone(timezone.utc)
                    if args.observed_at else None)
        print(json.dumps(run(args.data_root, payload_path=args.payload, retrieved_at=retrieved,
            persist=args.persist, run_id=args.run_id, retain_payload=args.retain_payload,
            observed_at_override=observed, source_url_override=args.source_url), indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError, ProviderAcquisitionError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
