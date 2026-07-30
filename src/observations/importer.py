"""Append-only import of plain-text pack reports into observation records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from repository.cards import load_card_repository

from .analytics import summarize_observations
from .verification import ObservationError, ObservationVerifier, canonical_json

_PACK_SEPARATOR = re.compile(r"(?m)^---[ \t]*(?:\r?\n|$)")
_TREATMENT = re.compile(r"^(.*?)\s+\[(.+)]\s*$")
_PACK_FILE = re.compile(r"^pack_(\d+)\.json$")


def parse_pack_text(text: str) -> list[list[dict[str, Any]]]:
    """Parse newline-delimited names; a line containing only ``---`` separates packs."""
    if not isinstance(text, str) or not text.strip():
        raise ObservationError("input must contain at least one card name")
    blocks = _PACK_SEPARATOR.split(text)
    packs: list[list[dict[str, Any]]] = []
    for block_number, block in enumerate(blocks, 1):
        lines = block.splitlines()
        cards = []
        for line in lines:
            if not line.strip():
                continue
            match = _TREATMENT.fullmatch(line)
            name = (match.group(1) if match else line).strip()
            treatment = match.group(2).strip() if match else None
            if not name or (match and not treatment):
                raise ObservationError(f"invalid card line in pack {block_number}: {line!r}")
            cards.append({"position": len(cards) + 1, "reported_name": name,
                          "reported_treatment": treatment})
        if not cards:
            raise ObservationError(f"pack {block_number} contains no cards")
        packs.append(cards)
    return packs


class ObservationImporter:
    """Import a complete input file as one atomic, append-only box update."""

    def __init__(self, *, observations_root: Path, derived_root: Path,
                 games_root: Path | None = None):
        self.observations_root = Path(observations_root)
        self.derived_root = Path(derived_root)
        self.games_root = Path(games_root) if games_root is not None else None

    def import_file(self, input_path: Path, *, game: str, product: str, box_id: str,
                    recorded_on: str | None = None, verifier_name: str = "canonical-repository-v1"
                    ) -> list[Path]:
        source_bytes = Path(input_path).read_bytes()
        try:
            source_text = source_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ObservationError("input must be UTF-8 text") from error
        packs = parse_pack_text(source_text)
        observed_on = recorded_on or date.today().isoformat()
        try:
            date.fromisoformat(observed_on)
        except ValueError as error:
            raise ObservationError("recorded_on must be an ISO date") from error

        box_root = self.observations_root / game / product / "boxes" / box_id
        manifest_path = box_root / "manifest.json"
        manifest = self._load_manifest(manifest_path, game, product, box_id)
        next_number = self._next_pack_number(box_root, manifest)
        cards, printings = load_card_repository(game, games_root=self.games_root)
        printing_by_card: dict[str, list[str]] = {}
        for printing in printings:
            memberships = printing.get("metadata", {}).get("product_membership", [])
            if product in memberships:
                printing_by_card.setdefault(str(printing["card_id"]), []).append(str(printing["id"]))
        index = []
        for card in cards:
            item = {"id": card["id"], "name": card["name"]}
            candidates = printing_by_card.get(str(card["id"]), [])
            if len(candidates) == 1:
                item["printing_id"] = candidates[0]
            index.append(item)
        verifier = ObservationVerifier(index, verifier=verifier_name)
        source = {"path": str(input_path), "sha256": hashlib.sha256(source_bytes).hexdigest(),
                  "text": source_text}
        raw_records = []
        verification_records = []
        created_at = datetime.now(timezone.utc).isoformat()
        new_entries = []
        for offset, card_list in enumerate(packs):
            number = next_number + offset
            pack_id = f"pack_{number:03d}"
            observation_id = f"{product}-{box_id}-{pack_id}"
            raw = {
                "observation_id": observation_id, "game": game,
                "product": {"slug": product},
                "container": {"box_id": box_id, "pack_id": pack_id},
                "observation": {"source_type": "user_report", "recorded_on": observed_on,
                                "verification_status": "verified_on_import",
                                "card_order_preserved": True, "card_count": len(card_list)},
                "import_source": {**source, "pack_number_in_source": offset + 1,
                                  "pack_count_in_source": len(packs)},
                "cards": card_list,
                "claims_boundary": {"canonical": False, "predictive": False},
            }
            raw_records.append(raw)
            verification_records.append(verifier.verify(raw, verified_at=created_at))
            new_entries.append({"pack_id": pack_id, "path": f"{pack_id}.json",
                                "card_count": len(card_list)})

        updated_manifest = dict(manifest)
        updated_manifest.update({"box_id": box_id, "game": game, "product": product,
                                 "pack_count_recorded": len(manifest.get("packs", [])) + len(packs),
                                 "packs": [*manifest.get("packs", []), *new_entries]})
        existing_packs = self._load_existing_packs(box_root, manifest)
        existing_verifications, backfilled_verifications = self._load_existing_verifications(
            game, product, box_id, existing_packs, verifier, created_at
        )
        analytics = summarize_observations(
            [*existing_packs, *raw_records], [*existing_verifications, *verification_records]
        )
        return self._commit(box_root, manifest_path, raw_records,
                            [*backfilled_verifications, *verification_records],
                            updated_manifest, analytics, game, product, box_id)

    @staticmethod
    def _load_manifest(path: Path, game: str, product: str, box_id: str) -> dict[str, Any]:
        if not path.exists():
            return {"box_id": box_id, "game": game, "product": product, "packs": []}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ObservationError(f"invalid manifest: {path}") from error
        if value.get("box_id") != box_id or value.get("game") not in (game, "magic_the_gathering"):
            raise ObservationError("manifest identity does not match import target")
        return value

    @staticmethod
    def _next_pack_number(root: Path, manifest: Mapping[str, Any]) -> int:
        numbers = []
        for entry in manifest.get("packs", []):
            match = _PACK_FILE.fullmatch(str(entry.get("path", "")))
            if not match:
                raise ObservationError("manifest contains an invalid pack path")
            numbers.append(int(match.group(1)))
        disk = {path.name for path in root.glob("pack_*.json")} if root.exists() else set()
        declared = {str(entry["path"]) for entry in manifest.get("packs", [])}
        if disk != declared:
            raise ObservationError("manifest and existing pack files disagree; refusing append")
        return max(numbers, default=0) + 1

    @staticmethod
    def _load_existing_packs(root: Path, manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        return [json.loads((root / entry["path"]).read_text(encoding="utf-8"))
                for entry in manifest.get("packs", [])]

    def _load_existing_verifications(
        self, game: str, product: str, box_id: str, raw_records: Sequence[Mapping[str, Any]],
        verifier: ObservationVerifier, verified_at: str,
    ) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
        root = self.derived_root / game / product / "boxes" / box_id / "verifications"
        records = []
        backfilled = []
        for raw in raw_records:
            path = root / f"{raw['observation_id']}.verification.json"
            if path.exists():
                record = json.loads(path.read_text(encoding="utf-8"))
                from .verification import VerificationStore
                VerificationStore.assert_matches_raw(record, raw)
            else:
                record = verifier.verify(raw, verified_at=verified_at)
                backfilled.append(record)
            records.append(record)
        return records, backfilled

    def _commit(self, box_root: Path, manifest_path: Path, raws: Sequence[Mapping[str, Any]],
                verifications: Sequence[Mapping[str, Any]], manifest: Mapping[str, Any],
                analytics: Mapping[str, Any], game: str, product: str, box_id: str) -> list[Path]:
        derived = self.derived_root / game / product / "boxes" / box_id
        targets = ([box_root / f"{raw['container']['pack_id']}.json" for raw in raws] +
                   [derived / "verifications" / f"{item['observation_id']}.verification.json"
                    for item in verifications])
        if any(path.exists() for path in targets):
            raise ObservationError("an import target already exists; refusing overwrite")
        box_root.mkdir(parents=True, exist_ok=True)
        (derived / "verifications").mkdir(parents=True, exist_ok=True)
        created: list[Path] = []
        try:
            for path, document in zip(targets, [*raws, *verifications]):
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(canonical_json(document))
                created.append(path)
            self._replace_json(manifest_path, manifest)
            analytics_path = derived / "analytics.json"
            self._replace_json(analytics_path, analytics)
            return [*created, manifest_path, analytics_path]
        except Exception:
            for path in created:
                path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _replace_json(path: Path, document: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import plain-text observed packs")
    parser.add_argument("input", type=Path)
    parser.add_argument("--game", required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--box", required=True, dest="box_id")
    parser.add_argument("--recorded-on")
    parser.add_argument("--observations-root", type=Path, default=Path("data/observations"))
    parser.add_argument("--derived-root", type=Path, default=Path("data/derived/observations"))
    parser.add_argument("--games-root", type=Path)
    args = parser.parse_args(argv)
    try:
        paths = ObservationImporter(observations_root=args.observations_root,
                                    derived_root=args.derived_root,
                                    games_root=args.games_root).import_file(
            args.input, game=args.game, product=args.product, box_id=args.box_id,
            recorded_on=args.recorded_on)
    except (ObservationError, OSError, ValueError) as error:
        parser.error(str(error))
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
