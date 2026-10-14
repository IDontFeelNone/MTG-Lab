#!/usr/bin/env python3
"""Retain or check one isolated contextual comparison; no admission or acquisition."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from card_intelligence.comparison import ContextualCardComparisonPilot, comparison_explanation
from card_intelligence.mechanics import stable_json


def build_artifacts(data_root: Path | None = None) -> dict[str, bytes]:
    data = Path(data_root if data_root is not None else ROOT / "data").resolve()
    repository_root = data.parent
    config = repository_root / "config/card_intelligence"
    pilot = ContextualCardComparisonPilot(data,
        plan_path=config / "contextual-comparison-pilot-v1.json",
        role_plan_path=config / "functional-role-pilot-v1.json",
        role_vocabulary_path=config / "functional-role-vocabulary-v1.json")
    dossier = pilot.dossier()
    artifacts = {"comparison.json": (dossier.to_json() + "\n").encode(),
        "decision-inputs.json": (stable_json(pilot.decision_inputs()) + "\n").encode(),
        "reasoning-context.json": (stable_json(pilot.reasoning_context()) + "\n").encode(),
        "explanation.md": comparison_explanation(dossier).encode()}
    source = pilot.cards[0]["source"]
    inputs = [pilot.plan_path, pilot.roles.plan_path, pilot.roles.vocabulary_path,
              repository_root / source["retained_source_reference"], repository_root / source["manifest_reference"]]
    manifest = {"schema_version": "contextual-card-comparison-manifest-v1",
        "canonical_main_baseline": pilot.plan["canonical_main_baseline"],
        "canonical_snapshot_id": pilot.roles.mechanical.snapshot_id,
        "comparison_id": dossier.to_dict()["comparison_id"], "plan_identity": pilot.plan_identity,
        "context_identity": pilot.context_identity, "prepared_at": pilot.plan["prepared_at"],
        "review": dossier.to_dict()["review"], "decision_outcome": "abstain",
        "input_files": {p.relative_to(repository_root).as_posix(): {"bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs},
        "files": {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                  for name, raw in sorted(artifacts.items())}}
    artifacts["manifest.json"] = (stable_json(manifest) + "\n").encode()
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="read-only byte-identical replay")
    args = parser.parse_args()
    artifacts = build_artifacts()
    destination = ROOT / "data/review/contextual-card-comparison"
    actual = {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()} if destination.exists() else {}
    if args.check:
        if actual != artifacts:
            raise ValueError("contextual comparison does not replay byte-identically")
    elif actual:
        if actual != artifacts:
            raise ValueError("refusing to overwrite conflicting review evidence")
    else:
        destination.mkdir(parents=True, exist_ok=True)
        for name, raw in artifacts.items():
            (destination / name).write_bytes(raw)
    print(json.dumps({"artifact_count": len(artifacts), "candidate_cards": 3,
                      "outcome": "abstain", "verified": args.check}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
