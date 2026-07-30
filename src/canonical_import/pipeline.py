"""Generic, local-only Canonical Import Pipeline v1."""
from __future__ import annotations

import csv
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from repository.canonical import CanonicalRepository, CanonicalRepositoryError

IMPORTER_VERSION = "1.0.0"
KINDS = ("cards", "printings", "products", "treatments", "finishes", "rarities",
         "product_versions", "packs", "slots", "sheets")
REQUIRED = {
    "cards": ("id", "name"), "printings": ("id", "card_id", "rarity"),
    "products": ("id", "name", "product_type"),
    "treatments": ("id", "name"), "finishes": ("id", "name"),
    "rarities": ("id", "name"),
    "product_versions": ("id", "product_id", "name", "pack_definition_ids"),
    "packs": ("id", "product_version_id", "name", "slot_ids"),
    "slots": ("id", "name", "sheet_id", "count"),
    "sheets": ("id", "name", "entries"),
}

class ImportError(ValueError): pass

class SourceAdapter(ABC):
    """A reviewed local source; adapters never perform network requests."""
    @abstractmethod
    def load(self) -> Mapping[str, Any]: ...

class JSONSource(SourceAdapter):
    def __init__(self, path: str | Path): self.path = Path(path)
    def load(self) -> Mapping[str, Any]:
        try: value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error: raise ImportError(f"Invalid JSON source: {error}") from error
        if not isinstance(value, dict): raise ImportError("Dataset must be a JSON object")
        return value

class CSVSource(SourceAdapter):
    """Directory adapter: dataset.json metadata plus one optional <kind>.csv per kind."""
    def __init__(self, path: str | Path): self.path = Path(path)
    def load(self) -> Mapping[str, Any]:
        value = JSONSource(self.path / "dataset.json").load()
        for kind in KINDS:
            file = self.path / f"{kind}.csv"
            if file.exists():
                with file.open(newline="", encoding="utf-8") as stream:
                    value[kind] = list(csv.DictReader(stream))
        return value

@dataclass(frozen=True)
class ImportReport:
    game: str; source: str; source_version: str; dataset_hash: str
    created: int; updated: int; unchanged: int; applied: bool; validation_only: bool
    coverage: Mapping[str, int] = field(default_factory=dict)
    conflicts: tuple[str, ...] = ()
    def to_dict(self): return asdict(self)

