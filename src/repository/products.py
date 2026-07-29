"""Generic loading for canonical product definitions."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from validation import SchemaValidationError, validate_document

_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_DEFAULT_GAMES_ROOT = Path(__file__).resolve().parents[2] / "data" / "canonical" / "games"


class ProductLoadError(ValueError):
    """Raised when a canonical product record cannot be loaded safely."""


def product_record_path(
    game: str, product_id: str, *, games_root: Path | None = None
) -> Path:
    """Return the canonical path for a product record without reading it."""
    _validate_identifier("game", game)
    _validate_identifier("product_id", product_id)
    root = Path(games_root) if games_root is not None else _DEFAULT_GAMES_ROOT
    return root / game / "products" / product_id / "product.json"


def load_product(
    game: str, product_id: str, *, games_root: Path | None = None
) -> Mapping[str, Any]:
    """Load and validate a canonical product record by stable identifiers."""
    record_path = product_record_path(game, product_id, games_root=games_root)
    try:
        with record_path.open(encoding="utf-8") as product_file:
            document = json.load(product_file)
    except FileNotFoundError as error:
        raise ProductLoadError(f"Product record not found: {record_path}") from error
    except json.JSONDecodeError as error:
        raise ProductLoadError(f"Product record is not valid JSON: {record_path}") from error

    if not isinstance(document, dict):
        raise ProductLoadError(f"Product record must be an object: {record_path}")

    try:
        validate_document(document, "product")
    except SchemaValidationError as error:
        raise ProductLoadError(f"Invalid product record {record_path}: {error}") from error

    if document["game"] != game or document["id"] != product_id:
        raise ProductLoadError(
            f"Product record identifiers do not match its canonical path: {record_path}"
        )
    return document


def _validate_identifier(label: str, value: str) -> None:
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a stable lowercase identifier")


__all__ = ["ProductLoadError", "load_product", "product_record_path"]
