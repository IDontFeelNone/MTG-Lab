"""Immutable, bounded retention of MTGJSON printings for the Phase 135 pilot."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping

from providers.mtgjson.streaming import StreamingMTGJSONPlanner, sha256_file

PILOT = (
    "Brainstorm", "Command Tower", "Counterspell", "Goblin Charbelcher", "Goblin King",
    "Sol Ring", "Swords to Plowshares", "Treasure Cruise", "Walking Ballista",
    "Wishclaw Talisman",
)
FILES = ("acquisition-report.json", "manifest.json", "source-pilot-printings.json")
SCHEMA = "mtgjson-pilot-printing-retention-v1"
SAFE_RUN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, separators=(",", ": "),
                       ensure_ascii=False) + "\n").encode()


def _unknown(value: Any) -> Any:
    return value if value is not None else "unknown"


def _printing(card: Mapping[str, Any], source_set: Mapping[str, Any], meta: Mapping[str, Any]) -> dict:
    identifiers = card.get("identifiers") if isinstance(card.get("identifiers"), Mapping) else {}
    return {
        "provider_printing_id": card["uuid"],
        "provider_card_or_oracle_id": _unknown(identifiers.get("scryfallOracleId")),
        "card_name": card["name"], "set_name": _unknown(source_set.get("name")),
        "set_code": _unknown(source_set.get("code")),
        "collector_number": _unknown(card.get("number")),
        "release_date": _unknown(source_set.get("releaseDate")),
        "language": _unknown(card.get("language", "English")),
        "finishes": _unknown(card.get("finishes")), "rarity": _unknown(card.get("rarity")),
        "frame_or_treatment": _unknown(card.get("frameVersion", card.get("frameEffects"))),
        "promotional": _unknown(card.get("isPromo")), "reprint": _unknown(card.get("isReprint")),
        "digital_or_paper": "digital" if card.get("isOnlineOnly") is True else (
            "paper" if card.get("isOnlineOnly") is False else "unknown"),
        "source_record_identity": f"{source_set.get('code', 'unknown')}:{card['uuid']}",
        "dataset_publication_timestamp": _unknown(meta.get("date")),
    }


class PilotPrintingRetention:
    """Acquire once, stream-select the pilot, then atomically publish three files."""

    def __init__(self, repository: Path | str, downloader: Callable[[str, Path], Mapping[str, Any]]):
        self.repository, self.downloader = Path(repository), downloader

    def acquire(self, *, run_id: str, source_url: str, canonical_snapshot: str,
                acquired_at: str) -> dict:
        if not SAFE_RUN.fullmatch(run_id) or Path(run_id).name != run_id:
            raise ValueError("unsafe acquisition run identity")
        if self.repository.is_symlink() or any(parent.is_symlink() for parent in self.repository.parents):
            raise ValueError("symlink evidence path is forbidden")
        try:
            parsed_acquired_at = datetime.fromisoformat(acquired_at.replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            raise ValueError("acquisition timestamp must be UTC RFC 3339") from None
        if not acquired_at.endswith("Z") or parsed_acquired_at.tzinfo != timezone.utc:
            raise ValueError("acquisition timestamp must be UTC RFC 3339")
        destination = self.repository / run_id
        staging = Path(tempfile.mkdtemp(prefix=f".{run_id}.", dir=self.repository.parent))
        source = staging / "AllPrintings.json.gz"
        try:
            transport = dict(self.downloader(source_url, source))  # exactly one call
            if transport.get("status") != 200:
                raise ValueError("provider transport did not return HTTP 200")
            content_type = str(transport.get("content_type", "")).split(";", 1)[0]
            if content_type not in {"application/gzip", "application/octet-stream"}:
                raise ValueError("unexpected provider content type")
            if source.read_bytes()[:2] != b"\x1f\x8b":
                raise ValueError("expected gzip-compressed provider source")
            if source.stat().st_size == 0:
                raise ValueError("empty provider source")
            source_digest = sha256_file(source)
            expected_digest = transport.get("expected_sha256")
            if expected_digest is not None and source_digest != expected_digest:
                raise ValueError("provider checksum verification failed")
            result = self.retain(source=source, run_id=run_id, source_url=source_url,
                                 canonical_snapshot=canonical_snapshot, acquired_at=acquired_at,
                                 transport=transport, destination=staging / "publication")
            self._publish(staging / "publication", destination)
            return result
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def retain(self, *, source: Path, run_id: str, source_url: str, canonical_snapshot: str,
               acquired_at: str, transport: Mapping[str, Any], destination: Path) -> dict:
        meta = StreamingMTGJSONPlanner._meta(source)
        records, seen, oracle_by_name = [], {}, defaultdict(set)
        counts, census = Counter(), Counter(scanned=0, malformed=0, ambiguous=0, unsupported=0)
        for _, source_set in StreamingMTGJSONPlanner._sets(source):
            cards = source_set.get("cards")
            if not isinstance(cards, list):
                census["malformed"] += 1; continue
            for card in cards:
                census["scanned"] += 1
                if not isinstance(card, Mapping) or not isinstance(card.get("name"), str):
                    census["malformed"] += 1; continue
                if card["name"] not in PILOT or str(source_set.get("code", "")).upper() == "MB2":
                    continue
                if not isinstance(card.get("uuid"), str) or not card["uuid"]:
                    census["unsupported"] += 1; continue
                record = _printing(card, source_set, meta)
                identity = record["provider_printing_id"]
                if identity in seen:
                    if seen[identity] != record: raise ValueError("conflicting provider printing identity")
                    census["duplicates"] += 1; continue
                seen[identity] = record
                oracle = record["provider_card_or_oracle_id"]
                if oracle != "unknown": oracle_by_name[card["name"]].add(oracle)
                records.append(record); counts[card["name"]] += 1
        for values in oracle_by_name.values():
            if len(values) > 1: census["ambiguous"] += 1
        records.sort(key=lambda row: row["provider_printing_id"])
        projection = {"schema_version": SCHEMA, "provider": "MTGJSON",
                      "dataset": "AllPrintings.json.gz", "pilot_printings": records}
        projection_bytes = canonical_bytes(projection)
        source_digest, projection_digest = sha256_file(source), hashlib.sha256(projection_bytes).hexdigest()
        missing = [name for name in PILOT if not counts[name]]
        manifest = {
            "schema_version": SCHEMA, "acquisition_run_id": run_id, "provider": "MTGJSON",
            "provider_dataset_identity": "AllPrintings.json.gz", "provider_version": meta.get("version"),
            "dataset_publication_timestamp": meta.get("date"), "acquisition_timestamp": acquired_at,
            "source_url_descriptor": source_url, "source_content_type": transport.get("content_type"),
            "source_compression": "gzip", "source_byte_count": source.stat().st_size,
            "source_sha256": source_digest, "normalized_projection_byte_count": len(projection_bytes),
            "normalized_projection_sha256": projection_digest, "pilot_scope": list(PILOT),
            "source_record_count_scanned": census["scanned"], "matching_card_record_count": len(records),
            "retained_printing_count": len(records), "printing_counts_by_pilot_card": dict(sorted(counts.items())),
            "unmatched_pilot_cards": missing, "ambiguous_records": census["ambiguous"],
            "duplicates": census["duplicates"], "malformed_records": census["malformed"],
            "unsupported_records": census["unsupported"], "license": "CC BY 4.0",
            "attribution": "MTGJSON AllPrintings", "provenance": "Official MTGJSON API v5",
            "retention_terms": "bounded attributed projection permitted under CC BY 4.0",
            "canonical_snapshot_identity": canonical_snapshot, "canonical_write": False,
            "promotion_performed": False, "facts_created": False,
        }
        report = {"schema_version": SCHEMA, "status": "retained" if not missing else "incomplete",
                  "manifest_sha256": hashlib.sha256(canonical_bytes(manifest)).hexdigest(),
                  "retained_file_inventory": list(FILES), "canonical_write": False,
                  "promotion_performed": False, "facts_created": False, "market_write": False}
        destination.mkdir(parents=True)
        (destination / "source-pilot-printings.json").write_bytes(projection_bytes)
        (destination / "manifest.json").write_bytes(canonical_bytes(manifest))
        (destination / "acquisition-report.json").write_bytes(canonical_bytes(report))
        return {"manifest": manifest, "report": report}

    @staticmethod
    def _publish(staging: Path, destination: Path) -> None:
        if tuple(sorted(x.name for x in staging.iterdir())) != FILES:
            raise ValueError("invalid retained-file inventory")
        if destination.exists():
            if not destination.is_dir() or any((destination / name).read_bytes() != (staging / name).read_bytes()
                                                for name in FILES):
                raise FileExistsError("conflicting acquisition replay")
            return
        os.replace(staging, destination)
