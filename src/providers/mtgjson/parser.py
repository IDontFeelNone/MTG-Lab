"""Deterministic parsing for local MTGJSON artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .validator import MTGJSONValidationError, validate_document


def parse_dataset(source: Path | str | bytes) -> Mapping[str, Any]:
    """Decode and validate a supplied artifact without modifying it or canonical state."""
    payload = source if isinstance(source, bytes) else Path(source).read_bytes()
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MTGJSONValidationError("artifact is not valid UTF-8 JSON") from error
    validate_document(document)
    return document
