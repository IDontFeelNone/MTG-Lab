#!/usr/bin/env python3
"""Bounded, replay-safe Scryfall acquisition for promoted MB2 printings."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
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
            "metadata_root_object_type": None, "metadata_parsing_shape": None,
            "bulk_entries_inspected": 0, "default_cards_matches": 0,
            "selected_bulk_type": None, "updated_at_present": False,
            "download_uri_valid": False, "download_uri_scheme": None,
            "download_uri_hostname": None, "download_uri_effective_port": None,
            "download_uri_has_userinfo": False, "download_uri_has_query": False,
            "download_uri_has_fragment": False, "download_uri_path_nonempty": False,
            "download_uri_hostname_allowlisted": False,
            "download_uri_rejection_reason": None, "attempts": 0}


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
                accepted_types = ({"application/json"} if endpoint_category == "scryfall_bulk_metadata"
                                  else {"application/json", "application/octet-stream"})
                if content_type not in accepted_types and not (
                        endpoint_category == "scryfall_bulk_metadata"
                        and content_type and content_type.endswith("+json")):
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


def parse_bulk_metadata(metadata_bytes: bytes, diagnostics: dict) -> tuple[str, datetime]:
    """Select and validate the one official default-cards bulk descriptor."""
    try:
        metadata = json.loads(metadata_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        _fail("Scryfall bulk metadata was malformed JSON", diagnostics, "metadata_parse")
    if not isinstance(metadata, dict):
        diagnostics["metadata_root_object_type"] = type(metadata).__name__
        _fail("Scryfall bulk metadata root was not an object", diagnostics, "metadata_validation")

    root_type = metadata.get("object")
    diagnostics["metadata_root_object_type"] = root_type if isinstance(root_type, str) else None
    if root_type == "error":
        _fail("Scryfall returned an error metadata object", diagnostics, "metadata_validation")

    if root_type == "bulk_data":
        diagnostics["metadata_parsing_shape"] = "direct_object"
        entries = [metadata]
    elif root_type == "list" and isinstance(metadata.get("data"), list):
        diagnostics["metadata_parsing_shape"] = "list_object"
        entries = metadata["data"]
    else:
        _fail("Scryfall bulk metadata had no supported response shape",
              diagnostics, "metadata_validation")

    diagnostics["bulk_entries_inspected"] = len(entries)
    matches = [entry for entry in entries
               if isinstance(entry, dict) and entry.get("type") == "default_cards"]
    diagnostics["default_cards_matches"] = len(matches)
    if len(matches) != 1:
        _fail("Scryfall bulk metadata must contain exactly one default_cards entry",
              diagnostics, "metadata_validation")
    selected = matches[0]
    diagnostics["selected_bulk_type"] = selected.get("type")
    if selected.get("object") != "bulk_data" or selected.get("type") != "default_cards":
        _fail("Scryfall default_cards metadata entry had an invalid contract",
              diagnostics, "metadata_validation")

    updated_at = selected.get("updated_at")
    diagnostics["updated_at_present"] = updated_at is not None
    try:
        observed_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        if observed_at.tzinfo is None:
            raise ValueError
    except (AttributeError, ValueError, TypeError):
        _fail("Scryfall bulk metadata had an invalid updated_at", diagnostics,
              "metadata_validation")

    download_uri = selected.get("download_uri")
    reason = None
    try:
        if not isinstance(download_uri, str) or not download_uri.strip():
            diagnostics["download_uri_rejection_reason"] = "blank_uri"
            _fail("Scryfall bulk metadata lacked a permitted secure download URI", diagnostics,
                  "download_uri_extraction")
        parsed = urllib.parse.urlsplit(download_uri)
        hostname = (parsed.hostname or "").lower().removesuffix(".")
        try:
            ipaddress.ip_address(hostname)
            is_ip_address = True
        except ValueError:
            is_ip_address = False
        labels = hostname.split(".")
        allowlisted = (not is_ip_address and len(labels) >= 3
                       and labels[-2:] == ["scryfall", "io"]
                       and all(labels))
        effective_port = parsed.port if parsed.port is not None else (
            443 if parsed.scheme.lower() == "https" else None)
        diagnostics.update(
            download_uri_scheme=parsed.scheme.lower() or None,
            download_uri_hostname=hostname or None,
            download_uri_effective_port=effective_port,
            download_uri_has_userinfo=(parsed.username is not None or parsed.password is not None),
            download_uri_has_query=bool(parsed.query),
            download_uri_has_fragment=bool(parsed.fragment),
            download_uri_path_nonempty=bool(parsed.path),
            download_uri_hostname_allowlisted=allowlisted)
        if parsed.scheme.lower() != "https":
            reason = "scheme_not_https"
        elif parsed.username is not None or parsed.password is not None:
            reason = "userinfo_present"
        elif parsed.port not in (None, 443):
            reason = "nondefault_port"
        elif not hostname:
            reason = "hostname_missing"
        elif is_ip_address:
            reason = "ip_address_hostname"
        elif hostname == "localhost":
            reason = "localhost_hostname"
        elif not allowlisted:
            reason = "hostname_not_allowlisted"
        elif not parsed.path or not parsed.path.startswith("/"):
            reason = "absolute_path_missing"
        elif parsed.fragment:
            reason = "fragment_present"
        valid_uri = reason is None
    except (TypeError, ValueError):
        valid_uri = False
        reason = "malformed_uri"
    diagnostics["download_uri_valid"] = valid_uri
    diagnostics["download_uri_rejection_reason"] = reason
    if not valid_uri:
        _fail("Scryfall bulk metadata lacked a permitted secure download URI", diagnostics,
              "download_uri_extraction")
    diagnostics["download_uri_obtained"] = True
    return download_uri, observed_at


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
        download_uri, observed_at = parse_bulk_metadata(metadata_bytes, diagnostic)
        # The validated URI is transport-only.  Reports and normalized provenance use a
        # stable dataset identifier so paths and query strings are never printed.
        source_url = "scryfall:default_cards"
        payload = fetch(download_uri, diagnostics=diagnostic,
                        endpoint_category="scryfall_bulk_payload",
                        stage="bulk_payload_response")
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
