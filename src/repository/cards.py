"""Canonical Card and Printing repository loading and validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from validation import SchemaValidationError, validate_document

_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_DEFAULT_GAMES_ROOT = Path(__file__).resolve().parents[2] / "data/canonical/games"


class CardRepositoryError(ValueError):
    """Raised when canonical Card or Printing data is not safe to consume."""


def card_record_path(game: str, card_id: str, *, games_root: Path | None = None) -> Path:
    """Return the canonical Card path for stable identifiers."""
    return _entity_path(game, "cards", card_id, "card.json", games_root)


def printing_record_path(
    game: str, printing_id: str, *, games_root: Path | None = None
) -> Path:
    """Return the canonical Printing path for stable identifiers."""
    return _entity_path(game, "printings", printing_id, "printing.json", games_root)


def load_card(game: str, card_id: str, *, games_root: Path | None = None) -> Mapping[str, Any]:
    """Load one structurally valid Card whose identity matches its path."""
    document = _load(card_record_path(game, card_id, games_root=games_root), "card")
    if document["id"] != card_id or document["game"] != game:
        raise CardRepositoryError("Card identifiers do not match its canonical path")
    _validate_provenance(game, document, games_root)
    return document


def load_printing(
    game: str, printing_id: str, *, games_root: Path | None = None
) -> Mapping[str, Any]:
    """Load one structurally valid Printing whose identity matches its path."""
    document = _load(printing_record_path(game, printing_id, games_root=games_root), "printing")
    if document["id"] != printing_id:
        raise CardRepositoryError("Printing identifier does not match its canonical path")
    _validate_provenance(game, document, games_root)
    return document


def load_card_repository(
    game: str, *, games_root: Path | None = None
) -> tuple[tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...]]:
    """Load the complete game repository and enforce Printing-to-Card references."""
    _validate_identifier("game", game)
    root = Path(games_root) if games_root is not None else _DEFAULT_GAMES_ROOT
    game_root = root / game
    cards = tuple(
        load_card(game, path.parent.name, games_root=root)
        for path in sorted((game_root / "cards").glob("*/card.json"))
    )
    printings = tuple(
        load_printing(game, path.parent.name, games_root=root)
        for path in sorted((game_root / "printings").glob("*/printing.json"))
    )
    _reject_duplicates(cards, "Card")
    _reject_duplicates(printings, "Printing")
    card_ids = {card["id"] for card in cards}
    for printing in printings:
        if printing["card_id"] not in card_ids:
            raise CardRepositoryError(
                f"Printing {printing['id']} references missing Card {printing['card_id']}"
            )
    return cards, printings


def canonical_repository_bytes(game: str, *, games_root: Path | None = None) -> bytes:
    """Return a deterministic JSON snapshot of validated Card and Printing data."""
    cards, printings = load_card_repository(game, games_root=games_root)
    snapshot = {"schema_version": "v1", "game": game, "cards": cards, "printings": printings}
    return (json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _entity_path(
    game: str, kind: str, entity_id: str, filename: str, games_root: Path | None
) -> Path:
    _validate_identifier("game", game)
    _validate_identifier(f"{kind[:-1]}_id", entity_id)
    root = Path(games_root) if games_root is not None else _DEFAULT_GAMES_ROOT
    return root / game / kind / entity_id / filename


def _load(path: Path, schema: str) -> Mapping[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CardRepositoryError(f"Canonical {schema} record not found: {path}") from error
    except json.JSONDecodeError as error:
        raise CardRepositoryError(f"Canonical {schema} record is not valid JSON: {path}") from error
    if not isinstance(document, dict):
        raise CardRepositoryError(f"Canonical {schema} record must be an object: {path}")
    try:
        validate_document(document, schema)
    except SchemaValidationError as error:
        raise CardRepositoryError(f"Invalid canonical {schema} record {path}: {error}") from error
    return document


def _validate_provenance(
    game: str, document: Mapping[str, Any], games_root: Path | None
) -> None:
    root = Path(games_root) if games_root is not None else _DEFAULT_GAMES_ROOT
    covered_fields: set[str] = set()
    evidence = document.get("assertions", document.get("provenance", ()))
    for provenance in evidence:
        source_id = provenance["source_id"]
        source = _load(root / game / "sources" / f"{source_id}.json", "source-record")
        if source["id"] != source_id:
            raise CardRepositoryError("Source identifier does not match its canonical path")
        covered_fields.update(provenance.get("field_paths", ()))
        if "path" in provenance:
            path = provenance["path"].lstrip("/").split("/", 1)[0]
            covered_fields.add(path)
    required_fields = set(document) - {"schema_version", "provenance", "assertions", "metadata"}
    unknown = covered_fields - required_fields - {"metadata"}
    if unknown:
        raise CardRepositoryError(
            f"Canonical {document['id']} has provenance for unknown fields: "
            f"{', '.join(sorted(unknown))}"
        )
    missing = required_fields - covered_fields
    if missing:
        raise CardRepositoryError(
            f"Canonical {document['id']} lacks field provenance for: {', '.join(sorted(missing))}"
        )
    promoted: dict[str, object] = {}
    for assertion in document.get("assertions", ()):
        if assertion["status"] != "promoted":
            continue
        path = assertion["path"]
        if path in promoted and promoted[path] != assertion["asserted_value"]:
            raise CardRepositoryError(f"Canonical {document['id']} has contradictory promoted facts at {path}")
        promoted[path] = assertion["asserted_value"]


def _reject_duplicates(documents: tuple[Mapping[str, Any], ...], label: str) -> None:
    identifiers = [document["id"] for document in documents]
    duplicates = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
    if duplicates:
        raise CardRepositoryError(f"Duplicate {label} identifiers: {', '.join(duplicates)}")


def _validate_identifier(label: str, value: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a stable lowercase identifier")


__all__ = [
    "CardRepositoryError", "canonical_repository_bytes", "card_record_path", "load_card",
    "load_card_repository", "load_printing", "printing_record_path",
]
