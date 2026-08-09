"""Strict review of the bounded Phase 142 Scryfall/EDHREC rank projection."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "card-demand-evidence-v1"
PILOT_NAMES = ("Brainstorm", "Command Tower", "Counterspell", "Goblin Charbelcher",
               "Goblin King", "Sol Ring", "Swords to Plowshares", "Treasure Cruise",
               "Walking Ballista", "Wishclaw Talisman")
REQUIRED_RECORD = {"card_id", "card_name", "canonical_oracle_id", "provider_printing_id",
                   "metric", "rank", "dataset_timestamp", "provider"}


class DemandEvidenceError(ValueError):
    """Retained usage evidence is malformed or cannot be mapped unambiguously."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n").encode()


def load_reviewed_demand(path: Path) -> dict[str, Any]:
    """Load and verify the complete, exactly-ten-record retained projection."""
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"schema_version", "evidence_source_id", "provider", "source_dataset",
                "source_endpoint", "dataset_timestamp", "retrieved_at", "source_sha256",
                "license_considerations", "metric_semantics", "identity_mapping",
                "completeness", "records", "records_sha256"}
    if not isinstance(document, dict) or set(document) != required or document["schema_version"] != SCHEMA:
        raise DemandEvidenceError("invalid demand evidence envelope")
    if document["provider"] != "scryfall" or document["source_dataset"] != "scryfall-default-cards":
        raise DemandEvidenceError("unsupported provider identity")
    records = document["records"]
    if not isinstance(records, list) or len(records) != 10:
        raise DemandEvidenceError("demand evidence must contain exactly ten records")
    if hashlib.sha256(canonical_bytes(records)).hexdigest() != document["records_sha256"]:
        raise DemandEvidenceError("demand evidence records digest mismatch")
    names, cards, oracle_ids, printing_ids = [], [], [], []
    for record in records:
        if not isinstance(record, dict) or set(record) != REQUIRED_RECORD:
            raise DemandEvidenceError("demand evidence record has missing or unexpected fields")
        if record["provider"] != "scryfall" or record["metric"] != "edhrec_rank":
            raise DemandEvidenceError("unsupported provider metric")
        if not isinstance(record["rank"], int) or isinstance(record["rank"], bool) or record["rank"] < 1:
            raise DemandEvidenceError("rank must be a positive integer")
        if record["dataset_timestamp"] != document["dataset_timestamp"]:
            raise DemandEvidenceError("conflicting dataset timestamp")
        names.append(record["card_name"]); cards.append(record["card_id"])
        oracle_ids.append(record["canonical_oracle_id"]); printing_ids.append(record["provider_printing_id"])
    if tuple(names) != PILOT_NAMES:
        raise DemandEvidenceError("records must use the sorted exact ten-card pilot")
    if any(len(values) != len(set(values)) for values in (cards, oracle_ids, printing_ids)):
        raise DemandEvidenceError("duplicate or conflicting card identity")
    return document
