"""Deterministic original fictional test fixtures, never an importer or approval.

The command checks retained fixtures by default; --write is explicit fixture
authoring. It never refreshes provider/historical data or retained approvals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from repository.snapshots import (CAPABILITIES, CONTRACT_VERSION, REPRESENTATION,
    REQUIRED_CHECKS, UNRUN_CHECKS, VALIDATOR_PROFILE, _schema_bindings,
    _validator_sha256, canonical_json, semantic_identity)


FIXTURES = Path(__file__).parent / "fixtures/canonical_snapshots"


def read(path):
    return json.loads(Path(path).read_bytes())


def save(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(document) + b"\n")


def ref(root, name):
    raw = (root / name).read_bytes()
    return {"path": name, "byte_length": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def rebind(root):
    """Explicit test-only rehashing for structural adversarial tests, not approval."""
    root = Path(root)
    content = read(root / "content-manifest.json")
    source = read(root / "source-manifest.json")
    source["source_manifest_id"] = semantic_identity("source-manifest", {k: v for k, v in source.items() if k != "source_manifest_id"})
    save(root / "source-manifest.json", source)
    content["files"] = [ref(root, item["path"]) for item in content["files"]]
    content["policy"] = ref(root, "policy.json")
    content["schema_bindings"] = ref(root, "schema-bindings.json")
    content["source_manifest"] = ref(root, "source-manifest.json")
    content["source_manifest_id"] = source["source_manifest_id"]
    content["schema_set_id"] = semantic_identity("schema-set", read(root / "schema-bindings.json"))
    content["policy_id"] = semantic_identity("policy", read(root / "policy.json"))
    inventory = {}
    for kind, folder in (("card", "cards"), ("printing", "printings")):
        entries = [{"id": path.parent.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                   for path in sorted((root / "data/canonical/games" / content["game"] / folder).glob("*/*.json"))]
        inventory[kind] = {"count": len(entries), "records": entries}
    inventory["identifier"] = {"count": 0, "records": []}
    content["entity_inventory"] = inventory
    content["content_id"] = semantic_identity("content-manifest", {k: v for k, v in content.items() if k != "content_id"})
    save(root / "content-manifest.json", content)
    validation_input = {"content_id": content["content_id"], "schema_set_id": content["schema_set_id"],
        "policy_id": content["policy_id"], "validator_profile": VALIDATOR_PROFILE,
        "validator_sha256": _validator_sha256(), "required_checks": list(REQUIRED_CHECKS)}
    validation_id = semantic_identity("validation-input", validation_input)
    report = {"schema_version": "v1", "game": content["game"], "content_id": content["content_id"],
        "validation_input_id": validation_id, "inventory_identity": semantic_identity("entity-inventory", inventory),
        "status": "valid_fictional", "checks": [{"name": name, "status": "passed"} for name in REQUIRED_CHECKS],
        "unrun_checks": list(UNRUN_CHECKS), "production_eligible": False, "approval_state": "not_granted"}
    save(root / "validation-report.json", report)
    release = {"schema_version": "v1", "contract_version": CONTRACT_VERSION,
        "scope": "original-fictional-only", "production_eligible": False,
        "approval_state": "not_granted", "source_policy_clearance": "not_granted",
        **{key: content[key] for key in ("game", "content_id", "source_manifest_id", "schema_set_id", "policy_id",
          "representation_profile", "entity_inventory", "capabilities")},
        "content_manifest": ref(root, "content-manifest.json"), "source_manifest": ref(root, "source-manifest.json"),
        "validation_report": ref(root, "validation-report.json"), "validation_input": validation_input,
        "validation_input_id": validation_id, "created_at": "2026-10-15T00:00:00Z", "decision_references": [],
        "compatibility": {"reader_profile": REPRESENTATION, "validator_profile": VALIDATOR_PROFILE}}
    release["snapshot_id"] = semantic_identity("release-manifest", release)
    save(root / "release-manifest.json", release)
    return release["snapshot_id"]


def build_snapshot(root, *, game, names, printing_counts):
    root = Path(root)
    assert len(names) == len(printing_counts)
    prefix = "data/canonical/games/" + game + "/"
    save(root / prefix / "game.json", {"id": game, "name": game.title() + " Fictional Fixture"})
    evidence = "Original fictional game " + game + ": " + "; ".join(names) + ". No provider, ownership or real-game evidence.\n"
    (root / "evidence").mkdir(parents=True)
    (root / "evidence/original-fictional.txt").write_text(evidence, encoding="utf-8")
    evidence_ref = ref(root, "evidence/original-fictional.txt")
    source_id = "original-fixture"
    def provenance(keys):
        return [{"source_id": source_id, "field_paths": keys, "claim": "Original fictional fixture definition only."}]
    save(root / prefix / "sources/original-fixture.json", {"schema_version": "v1", "id": source_id,
        "title": "Original fictional evidence", "source_classification": "internal", "provider": "Original fictional fixture",
        "source_location": "urn:mtg-lab:fictional:" + game, "access_date": "2026-10-15", "verification_status": "confirmed",
        "claims": ["Defines fictional fixture identities, not provider facts or physical ownership."], "record_version": "fixture-v1",
        "content_hash": evidence_ref["sha256"], "archival_location": evidence_ref["path"]})
    for index, (name, count) in enumerate(zip(names, printing_counts), 1):
        card_id = "unit-" + str(index)
        save(root / prefix / ("cards/" + card_id + "/card.json"), {"schema_version": "v1", "id": card_id,
            "game": game, "name": name, "provenance": provenance(["id", "game", "name"])})
        for number in range(1, count + 1):
            printing_id = "edition-" + str(index) + "-" + str(number)
            values = {"schema_version": "v1", "id": printing_id, "card_id": card_id, "set_code": "FICTIONAL",
                "collector_number": str(index) + "-" + str(number), "rarity": "fixture", "language": "en"}
            values["provenance"] = provenance([key for key in values if key != "schema_version"])
            save(root / prefix / ("printings/" + printing_id + "/printing.json"), values)
    save(root / "policy.json", {"schema_version": "v1", "policy_version": "fictional-local-read-only-v1",
        "scope": "original-fictional-only", "production_eligible": False, "approval_state": "not_granted", "source_policy_clearance": "not_granted"})
    save(root / "schema-bindings.json", _schema_bindings())
    source = {"schema_version": "v1", "scope": "original-fictional-only", "game": game, "sources": [{
        "source_id": source_id, "record_path": prefix + "sources/original-fixture.json", "evidence": evidence_ref,
        "provider": "Original fictional fixture", "version": "fictional-source-v1"}]}
    save(root / "source-manifest.json", source)
    files = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.name != "source-manifest.json")
    save(root / "content-manifest.json", {"schema_version": "v1", "scope": "original-fictional-only", "game": game,
        "representation_profile": REPRESENTATION, "capabilities": CAPABILITIES, "files": [ref(root, name) for name in files]})
    return rebind(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="explicitly author new fictional fixtures")
    args = parser.parse_args()
    for game, names, counts in (("lantern", ("Lantern Unit", "Paper Glider"), (1, 2)),
                                ("clockwork", ("Clockwork Parcel",), (1,))):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = build_snapshot(root, game=game, names=names, printing_counts=counts)
            expected = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            destination = FIXTURES / game
            if args.write:
                for path, raw in expected.items():
                    target = destination / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
            actual = {path.relative_to(destination): path.read_bytes() for path in destination.rglob("*") if path.is_file()}
            if expected != actual:
                raise ValueError("retained fictional fixture does not replay exactly: " + game)
            print(game, identity, "verified")


if __name__ == "__main__":
    main()
