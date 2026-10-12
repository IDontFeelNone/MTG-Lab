#!/usr/bin/env python3
"""Prepare or replay one isolated, non-promoting functional-role review bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from card_intelligence.mechanics import stable_json
from card_intelligence.roles import FunctionalRolePilot


def comparison_text(comparison: dict) -> str:
    """Render only supplied proposed functions, qualifiers and evidence references."""
    lines = ["# Functional comparison — pending human review", "",
        "These are engineer-authored proposals tied to retained evidence. No human approval or canonical role admission has occurred.", "",
        "Shared directly evidenced proposed roles: " + ", ".join(comparison["shared_known_function_roles"]) + ".", "",
        comparison["interpretation"], ""]
    for card in comparison["cards"]:
        lines.extend(["## " + card["card_identity"]["name"], "",
                      "Exact Card: `" + card["card_identity"]["card_id"] + "`.", ""])
        for candidate in card["role_candidates"]:
            state = candidate["value"]["status"]
            lines.extend([f"### {candidate['role_reference']['role_id']} — {state}; requires_review", "",
                          candidate["value"]["data"] or candidate["basis_explanation"], ""])
            if state != "known": lines.extend([candidate["basis_explanation"], ""])
            for key in ("costs", "conditions", "restrictions"):
                for text in candidate["qualifiers"][key]: lines.append(f"- {key}: {text}")
            lines.extend(["- timing: " + candidate["qualifiers"]["timing"]["description"]])
            for text in candidate["context_dependencies"]: lines.append("- context dependency: " + text)
            for text in candidate["limitations"]: lines.append("- limitation: " + text)
            lines.extend(["", "Evidence: `" + candidate["candidate_id"] + "`; `" +
                          candidate["mechanical_binding"]["dossier_id"] + "`.", "",
                          "Retained Oracle passage:", ""])
            lines.extend("> " + text for text in candidate["mechanical_binding"]["ability_lines"])
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def build_artifacts() -> dict[str, bytes]:
    pilot = FunctionalRolePilot(ROOT / "data")
    dossiers = [pilot.dossier(i) for i in sorted(pilot.cards)]
    comparison = pilot.comparison()
    artifacts = {"dossiers.jsonl": ("\n".join(stable_json(d) for d in dossiers) + "\n").encode(),
                 "review-report.json": (stable_json(pilot.report()) + "\n").encode(),
                 "comparison.json": (stable_json(comparison) + "\n").encode(),
                 "comparison.md": comparison_text(comparison).encode()}
    for card_id in sorted(pilot.plan["comparison_card_ids"]):
        artifacts[card_id + ".reasoning-context.json"] = (pilot.reasoning_context(card_id).to_json() + "\n").encode()
    manifest = {"schema_version": "functional-role-review-manifest-v1",
        "canonical_main_baseline": pilot.plan["canonical_main_baseline"],
        "canonical_snapshot_id": pilot.mechanical.snapshot_id,
        "annotation_plan_identity": pilot.plan_identity, "vocabulary_identity": pilot.vocabulary_identity,
        "input_files": {p.relative_to(ROOT).as_posix(): {"bytes": p.stat().st_size,
                        "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                        for p in (pilot.plan_path, pilot.vocabulary_path)},
        "review_status": "requires_review", "human_attestation": None, "canonical_admission": False,
        "dossiers": [{"card_id": d["card_identity"]["card_id"], "dossier_id": d["dossier_id"]} for d in dossiers],
        "files": {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                  for name, raw in sorted(artifacts.items())}}
    artifacts["manifest.json"] = (stable_json(manifest) + "\n").encode()
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare retained bytes without writing")
    args = parser.parse_args()
    artifacts = build_artifacts()
    destination = ROOT / "data/review/functional-role-pilot"
    actual = {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()} if destination.exists() else {}
    if args.check:
        if actual != artifacts: raise ValueError("functional-role pilot does not replay byte-identically")
    elif actual:
        if actual != artifacts: raise ValueError("refusing to overwrite conflicting review evidence")
    else:
        destination.mkdir(parents=True, exist_ok=True)
        for name, raw in artifacts.items(): (destination / name).write_bytes(raw)
    print(json.dumps({"artifact_count": len(artifacts), "pilot_cards": 15, "verified": args.check}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
