"""Validated canonical reads and explicit, recoverable staged imports."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import warnings
from pathlib import Path
from typing import Any, Iterable, Mapping

from canonical import (Card, Finish, Game, PackDefinition, PackVariant, PackSlot, Printing,
                       Product, ProductComponent, ProductVersion, Rarity, Sheet, SheetEntry, Treatment)
from repository.cards import load_card_repository
from repository.products import load_product
from repository.canonical_compatibility import (card_v3, legacy_product_graph, printing_v3,
                                                product_v2, sheet_v2, slot_v2)
from validation import validate_document

_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data/canonical/games"


class CanonicalRepositoryError(ValueError):
    """Canonical data is malformed or has inconsistent relationships."""


class CanonicalImportCleanupWarning(RuntimeWarning):
    """Publication succeeded, but recovery-directory cleanup needs inspection."""


def _pending_import_paths(root: Path, game: str) -> tuple[Path, ...]:
    paths = (root / f".{game}.import-backup", root / f".{game}.import-staging")
    # Retain old TemporaryDirectory-style candidates as well as new staging.
    legacy = sorted(root.glob(f"tmp*/{game}"))
    return tuple(p for p in (*paths, *legacy) if p.exists() or p.is_symlink())


def _import_fingerprint(directory: Path) -> tuple:
    """Prove ownership before compensation; never overwrite a changed candidate."""
    return tuple((p.relative_to(directory).as_posix(), p.is_dir(),
                  None if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest())
                 for p in sorted(directory.rglob("*")))


class CanonicalRepository:
    """Validated in-memory view; writes require the explicit apply_import API."""

    import_cleanup_pending: tuple[str, ...] = ()

    def __init__(self, game: str, *, games_root: Path | None = None,
                 read_inventory: Any = None):
        if not _ID.fullmatch(game):
            raise CanonicalRepositoryError("game must be a stable lowercase identifier")
        self.game_id = game
        self.root = Path(games_root) if games_root is not None else _DEFAULT_ROOT
        if not (self.root / game).exists() and _pending_import_paths(self.root, game):
            raise CanonicalRepositoryError(
                f"Canonical import recovery required for {game}: active directory is missing; "
                "preserve backup/staging and verify a recovery copy before retrying")
        self._read_inventory = read_inventory
        self.game = self._load_game()
        self.cards, self.printings = self._load_cards()
        product_documents = self._load_product_documents()
        self.products = tuple(product_v2(item) for item in product_documents)
        self.product_versions = self._load_product_versions()
        self.treatments = self._load("treatments", Treatment)
        self.finishes = self._load("finishes", Finish)
        self.rarities = self._load("rarities", Rarity)
        self.pack_definitions = self._load_pack_definitions()
        self.pack_slots = self._load_slots()
        self.sheets = self._load_sheets()
        for document in product_documents:
            versions, packs = legacy_product_graph(document)
            self.product_versions += versions; self.pack_definitions += packs
        self.product_versions = self._unique(self.product_versions, "ProductVersion")
        self.pack_definitions = self._unique(self.pack_definitions, "PackDefinition")
        self._validate_relationships()

    def get_card(self, identifier: str) -> Card:
        return self._get(self.cards, "Card", identifier)

    def get_printing(self, identifier: str) -> Printing:
        return self._get(self.printings, "Printing", identifier)

    def get_product(self, identifier: str) -> Product:
        return self._get(self.products, "Product", identifier)

    def get_pack_definition(self, identifier: str) -> PackDefinition:
        return self._get(self.pack_definitions, "PackDefinition", identifier)

    def get_product_version(self, identifier: str) -> ProductVersion:
        return self._get(self.product_versions, "ProductVersion", identifier)

    def get_pack_slot(self, identifier: str) -> PackSlot:
        return self._get(self.pack_slots, "PackSlot", identifier)

    def get_sheet(self, identifier: str) -> Sheet:
        return self._get(self.sheets, "Sheet", identifier)

    @classmethod
    def apply_import(cls, game: str, records: Mapping[str, Mapping[str, Any]], *,
                     games_root: Path | None = None) -> "CanonicalRepository":
        """Stage and verify an import; uncertain recovery state blocks new writes.

        A successful return means live verification completed. Cleanup failures
        retain that publication and expose ``import_cleanup_pending`` plus a
        warning. No stale backup or orphan candidate is automatically discarded.
        """
        if not _ID.fullmatch(game):
            raise CanonicalRepositoryError("game must be a stable lowercase identifier")
        root = Path(games_root) if games_root is not None else _DEFAULT_ROOT
        root.mkdir(parents=True, exist_ok=True)
        current = root / game
        backup = root / f".{game}.import-backup"
        staging = root / f".{game}.import-staging"
        pending = _pending_import_paths(root, game)
        if pending:
            raise CanonicalRepositoryError(
                "Canonical import recovery required; preserve and inspect "
                + ", ".join(str(p) for p in pending))
        try:
            # A fixed, exclusive directory also serializes cooperating importers.
            staging.mkdir()
        except FileExistsError as error:
            raise CanonicalRepositoryError(
                f"Canonical import recovery required: staging already exists: {staging}") from error
        staged = staging / game
        commit_started = False
        try:
            if current.exists():
                shutil.copytree(current, staged)
            else:
                staged.mkdir()
            for relative, document in sorted(records.items()):
                path = Path(relative)
                if path.is_absolute() or ".." in path.parts:
                    raise CanonicalRepositoryError(f"Unsafe canonical path: {relative}")
                destination = staged / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n",
                                       encoding="utf-8")
            cls(game, games_root=staging)
            candidate_fingerprint = _import_fingerprint(staged)
            candidate_stat = staged.stat()
            candidate_identity = (candidate_stat.st_dev, candidate_stat.st_ino)
            commit_started = True
            try:
                if backup.exists() or backup.is_symlink():
                    raise CanonicalRepositoryError("Recovery backup appeared during import")
                if current.exists():
                    current.rename(backup)
                staged.rename(current)
                verified = cls(game, games_root=root)
                live_stat = current.stat()
                if ((live_stat.st_dev, live_stat.st_ino) != candidate_identity
                        or _import_fingerprint(current) != candidate_fingerprint):
                    raise CanonicalRepositoryError("Candidate changed during final verification")
                # Successful-publication boundary: no automatic rollback below.
            except BaseException as error:
                try:
                    if current.exists() and not staged.exists():
                        now = current.stat()
                        if ((now.st_dev, now.st_ino) != candidate_identity
                                or _import_fingerprint(current) != candidate_fingerprint):
                            raise CanonicalRepositoryError("Current candidate changed; compensation refused")
                        current.rename(staged)  # Preserve the rejected candidate.
                    if backup.exists():
                        if current.exists():
                            raise CanonicalRepositoryError("Conflicting active directory; compensation refused")
                        backup.rename(current)
                except BaseException as recovery_error:
                    raise CanonicalRepositoryError(
                        f"Canonical import recovery required: compensation incomplete "
                        f"({recovery_error}); preserve {current}, {backup}, {staging}") from error
                raise CanonicalRepositoryError(
                    f"Canonical import not committed; original directory retained/restored if present. "
                    f"Recovery required: inspect preserved candidate at {staging}; "
                    "do not retry until recovery state is explicitly resolved") from error
        except BaseException as error:
            if not commit_started:
                try:
                    shutil.rmtree(staging)
                except OSError as cleanup_error:
                    error.add_note(f"Recovery required: preserve staging {staging}: {cleanup_error}")
            raise

        for path in (backup, staging):
            if not path.exists():
                continue
            try:
                if path == staging:
                    path.rmdir()  # Never delete unexpected recovery material.
                else:
                    shutil.rmtree(path)
            except Exception as error:
                verified.import_cleanup_pending = tuple(
                    p.name for p in (backup, staging) if p.exists() or p.is_symlink())
                message = (f"Canonical import COMMITTED and verified; cleanup pending at "
                           f"{verified.import_cleanup_pending}: {error}. Preserve these paths; "
                           "inspect before another import. Do not roll back a verified publication.")
                try:
                    warnings.warn(message, CanonicalImportCleanupWarning, stacklevel=2)
                except CanonicalImportCleanupWarning:
                    # Even warnings-as-errors must not turn a commit into an abort.
                    pass
                break
            except BaseException as error:
                error.add_note("Canonical import COMMITTED and verified; cleanup interrupted. "
                               f"Preserve {backup} and {staging}; inspect before retrying.")
                raise
        return verified

    def _load_game(self) -> Game:
        path = self.root / self.game_id / "game.json"
        if self._read_inventory is not None:
            self._read_inventory.require(path)
        if self._read_inventory is None and not path.exists():
            return Game(self.game_id, {}, self.game_id.replace("_", " ").title())
        data = self._read(path)
        try:
            game = Game.from_dict(data)
        except (TypeError, ValueError) as error:
            raise CanonicalRepositoryError(f"Invalid Game {path}: {error}") from error
        if game.id != self.game_id:
            raise CanonicalRepositoryError(f"Game identifier does not match path: {path}")
        return game

    def _load_cards(self) -> tuple[tuple[Card, ...], tuple[Printing, ...]]:
        try:
            cards, printings = load_card_repository(
                self.game_id, games_root=self.root, read_inventory=self._read_inventory)
        except ValueError as error:
            raise CanonicalRepositoryError(str(error)) from error
        return (
            tuple(card_v3(x) for x in cards),
            tuple(printing_v3(x) for x in printings),
        )

    def _load_product_documents(self) -> tuple[Mapping[str, Any], ...]:
        result = []
        for path in self._paths(self.root / self.game_id / "products", "*/product.json"):
            try: result.append(load_product(self.game_id, path.parent.name, games_root=self.root,
                                            read_inventory=self._read_inventory))
            except ValueError as error: raise CanonicalRepositoryError(str(error)) from error
        return tuple(result)

    def _documents(self, patterns: tuple[str, ...]) -> tuple[Mapping[str, Any], ...]:
        paths = {path for pattern in patterns for path in self._paths(self.root / self.game_id, pattern)}
        return tuple(self._read(path) for path in sorted(paths))

    def _load_product_versions(self) -> tuple[ProductVersion, ...]:
        records = []
        for data in self._documents(("product_versions/*.json", "product_versions/*/product-version.json")):
            if data.get("schema_version") == "v2": validate_document(data, "product-version")
            components = data.get("components")
            if components is None:
                components = [{"component_type":"pack_definition", "component_id":item, "quantity":1}
                              for item in data.get("pack_definition_ids", ())]
            records.append(ProductVersion(str(data["id"]), dict(data.get("metadata", {})), str(data["product_id"]),
                         str(data["name"]), tuple(ProductComponent(str(x["component_type"]), str(x["component_id"]), int(x["quantity"])) for x in components)))
        return self._unique(records, "ProductVersion")

    def _load_pack_definitions(self) -> tuple[PackDefinition, ...]:
        records=[]
        for data in self._documents(("packs/*.json", "packs/*/pack-definition.json")):
            native_variants = data.get("schema_version") == "v3"
            if data.get("schema_version") in ("v2", "v3"): validate_document(data, "pack-definition")
            records.append(PackDefinition(str(data["id"]), dict(data.get("metadata", {})),
                str(data["product_version_id"]), str(data["name"]),
                tuple(map(str, data.get("slot_ids", ()))), "v3" if native_variants else "v2",
                tuple(PackVariant(x["pack_definition_id"], x["weight"]) for x in data["variants"])
                if native_variants else None))
        return self._unique(records, "PackDefinition")

    def _load_slots(self) -> tuple[PackSlot, ...]:
        records=[]
        for data in self._documents(("slots/*.json", "slots/*/slot.json")):
            try:
                if data.get("schema_version") in ("v1","v2"): validate_document(data, "slot")
                records.append(slot_v2(data))
            except ValueError as error:
                raise CanonicalRepositoryError(f"Invalid PackSlot {data.get('id')}: {error}") from error
        return self._unique(records, "PackSlot")

    def _load_sheets(self) -> tuple[Sheet, ...]:
        records=[]
        for data in self._documents(("sheets/*.json", "print_sheets/*/print-sheet.json")):
            if data.get("schema_version") in ("v1","v2","v3"): validate_document(data, "print-sheet")
            records.append(sheet_v2(data))
        return self._unique(records, "Sheet")

    def _load(self, directory: str, model: type) -> tuple:
        records = []
        for path in self._paths(self.root / self.game_id / directory, "*.json"):
            data = self._read(path)
            try:
                records.append(self._construct(model, data))
            except (KeyError, TypeError, ValueError) as error:
                raise CanonicalRepositoryError(f"Invalid {model.__name__} {path}: {error}") from error
        return self._unique(records, model.__name__)

    @staticmethod
    def _construct(model: type, data: Mapping[str, Any]):
        required = {
            ProductVersion: ("id", "product_id", "name", "pack_definition_ids"),
            Treatment: ("id", "game_id", "name"), Finish: ("id", "game_id", "name"),
            Rarity: ("id", "game_id", "name"),
            PackDefinition: ("id", "product_version_id", "name", "slot_ids"),
            PackSlot: ("id", "name", "sheet_id", "count"),
            Sheet: ("id", "name", "entries"),
        }[model]
        missing = sorted(key for key in required if key not in data)
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        meta = dict(data.get("metadata", {}))
        if model is Sheet:
            entries = tuple(SheetEntry(str(x["printing_id"]), int(x.get("weight", 1)),
                                       x.get("finish_id")) for x in data["entries"])
            if not entries or any(x.weight < 1 for x in entries):
                raise ValueError("entries must be non-empty with positive weights")
            return Sheet(str(data["id"]), meta, str(data["name"]), entries)
        if model is PackSlot:
            count = int(data["count"])
            if count < 1: raise ValueError("count must be positive")
            return PackSlot(str(data["id"]), meta, str(data["name"]), str(data["sheet_id"]), count)
        values = [str(data[key]) for key in required]
        for index, key in enumerate(required):
            if key.endswith("_ids"): values[index] = tuple(map(str, data[key]))
        return model(values[0], meta, *values[1:])

    def _validate_relationships(self) -> None:
        for label, records in (("Treatment", self.treatments), ("Finish", self.finishes),
                               ("Rarity", self.rarities)):
            for record in records:
                if record.game_id != self.game_id:
                    raise CanonicalRepositoryError(
                        f"{label} {record.id} references missing Game {record.game_id}"
                    )
        self._refs(self.printings, "card_id", self.cards, "Printing", "Card")
        namespaces: set[tuple[str, str, str, str]] = set()
        for printing in self.printings:
            namespace = (printing.set_id, printing.language,
                         str(printing.facts.get("collector_number_namespace", "default")),
                         printing.collector_number)
            if namespace in namespaces:
                raise CanonicalRepositoryError(
                    f"Duplicate collector number {printing.collector_number} in {namespace[:-1]}"
                )
            namespaces.add(namespace)
        self._refs(self.product_versions, "product_id", self.products, "ProductVersion", "Product")
        self._refs_many(self.products, "version_ids", self.product_versions, "Product", "ProductVersion")
        versions = {item.id: item for item in self.product_versions}
        for product in self.products:
            if product.lifecycle_status == "validated" and not product.version_ids:
                raise CanonicalRepositoryError(f"Validated Product {product.id} has no ProductVersion")
            for identifier in product.version_ids:
                if versions[identifier].product_id != product.id:
                    raise CanonicalRepositoryError(
                        f"Product {product.id} references ProductVersion {identifier} owned by {versions[identifier].product_id}"
                    )
        self._validate_components()
        packs = {item.id: item for item in self.pack_definitions}
        for pack in self.pack_definitions:
            if pack.variants is None: continue
            identifiers = [v.pack_definition_id for v in pack.variants]
            if len(identifiers) != len(set(identifiers)):
                raise CanonicalRepositoryError(f"PackDefinition {pack.id} has duplicate variants")
            for identifier in identifiers:
                child = packs.get(identifier)
                if (child is None or child.product_version_id != pack.product_version_id
                        or child.variants is not None):
                    raise CanonicalRepositoryError(f"PackDefinition {pack.id} has missing, foreign or nested variant {identifier}")
        self._refs_many(self.pack_definitions, "slot_ids", self.pack_slots, "PackDefinition", "PackSlot")
        self._refs(self.pack_slots, "print_sheet_id", self.sheets, "PackSlot", "Sheet")
        if self.rarities:
            self._refs(self.printings, "rarity_id", self.rarities, "Printing", "Rarity")
        if self.treatments:
            self._refs_many(self.printings, "treatment_ids", self.treatments,
                            "Printing", "Treatment")
        if self.finishes:
            self._refs_many(self.printings, "finish_ids", self.finishes, "Printing", "Finish")
        ids = {x.id for x in self.printings}
        for sheet in self.sheets:
            entry_ids = [(entry.printing_id, entry.finish_id) for entry in sheet.entries]
            if len(entry_ids) != len(set(entry_ids)):
                raise CanonicalRepositoryError(f"Sheet {sheet.id} has duplicate Printing entries")
            for entry in sheet.entries:
                if entry.printing_id not in ids:
                    raise CanonicalRepositoryError(f"Sheet {sheet.id} references missing Printing {entry.printing_id}")
                if entry.finish_id is not None:
                    printing = next(p for p in self.printings if p.id == entry.printing_id)
                    if (entry.finish_id not in {f.id for f in self.finishes}
                            or entry.finish_id not in printing.finish_ids):
                        raise CanonicalRepositoryError(
                            f"Sheet {sheet.id} has unsupported Printing/Finish outcome")
        sheets = {item.id: item for item in self.sheets}
        for slot in self.pack_slots:
            if not slot.replacement and slot.draw_count > sum(item.weight for item in sheets[slot.print_sheet_id].entries):
                raise CanonicalRepositoryError(f"PackSlot {slot.id} has impossible no-replacement draw_count")

    def _validate_components(self) -> None:
        versions = {item.id: item for item in self.product_versions}; packs = {item.id for item in self.pack_definitions}
        for version in self.product_versions:
            for component in version.components:
                if component.quantity < 1: raise CanonicalRepositoryError(f"ProductVersion {version.id} has non-positive component quantity")
                targets = packs if component.component_type == "pack_definition" else versions if component.component_type == "product_version" else None
                if targets is None or component.component_id not in targets:
                    raise CanonicalRepositoryError(f"ProductVersion {version.id} references missing {component.component_type} {component.component_id}")
                if component.component_type == "pack_definition":
                    pack = next(item for item in self.pack_definitions if item.id == component.component_id)
                    if pack.product_version_id != version.id:
                        raise CanonicalRepositoryError(
                            f"ProductVersion {version.id} references PackDefinition {pack.id} owned by {pack.product_version_id}"
                        )
        visiting=set(); visited=set()
        def visit(identifier):
            if identifier in visiting: raise CanonicalRepositoryError(f"ProductVersion composition cycle: {identifier}")
            if identifier in visited: return
            visiting.add(identifier)
            for component in versions[identifier].components:
                if component.component_type == "product_version": visit(component.component_id)
            visiting.remove(identifier); visited.add(identifier)
        for identifier in sorted(versions): visit(identifier)

    def _paths(self, root: Path, pattern: str) -> tuple[Path, ...]:
        if self._read_inventory is not None:
            return tuple(self._read_inventory.paths(root, pattern))
        return tuple(sorted(root.glob(pattern)))

    def _read(self, path: Path) -> Mapping[str, Any]:
        try:
            data = (self._read_inventory.read_json(path) if self._read_inventory is not None
                    else json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as error: raise CanonicalRepositoryError(f"Invalid JSON: {path}") from error
        if not isinstance(data, dict): raise CanonicalRepositoryError(f"Canonical record must be an object: {path}")
        return data

    @staticmethod
    def _unique(items: Iterable, label: str) -> tuple:
        values = tuple(items); seen = set()
        for item in values:
            if not _ID.fullmatch(item.id): raise CanonicalRepositoryError(f"Invalid {label} identifier: {item.id}")
            if item.id in seen: raise CanonicalRepositoryError(f"Duplicate {label} identifier: {item.id}")
            seen.add(item.id)
        return values

    @staticmethod
    def _get(items: Iterable, label: str, identifier: str):
        for item in items:
            if item.id == identifier: return item
        raise KeyError(f"{label} not found: {identifier}")

    def _refs(self, sources, attr, targets, source_label, target_label):
        ids = {x.id for x in targets}
        for source in sources:
            value = getattr(source, attr)
            if value not in ids: raise CanonicalRepositoryError(f"{source_label} {source.id} references missing {target_label} {value}")

    def _refs_many(self, sources, attr, targets, source_label, target_label):
        ids = {x.id for x in targets}
        for source in sources:
            for value in getattr(source, attr):
                if value not in ids: raise CanonicalRepositoryError(f"{source_label} {source.id} references missing {target_label} {value}")


def load_canonical_repository(game: str, *, games_root: Path | None = None,
                              read_inventory: Any = None) -> CanonicalRepository:
    return CanonicalRepository(game, games_root=games_root, read_inventory=read_inventory)


__all__ = ["CanonicalRepository", "CanonicalRepositoryError", "load_canonical_repository"]
