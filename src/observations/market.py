"""Append-only, dated price snapshots for canonical card/printing identifiers."""

from __future__ import annotations

import json
import os
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from .verification import ObservationError, canonical_json


class MarketSnapshotStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    def capture(self, *, snapshot_id: str, captured_on: str, provider: str,
                currency: str, prices: Mapping[str, Any]) -> Path:
        try:
            date.fromisoformat(captured_on)
        except ValueError as error:
            raise ObservationError("captured_on must be an ISO date") from error
        normalized = {}
        for identifier, amount in prices.items():
            try:
                decimal = Decimal(str(amount))
            except InvalidOperation as error:
                raise ObservationError(f"invalid price for {identifier}") from error
            if decimal < 0:
                raise ObservationError("prices cannot be negative")
            normalized[str(identifier)] = format(
                decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"
            )
        record = {"schema_version": "v1", "snapshot_id": snapshot_id,
                  "captured_on": captured_on, "provider": provider,
                  "currency": currency.upper(), "prices": normalized}
        path = self.root / f"{captured_on}-{snapshot_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as error:
            raise ObservationError(f"market snapshot already exists: {path}") from error
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical_json(record))
        return path

    @staticmethod
    def load(path: Path) -> Mapping[str, Any]:
        return json.loads(Path(path).read_text(encoding="utf-8"))
