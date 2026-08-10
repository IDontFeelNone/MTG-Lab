#!/usr/bin/env python3
"""Fail closed unless Git contains exactly the Phase 143 evidence change."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


EVIDENCE_PATH = "data/card_intelligence/demand/phase-143/mtgjson-decks.json"


def parse_porcelain_v1_z(payload: bytes) -> list[dict[str, str]]:
    """Parse ``git status --porcelain=v1 -z`` including rename source paths."""
    fields = payload.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    entries: list[dict[str, str]] = []
    index = 0
    while index < len(fields):
        field = fields[index]
        if len(field) < 4 or field[2:3] != b" ":
            raise ValueError("malformed git status record")
        status_code = field[:2].decode("ascii", "strict")
        entry = {"status": status_code, "path": os.fsdecode(field[3:])}
        index += 1
        if "R" in status_code or "C" in status_code:
            if index >= len(fields):
                raise ValueError("incomplete git rename record")
            entry["original_path"] = os.fsdecode(fields[index])
            index += 1
        entries.append(entry)
    return entries


def _status(repository: Path) -> bytes:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=repository, check=True, stdout=subprocess.PIPE,
    ).stdout


def verify(repository: Path, boundary: str) -> dict[str, object]:
    """Inventory all Git states and enforce the pre-commit or staged boundary."""
    reasons: set[str] = set()
    try:
        entries = parse_porcelain_v1_z(_status(repository))
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError):
        entries = []
        reasons.add("git_status_parse_failed")

    actual_paths = sorted({path for entry in entries
                           for path in (entry["path"], entry.get("original_path")) if path})
    unexpected_paths = sorted(set(actual_paths) - {EVIDENCE_PATH})
    staged_paths = sorted(entry["path"] for entry in entries
                          if entry["status"][0] not in (" ", "?"))
    if EVIDENCE_PATH not in actual_paths:
        reasons.add("expected_path_absent_from_git_state")
    if unexpected_paths:
        reasons.add("unexpected_path")
    if any("D" in entry["status"] for entry in entries):
        reasons.add("deletion_not_permitted")
    if any("R" in entry["status"] or "C" in entry["status"] for entry in entries):
        reasons.add("rename_or_copy_not_permitted")

    expected_status = "??" if boundary == "pre-commit" else "A "
    if len(entries) != 1 or entries[0].get("path") != EVIDENCE_PATH or entries[0]["status"] != expected_status:
        reasons.add("boundary_status_mismatch")
    if boundary == "pre-commit" and staged_paths:
        reasons.add("staged_path_before_verification")
    if boundary == "staged" and staged_paths != [EVIDENCE_PATH]:
        reasons.add("staged_boundary_mismatch")

    evidence = repository / EVIDENCE_PATH
    try:
        metadata = evidence.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            reasons.add("evidence_symlink")
        elif not stat.S_ISREG(metadata.st_mode):
            reasons.add("evidence_not_regular_file")
    except FileNotFoundError:
        reasons.add("evidence_file_absent")
    except OSError:
        reasons.add("evidence_file_unreadable")

    return {
        "schema_version": "phase-143-deck-usage-boundary-v1",
        "boundary": boundary,
        "expected_path": EVIDENCE_PATH,
        "actual_paths": actual_paths,
        "path_statuses": entries,
        "staged_paths": staged_paths,
        "unexpected_paths": unexpected_paths,
        "failure_reason_codes": sorted(reasons),
        "valid": not reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--boundary", choices=("pre-commit", "staged"), required=True)
    args = parser.parse_args()
    report = verify(args.repository.resolve(), args.boundary)
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
