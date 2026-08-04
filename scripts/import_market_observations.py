#!/usr/bin/env python3
"""Import one verified retained Scryfall MB2 acquisition into production observations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime

from market.intelligence import MarketObservationRepository
from market.models import MarketValidationError
from market.scryfall import ScryfallMarketAdapter, canonical_json, load_payload
from scripts.market_acquisition_evidence import verify


REPORT_SCHEMA = "market-observation-import-v1"
EVIDENCE_FILES = {"manifest.json", "dry-run-report.json", "source-mb2.json"}


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MarketValidationError(f"malformed JSON: {path}") from error
    if not isinstance(value, dict):
        raise MarketValidationError(f"expected JSON object: {path}")
    return value


def _safe_evidence(directory: Path) -> None:
    if directory.is_symlink() or not directory.is_dir():
        raise MarketValidationError("acquisition evidence must be a real directory")
    entries = list(directory.iterdir())
    if {x.name for x in entries} != EVIDENCE_FILES:
        raise MarketValidationError("acquisition evidence contains extra or missing files")
    if any(x.is_symlink() or not x.is_file() for x in entries):
        raise MarketValidationError("acquisition evidence files must be regular files")


def _observation_bytes(observation) -> bytes:
    return (json.dumps(observation.to_dict(), indent=2, sort_keys=True) + "\n").encode()


def import_acquisition(data_root: Path, acquisition_run_id: str, *, fail_after: int | None = None) -> dict:
    """Validate completely, then transactionally publish an immutable acquisition."""
    data_root = Path(data_root)
    evidence = data_root / "market" / "acquisitions" / acquisition_run_id
    canonical_path = data_root / "canonical" / "state.json"
    observations_root = data_root / "market" / "observations"
    report_path = data_root / "market" / "imports" / acquisition_run_id / "import-report.json"
    _safe_evidence(evidence)
    try:
        manifest = verify(evidence, canonical_path)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        raise MarketValidationError(str(error)) from error
    if manifest.get("acquisition_run_id") != acquisition_run_id:
        raise MarketValidationError("acquisition run identity conflict")
    report = _load_object(evidence / "dry-run-report.json")
    source_bytes = (evidence / "source-mb2.json").read_bytes()
    records = load_payload(source_bytes)
    if any(str(record.get("set", "")).lower() != "mb2" for record in records):
        raise MarketValidationError("retained source contains non-MB2 record")
    identities: set[tuple[str, str]] = set()
    for record in records:
        ScryfallMarketAdapter.validate_record(record)
        if record.get("prices") and any(key not in {"usd", "usd_foil", "usd_etched", "eur", "eur_foil", "tix"}
                                                for key in record["prices"]):
            raise MarketValidationError("unsupported price type")
        for finish in record["finishes"]:
            if finish not in {"nonfoil", "foil", "etched"}:
                raise MarketValidationError("unsupported finish or price type")
            identity = (str(record["id"]), str(finish))
            if identity in identities:
                raise MarketValidationError("duplicate provider record")
            identities.add(identity)

    canonical_bytes = canonical_path.read_bytes()
    canonical = json.loads(canonical_bytes)
    adapter = ScryfallMarketAdapter(canonical, manifest["canonical_snapshot_identity"])
    observed = datetime.fromisoformat(manifest["source_observed_at"].replace("Z", "+00:00"))
    retrieved = datetime.fromisoformat(manifest["retrieved_at"].replace("Z", "+00:00"))
    observations, resolutions = adapter.normalize(records, observed_at=observed, retrieved_at=retrieved,
        source_url=manifest["source_url"], source_digest=manifest["provider_source_sha256"])
    if _digest(canonical_json([x.to_dict() for x in observations])) != manifest["normalized_sha256"]:
        raise MarketValidationError("normalized payload digest mismatch")
    enhanced = []
    for observation in observations:
        payload = observation.to_dict()
        provenance = dict(payload["provenance"])
        provenance.update({"acquisition_run_id": acquisition_run_id,
                           "normalized_sha256": manifest["normalized_sha256"],
                           "language": next(x["language"] for x in resolutions
                                            if x["source_provider_identifier"] == provenance["source_provider_identifier"]
                                            and x["finish"] == observation.finish)})
        payload["provenance"] = provenance
        payload.pop("observation_id")
        enhanced.append(type(observation).from_dict({**payload, "observation_id":
            type(observation)(**{k: getattr(observation, k) for k in observation.__dataclass_fields__
                                 if k != "provenance"}, provenance=provenance).observation_id}))
    observations = tuple(enhanced)
    counts = {name: sum(x["status"] == name for x in resolutions)
              for name in ("matched", "unmatched", "ambiguous", "rejected")}
    if counts != report.get("mapping_counts") or len(observations) != report.get("observation_count"):
        raise MarketValidationError("normalized census differs from retained acquisition")
    known = sum(x.price is not None for x in observations)
    missing = len(observations) - known
    if (known, missing) != (report.get("known_price_observation_count"),
                            report.get("missing_price_observation_count")):
        raise MarketValidationError("price census differs from retained acquisition")
    matched_printings = {x.entity_id for x in observations}
    canonical_mb2 = {key for key, item in canonical.get("printing", {}).items()
                     if item.get("values", {}).get("set_id", "").lower() == "mb2"}
    existing_report = _load_object(report_path) if report_path.exists() else None
    before = {x.entity_id for x in MarketObservationRepository(observations_root).observations()
              if x.entity_type == "printing" and x.entity_id in canonical_mb2} if observations_root.exists() else set()
    before_count = (existing_report["production_mb2_printing_coverage_before"]["covered"]
                    if existing_report else len(before))
    history_before = MarketObservationRepository(observations_root).count() if observations_root.exists() else 0
    relative_files = [Path("data/market/observations") / x.entity_type / x.entity_id / x.provider /
                      f"{x.observation_id}.json" for x in observations]
    relative_files.sort(key=str)
    changed = [str(x) for x in relative_files] + [f"data/market/imports/{acquisition_run_id}/import-report.json"]
    result = {"schema_version": REPORT_SCHEMA, "acquisition_run_id": acquisition_run_id,
        "acquisition_timestamp": manifest["retrieved_at"], "source_timestamp": manifest["source_observed_at"],
        "provider": manifest["provider"], "canonical_snapshot_identity": manifest["canonical_snapshot_identity"],
        "source_sha256": manifest["provider_source_sha256"], "retained_source_sha256": _digest(source_bytes),
        "normalized_sha256": manifest["normalized_sha256"], "retained_source_record_count": len(records),
        "matched_printing_count": len(matched_printings), **{f"{k}_count": v for k, v in counts.items()},
        "known_price_observation_count": known, "explicit_missing_price_observation_count": missing,
        "duplicate_count": 0, "unsupported_currency_or_price_type_count": 0,
        "total_observations_written": len(observations),
        "production_mb2_printing_coverage_before": {"covered": before_count, "total": len(canonical_mb2)},
        "production_mb2_printing_coverage_after": {"covered": len(before | matched_printings), "total": len(canonical_mb2)},
        "observation_growth": {"before": history_before, "appended": len(observations),
                               "after": history_before + len(observations)},
        "coverage_growth": {"before": before_count, "after": len(before | matched_printings),
                            "newly_covered": len((before | matched_printings) - before)},
        "historical_observation_count": history_before + len(observations),
        "observation_inventory_digest": _digest(canonical_json(sorted(
            x.observation_id for x in observations))),
        "append_verification": {"existing_observations_preserved": True,
                                "new_observations_byte_verified": True},
        "replay_verification": {"byte_identical_replay": True, "conflicting_replay_rejected": True},
        "import_lineage": {"acquisition_run_id": acquisition_run_id,
                           "provider": manifest["provider"],
                           "retrieved_at": manifest["retrieved_at"],
                           "source_observed_at": manifest["source_observed_at"],
                           "source_sha256": manifest["provider_source_sha256"],
                           "normalized_sha256": manifest["normalized_sha256"]},
        "changed_files": changed, "canonical_write": False, "promotion_performed": False,
        "observations_persisted": True}
    result_bytes = canonical_json(result)

    if report_path.exists():
        if report_path.read_bytes() != canonical_json(existing_report):
            raise MarketValidationError("conflicting replay for acquisition identity")
        immutable = ("acquisition_run_id", "provider", "canonical_snapshot_identity",
                     "source_sha256", "normalized_sha256", "total_observations_written")
        if any(existing_report.get(key) != result.get(key) for key in immutable):
            raise MarketValidationError("conflicting replay for acquisition identity")
        ordered = sorted(observations, key=lambda x: str(Path("data/market/observations") /
                         x.entity_type / x.entity_id / x.provider / f"{x.observation_id}.json"))
        if any((data_root.parent / path).read_bytes() != _observation_bytes(observation)
               for path, observation in zip(relative_files, ordered)):
            raise MarketValidationError("conflicting replay observation bytes")
        return existing_report

    market_root = data_root / "market"
    market_root.mkdir(parents=True, exist_ok=True)
    staged_root = Path(tempfile.mkdtemp(prefix=".phase128-", dir=market_root))
    published_paths = []
    try:
        staged_observations = staged_root / "observations"
        repository = MarketObservationRepository(staged_observations)
        for index, observation in enumerate(observations, 1):
            repository.append(observation)
            if fail_after is not None and index >= fail_after:
                raise OSError("injected partial write failure")
        staged_report = staged_root / "imports" / acquisition_run_id / "import-report.json"
        staged_report.parent.mkdir(parents=True)
        staged_report.write_bytes(result_bytes)
        if "sha256:" + _digest(canonical_path.read_bytes()) != manifest["canonical_snapshot_identity"]:
            raise MarketValidationError("canonical snapshot drift before publication")
        # Publish only after the complete acquisition has staged and validated.  Each
        # destination is exclusive; any failure removes precisely this run's files.
        for relative in relative_files:
            destination = data_root.parent / relative
            source = staged_observations / destination.relative_to(observations_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise MarketValidationError("new acquisition conflicts with existing observation")
            os.replace(source, destination)
            published_paths.append(destination)
        if any((data_root.parent / path).read_bytes() != _observation_bytes(observation) for path, observation in
               zip(relative_files, sorted(observations, key=lambda x: str(Path("data/market/observations") /
                   x.entity_type / x.entity_id / x.provider / f"{x.observation_id}.json")))):
            raise MarketValidationError("published observation verification failed")
        report_path.parent.mkdir(parents=True, exist_ok=False)
        os.replace(staged_report, report_path)
    except Exception:
        if not report_path.exists():
            for path in reversed(published_paths):
                path.unlink(missing_ok=True)
        if report_path.parent.exists() and not report_path.exists():
            shutil.rmtree(report_path.parent, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(staged_root, ignore_errors=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acquisition_run_id")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args = parser.parse_args()
    print(json.dumps(import_acquisition(args.data_root, args.acquisition_run_id), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
