#!/usr/bin/env python3
"""Compare fixed public validation cycles in isolated checkouts.

Every timed cycle loads the actual retained package and builds its manifest.
Fresh-process samples include imports and first-use metadata setup. Warm samples
reuse immutable metadata in that process while still reading historical files.
OS page caches are deliberately uncontrolled; no sample claims cold storage.
No source artifact or selector is required. Profiling is separate from timing.
"""
from __future__ import annotations

import argparse
import cProfile
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import pstats
import subprocess
import sys
import time


PACKAGES = ("shared_target_declaration", "shared_target_allocation", "shared_proposal_legality")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def worker(args):
    started = time.perf_counter()
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo / "src"))
    package = importlib.import_module("gameplay_rules." + args.package + ".package")
    root = repo / "reference-reviews"

    def cycle():
        records = package.load_package(root / package.PACKAGE_NAME, review_root=root)
        metadata = package.manifest(records, review_root=root)
        return {"package_id": metadata["package_id"],
                "output_sha256": hashlib.sha256(canonical({"records": records, "manifest": metadata})).hexdigest()}

    if args.profile:
        profiler = cProfile.Profile()
        profiler.enable()
        result = cycle()
        profiler.disable()
        profiler.dump_stats(str(args.profile))
        stats = pstats.Stats(profiler)
        interesting = []
        for (filename, line, name), (primitive, calls, own, cumulative, _) in stats.stats.items():
            if "/gameplay_rules/" in filename and name in {
                    "_read", "_expected_records", "retained_binding", "validate_historical",
                    "load_package", "manifest", "verify_prior_packages", "_historical_tool"}:
                interesting.append({"file": filename.split("/src/")[-1], "function": name,
                                    "calls": calls, "primitive_calls": primitive,
                                    "own_seconds": own, "cumulative_seconds": cumulative})
        result.update(profile_calls=sorted(interesting, key=lambda item: item["cumulative_seconds"], reverse=True),
                      profile_total_calls=stats.total_calls, profile_primitive_calls=stats.prim_calls,
                      profile_total_seconds=stats.total_tt)
    else:
        result = cycle()
        result["first_cycle_with_import_seconds"] = time.perf_counter() - started
        result["warm_cycle_seconds"] = []
        for _ in range(args.warm):
            warm_started = time.perf_counter()
            observed = cycle()
            result["warm_cycle_seconds"].append(time.perf_counter() - warm_started)
            if observed["output_sha256"] != result["output_sha256"]:
                raise RuntimeError("public operation outputs changed across repetitions")
    print(json.dumps(result, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--package", choices=PACKAGES, action="append")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--warm", type=int, default=2)
    parser.add_argument("--profile-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--profile", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        args.package = args.package[0]
        worker(args)
        return
    repo = args.repo.resolve()
    if args.repetitions < 1 or args.warm < 0:
        parser.error("positive repetitions and nonnegative warm count required")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(repo / "src")
    environment["PYTHONHASHSEED"] = "0"
    # Explicitly record selector presence without revealing values or paths.
    configured = sorted(key for key in environment if key.startswith("MTGLAB_") and key.endswith("_SOURCE"))
    implementation_paths = ["src/gameplay_rules/" + name + "/package.py" for name in PACKAGES]
    implementation_paths += ["src/gameplay_rules/retained_stage_validation.py"]
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)),
        "python": sys.version, "platform": platform.platform(), "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "implementation_sha256": {name: hashlib.sha256((repo / name).read_bytes()).hexdigest()
                                  for name in implementation_paths if (repo / name).is_file()},
        "pythonhashseed": "0", "configured_source_selectors": configured,
        "operation": "load_package(actual retained package) followed by manifest(records)",
        "cache_qualification": "fresh Python processes / warm immutable metadata; OS page cache uncontrolled",
        "whole_process_qualification": "includes startup, imports, first cycle, all warm cycles, and teardown",
        "repetitions": args.repetitions, "warm_per_process": args.warm, "samples": {}, "profiles": {},
    }
    for package in args.package or PACKAGES:
        command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--repo", str(repo),
                   "--package", package, "--warm", str(args.warm)]
        samples = []
        for _ in range(args.repetitions):
            started = time.perf_counter()
            observed = json.loads(subprocess.check_output(command, cwd=repo, env=environment, text=True))
            observed["whole_process_seconds"] = time.perf_counter() - started
            samples.append(observed)
        report["samples"][package] = samples
        if args.profile_dir:
            args.profile_dir.mkdir(parents=True, exist_ok=True)
            profile = args.profile_dir / (package + ".prof")
            report["profiles"][package] = json.loads(subprocess.check_output(
                command + ["--profile", str(profile)], cwd=repo, env=environment, text=True))
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
