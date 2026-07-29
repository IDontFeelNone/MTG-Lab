"""Versioned JSON Schema contracts for MTG Lab canonical data."""

from __future__ import annotations

from pathlib import Path

SCHEMA_VERSION = "v1"
SCHEMA_NAMES = ("card", "product", "printing", "slot", "print-sheet")


def schema_path(name: str, version: str = SCHEMA_VERSION) -> Path:
    """Return the on-disk path for a registered schema version."""
    if name not in SCHEMA_NAMES:
        raise ValueError(f"Unknown schema: {name}")
    return Path(__file__).parent / version / f"{name}.schema.json"


__all__ = ["SCHEMA_NAMES", "SCHEMA_VERSION", "schema_path"]
