#!/usr/bin/env python3
"""Measure real current-catalog consumers; optional profiling is a separate run.

Expanded input is prepared only by the existing real-writer disposable fixture.
No publication or admission evidence is fabricated. OS page caches are uncontrolled.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import stat
import subprocess
import sys
import time
import unittest


WORKLOADS = ("role_comparison", "current_consumers", "snapshot_attachment")
CONTROL = "config/catalog_profiles/legacy-public-tier-a.json"
IMPLEMENTATIONS = ("src/query/engine.py", "src/repository/legacy_profile.py")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def timed(operation):
    started = time.perf_counter()
    value = operation()
    return value, time.perf_counter() - started


def test_method(case, name):
    result = unittest.TestResult()
    case(name).run(result)
    if result.errors or result.failures or result.skipped or result.testsRun != 1:
        raise RuntimeError(repr((result.errors, result.failures, result.skipped)))


def worker(args):
    started = time.perf_counter()
    root = args.repo.resolve()
    sys.path[:0] = [str(root / "src"), str(root / "tests")]
    state = json.loads((root / "data/canonical/state.json").read_bytes())
    control = json.loads((root / CONTROL).read_bytes())
    intact = all(hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() == row["sha256"]
                 for row in control["files"])
    result = {"catalog_counts": {key: len(rows) for key, rows in sorted(state.items())},
              "catalog_state_sha256": hashlib.sha256((root / "data/canonical/state.json").read_bytes()).hexdigest(),
              "profile_branch": "intact_full_parity" if intact else "historical_profile_drift_rejection",
              "workload": args.workload, "seconds": {}}

    def cycles(label, operation):
        values = []
        for _ in range(args.warm + 1):
            value, elapsed = timed(operation)
            result["seconds"].setdefault(label, []).append(elapsed)
            values.append(value)
            print(f"  {label}: {elapsed:.6f}s", file=sys.stderr, flush=True)
        return values

    if args.workload == "role_comparison":
        module = importlib.import_module("test_role_comparison_public_compatibility")
        original_digest = module.digest
        artifact_digests = []

        def capture_digest(value):
            observed = original_digest(value)
            artifact_digests.append(observed)
            return observed

        module.digest = capture_digest

        def parity():
            artifact_digests.clear()
            test_method(module.RoleComparisonPublicCompatibilityTests,
                "test_current_public_exact_role_comparison_parity_or_explicit_baseline_drift_block")
            return digest(artifact_digests)

        signatures = cycles("actual_compatibility_test", parity)
        if len(set(signatures)) != 1:
            raise RuntimeError("role/comparison outputs changed across unchanged calls")
        result["consumer_output_digest_sequence_sha256"] = signatures[0]
        result["consumer_artifact_digest_count"] = len(artifact_digests)
        result["assertion_scope"] = ("full original role/comparison parity assertions" if intact else
                                     "old profile must reject; expensive parity branch did not execute")
    elif args.workload == "current_consumers":
        module = importlib.import_module("test_current_catalog_validation")
        case = module.CurrentCatalogValidationTests
        _, result["seconds"]["cold_class_construction"] = timed(case.setUpClass)
        print(f"  cold_class_construction: {result['seconds']['cold_class_construction']:.6f}s",
              file=sys.stderr, flush=True)
        for name in ("test_query_and_collection_read_actual_current_catalog",
                     "test_mechanical_coverage_is_accounted_without_claiming_completeness"):
            cycles(name, lambda name=name: test_method(case, name))
        result["query_snapshot_id"] = case.query.snapshot().snapshot_id
        result["resolver_snapshot_id"] = case.resolver.canonical_snapshot_id
        result["mechanical_snapshot_id"] = case.mechanical.snapshot_id
        result["reconciliation_sha256"] = digest(case.mechanical.reconciliation)
        result["mechanical_missing_count"] = len(case.mechanical.reconciliation["missing_canonical_card_ids"])
    else:
        from query.engine import CanonicalQueryEngine
        from repository.legacy_profile import attach_legacy_compatibility
        from repository.snapshots import SnapshotError
        query, result["seconds"]["cold_query_construction"] = timed(lambda: CanonicalQueryEngine(
            "magic", data_root=root / "data", games_root=root / "data/canonical/games"))
        snapshots = cycles("query_snapshot", query.snapshot)
        result["query_snapshot_id"] = snapshots[0].snapshot_id
        if any(s.snapshot_id != result["query_snapshot_id"] for s in snapshots):
            raise RuntimeError("snapshot identity changed across unchanged calls")
        exported = snapshots[-1].as_dict()
        result["snapshot_export_sha256"] = digest(exported)
        result["entity_counts"] = dict(Counter(x.entity_type for x in snapshots[-1].entities))

        def attach():
            return attach_legacy_compatibility(root, control_path=CONTROL, game="magic",
                                              expected_profile_id=control["profile_id"])

        if intact:
            attachment, result["seconds"]["cold_attachment_construction"] = timed(attach)
            cycles("attachment_verify_unchanged", attachment.verify_unchanged)
            attached, result["seconds"]["cold_attached_query_construction"] = timed(
                lambda: CanonicalQueryEngine.from_attachment(attachment))
            attached_snapshots = cycles("attached_query_snapshot", attached.snapshot)
            if any(s.as_dict() != exported for s in attached_snapshots):
                raise RuntimeError("attached and ordinary current query exports differ")
            result["profile_id"] = attachment.binding["profile_id"]
            result["closure_id"] = attachment.binding["closure_id"]
        else:
            def reject():
                try:
                    attach()
                except SnapshotError as error:
                    return error.code
                raise RuntimeError("expanded current catalog accepted historical profile")
            result["rejection_codes"] = cycles("historical_attachment_rejection", reject)
    result["first_process_operations_with_import_seconds"] = time.perf_counter() - started
    result["max_rss_kib_linux"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return result


def revision(root):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()
    return {"head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
            "dirty": bool(git("status", "--porcelain")),
            "implementation_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                      for name in IMPLEMENTATIONS}}


def input_inventory(root):
    """Pin the disposable query's canonical/audit inputs, outside timed operations."""
    rows = []
    for family in ("data/canonical", "data/audit"):
        for path in sorted((root / family).rglob("*")):
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise RuntimeError("query input inventory contains a symlink")
            if stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode):
                raise RuntimeError("query input inventory contains a nonregular file")
            raw = path.read_bytes()
            rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(raw),
                         "sha256": hashlib.sha256(raw).hexdigest()})
    return {"sha256": digest(rows), "files": rows, "file_count": len(rows),
            "total_bytes": sum(row["bytes"] for row in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--state", choices=("ordinary", "expanded", "both"), default="both")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--warm", type=int, default=2)
    parser.add_argument("--workload", choices=WORKLOADS, action="append")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--comparison-repo", type=Path,
                        help="Expanded only: compare its two authorized implementations on the SAME prepared inputs")
    parser.add_argument("--profile", type=Path, help="Separate targeted profile; requires one workload and state")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        args.workload = args.workload[0]
        if args.profile:
            import cProfile
            profiler = cProfile.Profile()
            observed = profiler.runcall(worker, args)
            profiler.dump_stats(str(args.profile))
            observed["profiled_not_ordinary_runtime"] = True
        else:
            observed = worker(args)
        print(json.dumps(observed, sort_keys=True))
        return
    if args.repetitions < 1 or args.warm < 0:
        parser.error("positive repetitions and nonnegative warm count required")
    workloads = args.workload or WORKLOADS
    if args.profile and (len(workloads) != 1 or args.state == "both" or args.repetitions != 1):
        parser.error("profile separately with one workload, one state, and --repetitions 1")
    if args.comparison_repo and (args.state != "expanded" or args.profile):
        parser.error("--comparison-repo requires expanded state and unprofiled measurements")
    root = args.repo.resolve()
    environment = dict(os.environ, PYTHONPATH=str(root / "src") + os.pathsep + str(root / "tests"),
                       PYTHONHASHSEED="0")
    report = {"revision": revision(root), "python": sys.version, "platform": platform.platform(),
              "cpu_count": os.cpu_count(), "pythonhashseed": "0", "command": sys.argv,
              "cache_qualification": "fresh subprocess per sample; repeated calls within sample; OS page cache uncontrolled",
              "memory_qualification": "Linux maximum RSS includes imports/operations and may include the pre-exec parent image; expanded-worker RSS is not an isolated consumer allocation measurement",
              "configured_source_selector_names": sorted(key for key in environment
                  if key.startswith("MTGLAB_") and key.endswith("_SOURCE")), "states": {}}
    if args.comparison_repo:
        report["comparison_revision"] = revision(args.comparison_repo.resolve())
    fixture = None
    try:
        for state in (("ordinary", "expanded") if args.state == "both" else (args.state,)):
            selected_root = root
            preparation = 0.0
            if state == "expanded":
                sys.path[:0] = [str(root / "src"), str(root / "tests")]
                from publication_validation_regression import ExpandedPublicationValidationRegression
                fixture = ExpandedPublicationValidationRegression()
                _, preparation = timed(fixture.prepare_writer_expansion)
                selected_root = fixture.root
            samples = {}
            report["states"][state] = {"preparation_seconds": preparation, "workloads": samples,
                "preparation_path": ("existing real writer prepare_writer_expansion; no publication invoked"
                                     if state == "expanded" else "ordinary actual checkout; no preparation")}
            before = input_inventory(selected_root) if args.comparison_repo else None
            if before is not None:
                report["states"][state]["input_inventory_before"] = before
            for implementation in (("baseline", "comparison") if args.comparison_repo else ("selected",)):
                if implementation == "comparison":
                    for name in IMPLEMENTATIONS:
                        source = args.comparison_repo.resolve() / name
                        if not stat.S_ISREG(source.lstat().st_mode):
                            raise RuntimeError("comparison implementation is not a regular file")
                        shutil.copyfile(source, selected_root / name)
                        if hashlib.sha256((selected_root / name).read_bytes()).hexdigest() != report["comparison_revision"]["implementation_sha256"][name]:
                            raise RuntimeError("comparison implementation changed during copy")
                    if input_inventory(selected_root) != before:
                        raise RuntimeError("query inputs changed during implementation-only overlay")
                    samples = {}
                    report["states"][state]["comparison_workloads"] = samples
                for workload in workloads:
                    samples[workload] = []
                    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--repo", str(selected_root),
                               "--workload", workload, "--warm", str(args.warm)]
                    if args.profile:
                        command += ["--profile", str(args.profile.resolve())]
                    for repetition in range(args.repetitions):
                        print(f"Measuring {state}/{implementation}/{workload} sample {repetition + 1}", file=sys.stderr, flush=True)
                        observed, elapsed = timed(lambda: json.loads(subprocess.check_output(
                            command, cwd=selected_root, env=environment, text=True)))
                        observed["whole_subprocess_seconds"] = elapsed
                        samples[workload].append(observed)
                        if args.output:
                            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            if before is not None:
                after = input_inventory(selected_root)
                if after != before:
                    raise RuntimeError("query inputs changed across controlled measurements")
                report["states"][state]["input_inventory_after"] = after
    finally:
        if fixture is not None:
            fixture.doCleanups()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
