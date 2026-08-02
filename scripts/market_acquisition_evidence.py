#!/usr/bin/env python3
"""Verify and durably retain one bounded, nonpersistent market acquisition."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile


RUN_ID = re.compile(r"scryfall-mb2-[1-9][0-9]*-[1-9][0-9]*")


def canonical_json(value: object) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")).encode() + b"\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def branch_name(run_id: str) -> str:
    _validate_run_id(run_id)
    return f"market-acquisition/{run_id}"


def _validate_run_id(run_id: str) -> None:
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("invalid acquisition run identity")


def _load_object(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def retain(report_path: Path, source_path: Path, data_root: Path) -> dict:
    """Validate inputs and atomically create or replay the evidence directory."""
    report = _load_object(report_path)
    run_id = report.get("run_id", "")
    _validate_run_id(run_id)
    required_false = ("canonical_write", "promotion_performed", "persisted")
    if any(report.get(field) is not False for field in required_false):
        raise ValueError("acquisition report does not prove nonpersistent isolation")
    if report.get("provider") != "scryfall" or report.get("target") != {
            "set": "MB2", "promoted_only": True}:
        raise ValueError("acquisition report is not the bounded Scryfall MB2 target")
    canonical_identity = report.get("canonical_snapshot_identity")
    if not isinstance(canonical_identity, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", canonical_identity):
        raise ValueError("invalid canonical snapshot identity")

    source = json.loads(source_path.read_text())
    if not isinstance(source, list) or len(source) > 1000:
        raise ValueError("retained provider projection is not bounded")
    if len(source) != report.get("mb2_record_count"):
        raise ValueError("retained provider projection census mismatch")
    for record in source:
        if not isinstance(record, dict) or str(record.get("set", "")).lower() != "mb2":
            raise ValueError("retained provider projection contains a non-MB2 record")

    source_bytes = canonical_json(source)
    report_bytes = canonical_json(report)
    manifest = {
        "schema_version": "market-acquisition-evidence-v1",
        "acquisition_run_id": run_id,
        "provider": "scryfall",
        "target": {"set": "MB2", "promoted_only": True},
        "retrieved_at": report.get("retrieved_at"),
        "source_observed_at": report.get("source_observed_at"),
        "canonical_snapshot_identity": canonical_identity,
        "source_dataset": report.get("source_dataset"),
        "source_url": report.get("source_url"),
        "provider_source_sha256": report.get("source_sha256"),
        "normalized_sha256": report.get("normalized_sha256"),
        "mapping_counts": report.get("mapping_counts"),
        "price_census": {
            "known": report.get("known_price_observation_count"),
            "missing": report.get("missing_price_observation_count"),
            "observations": report.get("observation_count"),
        },
        "source_record_count": report.get("source_record_count"),
        "mb2_record_count": report.get("mb2_record_count"),
        "canonical_write": False,
        "promotion_performed": False,
        "observations_persisted": False,
        "files": {
            "dry-run-report.json": {"sha256": digest(report_bytes), "bytes": len(report_bytes)},
            "source-mb2.json": {"sha256": digest(source_bytes), "bytes": len(source_bytes)},
        },
    }
    # A manifest cannot contain the byte digest of itself; bind its logical content
    # by hashing the canonical form before adding this one explicitly defined field.
    manifest["manifest_content_sha256"] = digest(canonical_json(manifest))
    manifest_bytes = canonical_json(manifest)
    destination = data_root / "market" / "acquisitions" / run_id
    expected = {"manifest.json": manifest_bytes, "dry-run-report.json": report_bytes,
                "source-mb2.json": source_bytes}
    if destination.exists():
        actual = {path.name: path.read_bytes() for path in destination.iterdir() if path.is_file()}
        if actual != expected:
            raise ValueError("conflicting acquisition evidence replay")
        return manifest
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        staged = Path(temporary) / run_id
        staged.mkdir()
        for name, content in expected.items():
            (staged / name).write_bytes(content)
        shutil.move(str(staged), destination)
    return manifest


def verify(evidence_dir: Path, canonical_path: Path) -> dict:
    manifest = _load_object(evidence_dir / "manifest.json")
    content_identity = manifest.get("manifest_content_sha256")
    unhashed_manifest = dict(manifest)
    unhashed_manifest.pop("manifest_content_sha256", None)
    if content_identity != digest(canonical_json(unhashed_manifest)):
        raise ValueError("manifest content digest mismatch")
    if set(path.name for path in evidence_dir.iterdir()) != {
            "manifest.json", "dry-run-report.json", "source-mb2.json"}:
        raise ValueError("acquisition evidence contains unexpected files")
    for name, identity in manifest.get("files", {}).items():
        content = (evidence_dir / name).read_bytes()
        if digest(content) != identity.get("sha256") or len(content) != identity.get("bytes"):
            raise ValueError(f"retained file digest mismatch: {name}")
    if set(manifest.get("files", {})) != {"dry-run-report.json", "source-mb2.json"}:
        raise ValueError("manifest file inventory is incomplete")
    expected_canonical = "sha256:" + digest(canonical_path.read_bytes())
    if manifest.get("canonical_snapshot_identity") != expected_canonical:
        raise ValueError("canonical snapshot identity changed")
    # Reuse retention validation without writing by checking the durable report and source.
    report = _load_object(evidence_dir / "dry-run-report.json")
    source = json.loads((evidence_dir / "source-mb2.json").read_text())
    if any(manifest.get(x) is not False for x in
           ("canonical_write", "promotion_performed", "observations_persisted")):
        raise ValueError("manifest does not prove write isolation")
    linked = {
        "acquisition_run_id": "run_id", "provider": "provider", "target": "target",
        "retrieved_at": "retrieved_at", "source_observed_at": "source_observed_at",
        "canonical_snapshot_identity": "canonical_snapshot_identity",
        "source_dataset": "source_dataset", "source_url": "source_url",
        "provider_source_sha256": "source_sha256", "normalized_sha256": "normalized_sha256",
        "mapping_counts": "mapping_counts", "source_record_count": "source_record_count",
        "mb2_record_count": "mb2_record_count",
    }
    if any(manifest.get(left) != report.get(right) for left, right in linked.items()):
        raise ValueError("report and manifest disagree")
    price = {"known": report.get("known_price_observation_count"),
             "missing": report.get("missing_price_observation_count"),
             "observations": report.get("observation_count")}
    if manifest.get("price_census") != price or report.get("persisted") is not False or len(source) != manifest.get("mb2_record_count"):
        raise ValueError("report and manifest disagree")
    if any(not isinstance(x, dict) or str(x.get("set", "")).lower() != "mb2" for x in source):
        raise ValueError("retained provider projection contains a non-MB2 record")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    keep = sub.add_parser("retain")
    keep.add_argument("--report", type=Path, required=True)
    keep.add_argument("--source", type=Path, required=True)
    keep.add_argument("--data-root", type=Path, default=Path("data"))
    check = sub.add_parser("verify")
    check.add_argument("--evidence", type=Path, required=True)
    check.add_argument("--canonical", type=Path, default=Path("data/canonical/state.json"))
    args = parser.parse_args()
    result = (retain(args.report, args.source, args.data_root) if args.command == "retain"
              else verify(args.evidence, args.canonical))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
