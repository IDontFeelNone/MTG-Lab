"""Operate the explicit raw acquisition stages without canonical promotion."""
import argparse
import json
from pathlib import Path

from acquisition import (AcquisitionEngine, FixtureProvider, ProviderTrustPolicy,
                         RawSnapshotStore, ProviderPolicy, assertions_from_normalized,
                         build_review_package, generate_reports, normalize_snapshot,
                         validate_pipeline, write_json)


def _load(path): return json.loads(path.read_text())


def _items(path, key):
    value = _load(path)
    return value.get(key, value if isinstance(value, list) else [value])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--run-root", type=Path, default=Path("data/acquisition-runs"))
    sub = parser.add_subparsers(dest="command", required=True)
    acquire = sub.add_parser("acquire")
    acquire.add_argument("provider", choices=("fixture",)); acquire.add_argument("dataset")
    acquire.add_argument("--fixture", type=Path, required=True); acquire.add_argument("--timestamp", required=True)
    acquire.add_argument("--run-id"); acquire.add_argument("--license-reference")
    normalize = sub.add_parser("normalize")
    normalize.add_argument("snapshot", type=Path); normalize.add_argument("--output", type=Path, required=True)
    assertions = sub.add_parser("assertions")
    assertions.add_argument("normalized", type=Path); assertions.add_argument("--output", type=Path, required=True)
    assertions.add_argument("--timestamp", required=True); assertions.add_argument("--evidence-class", default="unknown")
    assertions.add_argument("--confidence", type=float, default=0.0); assertions.add_argument("--verification-status", default="unverified")
    review = sub.add_parser("review-package")
    reports = sub.add_parser("reports")
    for command in (review, reports):
        command.add_argument("--run", type=Path, required=True); command.add_argument("--snapshots", type=Path, required=True)
        command.add_argument("--normalized", type=Path, required=True); command.add_argument("--assertions", type=Path, required=True)
        command.add_argument("--policy", type=Path, required=True); command.add_argument("--output", type=Path, required=True)
        command.add_argument("--previous-assertions", type=Path)
    review.add_argument("--acquisition-version", required=True)
    report = sub.add_parser("acquisition-report"); report.add_argument("run_id")
    args = parser.parse_args(argv)
    store = RawSnapshotStore(args.raw_root); engine = AcquisitionEngine(store, args.run_root)
    if args.command == "acquire":
        provider = FixtureProvider({args.dataset: args.fixture.read_bytes()}); engine.register(provider)
        result = engine.acquire(args.provider, args.dataset, started_at=args.timestamp,
                                run_id=args.run_id, license_reference=args.license_reference)
    elif args.command == "normalize":
        result = normalize_snapshot(FixtureProvider({}), store, args.snapshot, args.output)
    elif args.command == "assertions":
        document = json.loads(args.normalized.read_text())
        result = {"schema_version": "source-assertion-set-v1", "assertions": assertions_from_normalized(
            document, ProviderTrustPolicy(args.evidence_class, args.confidence, args.verification_status), args.timestamp)}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    elif args.command in {"review-package", "reports"}:
        run = _load(args.run); snapshots = _items(args.snapshots, "snapshots")
        normalized = _items(args.normalized, "documents"); assertions_data = _items(args.assertions, "assertions")
        previous = _items(args.previous_assertions, "assertions") if args.previous_assertions else []
        policy = ProviderPolicy.from_dict(_load(args.policy))
        if args.command == "review-package":
            result = build_review_package(run, snapshots, normalized, assertions_data, policy,
                                          args.acquisition_version, previous)
        else:
            validation = validate_pipeline(run, snapshots, normalized, assertions_data, policy)
            if not validation["valid"]: raise ValueError("pipeline validation failed: " + "; ".join(validation["errors"]))
            result = generate_reports(run, snapshots, normalized, assertions_data, validation, previous)
        write_json(args.output, result)
    else: result = engine.report(args.run_id)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__": raise SystemExit(main())
