"""Original fictional inputs for the explicit catalog/mechanical vertical.

The mechanical subsystem currently accepts one Scryfall-shaped retained-source
contract. These test-authored bytes exercise that shape; they are not a Scryfall
capture, provider assertions, ownership, approval, or permission evidence.
"""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import shutil

from card_intelligence.mechanics import DEFAULT_ACQUISITION, content_identity
from legacy_profile_fixture import (CONTROL, SELECTED_AUDITS, binding,
                                    build_legacy_fixture, read, save)
from query import CanonicalQueryEngine
from repository.legacy_profile import (attach_legacy_compatibility,
                                      closure_identity, profile_identity)

CARD_IDS = ("cloth-unit", "copper-unit")
PRINTING_IDS = ("cloth-edition", "copper-edition")
SOURCE_NAME = "source-fictional.json"


def rebind_catalog(root):
    """Re-identify only explicitly authored fictional fixture changes."""
    root = Path(root)
    document = read(root / CONTROL)
    document["files"] = [binding(root, row["path"], row["placement"])
                         for row in document["files"]]
    document["closure_id"] = closure_identity(document["files"])
    query = CanonicalQueryEngine("magic", data_root=root / "data",
                                 games_root=root / "data/canonical/games")
    snapshot = query.snapshot()
    document["query_snapshot_id"] = snapshot.snapshot_id
    document["entity_counts"] = dict(Counter(x.entity_type for x in snapshot.entities))
    document["profile_id"] = profile_identity(document)
    save(root / CONTROL, document)
    return document


def write_mechanical_source(directory, rows):
    directory = Path(directory)
    rows = copy.deepcopy(rows)
    save(directory / SOURCE_NAME, rows)
    source_digest = hashlib.sha256((directory / SOURCE_NAME).read_bytes()).hexdigest()
    run = "fictional-source-shape-test-only"
    observed = "2026-10-15T00:00:00Z"
    manifest = {
        "schema_version": "market-acquisition-evidence-v1", "provider": "scryfall",
        "source_dataset": "original-fictional-schema-exercise-not-provider-data",
        "source_url": "urn:mtg-lab:original-fictional-test-source",
        "acquisition_run_id": run, "source_observed_at": observed,
        "retrieved_at": observed, "mb2_record_count": len(rows),
        "provider_source_sha256": source_digest, "normalized_sha256": source_digest,
        "canonical_snapshot_identity": content_identity({"fictional_source_contract": run}),
        "canonical_write": False, "promotion_performed": False,
        "observations_persisted": False,
        "notice": "Original fictional bytes only. The provider label selects an existing test contract shape; no provider fact, network acquisition, permission, or human approval is asserted.",
    }
    save(directory / "dry-run-report.json", {
        "run_id": run, "source_sha256": source_digest,
        "normalized_sha256": source_digest, "source_observed_at": observed,
        "retrieved_at": observed, "mb2_record_count": len(rows)})
    manifest["files"] = {
        name: {"bytes": len((directory / name).read_bytes()),
               "sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest()}
        for name in (SOURCE_NAME, "dry-run-report.json")}
    encoded = (json.dumps(manifest, indent=2, sort_keys=True,
                          separators=(",", ": ")) + "\n").encode()
    manifest["manifest_content_sha256"] = hashlib.sha256(encoded).hexdigest()
    save(directory / "manifest.json", manifest)


def build_intelligence_fixture(root, *, rows_change=None):
    root = Path(root)
    catalog = root / "catalog"
    build_legacy_fixture(catalog, game="magic")
    state = read(catalog / "data/canonical/state.json")
    original = state["card"][CARD_IDS[0]]
    original["values"].update(card_reference=CARD_IDS[0], layout="normal")
    state["card"][CARD_IDS[1]] = copy.deepcopy(original)
    state["card"][CARD_IDS[1]]["values"].update(
        card_reference=CARD_IDS[1], name="Copper Wayfinder")
    state["printing"][PRINTING_IDS[0]]["values"].update(
        identifiers={"scryfallId": "fictional-cloth-record"})
    state["printing"][PRINTING_IDS[1]] = copy.deepcopy(state["printing"][PRINTING_IDS[0]])
    state["printing"][PRINTING_IDS[1]]["values"].update(
        uuid=PRINTING_IDS[1], card_id=CARD_IDS[1], collector_number="3",
        identifiers={"scryfallId": "fictional-copper-record"})
    save(catalog / "data/canonical/state.json", state)
    audit = read(catalog / SELECTED_AUDITS[1])
    audit["promoted_entities"].extend([CARD_IDS[1], PRINTING_IDS[1]])
    save(catalog / SELECTED_AUDITS[1], audit)
    control = rebind_catalog(catalog)
    mechanical_data = root / "mechanical" / "data"
    directory = mechanical_data / "market/acquisitions" / DEFAULT_ACQUISITION
    rows = [{"object": "card", "id": "fictional-" + label + "-record",
             "oracle_id": card_id, "name": state["card"][card_id]["values"]["name"],
             "layout": "normal", "oracle_text": "Original fictional fixture instruction.",
             "type_line": "Artifact", "mana_cost": "{2}", "cmc": 2,
             "colors": [], "color_identity": [], "keywords": []}
            for card_id, label in zip(CARD_IDS, ("cloth", "copper"))]
    if rows_change is not None:
        rows_change(rows)
    write_mechanical_source(directory, rows)
    # A fictional-only mirror permits exact legacy constructor characterization.
    # The explicit attachment tests select the independent mechanical root.
    shutil.copytree(directory, catalog / "data/market/acquisitions" / DEFAULT_ACQUISITION)
    return {"catalog": catalog, "mechanical_data": mechanical_data,
            "source_directory": directory, "control": control, "rows": rows}


def attach_fixture(fixture):
    return attach_legacy_compatibility(fixture["catalog"], control_path=CONTROL,
                                      game="magic", expected_profile_id=fixture["control"]["profile_id"])


def abstaining_packet(snapshot_id):
    """Absent buyer/offer evidence yields honest deterministic abstention."""
    return {"schema_version": "card-acquisition-input-v1",
            "mode": "synthetic_demonstration", "as_of": "2026-10-15T00:00:00Z",
            "canonical_snapshot_id": snapshot_id, "sources": [],
            "context": {"value": None, "binding": None},
            "ownership": {"value": None, "binding": None},
            "candidates": [{"card_id": card_id, "printing_id": printing_id,
                            "acceptable_printing_ids": [printing_id], "desired_quantity": None,
                            "preferred_dimensions": {"language": "Japanese", "finish": "plain", "treatment": None},
                            "requirements_binding": None, "offer": None, "eligibility": None}
                           for card_id, printing_id in zip(CARD_IDS, PRINTING_IDS)]}