def _stable(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()

def import_dataset(adapter: SourceAdapter, game: str, *, games_root: Path | None = None,
                   dry_run: bool = False, validation_only: bool = False,
                   timestamp: str | None = None) -> ImportReport:
    data = dict(adapter.load())
    for key in ("schema_version", "source", "source_version", "review_status"):
        if not data.get(key): raise ImportError(f"Dataset missing required field: {key}")
    if data["schema_version"] not in {"v1", "v3"}: raise ImportError("Unsupported dataset schema_version")
    if data["review_status"] != "reviewed": raise ImportError("Dataset is not reviewed")
    if data.get("game", game) != game: raise ImportError("Dataset game does not match requested game")
    dataset_hash = hashlib.sha256(_stable(data)).hexdigest()
    # A reviewed timestamp (or explicit caller timestamp) makes byte output replayable.
    imported_at = timestamp or data.get("import_timestamp") or "1970-01-01T00:00:00+00:00"
    provenance = {"source": data["source"], "source_version": str(data["source_version"]),
                  "import_timestamp": imported_at, "importer_version": IMPORTER_VERSION,
                  "review_status": data["review_status"], "dataset_hash": dataset_hash}
    paths: dict[str, Mapping[str, Any]] = {}
    seen: set[tuple[str, str]] = set()
    for kind in KINDS:
        rows = data.get(kind, [])
        if not isinstance(rows, list): raise ImportError(f"{kind} must be an array")
        for raw in rows:
            if not isinstance(raw, dict): raise ImportError(f"{kind} records must be objects")
            required = REQUIRED[kind]
            if data["schema_version"] == "v3" and kind == "cards":
                required = ("id", "game", "name", "normalized_name", "layout", "assertions")
            elif data["schema_version"] == "v3" and kind == "printings":
                required = ("id", "card_id", "set_id", "collector_number", "language", "assertions")
            missing = [x for x in required if x not in raw]
            if missing: raise ImportError(f"Invalid {kind} record; missing: {', '.join(missing)}")
            identity = (kind, str(raw["id"]))
            if identity in seen: raise ImportError(f"Duplicate {kind} identifier: {raw['id']}")
            seen.add(identity)
            record = dict(raw); metadata = dict(record.get("metadata", {})); metadata["import_provenance"] = provenance
            record["metadata"] = metadata
            if kind in ("cards", "products"): record.setdefault("game", game)
            if kind in ("treatments", "finishes", "rarities"): record.setdefault("game_id", game)
            if kind == "cards":
                record.setdefault("schema_version", data["schema_version"])
                fields = sorted(set(record) - {"schema_version", "provenance"})
                if record["schema_version"] == "v1":
                    record["provenance"] = [{"source_id": str(data["source"]), "field_paths": fields,
                                              "claim": "Imported from reviewed canonical dataset."}]
                elif "assertions" not in record:
                    raise ImportError("v3 cards must preserve explicit assertions")
            if kind == "printings":
                record.setdefault("schema_version", data["schema_version"])
                if record["schema_version"] == "v1": record.setdefault("set_code", "UNKNOWN")
                record.setdefault("collector_number", record["id"])
                fields = sorted(set(record) - {"schema_version", "provenance", "metadata"})
                if record["schema_version"] == "v1":
                    record["provenance"] = [{"source_id": str(data["source"]), "field_paths": fields,
                                              "claim": "Imported from reviewed canonical dataset."}]
                elif "assertions" not in record:
                    raise ImportError("v3 printings must preserve explicit assertions")
            if kind == "products":
                record.setdefault("schema_version", "v1"); record.setdefault("lifecycle_status", "foundation"); record.setdefault("slot_ids", [])
                record["provenance"] = [{"claim": "Imported from reviewed canonical dataset.", "source_classification": "internal",
                                          "source_location": str(data["source"]), "verification_status": "confirmed"}]
            path = f"{kind}/{record['id']}.json"
            if kind == "cards": path = f"cards/{record['id']}/card.json"
            elif kind == "printings": path = f"printings/{record['id']}/printing.json"
            elif kind == "products": path = f"products/{record['id']}/product.json"
            paths[path] = record
    # Validate the complete prospective state using the repository transaction on a disposable root.
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "games"; root.mkdir()
        actual = Path(games_root) if games_root else Path(__file__).resolve().parents[2] / "data/canonical/games"
        import shutil
        if (actual / game).exists(): shutil.copytree(actual / game, root / game)
        else: (root / game).mkdir()
        # Card provenance requires a source record. The reviewed dataset itself is its audit source.
        if data.get("cards") or data.get("printings"):
            src = {"schema_version":"v1", "id":str(data["source"]), "title":str(data["source"]),
                   "source_classification":"internal", "provider":"Reviewed dataset", "source_location":str(data["source"]),
                   "access_date":imported_at[:10], "verification_status":"confirmed", "claims":["Reviewed canonical import."],
                   "record_version":str(data["source_version"])}
            paths[f"sources/{data['source']}.json"] = src
        try: CanonicalRepository.apply_import(game, paths, games_root=root)
        except (CanonicalRepositoryError, ValueError) as error: raise ImportError(f"Validation failed: {error}") from error
    existing = {}
    actual_root = Path(games_root) if games_root else Path(__file__).resolve().parents[2] / "data/canonical/games"
    for relative in paths:
        file = actual_root / game / relative
        if file.exists():
            try: existing[relative] = json.loads(file.read_text())
            except Exception: pass
    identity_fields = {
        "cards": ("game", "name"),
        "printings": ("card_id", "set_id", "set_code", "collector_number", "language"),
    }
    for relative, prior in existing.items():
        kind = relative.split("/", 1)[0]
        for key in identity_fields.get(kind, ()):
            if key in prior and key in paths[relative] and prior[key] != paths[relative][key]:
                raise ImportError(
                    f"Identity conflict for {relative}: {key} changes from {prior[key]!r} "
                    f"to {paths[relative][key]!r}"
                )
    created = sum(x not in existing for x in paths); updated = sum(x in existing and existing[x] != paths[x] for x in paths)
    unchanged = len(paths) - created - updated
    applied = not dry_run and not validation_only
    if applied: CanonicalRepository.apply_import(game, paths, games_root=actual_root)
    conflicts = tuple(sorted(
        f"{kind}/{row['id']}:{a['path']}" for kind in ("cards", "printings")
        for row in data.get(kind, ()) for a in row.get("assertions", ())
        if a.get("status") == "conflicting"
    ))
    coverage = {kind: len(data.get(kind, ())) for kind in KINDS}
    return ImportReport(game, str(data["source"]), str(data["source_version"]), dataset_hash,
                        created, updated, unchanged, applied, validation_only, coverage, conflicts)
