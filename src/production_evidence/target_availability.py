"""Fail-closed target discovery and bounded retention for MTGJSON evidence."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "mtgjson-target-availability-v1"
SNAPSHOT_SCHEMA = "mtgjson-trusted-snapshot-v1"


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def register_trusted_snapshot(source: Path, expected_sha256: str, repository: Path) -> dict:
    """Checksum and immutably retain caller-acquired AllPrintings bytes.

    Acquisition is deliberately separate: the expected digest must come from the trusted
    delivery path.  Existing evidence is reusable only when both its manifest and bytes are
    identical; an identity collision fails closed.
    """
    raw = source.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if len(expected_sha256) != 64 or actual != expected_sha256.casefold():
        raise ValueError("source checksum verification failed")
    try:
        payload = gzip.decompress(raw) if source.name.endswith(".gz") else raw
        document = json.loads(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("source is not a readable MTGJSON document") from error
    if not isinstance(document, Mapping) or not isinstance(document.get("meta"), Mapping) \
            or not isinstance(document.get("data"), Mapping):
        raise ValueError("expected AllPrintings meta and data objects")
    meta = document["meta"]
    version, publication_date = meta.get("version"), meta.get("date")
    if not isinstance(version, str) or not version or not isinstance(publication_date, str) or not publication_date:
        raise ValueError("provider publication identity is incomplete")
    identity = f"mtgjson-allprintings-{version}+{publication_date.replace('-', '')}-{actual[:12]}"
    destination = repository / identity
    artifact_name = "AllPrintings.json.gz" if source.name.endswith(".gz") else "AllPrintings.json"
    manifest = {
        "schema_version": SNAPSHOT_SCHEMA, "evidence_identity": identity,
        "provider": "MTGJSON", "provider_version": version, "provider_date": publication_date,
        "source_sha256": actual, "retained_artifact": artifact_name,
        "retained_byte_length": len(raw), "checksum_verified": True,
        "canonical_write": False, "promotion_performed": False,
    }
    manifest_bytes = canonical_json(manifest) + b"\n"
    if destination.exists():
        artifact = destination / artifact_name
        if not artifact.is_file() or artifact.read_bytes() != raw \
                or (destination / "manifest.json").read_bytes() != manifest_bytes:
            raise FileExistsError("immutable evidence identity collision")
        return manifest
    destination.mkdir(parents=True)
    (destination / artifact_name).write_bytes(raw)
    (destination / "manifest.json").write_bytes(manifest_bytes)
    return manifest


def _contains(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return needle in value.casefold()
    if isinstance(value, Mapping):
        return any(_contains(item, needle) for item in value.values())
    if isinstance(value, list):
        return any(_contains(item, needle) for item in value)
    return False


def inspect_mtgjson_target(document: Mapping[str, Any], requested_name: str) -> dict:
    """Inventory every set-level plausible match without guessing a set code.

    Card arrays are deliberately excluded from discovery: a card name/flavour string cannot
    establish that its containing product is the independently requested set.
    """
    meta, sets = document.get("meta"), document.get("data")
    if not isinstance(meta, Mapping) or not isinstance(sets, Mapping):
        return {"schema_version": SCHEMA, "provider": "MTGJSON", "requested_name": requested_name,
                "status": "unsupported_by_current_adapter", "plausible_target_count": 0,
                "matches": [], "blockers": ["expected AllPrintings meta and data objects"]}
    needle = requested_name.casefold().strip()
    matches = []
    for key, value in sorted(sets.items(), key=lambda item: str(item[0]).casefold()):
        if not isinstance(value, Mapping):
            continue
        set_metadata = {name: item for name, item in value.items() if name != "cards"}
        if _contains(set_metadata, needle):
            code = value.get("code") or key
            matches.append({"data_key": key, "code": code, "name": value.get("name"),
                            "parent_code": value.get("parentCode"),
                            "release_date": value.get("releaseDate"),
                            "set_type": value.get("type"), "set_metadata": set_metadata})
    if not matches:
        status, blockers = "not_yet_published_by_provider", ["no set-level metadata matched the requested name"]
    elif len(matches) > 1:
        status, blockers = "ambiguous_with_another_product", ["multiple set-level targets are plausible"]
    else:
        match = matches[0]
        missing = [field for field in ("code", "name") if not match.get(field)]
        status = "present_but_incomplete" if missing else "present_and_uniquely_identifiable"
        blockers = (["unique target lacks required identity fields: " + ", ".join(missing)] if missing else [])
    return {"schema_version": SCHEMA, "provider": "MTGJSON", "requested_name": requested_name,
            "provider_version": meta.get("version"), "provider_date": meta.get("date"),
            "status": status, "plausible_target_count": len(matches), "matches": matches,
            "blockers": blockers}


def bounded_target_evidence(document: Mapping[str, Any], availability: Mapping[str, Any],
                            source_sha256: str) -> dict:
    """Return a deterministic one-set projection only after unique availability succeeds."""
    if availability.get("status") != "present_and_uniquely_identifiable":
        raise ValueError("target availability is not uniquely identifiable")
    match = availability["matches"][0]
    target = document["data"][match["data_key"]]
    projection = {"schema_version": "mtgjson-bounded-target-evidence-v1", "provider": "MTGJSON",
                  "source_sha256": source_sha256, "provider_meta": document["meta"],
                  "target_code": match["code"], "target_name": match["name"], "target_payload": target,
                  "canonical_write": False, "promotion_performed": False}
    projection_sha256 = hashlib.sha256(canonical_json(projection)).hexdigest()
    return {**projection, "projection_sha256": projection_sha256,
            "evidence_identity": f"mtgjson-target-{str(match['code']).casefold()}-{projection_sha256[:16]}"}
