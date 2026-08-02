#!/usr/bin/env python3
"""Verify the exact working-tree and commit boundaries for market evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


RUN_ID = re.compile(r"scryfall-mb2-[1-9][0-9]*-[1-9][0-9]*")
DURABLE_NAMES = ("dry-run-report.json", "manifest.json", "source-mb2.json")
TRANSIENT_PATHS = (
    "market-acquisition-dry-run.json",
    "market-acquisition-run-id.txt",
    "market-acquisition-source-mb2.json",
    "market-acquisition-stamp.txt",
)


def _git_status(repository: Path) -> bytes:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=repository, check=True, stdout=subprocess.PIPE,
    ).stdout


def parse_porcelain(payload: bytes) -> list[dict[str, str]]:
    """Parse porcelain v1 -z without whitespace or quoting assumptions."""
    fields = payload.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    entries: list[dict[str, str]] = []
    index = 0
    while index < len(fields):
        field = fields[index]
        if len(field) < 4 or field[2:3] != b" ":
            raise ValueError("malformed git status record")
        code = field[:2].decode("ascii", "strict")
        entry = {"path": os.fsdecode(field[3:]), "status": code}
        index += 1
        if "R" in code or "C" in code:
            if index >= len(fields):
                raise ValueError("incomplete git rename record")
            entry["original_path"] = os.fsdecode(fields[index])
            index += 1
        entries.append(entry)
    return entries


def _unsafe(path: str) -> bool:
    pure = PurePosixPath(path)
    return (not path or path.startswith("/") or ".." in pure.parts or
            any(ord(character) < 32 or ord(character) == 127 for character in path) or
            path != pure.as_posix())


def verify(repository: Path, run_id: str, boundary: str) -> dict:
    durable = [f"data/market/acquisitions/{run_id}/{name}" for name in DURABLE_NAMES]
    result: dict[str, object] = {
        "schema_version": "market-evidence-changed-file-verification-v1",
        "boundary": boundary,
        "run_id": run_id,
        "expected_durable_paths": durable,
        "permitted_transient_paths": list(TRANSIENT_PATHS),
        "actual_changed_paths": [],
        "path_statuses": [],
        "missing_durable_paths": [],
        "unexpected_paths": [],
        "canonical_paths": [],
        "market_observation_paths": [],
        "unsafe_paths": [],
        "failure_reason_codes": [],
        "valid": False,
    }
    reasons: set[str] = set()
    if not RUN_ID.fullmatch(run_id):
        reasons.add("unsafe_run_id")

    try:
        statuses = parse_porcelain(_git_status(repository))
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError):
        statuses = []
        reasons.add("git_status_parse_failed")
    result["path_statuses"] = statuses
    actual = sorted({value for item in statuses
                     for value in (item["path"], item.get("original_path")) if value})
    result["actual_changed_paths"] = actual

    durable_set = set(durable)
    transient_set = set(TRANSIENT_PATHS)
    allowed = durable_set | transient_set
    missing = sorted(durable_set - set(actual))
    missing_transient = sorted(transient_set - set(actual))
    unexpected = sorted(set(actual) - allowed)
    canonical = sorted(path for path in actual if path.startswith("data/canonical/"))
    observations = sorted(path for path in actual if path.startswith("data/market/observations/"))
    unsafe = sorted(path for path in actual if _unsafe(path) or
                    (" " in path and path not in allowed))
    result["missing_durable_paths"] = missing
    result["unexpected_paths"] = unexpected
    result["canonical_paths"] = canonical
    result["market_observation_paths"] = observations
    result["unsafe_paths"] = unsafe
    if missing:
        reasons.add("missing_durable_path")
    if missing_transient:
        reasons.add("missing_transient_path")
    if unexpected:
        reasons.add("unexpected_path")
    if canonical:
        reasons.add("canonical_change")
    if observations:
        reasons.add("market_observation_change")
    if unsafe:
        reasons.add("unsafe_path")
    if any("D" in item["status"] for item in statuses):
        reasons.add("deletion_not_permitted")
    if any("R" in item["status"] or "C" in item["status"] for item in statuses):
        reasons.add("rename_not_permitted")

    status_by_path = {item["path"]: item["status"] for item in statuses}
    required_status = ({path: "??" for path in allowed} if boundary == "pre-commit" else
                       ({path: "A " for path in durable_set} |
                        {path: "??" for path in transient_set}))
    if any(status_by_path.get(path) != code for path, code in required_status.items()):
        reasons.add("unexpected_status_code")

    if RUN_ID.fullmatch(run_id):
        evidence = repository / "data" / "market" / "acquisitions" / run_id
        if evidence.is_symlink() or evidence.resolve() != evidence.absolute():
            reasons.add("unsafe_evidence_location")
        for path_text in durable:
            path = repository / path_text
            try:
                metadata = path.lstat()
                if path.is_symlink():
                    reasons.add("evidence_symlink")
                elif not path.is_file():
                    reasons.add("evidence_not_regular_file")
            except FileNotFoundError:
                reasons.add("missing_evidence_file")
        manifest_path = evidence / "manifest.json"
        if manifest_path.exists() and not manifest_path.is_symlink():
            try:
                manifest = json.loads(manifest_path.read_text())
                if not isinstance(manifest, dict):
                    raise ValueError
                if manifest.get("acquisition_run_id") != run_id:
                    reasons.add("manifest_run_id_mismatch")
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
                reasons.add("manifest_invalid")

    staged = sorted(item["path"] for item in statuses if item["status"][0] not in (" ", "?"))
    result["staged_paths"] = staged
    if boundary == "pre-commit":
        if staged:
            reasons.add("staged_path_before_commit")
    elif set(staged) != durable_set or len(staged) != len(durable):
        reasons.add("commit_boundary_mismatch")
    if any(path not in durable_set for path in staged):
        reasons.add("unauthorized_staged_path")

    result["failure_reason_codes"] = sorted(reasons)
    result["valid"] = not reasons
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--boundary", choices=("pre-commit", "commit"), default="pre-commit")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.repository.resolve(), args.run_id, args.boundary)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    sys.stdout.write(rendered)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
