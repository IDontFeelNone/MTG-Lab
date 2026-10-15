"""Original fictional mixed-catalog fixture for the read-only Tier A seam.

These authored identities and source/audit documents describe no real game,
provider, collection, admission decision, or source-policy permission. Rebinding
is an explicit test-authoring operation, never a production integrity repair.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

from query.engine import CanonicalQueryEngine
from repository.legacy_profile import (AUTHORITY, CAPABILITIES, OPERATIONS,
    PRECEDENCE, PROFILE, TIER, closure_identity, namespace_patterns, profile_identity)
from repository.snapshots import canonical_json

CONTROL = "controls/legacy-public.json"
SELECTED_AUDITS = ("data/audit/fixture/typed.json", "data/audit/fixture/promoted.json")
EXCLUDED_AUDIT = "data/audit/fixture/excluded.json"


def read(path):
    return json.loads(Path(path).read_bytes())


def save(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(document) + b"\n")


def binding(root, name, placement):
    raw = (Path(root) / name).read_bytes()
    return {"path": name, "byte_length": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "placement": placement}


def resign(root, mutate=None):
    """Re-identify explicitly altered fictional control metadata for attack tests."""
    document = read(Path(root) / CONTROL)
    if mutate is not None:
        mutate(document)
    document["profile_id"] = profile_identity(document)
    save(Path(root) / CONTROL, document)
    return document["profile_id"]


def build_legacy_fixture(root, *, game="paper-world"):
    root = Path(root)
    prefix = "data/canonical/games/" + game + "/"
    selected_source = prefix + "sources/original-author.json"
    unselected_source = prefix + "sources/unselected-author.json"
    save(root / prefix / "game.json", {"id": game, "name": "Original Fictional Paper World"})
    source = {"schema_version": "v1", "id": "original-author", "title": "Original fictional authorship",
        "source_classification": "internal", "provider": "Fixture author",
        "source_location": "urn:mtg-lab:fictional:" + game, "access_date": "2026-10-15",
        "verification_status": "confirmed", "claims": ["Fictional definitions, no ownership or real provider facts."],
        "record_version": "fictional-v1"}
    save(root / selected_source, source)
    save(root / unselected_source, {**source, "id": "unselected-author", "title": "Outside selected Tier A context"})

    def provenance(keys):
        return [{"source_id": "original-author", "field_paths": list(keys),
                 "claim": "Original fictional fixture; no admission or permission decision."}]

    card = {"schema_version": "v1", "id": "paper-unit", "game": game, "name": "Paper Voyager"}
    card["provenance"] = provenance(["id", "game", "name"])
    save(root / prefix / "cards/paper-unit/card.json", card)
    printing = {"schema_version": "v1", "id": "paper-edition", "card_id": "paper-unit",
        "set_code": "PAPER", "collector_number": "1", "rarity": "original", "language": "en"}
    printing["provenance"] = provenance([key for key in printing if key != "schema_version"])
    save(root / prefix / "printings/paper-edition/printing.json", printing)
    save(root / prefix / "products/paper-box/product.json", {"schema_version": "v1", "id": "paper-box",
        "game": game, "name": "Fictional Empty Box", "product_type": "fictional", "lifecycle_status": "foundation",
        "slot_ids": [], "provenance": [{"claim": "Original fictional product identity only.",
            "source_classification": "internal", "source_location": "urn:fixture:paper-box", "verification_status": "confirmed"}]})

    def promoted(kind, values):
        return {"entity_type": kind, "values": values, "promotion_id": "fixture-promotion",
            "confidence": 1, "uncertainty_state": "known", "superseded_status": False,
            "evidence_references": ["fictional-assertion"],
            "provenance": {"source_id": "original-author", "scope": "fictional-only"},
            "acquisition_lineage": [{"source_id": "original-author", "operation": "fictional-test-authoring"}]}

    state = {"card": {
        "cloth-unit": promoted("card", {"name": "Cloth Cartographer"}),
        "paper-unit": promoted("card", {"name": "Shadow Must Not Replace Typed Card"})},
        "printing": {
            "cloth-edition": promoted("printing", {"uuid": "cloth-edition", "card_id": "cloth-unit", "set_id": "cloth",
                "collector_number": "2", "language": "Japanese", "finish_ids": ["plain"], "treatment_ids": []}),
            "paper-edition": promoted("printing", {"card_id": "cloth-unit", "set_id": "wrong-shadow"})},
        "identifier": {"cloth-alias": promoted("identifier", {"namespace": "fictional-provider", "value": "external-cloth",
            "printing_uuid": "cloth-edition"})},
        "finish": {"plain": promoted("finish", {"name": "Plain fictional finish"})}}
    save(root / "data/canonical/state.json", state)
    save(root / SELECTED_AUDITS[0], {"schema_version": "v1", "promotion_id": "fixture-typed-context",
        "result": "fictional_test_context_only", "promoted_entities": ["paper-unit", "paper-edition"]})
    save(root / SELECTED_AUDITS[1], {"schema_version": "v1", "promotion_id": "fixture-promotion",
        "result": "fictional_test_context_only", "promoted_entities": ["cloth-unit", "cloth-edition", "cloth-alias", "plain"]})
    save(root / EXCLUDED_AUDIT, {"promotion_id": "outside-tier-a", "promoted_entities": ["unrelated-fictional-identity"],
        "rejected_entities": ["outside-scope"], "validation_results": {"valid": False}})
    selected_core = [prefix + suffix for suffix in (
        "game.json", "cards/paper-unit/card.json", "printings/paper-edition/printing.json", "products/paper-box/product.json")]
    selected_core.append("data/canonical/state.json")
    files = sorted([binding(root, name, "CORE_CATALOG_CONTENT") for name in selected_core]
        + [binding(root, selected_source, "SOURCE_EVIDENCE_REFERENCE")]
        + [binding(root, name, "AUDIT_CONTEXT") for name in SELECTED_AUDITS], key=lambda row: row["path"])
    query = CanonicalQueryEngine(game, data_root=root / "data", games_root=root / "data/canonical/games")
    snapshot = query.snapshot()
    document = {"profile": PROFILE, "contract_version": "v1", "game": game,
        "capability_tier": TIER, "data_root": "data", "games_root": "data/canonical/games",
        "profile_id": "", "closure_id": closure_identity(files), "files": files,
        "namespaces": [{"pattern": pattern, "paths": sorted(path.relative_to(root).as_posix()
            for path in root.glob(pattern))} for pattern in namespace_patterns(game)],
        "game_namespaces": [game], "absent": ["data/canonical/knowledge/state.json"],
        "query_snapshot_id": snapshot.snapshot_id, "entity_counts": dict(Counter(item.entity_type for item in snapshot.entities)),
        "precedence": PRECEDENCE, "capabilities": dict(CAPABILITIES),
        "permissions": dict.fromkeys(OPERATIONS, "NOT_ESTABLISHED"), **AUTHORITY,
        "incompleteness": {"typed_materialization": "incomplete", "gameplay_rules": "unsupported",
            "optional_knowledge_state": "absent", "product_collation": "unsupported", "mechanical_evidence": "outside_tier_a",
            "finish_references": {"status": "incomplete", "unresolved_by_identifier": {}},
            "product_slots": 0},
        "historical_prestate_reference": hashlib.sha256(b"fictional informational prestate, not certified by Tier A").hexdigest()}
    document["profile_id"] = profile_identity(document)
    save(root / CONTROL, document)
    return document
