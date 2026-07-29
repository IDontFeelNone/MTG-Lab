"""Canonical Print Sheet and Slot repository loading and validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from validation import SchemaValidationError, validate_document

from .cards import load_card_repository
from .products import load_product

_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_DEFAULT_GAMES_ROOT = Path(__file__).resolve().parents[2] / "data/canonical/games"


class RulesRepositoryError(ValueError):
    """Raised when canonical Print Sheet or Slot data is unsafe to consume."""


def print_sheet_record_path(
    game: str, print_sheet_id: str, *, games_root: Path | None = None
) -> Path:
    return _entity_path(game, "print_sheets", print_sheet_id, "print-sheet.json", games_root)


def slot_record_path(game: str, slot_id: str, *, games_root: Path | None = None) -> Path:
    return _entity_path(game, "slots", slot_id, "slot.json", games_root)


def load_print_sheet(
    game: str, print_sheet_id: str, *, games_root: Path | None = None
) -> Mapping[str, Any]:
    document = _load(print_sheet_record_path(game, print_sheet_id, games_root=games_root), "print-sheet")
    if document["id"] != print_sheet_id or document["game"] != game:
        raise RulesRepositoryError("Print Sheet identifiers do not match its canonical path")
    _validate_provenance(game, document, games_root)
    return document


def load_slot(game: str, slot_id: str, *, games_root: Path | None = None) -> Mapping[str, Any]:
    document = _load(slot_record_path(game, slot_id, games_root=games_root), "slot")
    if document["id"] != slot_id or document["game"] != game:
        raise RulesRepositoryError("Slot identifiers do not match its canonical path")
    _validate_provenance(game, document, games_root)
    return document


def load_rules_repository(
    game: str, *, games_root: Path | None = None
) -> tuple[tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...]]:
    """Load rule records and validate the complete canonical dependency graph."""
    _validate_identifier("game", game)
    root = Path(games_root) if games_root is not None else _DEFAULT_GAMES_ROOT
    game_root = root / game
    _, printings = load_card_repository(game, games_root=root)
    sheets = tuple(
        load_print_sheet(game, path.parent.name, games_root=root)
        for path in sorted((game_root / "print_sheets").glob("*/print-sheet.json"))
    )
    slots = tuple(
        load_slot(game, path.parent.name, games_root=root)
        for path in sorted((game_root / "slots").glob("*/slot.json"))
    )
    _reject_duplicates(sheets, "Print Sheet")
    _reject_duplicates(slots, "Slot")
    printing_ids = {printing["id"] for printing in printings}
    for sheet in sheets:
        entry_ids = [entry["printing_id"] for entry in sheet["entries"]]
        duplicates = sorted({item for item in entry_ids if entry_ids.count(item) > 1})
        if duplicates:
            raise RulesRepositoryError(
                f"Print Sheet {sheet['id']} has duplicate Printing entries: {', '.join(duplicates)}"
            )
        for printing_id in entry_ids:
            if printing_id not in printing_ids:
                raise RulesRepositoryError(
                    f"Print Sheet {sheet['id']} references missing Printing {printing_id}"
                )
    sheet_ids = {sheet["id"] for sheet in sheets}
    for slot in slots:
        if slot["print_sheet_id"] not in sheet_ids:
            raise RulesRepositoryError(
                f"Slot {slot['id']} references missing Print Sheet {slot['print_sheet_id']}"
            )
    slot_ids = {slot["id"] for slot in slots}
    for path in sorted((game_root / "products").glob("*/product.json")):
        product = load_product(game, path.parent.name, games_root=root)
        for slot_id in product["slot_ids"]:
            if slot_id not in slot_ids:
                raise RulesRepositoryError(
                    f"Product {product['id']} references missing Slot {slot_id}"
                )
    return sheets, slots


def canonical_rules_repository_bytes(game: str, *, games_root: Path | None = None) -> bytes:
    sheets, slots = load_rules_repository(game, games_root=games_root)
    snapshot = {"schema_version": "v1", "game": game, "print_sheets": sheets, "slots": slots}
    return (json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _entity_path(game: str, kind: str, entity_id: str, filename: str,
                 games_root: Path | None) -> Path:
    _validate_identifier("game", game)
    _validate_identifier(f"{kind[:-1]}_id", entity_id)
    root = Path(games_root) if games_root is not None else _DEFAULT_GAMES_ROOT
    return root / game / kind / entity_id / filename


def _load(path: Path, schema: str) -> Mapping[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RulesRepositoryError(f"Canonical {schema} record not found: {path}") from error
    except json.JSONDecodeError as error:
        raise RulesRepositoryError(f"Canonical {schema} record is not valid JSON: {path}") from error
    if not isinstance(document, dict):
        raise RulesRepositoryError(f"Canonical {schema} record must be an object: {path}")
    try:
        validate_document(document, schema)
    except SchemaValidationError as error:
        raise RulesRepositoryError(f"Invalid canonical {schema} record {path}: {error}") from error
    return document


def _validate_provenance(game: str, document: Mapping[str, Any], games_root: Path | None) -> None:
    root = Path(games_root) if games_root is not None else _DEFAULT_GAMES_ROOT
    covered: set[str] = set()
    for provenance in document["provenance"]:
        source_id = provenance["source_id"]
        source = _load(root / game / "sources" / f"{source_id}.json", "source-record")
        if source["id"] != source_id:
            raise RulesRepositoryError("Source identifier does not match its canonical path")
        covered.update(provenance["field_paths"])
    required = set(document) - {"schema_version", "provenance", "metadata"}
    unknown = covered - required - {"metadata"}
    if unknown:
        raise RulesRepositoryError(
            f"Canonical {document['id']} has provenance for unknown fields: {', '.join(sorted(unknown))}"
        )
    missing = required - covered
    if missing:
        raise RulesRepositoryError(
            f"Canonical {document['id']} lacks field provenance for: {', '.join(sorted(missing))}"
        )


def _reject_duplicates(documents: tuple[Mapping[str, Any], ...], label: str) -> None:
    identifiers = [document["id"] for document in documents]
    duplicates = sorted({item for item in identifiers if identifiers.count(item) > 1})
    if duplicates:
        raise RulesRepositoryError(f"Duplicate {label} identifiers: {', '.join(duplicates)}")


def _validate_identifier(label: str, value: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a stable lowercase identifier")


__all__ = [
    "RulesRepositoryError", "canonical_rules_repository_bytes", "load_print_sheet",
    "load_rules_repository", "load_slot", "print_sheet_record_path", "slot_record_path",
]
