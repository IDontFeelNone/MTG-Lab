"""Verify observations without editing either raw observations or canonical data."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


class ObservationError(ValueError):
    """An observation or derived record violates the append-only contract."""


def normalize_card_name(name: str) -> str:
    """Produce a conservative lookup key while retaining the reported name elsewhere."""
    value = unicodedata.normalize("NFKC", name).casefold().replace("’", "'")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def canonical_json(document: Mapping[str, Any]) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


class ObservationVerifier:
    """Resolve reported names against a read-only caller-supplied canonical index."""

    def __init__(self, canonical_cards: Iterable[Mapping[str, Any]], *, verifier: str):
        self.verifier = verifier
        self._index: dict[str, list[Mapping[str, Any]]] = {}
        for card in canonical_cards:
            self._index.setdefault(normalize_card_name(str(card["name"])), []).append(card)

    def verify(self, raw: Mapping[str, Any], *, verified_at: str | None = None) -> dict[str, Any]:
        raw_bytes = canonical_json(raw)
        results = []
        for reported in raw.get("cards", []):
            normalized = normalize_card_name(str(reported["reported_name"]))
            matches = self._index.get(normalized, [])
            result: dict[str, Any] = {
                "position": reported["position"], "reported_name": reported["reported_name"],
                "normalized_name": normalized,
                "verification_status": "verified" if len(matches) == 1 else ("ambiguous" if matches else "unmatched"),
                "canonical_card_id": matches[0]["id"] if len(matches) == 1 else None,
                "canonical_printing_id": matches[0].get("printing_id") if len(matches) == 1 else None,
            }
            if len(matches) > 1:
                result["candidate_card_ids"] = sorted(str(item["id"]) for item in matches)
            results.append(result)
        return {
            "schema_version": "v1", "observation_id": raw["observation_id"],
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "verified_at": verified_at or datetime.now(timezone.utc).isoformat(),
            "verifier": self.verifier, "cards": results,
        }


class VerificationStore:
    """Write immutable derived verification records outside canonical storage."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def save(self, record: Mapping[str, Any]) -> Path:
        path = self.root / f"{record['observation_id']}.verification.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = canonical_json(record)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as error:
            raise ObservationError(f"immutable verification already exists: {path}") from error
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
        return path

    @staticmethod
    def assert_matches_raw(record: Mapping[str, Any], raw: Mapping[str, Any]) -> None:
        digest = hashlib.sha256(canonical_json(raw)).hexdigest()
        if record.get("raw_sha256") != digest:
            raise ObservationError("raw observation has changed since verification")
