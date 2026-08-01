#!/usr/bin/env python3
"""Fail closed when an update branch changes anything outside durable update outputs."""
import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(); parser.add_argument("--base", required=True); args = parser.parse_args()
subprocess.run(["git", "fetch", "origin", args.base], check=True)
changed = subprocess.check_output(["git", "diff", "--name-only", f"origin/{args.base}...HEAD"], text=True).splitlines()
allowed = ("data/canonical/", "data/audit/bounded_promotions/", "data/automatic_updates/")
bad = [path for path in changed if not path.startswith(allowed)]
if bad: raise SystemExit("changed-file boundary violation: " + ", ".join(bad))
if not changed: raise SystemExit("update produced no durable changes")
