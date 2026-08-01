#!/usr/bin/env python3
"""Bounded, replay-safe Scryfall acquisition for promoted MB2 printings."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

from market import MarketObservationRepository, MarketValidationError
from market.scryfall import (PROVIDER, SOURCE_DATASET, ProviderAcquisitionError,
    ProviderRateLimitError, ScryfallMarketAdapter, canonical_json, load_payload, sha256_bytes)

METADATA_URL = "https://api.scryfall.com/bulk-data/default_cards"
USER_AGENT = "MTG-Lab market acquisition/127B (+https://github.com/IDontFeelNone/MTG-Lab)"
MAX_ATTEMPTS = 3


def new_diagnostics() -> dict:
    """Return the stable, payload-free acquisition diagnostic contract."""
    return {"failing_stage": None, "endpoint_category": "scryfall_bulk_metadata",
            "http_status": None, "response_content_type": None,
            "metadata_fetched": False, "download_uri_obtained": False,
            "bulk_payload_download_began": False, "payload_bytes_retained": False,
            "attempts": 0}


def _fail(message: str, diagnostics: dict, stage: str, *, status: int | None = None,
          content_type: str | None = None, rate_limited: bool = False):
    diagnostics.update(failing_stage=stage, http_status=status,
                       response_content_type=content_type)
    error_type = ProviderRateLimitError if rate_limited else ProviderAcquisitionError
    error = error_type(message)
    error.diagnostics = dict(diagnostics)
    raise error


def fetch(url: str, *, diagnostics: dict | None = None, endpoint_category: str = "scryfall_bulk_payload",
          stage: str = "bulk_payload_response", sleep=None) -> bytes:
    """Fetch official JSON with deterministic redirect, timeout, and retry behavior."""
    diagnostic = diagnostics if diagnostics is not None else new_diagnostics()
    sleeper = sleep or time.sleep
    diagnostic["endpoint_category"] = endpoint_category
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "application/json"})
    for attempt in range(1, MAX_ATTEMPTS + 1):
        diagnostic["attempts"] = attempt
        try:
            # urllib's default opener follows HTTP redirects, including HTTPS Location values.
            with urllib.request.urlopen(request, timeout=120) as response:
                status = getattr(response, "status", None) or response.getcode()
                content_type = response.headers.get_content_type()
                diagnostic.update(http_status=status, response_content_type=content_type)
                if endpoint_category == "scryfall_bulk_payload":
                    diagnostic["bulk_payload_download_began"] = True
                if content_type not in {"application/json", "application/octet-stream"}:
                    _fail("Scryfall returned an invalid response content type", diagnostic,
                          stage, status=status, content_type=content_type)
                return response.read()
        except urllib.error.HTTPError as error:
            content_type = error.headers.get_content_type() if error.headers else None
            transient = error.code == 429 or 500 <= error.code <= 599
            if transient and attempt < MAX_ATTEMPTS:
                sleeper(2 ** (attempt - 1))
                continue
            _fail(f"Scryfall request failed with HTTP {error.code}", diagnostic, stage,
                  status=error.code, content_type=content_type, rate_limited=error.code == 429)
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt < MAX_ATTEMPTS:
                sleeper(2 ** (attempt - 1))
                continue
            # Deliberately omit URLs, headers, exception text, and response bodies.
            _fail("Scryfall request timed out or failed before a response", diagnostic, stage)
    raise AssertionError("unreachable")


def run(data_root: Path, *, payload_path: Path | None, retrieved_at: datetime,
        persist: bool, run_id: str, retain_payload: Path | None = None,
        observed_at_override: datetime | None = None,
        source_url_override: str | None = None, diagnostics: dict | None = None) -> dict:
    diagnostic = diagnostics if diagnostics is not None else new_diagnostics()
    canonical_path = data_root / "canonical" / "state.json"
    canonical_bytes = canonical_path.read_bytes()
    canonical_identity = "sha256:" + sha256_bytes(canonical_bytes)
    if payload_path:
        payload = payload_path.read_bytes()
        source_url = source_url_override or f"file:{payload_path.name}"
        observed_at = observed_at_override or retrieved_at
    else:
        metadata_bytes = fetch(METADATA_URL, diagnostics=diagnostic,
                               endpoint_category="scryfall_bulk_metadata",
                               stage="metadata_response")
        diagnostic["metadata_fetched"] = True
        try:
            metadata = json.loads(metadata_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError):
            _fail("Scryfall bulk metadata was malformed JSON", diagnostic, "metadata_parse")
        if metadata.get("object") != "bulk_data" or metadata.get("type") != "default_cards":
            _fail("Scryfall bulk metadata did not match the default_cards contract",
                  diagnostic, "metadata_validation")
        download_uri = metadata.get("download_uri")
        if not isinstance(download_uri, str) or not download_uri.startswith("https://"):
            _fail("Scryfall bulk metadata lacked a secure download URI", diagnostic,
                  "download_uri_extraction")
        diagnostic["download_uri_obtained"] = True
        source_url = download_uri
        payload = fetch(source_url, diagnostics=diagnostic,
                        endpoint_category="scryfall_bulk_payload",
                        stage="bulk_payload_response")
        try:
            observed_at = datetime.fromisoformat(str(metadata["updated_at"]).replace("Z", "+00:00"))
        except (KeyError, ValueError, TypeError):
            _fail("Scryfall bulk metadata had an invalid updated_at", diagnostic,
                  "metadata_validation")
        if retain_payload:
            retain_payload.write_bytes(payload)
            diagnostic["payload_bytes_retained"] = True
    source_digest = sha256_bytes(payload)
    records = load_payload(payload)
    adapter = ScryfallMarketAdapter(json.loads(canonical_bytes), canonical_identity)
    observations, mappings = adapter.normalize(records, observed_at=observed_at,
        retrieved_at=retrieved_at, source_url=source_url, source_digest=source_digest)
    normalized = canonical_json([item.to_dict() for item in observations])
    counts = {status: sum(item["status"] == status for item in mappings)
              for status in ("matched", "unmatched", "ambiguous", "rejected")}
    selected_records = [item for item in records
                        if str(item.get("set", "")).lower() == "mb2"]
    observed_printings = {item.entity_id for item in observations}
    known_prices = sum(item.price is not None for item in observations)
    missing_prices = len(observations) - known_prices
    result = {"schema_version": "market-acquisition-run-v1", "run_id": run_id,
        "provider": PROVIDER, "source_dataset": SOURCE_DATASET, "source_url": source_url,
        "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
        "source_observed_at": observed_at.isoformat().replace("+00:00", "Z"),
        "currency": "USD", "target": {"set": "MB2", "promoted_only": True},
        "source_sha256": source_digest, "normalized_sha256": sha256_bytes(normalized),
        "canonical_snapshot_identity": canonical_identity, "mapping_counts": counts,
        "source_record_count": len(records), "mb2_record_count": len(selected_records),
        "matched_printing_count": len(observed_printings),
        "known_price_observation_count": known_prices,
        "missing_price_observation_count": missing_prices,
        "observation_count": len(observations), "canonical_write": False,
        "promotion_performed": False, "persisted": persist,
        "acquisition_diagnostics": diagnostic}
    if persist:
        run_root = data_root / "market" / "acquisitions" / run_id
        run_root.mkdir(parents=True, exist_ok=False)
        # Retain only the bounded MB2 source subset; the workflow artifact retains
        # the fetched source for diagnostics without growing Git indefinitely.
        (run_root / "source-mb2.json").write_bytes(canonical_json(selected_records))
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
    diagnostic = new_diagnostics()
    try:
        retrieved = datetime.fromisoformat(args.retrieved_at.replace("Z", "+00:00")).astimezone(timezone.utc)
        observed = (datetime.fromisoformat(args.observed_at.replace("Z", "+00:00")).astimezone(timezone.utc)
                    if args.observed_at else None)
        print(json.dumps(run(args.data_root, payload_path=args.payload, retrieved_at=retrieved,
            persist=args.persist, run_id=args.run_id, retain_payload=args.retain_payload,
            observed_at_override=observed, source_url_override=args.source_url,
            diagnostics=diagnostic), indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError, MarketValidationError,
            ProviderAcquisitionError) as error:
        report = getattr(error, "diagnostics", diagnostic)
        if report["failing_stage"] is None:
            report["failing_stage"] = "local_validation"
        print(json.dumps({"valid": False, "error": str(error),
                          "acquisition_diagnostics": report}, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
