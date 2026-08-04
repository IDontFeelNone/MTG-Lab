#!/usr/bin/env python3
"""Bounded, fail-closed Scryfall JSONL acquisition for promoted MB2 printings."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import hashlib
import ipaddress
import io
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

from market import MarketValidationError
from market.scryfall import (PROVIDER, SOURCE_DATASET, ProviderAcquisitionError,
    ProviderRateLimitError, ScryfallMarketAdapter, canonical_json, load_payload, sha256_bytes)

METADATA_URL = "https://api.scryfall.com/bulk-data/default_cards"
USER_AGENT = "MTG-Lab market acquisition/127G (+https://github.com/IDontFeelNone/MTG-Lab)"
MAX_ATTEMPTS = 3
JSONL_MEDIA_TYPES = frozenset(("application/json", "application/jsonl",
    "application/jsonlines", "application/x-ndjson", "application/octet-stream"))
GZIP_MEDIA_TYPES = frozenset(("application/gzip", "application/x-gzip"))
MAX_RETAINED_MB2_RECORDS = 1_000
MAX_JSONL_LINE_BYTES = 2_000_000
STRUCTURAL_DIAGNOSTIC_FIELDS = ("object", "id", "name", "set", "set_type", "layout", "lang")
REQUIRED_CARD_IDENTITY_FIELDS = ("id", "object", "set", "collector_number", "lang", "finishes", "prices")
MAX_DIAGNOSTIC_VALUE_CHARS = 160


def new_diagnostics() -> dict:
    """Return the stable diagnostic contract; it never contains transport values."""
    return {"failing_stage": None, "endpoint_category": "scryfall_bulk_metadata",
        "http_status": None, "response_media_type": None, "metadata_fetched": False,
        "bulk_payload_download_began": False, "metadata_root_object_type": None,
        "metadata_parsing_shape": None, "metadata_top_level_keys": [],
        "selected_descriptor_keys": [], "bulk_entries_inspected": 0,
        "default_cards_matches": 0, "selected_bulk_type": None,
        "updated_at_present": False, "transport_field_selected": None,
        "transport_format": None, "legacy_compatibility_used": False,
        "jsonl_download_uri_present": False, "download_uri_present": False,
        "jsonl_download_uri_runtime_type": None, "download_uri_runtime_type": None,
        "transport_field_extraction_reason": None,
        "descriptor_selection_preserved_original_field": False,
        "transport_and_diagnostic_objects_distinct": False,
        "transport_uri_valid": False, "transport_uri_scheme": None,
        "transport_uri_hostname": None, "transport_uri_effective_port": None,
        "transport_uri_has_userinfo": False, "transport_uri_has_query": False,
        "transport_uri_has_fragment": False, "transport_uri_path_nonempty": False,
        "transport_uri_hostname_allowlisted": False, "transport_uri_rejection_reason": None,
        "compression_mode": None, "declared_content_length": None,
        "bytes_downloaded": 0, "compressed_bytes_read": 0,
        "decompressed_bytes_processed": 0, "gzip_framing_valid": False,
        "stream_completed": False, "total_lines": 0,
        "records_decoded": 0, "malformed_record_count": 0,
        "selected_mb2_record_count": 0, "duplicate_record_count": 0,
        "duplicate_identity_count": 0, "attempts": 0, "unsupported_record_diagnostic": None}


def _fail(message, diagnostics, stage, *, status=None, media_type=None, rate_limited=False):
    diagnostics.update(failing_stage=stage, http_status=status,
                       response_media_type=media_type)
    error = (ProviderRateLimitError if rate_limited else ProviderAcquisitionError)(message)
    error.diagnostics = dict(diagnostics)
    raise error


@dataclass(frozen=True)
class SelectedBulkDescriptor:
    provider: dict
    diagnostic_projection: dict


@dataclass(frozen=True)
class Transport:
    uri: str
    field: str
    format: str
    observed_at: datetime


@dataclass(frozen=True)
class ParsedPayload:
    records: tuple[dict, ...]
    source_digest: str
    source_record_count: int


def _select_bulk_descriptor(metadata: dict, diagnostics: dict) -> SelectedBulkDescriptor:
    diagnostics["metadata_top_level_keys"] = sorted(str(key) for key in metadata)
    root_type = metadata.get("object")
    diagnostics["metadata_root_object_type"] = root_type if isinstance(root_type, str) else None
    if root_type == "error":
        _fail("Scryfall returned an error metadata object", diagnostics, "metadata_validation")
    if root_type == "bulk_data":
        diagnostics["metadata_parsing_shape"] = "direct_object"; entries = [metadata]
    elif root_type == "list" and isinstance(metadata.get("data"), list):
        diagnostics["metadata_parsing_shape"] = "list_object"; entries = metadata["data"]
    else:
        _fail("Scryfall bulk metadata had no supported response shape", diagnostics,
              "metadata_validation")
    diagnostics["bulk_entries_inspected"] = len(entries)
    matches = [x for x in entries if isinstance(x, dict) and x.get("type") == "default_cards"]
    diagnostics["default_cards_matches"] = len(matches)
    if len(matches) != 1:
        _fail("Scryfall bulk metadata must contain exactly one default_cards entry",
              diagnostics, "metadata_validation")
    provider = matches[0]
    keys = sorted(str(key) for key in provider)
    projection = {"keys": keys, "value_types": {str(k): type(v).__name__
                                                   for k, v in provider.items()}}
    diagnostics["selected_descriptor_keys"] = keys
    diagnostics["transport_and_diagnostic_objects_distinct"] = provider is not projection
    diagnostics["descriptor_selection_preserved_original_field"] = provider is matches[0]
    return SelectedBulkDescriptor(provider, projection)


def fetch(url: str, *, diagnostics=None, endpoint_category="scryfall_bulk_metadata",
          stage="metadata_response", sleep=None) -> bytes:
    """Fetch the small metadata document with bounded retry behavior."""
    diagnostic = diagnostics if diagnostics is not None else new_diagnostics()
    sleeper = sleep or time.sleep
    diagnostic["endpoint_category"] = endpoint_category
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "application/json"})
    for attempt in range(1, MAX_ATTEMPTS + 1):
        diagnostic["attempts"] = attempt
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                status = getattr(response, "status", None) or response.getcode()
                media = response.headers.get_content_type()
                if media != "application/json" and not (media and media.endswith("+json")):
                    _fail("Scryfall returned an invalid metadata content type", diagnostic,
                          stage, status=status, media_type=media)
                return response.read()
        except urllib.error.HTTPError as error:
            media = error.headers.get_content_type() if error.headers else None
            transient = error.code == 429 or 500 <= error.code <= 599
            if transient and attempt < MAX_ATTEMPTS:
                sleeper(2 ** (attempt - 1)); continue
            _fail(f"Scryfall request failed with HTTP {error.code}", diagnostic, stage,
                  status=error.code, media_type=media, rate_limited=error.code == 429)
        except (urllib.error.URLError, TimeoutError):
            if attempt < MAX_ATTEMPTS:
                sleeper(2 ** (attempt - 1)); continue
            _fail("Scryfall request timed out or failed before a response", diagnostic, stage)
    raise AssertionError("unreachable")


def _validate_uri(value: str, diagnostics: dict) -> None:
    reason = None
    try:
        parsed = urllib.parse.urlsplit(value)
        hostname = (parsed.hostname or "").lower().removesuffix(".")
        try: ipaddress.ip_address(hostname); is_ip = True
        except ValueError: is_ip = False
        labels = hostname.split(".")
        allowed = not is_ip and len(labels) >= 3 and labels[-2:] == ["scryfall", "io"] and all(labels)
        port = parsed.port if parsed.port is not None else (443 if parsed.scheme.lower() == "https" else None)
        diagnostics.update(transport_uri_scheme=parsed.scheme.lower() or None,
            transport_uri_hostname=hostname or None, transport_uri_effective_port=port,
            transport_uri_has_userinfo=parsed.username is not None or parsed.password is not None,
            transport_uri_has_query=bool(parsed.query), transport_uri_has_fragment=bool(parsed.fragment),
            transport_uri_path_nonempty=bool(parsed.path), transport_uri_hostname_allowlisted=allowed)
        if parsed.scheme.lower() != "https": reason = "scheme_not_https"
        elif parsed.username is not None or parsed.password is not None: reason = "userinfo_present"
        elif parsed.port not in (None, 443): reason = "nondefault_port"
        elif not hostname: reason = "hostname_missing"
        elif is_ip: reason = "ip_address_hostname"
        elif hostname == "localhost": reason = "localhost_hostname"
        elif not allowed: reason = "hostname_not_allowlisted"
        elif not parsed.path or not parsed.path.startswith("/"): reason = "absolute_path_missing"
        elif parsed.fragment: reason = "fragment_present"
    except (TypeError, ValueError): reason = "malformed_uri"
    diagnostics["transport_uri_valid"] = reason is None
    diagnostics["transport_uri_rejection_reason"] = reason
    if reason:
        _fail("Scryfall metadata lacked a permitted secure transport URI", diagnostics,
              "transport_uri_validation")


def parse_bulk_metadata(metadata_bytes: bytes, diagnostics: dict) -> Transport:
    try: metadata = json.loads(metadata_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        _fail("Scryfall bulk metadata was malformed JSON", diagnostics, "metadata_parse")
    if not isinstance(metadata, dict):
        diagnostics["metadata_root_object_type"] = type(metadata).__name__
        _fail("Scryfall bulk metadata root was not an object", diagnostics, "metadata_validation")
    selected = _select_bulk_descriptor(metadata, diagnostics).provider
    diagnostics["selected_bulk_type"] = selected.get("type")
    if selected.get("object") != "bulk_data" or selected.get("type") != "default_cards":
        _fail("Scryfall default_cards metadata entry had an invalid contract", diagnostics,
              "metadata_validation")
    updated = selected.get("updated_at"); diagnostics["updated_at_present"] = updated is not None
    try:
        observed = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        if observed.tzinfo is None: raise ValueError
    except (AttributeError, ValueError, TypeError):
        _fail("Scryfall bulk metadata had an invalid updated_at", diagnostics, "metadata_validation")
    present = {name: name in selected for name in ("jsonl_download_uri", "download_uri")}
    for name in present:
        diagnostics[name + "_present"] = present[name]
        diagnostics[name + "_runtime_type"] = type(selected.get(name)).__name__
    if not any(present.values()): reason = "supported_transport_field_absent"
    elif all(present.values()) and selected["jsonl_download_uri"] != selected["download_uri"]:
        reason = "conflicting_transport_fields"
    else: reason = None
    if reason:
        diagnostics["transport_field_extraction_reason"] = reason
        _fail("Scryfall metadata had no unambiguous supported transport field", diagnostics,
              "transport_field_extraction")
    field = "jsonl_download_uri" if present["jsonl_download_uri"] else "download_uri"
    value = selected.get(field)
    if not isinstance(value, str): reason = "selected_transport_not_string"
    elif not value.strip(): reason = "selected_transport_blank"
    else: reason = "jsonl_transport_selected" if field.startswith("jsonl_") else "legacy_transport_selected"
    diagnostics.update(transport_field_selected=field,
        transport_format="jsonl" if field.startswith("jsonl_") else "json-array",
        legacy_compatibility_used=field == "download_uri", transport_field_extraction_reason=reason)
    if reason in ("selected_transport_not_string", "selected_transport_blank"):
        _fail("Scryfall metadata transport field was invalid", diagnostics,
              "transport_field_extraction")
    _validate_uri(value, diagnostics)
    return Transport(value, field, diagnostics["transport_format"], observed)


class _HashingReader(io.RawIOBase):
    def __init__(self, raw, diagnostics):
        self.raw, self.digest, self.count = raw, hashlib.sha256(), 0
        self.diagnostics = diagnostics
    def readable(self): return True
    def readinto(self, target):
        chunk = self.raw.read(len(target))
        if not chunk: return 0
        target[:len(chunk)] = chunk; self.digest.update(chunk); self.count += len(chunk)
        self.diagnostics["bytes_downloaded"] = self.count
        self.diagnostics["compressed_bytes_read"] = self.count
        return len(chunk)


class _CountingReader(io.RawIOBase):
    """Count decompressed bytes without retaining them."""
    def __init__(self, raw, diagnostics): self.raw, self.diagnostics = raw, diagnostics
    def readable(self): return True
    def readinto(self, target):
        chunk = self.raw.read(len(target))
        if not chunk: return 0
        target[:len(chunk)] = chunk
        self.diagnostics["decompressed_bytes_processed"] += len(chunk)
        return len(chunk)


def _json_type(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _safe_diagnostic_value(value):
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value if len(value) <= MAX_DIAGNOSTIC_VALUE_CHARS else value[:MAX_DIAGNOSTIC_VALUE_CHARS] + "…"
    if isinstance(value, list):
        return {"type": "array", "count": len(value)}
    if isinstance(value, dict):
        return {"type": "object", "keys": sorted(str(key) for key in value)[:MAX_DIAGNOSTIC_VALUE_CHARS]}
    return {"type": type(value).__name__}


def _record_shape_diagnostic(diagnostics: dict, *, line_number: int, raw_line: bytes,
                             decoded=None, reason_code: str) -> None:
    identity_present = {field: False for field in REQUIRED_CARD_IDENTITY_FIELDS}
    structural = {}
    top_keys = []
    if isinstance(decoded, dict):
        top_keys = sorted(str(key) for key in decoded)
        identity_present = {field: field in decoded for field in REQUIRED_CARD_IDENTITY_FIELDS}
        structural = {field: _safe_diagnostic_value(decoded.get(field))
                      for field in STRUCTURAL_DIAGNOSTIC_FIELDS if field in decoded}
    diagnostics["unsupported_record_diagnostic"] = {
        "line_number": line_number,
        "raw_record_byte_count": len(raw_line),
        "raw_record_sha256": hashlib.sha256(raw_line).hexdigest(),
        "decoded_top_level_json_type": _json_type(decoded),
        "top_level_keys": top_keys,
        "structural_fields": structural,
        "required_card_identity_fields_present": identity_present,
        "rejection_reason_code": reason_code,
        "records_decoded_before_failure": diagnostics["records_decoded"],
    }


def _record_validation_reason(record: dict) -> str | None:
    missing = [field for field in REQUIRED_CARD_IDENTITY_FIELDS if field not in record]
    if missing:
        return "missing_required_card_identity_fields:" + ",".join(missing)
    if record["object"] != "card":
        return "unsupported_object_type:" + str(record["object"])
    if not isinstance(record["prices"], dict):
        return "prices_not_object"
    if not isinstance(record["finishes"], list):
        return "finishes_not_array"
    if not record["finishes"]:
        return "finishes_empty"
    return None


def _parse_jsonl_stream(raw, diagnostics: dict, *, content_encoding=None,
                        compression_mode=None) -> ParsedPayload:
    hashing = _HashingReader(raw, diagnostics); buffered = io.BufferedReader(hashing)
    encoding = (content_encoding or "").lower().strip()
    if encoding not in ("", "identity", "gzip"):
        diagnostics["compression_mode"] = encoding
        _fail("Scryfall payload used unsupported compression", diagnostics, "payload_decompression")
    requested = compression_mode or ("gzip" if encoding == "gzip" else "identity")
    magic_gzip = buffered.peek(2)[:2] == b"\x1f\x8b"
    if requested == "gzip":
        diagnostics["compression_mode"] = "gzip"
        diagnostics["gzip_framing_valid"] = magic_gzip
        if not magic_gzip:
            _fail("Scryfall gzip payload had invalid framing", diagnostics,
                  "payload_decompression")
        binary = gzip.GzipFile(fileobj=buffered)
    else:
        if magic_gzip:
            _fail("Scryfall JSONL compression was not declared unambiguously", diagnostics,
                  "payload_decompression")
        diagnostics["compression_mode"] = "identity"; binary = buffered
    counted = io.BufferedReader(_CountingReader(binary, diagnostics))
    selected, seen = [], set()
    try:
        for number, raw_line in enumerate(counted, 1):
            diagnostics["total_lines"] = number
            if len(raw_line) > MAX_JSONL_LINE_BYTES:
                diagnostics["malformed_record_count"] += 1
                _record_shape_diagnostic(diagnostics, line_number=number, raw_line=raw_line,
                                         decoded=None, reason_code="line_too_large")
                _fail("Scryfall JSONL record exceeded maximum line size", diagnostics,
                      "payload_jsonl_validation")
            if not raw_line.strip():
                continue
            try:
                line = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                _record_shape_diagnostic(diagnostics, line_number=number, raw_line=raw_line,
                                         decoded=None, reason_code="invalid_utf8")
                _fail("Scryfall JSONL was not valid UTF-8", diagnostics, "payload_utf8_validation")
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                diagnostics["malformed_record_count"] += 1
                _record_shape_diagnostic(diagnostics, line_number=number, raw_line=raw_line,
                                         decoded=None, reason_code="malformed_json")
                _fail("Scryfall JSONL contained malformed JSON", diagnostics, "payload_jsonl_validation")
            if not isinstance(record, dict):
                diagnostics["malformed_record_count"] += 1
                _record_shape_diagnostic(diagnostics, line_number=number, raw_line=raw_line,
                                         decoded=record, reason_code="top_level_not_object")
                _fail("Scryfall JSONL record was not an object", diagnostics, "payload_jsonl_validation")
            reason = _record_validation_reason(record)
            if reason is not None:
                diagnostics["malformed_record_count"] += 1
                _record_shape_diagnostic(diagnostics, line_number=number, raw_line=raw_line,
                                         decoded=record, reason_code=reason)
                _fail("Scryfall JSONL record had an unsupported shape", diagnostics, "payload_jsonl_validation")
            try: ScryfallMarketAdapter.validate_record(record)
            except MarketValidationError:
                diagnostics["malformed_record_count"] += 1
                _record_shape_diagnostic(diagnostics, line_number=number, raw_line=raw_line,
                                         decoded=record, reason_code="adapter_validation_failed")
                _fail("Scryfall JSONL record had an unsupported shape", diagnostics, "payload_jsonl_validation")
            identity = record["id"]
            if not isinstance(identity, str) or not identity.strip():
                diagnostics["malformed_record_count"] += 1
                _record_shape_diagnostic(diagnostics, line_number=number, raw_line=raw_line,
                                         decoded=record, reason_code="invalid_provider_identity")
                _fail("Scryfall JSONL record had an invalid identity", diagnostics, "payload_jsonl_validation")
            if identity in seen:
                diagnostics["duplicate_record_count"] += 1
                diagnostics["duplicate_identity_count"] += 1
                _record_shape_diagnostic(diagnostics, line_number=number, raw_line=raw_line,
                                         decoded=record, reason_code="duplicate_provider_identity")
                _fail("Scryfall JSONL contained a duplicate record identity", diagnostics,
                      "payload_jsonl_validation")
            seen.add(identity); diagnostics["records_decoded"] += 1
            if str(record["set"]).lower() == "mb2":
                if len(selected) >= MAX_RETAINED_MB2_RECORDS:
                    _fail("Scryfall MB2 projection exceeded its retention bound", diagnostics,
                          "payload_jsonl_validation")
                selected.append(record)
    except (gzip.BadGzipFile, EOFError, OSError):
        _fail("Scryfall payload decompression failed or stream was incomplete", diagnostics,
              "payload_decompression")
    diagnostics["stream_completed"] = True
    diagnostics["selected_mb2_record_count"] = len(selected)
    return ParsedPayload(tuple(selected), hashing.digest.hexdigest(), diagnostics["records_decoded"])


def download_jsonl(uri: str, diagnostics: dict) -> ParsedPayload:
    """Download exactly once and validate the response as streaming JSON Lines."""
    diagnostics["endpoint_category"] = "scryfall_bulk_payload"
    request = urllib.request.Request(uri, headers={"User-Agent": USER_AGENT,
        "Accept": "application/x-ndjson, application/octet-stream, application/json"})
    diagnostics["attempts"] = 1
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            diagnostics["bulk_payload_download_began"] = True
            status = getattr(response, "status", None) or response.getcode()
            media = response.headers.get_content_type()
            diagnostics.update(http_status=status, response_media_type=media)
            if not 200 <= status < 300:
                _fail("Scryfall payload request was not successful", diagnostics,
                      "bulk_payload_response", status=status, media_type=media)
            if media not in JSONL_MEDIA_TYPES and media not in GZIP_MEDIA_TYPES:
                _fail("Scryfall returned an unsupported payload media type", diagnostics,
                      "payload_content_type", status=status, media_type=media)
            length = response.headers.get("Content-Length")
            try: expected = int(length) if length is not None else None
            except ValueError:
                _fail("Scryfall payload had an invalid content length", diagnostics,
                      "payload_stream_completion")
            if expected is not None and expected < 0:
                _fail("Scryfall payload had an invalid content length", diagnostics,
                      "payload_stream_completion")
            diagnostics["declared_content_length"] = expected
            content_encoding = response.headers.get("Content-Encoding")
            if media in GZIP_MEDIA_TYPES and (content_encoding or "").lower().strip() not in ("", "identity"):
                _fail("Scryfall gzip payload had ambiguous content encoding", diagnostics,
                      "payload_decompression")
            parsed = _parse_jsonl_stream(response, diagnostics,
                content_encoding=content_encoding,
                compression_mode="gzip" if media in GZIP_MEDIA_TYPES else None)
            if expected is not None and expected != diagnostics["bytes_downloaded"]:
                _fail("Scryfall payload stream was incomplete", diagnostics,
                      "payload_stream_completion")
            return parsed
    except urllib.error.HTTPError as error:
        _fail(f"Scryfall request failed with HTTP {error.code}", diagnostics,
              "bulk_payload_response", status=error.code, rate_limited=error.code == 429)
    except (urllib.error.URLError, TimeoutError):
        _fail("Scryfall payload request failed before completion", diagnostics,
              "bulk_payload_response")


def run(data_root: Path, *, payload_path: Path | None, retrieved_at: datetime,
        persist: bool, run_id: str, retain_payload: Path | None = None,
        observed_at_override: datetime | None = None, source_url_override: str | None = None,
        diagnostics: dict | None = None) -> dict:
    if persist:
        raise MarketValidationError("Phase 127F prohibits persist=true")
    diagnostic = diagnostics if diagnostics is not None else new_diagnostics()
    canonical_bytes = (data_root / "canonical/state.json").read_bytes()
    canonical_identity = "sha256:" + sha256_bytes(canonical_bytes)
    if payload_path:
        observed_at = observed_at_override or retrieved_at
        diagnostic.update(transport_field_selected="jsonl_download_uri", transport_format="jsonl")
        with payload_path.open("rb") as stream:
            parsed = _parse_jsonl_stream(stream, diagnostic)
    else:
        metadata = fetch(METADATA_URL, diagnostics=diagnostic)
        diagnostic["metadata_fetched"] = True
        transport = parse_bulk_metadata(metadata, diagnostic); observed_at = transport.observed_at
        if transport.format == "jsonl": parsed = download_jsonl(transport.uri, diagnostic)
        else:
            # Legacy compatibility remains bounded to existing array fixtures.
            payload = fetch(transport.uri, diagnostics=diagnostic,
                endpoint_category="scryfall_bulk_metadata", stage="bulk_payload_response")
            records = load_payload(payload)
            ids = [x.get("id") for x in records]
            if len(ids) != len(set(ids)): raise MarketValidationError("duplicate provider identity")
            parsed = ParsedPayload(tuple(x for x in records if str(x.get("set", "")).lower() == "mb2"),
                                   sha256_bytes(payload), len(records))
    records = parsed.records
    if retain_payload:
        retain_payload.write_bytes(canonical_json(list(records)))
    adapter = ScryfallMarketAdapter(json.loads(canonical_bytes), canonical_identity)
    observations, mappings = adapter.normalize(records, observed_at=observed_at,
        retrieved_at=retrieved_at, source_url="scryfall:default_cards",
        source_digest=parsed.source_digest)
    normalized = canonical_json([x.to_dict() for x in observations])
    counts = {s: sum(x["status"] == s for x in mappings)
              for s in ("matched", "unmatched", "ambiguous", "rejected")}
    known = sum(x.price is not None for x in observations)
    diagnostic.update(mapping_census=counts,
        known_price_count=known,
        explicit_missing_price_count=len(observations)-known)
    result = {"schema_version":"market-acquisition-run-v1", "run_id":run_id,
        "provider":PROVIDER, "source_dataset":SOURCE_DATASET, "source_url":"scryfall:default_cards",
        "retrieved_at":retrieved_at.isoformat().replace("+00:00","Z"),
        "source_observed_at":observed_at.isoformat().replace("+00:00","Z"), "currency":"USD",
        "target":{"set":"MB2","promoted_only":True}, "source_sha256":parsed.source_digest,
        "normalized_sha256":sha256_bytes(normalized), "canonical_snapshot_identity":canonical_identity,
        "mapping_counts":counts, "source_record_count":parsed.source_record_count,
        "mb2_record_count":len(records), "matched_printing_count":len({x.entity_id for x in observations}),
        "known_price_observation_count":known,
        "missing_price_observation_count":len(observations)-known,
        "observation_count":len(observations), "duplicate_record_count":diagnostic["duplicate_record_count"],
        "canonical_write":False, "promotion_performed":False, "persisted":False,
        "acquisition_diagnostics":diagnostic}
    return result


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--data-root",type=Path,default=Path("data"))
    parser.add_argument("--payload",type=Path); parser.add_argument("--retrieved-at",required=True)
    parser.add_argument("--run-id",required=True); parser.add_argument("--persist",action="store_true")
    parser.add_argument("--retain-payload",type=Path); parser.add_argument("--observed-at")
    args=parser.parse_args(); diagnostic=new_diagnostics()
    try:
        retrieved=datetime.fromisoformat(args.retrieved_at.replace("Z","+00:00")).astimezone(timezone.utc)
        observed=(datetime.fromisoformat(args.observed_at.replace("Z","+00:00")).astimezone(timezone.utc)
                  if args.observed_at else None)
        print(json.dumps(run(args.data_root,payload_path=args.payload,retrieved_at=retrieved,
            persist=args.persist,run_id=args.run_id,retain_payload=args.retain_payload,
            observed_at_override=observed,diagnostics=diagnostic),indent=2,sort_keys=True)); return 0
    except (ValueError,OSError,KeyError,json.JSONDecodeError,MarketValidationError,
            ProviderAcquisitionError) as error:
        report=getattr(error,"diagnostics",diagnostic)
        if report["failing_stage"] is None: report["failing_stage"]="local_validation"
        print(json.dumps({"valid":False,"error":str(error),"acquisition_diagnostics":report},
                         indent=2,sort_keys=True)); return 2


if __name__ == "__main__": raise SystemExit(main())
