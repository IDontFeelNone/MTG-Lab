#!/usr/bin/env python3
"""Replay all production mechanical dossiers into isolated derived review outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from card_intelligence.mechanics import MechanicalCardIntelligence, stable_json

BASELINE = "c8941c568fb275a735ab6902e3663947f21760ee"
EXAMPLES = (("sol-ring", "6ad8011d-3471-4369-9d68-b264cc027487"),
    ("counterspell", "cc187110-1148-4090-bbb8-e205694a39f5"),
    ("lilianas-other-contract", "150be0e9-a65f-4209-bdea-8cf4c691d217"),
    ("there-theyre-their", "a865ed92-d1aa-416a-b8cd-d4cef11b0fef"))


def build_artifacts() -> dict[str, bytes]:
    engine = MechanicalCardIntelligence(ROOT / "data")
    dossiers = [engine.dossier(identity) for identity in sorted(engine.cards)]
    artifacts = {"dossiers.jsonl": ("\n".join(d.to_json() for d in dossiers) + "\n").encode(),
                 "cohort-report.json": (stable_json(engine.cohort_report()) + "\n").encode()}
    for slug, card_id in EXAMPLES:
        artifacts[slug + ".dossier.json"] = (engine.dossier(card_id).to_json() + "\n").encode()
        artifacts[slug + ".reasoning-context.json"] = (engine.reasoning_context(card_id).to_json() + "\n").encode()
    manifest = {"schema_version": "mechanical-cohort-review-manifest-v1",
        "canonical_main_baseline": BASELINE, "card_count": len(dossiers),
        "dossier_ordering": "exact canonical Card ID", "derived_only": True,
        "dossiers": [{"card_id": d.to_dict()["card_identity"]["card_id"],
                      "dossier_id": d.to_dict()["dossier_id"]} for d in dossiers],
        "files": {name: {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
                  for name, raw in sorted(artifacts.items())}}
    artifacts["manifest.json"] = (stable_json(manifest) + "\n").encode()
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify retained bytes without writing")
    args = parser.parse_args()
    artifacts = build_artifacts()
    destination = ROOT / "data/review/mechanical-card-cohort"
    actual = {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()} if destination.exists() else {}
    if args.check:
        if actual != artifacts:
            raise ValueError("mechanical cohort does not replay byte-identically")
    elif actual:
        if actual != artifacts:
            raise ValueError("refusing to overwrite conflicting retained review artifacts")
    else:
        destination.mkdir(parents=True, exist_ok=True)
        for name, raw in artifacts.items():
            (destination / name).write_bytes(raw)
    print(json.dumps({"verified": args.check, "card_count": len(json.loads(artifacts["manifest.json"])["dossiers"]),
                      "artifact_count": len(artifacts)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
