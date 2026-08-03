#!/usr/bin/env python3
"""Fail-closed verifier for the Phase 135 production evidence commit boundary."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

from production_evidence.pilot_printings import FILES, PILOT

RUN_ID = re.compile(r"mtgjson-pilot-[1-9][0-9]*-[1-9][0-9]*")
UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}")


def _status(root: Path) -> list[dict[str, str]]:
    raw = subprocess.run(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
                         cwd=root, check=True, stdout=subprocess.PIPE).stdout
    fields = raw.split(b"\0"); fields.pop() if fields and fields[-1] == b"" else None
    result, index = [], 0
    while index < len(fields):
        field = fields[index]
        if len(field) < 4 or field[2:3] != b" ": raise ValueError("malformed git status")
        code = field[:2].decode("ascii"); item = {"status": code, "path": os.fsdecode(field[3:])}; index += 1
        if "R" in code or "C" in code:
            if index >= len(fields): raise ValueError("incomplete rename")
            item["original_path"] = os.fsdecode(fields[index]); index += 1
        result.append(item)
    return result


def verify(root: Path, run_id: str, boundary: str) -> dict:
    expected = {f"data/evidence/phase-135/{run_id}/{name}" for name in FILES}
    report: dict[str, object] = {"schema_version": "pilot-printing-boundary-v1", "run_id": run_id,
        "boundary": boundary, "expected_paths": sorted(expected), "statuses": [], "failure_reason_codes": []}
    reasons: set[str] = set()
    if not RUN_ID.fullmatch(run_id): reasons.add("unsafe_run_id")
    try: statuses = _status(root)
    except Exception: statuses = []; reasons.add("git_status_parse_failed")
    report["statuses"] = statuses
    paths = {p for item in statuses for p in (item["path"], item.get("original_path")) if p}
    if paths != expected: reasons.add("changed_file_boundary_mismatch")
    if any("D" in x["status"] for x in statuses): reasons.add("deletion_not_permitted")
    if any("R" in x["status"] or "C" in x["status"] for x in statuses): reasons.add("rename_not_permitted")
    for path in paths:
        pure = PurePosixPath(path)
        if path.startswith("/") or ".." in pure.parts or path != pure.as_posix(): reasons.add("unsafe_path")
        if path.startswith(("data/canonical/", "data/market/", "data/knowledge/facts/")): reasons.add("protected_data_change")
    wanted = "??" if boundary == "pre-commit" else "A "
    if len(statuses) != 3 or any(x["status"] != wanted for x in statuses): reasons.add("unexpected_status")

    directory = root / "data/evidence/phase-135" / run_id
    try:
        if directory.is_symlink() or directory.resolve() != directory.absolute(): reasons.add("unsafe_evidence_directory")
        if {x.name for x in directory.iterdir()} != set(FILES): reasons.add("inventory_mismatch")
        if any((directory / name).is_symlink() or not (directory / name).is_file() for name in FILES): reasons.add("unsafe_evidence_file")
        manifest = json.loads((directory / "manifest.json").read_text())
        projection = json.loads((directory / "source-pilot-printings.json").read_text())
        rows = projection.get("pilot_printings")
        counts = manifest.get("printing_counts_by_pilot_card")
        if manifest.get("acquisition_run_id") != run_id: reasons.add("manifest_run_id_mismatch")
        if manifest.get("pilot_scope") != list(PILOT) or not isinstance(rows, list) or not isinstance(counts, dict): reasons.add("pilot_scope_mismatch")
        else:
            if not rows or set(counts) != set(PILOT) or any(not isinstance(counts[x], int) or counts[x] < 1 for x in PILOT): reasons.add("incomplete_pilot_census")
            if any(row.get("card_name") not in PILOT for row in rows): reasons.add("unrelated_record")
            if any(str(row.get("set_code", "")).upper() == "MB2" for row in rows): reasons.add("mb2_record")
            if any(not UUID.fullmatch(str(row.get("provider_printing_id", ""))) for row in rows): reasons.add("unstable_printing_identity")
        gates = {"unmatched_pilot_cards": [], "ambiguous_records": 0, "malformed_records": 0,
                 "unsupported_records": 0, "canonical_write": False, "promotion_performed": False,
                 "facts_created": False}
        if any(manifest.get(k) != v for k, v in gates.items()): reasons.add("census_or_safety_gate_failed")
        if manifest.get("retained_printing_count", 0) <= 0 or manifest.get("retained_printing_count") != len(rows or []): reasons.add("retained_count_mismatch")
    except (OSError, ValueError, TypeError, json.JSONDecodeError): reasons.add("invalid_evidence")
    report["failure_reason_codes"] = sorted(reasons); report["valid"] = not reasons
    return report


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--run-id", required=True); parser.add_argument("--boundary", choices=("pre-commit", "commit"), default="pre-commit")
    parser.add_argument("--output", type=Path); args = parser.parse_args()
    report = verify(args.repository.resolve(), args.run_id, args.boundary); rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output: args.output.write_text(rendered)
    sys.stdout.write(rendered); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
