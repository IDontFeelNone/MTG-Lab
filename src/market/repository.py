"""Append-only persistence for immutable market snapshots."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from .models import MarketSnapshot, MarketValidationError, PriceValues


class MarketSnapshotRepository:
    def __init__(self, root: Path):
        self.root = Path(root)

    def append(self, snapshot: MarketSnapshot) -> Path:
        if not isinstance(snapshot, MarketSnapshot):
            raise MarketValidationError("only MarketSnapshot values may be appended")
        path = self.root / snapshot.provider / snapshot.printing_id / f"{snapshot.snapshot_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(snapshot.to_dict(), indent=2, sort_keys=True) + "\n"
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as error:
            raise MarketValidationError(f"snapshot already exists: {snapshot.snapshot_id}") from error
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
        return path

    def load(self, path: Path) -> MarketSnapshot:
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("schema_version") != "market-snapshot-v1":
                raise MarketValidationError("unsupported market snapshot schema")
            values = PriceValues(**data["values"]) if data.get("values") else None
            variants = {name: PriceValues(**item) for name, item in data.get("variants", {}).items()}
            snapshot = MarketSnapshot(
                printing_id=data["printing_id"], provider=data["provider"],
                timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
                retrieved_at=datetime.fromisoformat(data["retrieved_at"].replace("Z", "+00:00")),
                currency=data["currency"], values=values, variants=variants,
                provenance=data.get("provenance", {}),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            if isinstance(error, MarketValidationError):
                raise
            raise MarketValidationError(f"invalid market snapshot: {path}") from error
        if data.get("snapshot_id") != snapshot.snapshot_id:
            raise MarketValidationError("snapshot_id does not match snapshot content")
        expected = self.root / snapshot.provider / snapshot.printing_id / f"{snapshot.snapshot_id}.json"
        if path.resolve() != expected.resolve():
            raise MarketValidationError("snapshot path does not match snapshot content")
        return snapshot

    def list(self) -> tuple[MarketSnapshot, ...]:
        return tuple(self.load(path) for path in sorted(self.root.glob("*/*/*.json")))
