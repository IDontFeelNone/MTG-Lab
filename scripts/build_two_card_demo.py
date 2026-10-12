#!/usr/bin/env python3
"""Replay exactly two retained Card dossiers into an isolated review directory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.card_dossier import CardEvidenceDossierBuilder, canonical_json, render_explanation

TARGETS = (("sol-ring", "6ad8011d-3471-4369-9d68-b264cc027487", "Sol Ring"),
           ("counterspell", "cc187110-1148-4090-bbb8-e205694a39f5", "Counterspell"))
BASELINE = "e5e11c41818b3a7e6bec85418a75a37e0ef638f0"


def build_artifacts() -> dict[str, bytes]:
    builder = CardEvidenceDossierBuilder(ROOT / "data")
    artifacts = {}
    cards = []
    for slug, card_id, name in TARGETS:
        dossier = builder.build(card_id)
        if dossier.to_dict()["card_identity"]["name"] != name:
            raise ValueError("authorized exact Card identity/name binding changed")
        artifacts[f"{slug}.dossier.json"] = (dossier.to_json() + "\n").encode()
        artifacts[f"{slug}.reasoning-context.json"] = (dossier.reasoning_context.to_json() + "\n").encode()
        artifacts[f"{slug}.explanation.md"] = render_explanation(dossier).encode()
        cards.append({"card_id": card_id, "name": name, "dossier_id": dossier.to_dict()["dossier_id"],
                      "reasoning_context_id": dossier.reasoning_context.context_id})
    manifest = {"schema_version": "two-card-evidence-demo-manifest-v1", "canonical_main_baseline": BASELINE,
        "cards": cards, "delivery": "read-only manual handoff; no model execution or transport",
        "files": {name: {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
                  for name, raw in sorted(artifacts.items())}}
    artifacts["manifest.json"] = (canonical_json(manifest) + "\n").encode()
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify retained artifacts without writing")
    args = parser.parse_args()
    destination = ROOT / "data/review/two-card-chatgpt-demo"
    artifacts = build_artifacts()
    if args.check:
        actual = {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()}
        if actual != artifacts:
            raise ValueError("retained two-Card demonstration does not replay byte-identically")
    else:
        destination.mkdir(parents=True, exist_ok=True)
        if any(destination.iterdir()):
            actual = {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()}
            if actual != artifacts:
                raise ValueError("refusing to overwrite conflicting retained review artifacts")
        else:
            for name, raw in artifacts.items():
                (destination / name).write_bytes(raw)
    print(json.dumps({"verified": args.check, "card_count": 2, "artifact_count": len(artifacts)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
