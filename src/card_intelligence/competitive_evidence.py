"""Fail-closed validation for a not-yet-admitted competitive evidence snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA = Path(__file__).parents[1] / "schemas/v1/card-competitive-evidence.schema.json"


def records_digest(records: list[dict[str, Any]]) -> str:
    payload = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_competitive_snapshot(path: Path, *, require_acquisition_ready: bool = True) -> dict[str, Any]:
    """Validate shape, replay identity, scope, and the licensing admission gate.

    This deliberately performs no network request and creates no knowledge fact.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document),
                    key=lambda error: list(error.absolute_path))
    if errors:
        where = ".".join(map(str, errors[0].absolute_path)) or "<root>"
        raise ValueError(f"competitive evidence schema error at {where}: {errors[0].message}")
    if records_digest(document["records"]) != document["records_sha256"]:
        raise ValueError("competitive evidence records digest mismatch")
    identities = [(r["source_record_identity"], r["card_identity"]["card_id"])
                  for r in document["records"]]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate source-record/card identity")
    if require_acquisition_ready:
        review = document["license_review"]
        if review["status"] != "approved" or not review["retention_permitted"]:
            raise ValueError("competitive acquisition blocked: retention rights are not approved")
    return document


__all__ = ["records_digest", "validate_competitive_snapshot"]
