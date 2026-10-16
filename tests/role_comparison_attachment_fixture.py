"""Original fictional role/comparison plans using the existing attachment fixture.

The ten authored subjects satisfy the existing bounded pilot contract. These
Scryfall-shaped test bytes describe no provider facts, real cards or approval.
"""
import copy
from pathlib import Path
import shutil

from card_intelligence.mechanics import MechanicalCardIntelligence
from card_intelligence.roles import FunctionalRolePilot
from card_intelligence_attachment_fixture import (
    CARD_IDS, build_intelligence_fixture, rebind_catalog, write_mechanical_source)
from legacy_profile_fixture import SELECTED_AUDITS, read, save


def build_role_comparison_fixture(root):
    root = Path(root)
    fixture = build_intelligence_fixture(root)
    catalog = fixture["catalog"]
    state = read(catalog / "data/canonical/state.json")
    audit = read(catalog / SELECTED_AUDITS[1])
    rows = copy.deepcopy(fixture["rows"])
    for index in range(2, 10):
        card_id, printing_id = f"fictional-unit-{index}", f"fictional-edition-{index}"
        state["card"][card_id] = copy.deepcopy(state["card"][CARD_IDS[0]])
        state["card"][card_id]["values"].update(
            card_reference=card_id, name=f"Original Fictional Instrument {index}")
        state["printing"][printing_id] = copy.deepcopy(state["printing"]["cloth-edition"])
        state["printing"][printing_id]["values"].update(
            uuid=printing_id, card_id=card_id, collector_number=str(index + 2),
            identifiers={"scryfallId": f"fictional-record-{index}"})
        audit["promoted_entities"].extend([card_id, printing_id])
        rows.append({**copy.deepcopy(rows[0]), "id": f"fictional-record-{index}",
                     "oracle_id": card_id, "name": state["card"][card_id]["values"]["name"]})
    save(catalog / "data/canonical/state.json", state)
    save(catalog / SELECTED_AUDITS[1], audit)
    fixture["control"] = rebind_catalog(catalog)
    write_mechanical_source(fixture["source_directory"], rows)
    mirror = catalog / "data/market/acquisitions" / fixture["source_directory"].name
    shutil.copytree(fixture["source_directory"], mirror, dirs_exist_ok=True)
    fixture["rows"] = rows
    mechanical = MechanicalCardIntelligence(catalog / "data")
    vocabulary_path = root / "plans/fictional-role-vocabulary.json"
    role_path = root / "plans/fictional-role-plan.json"
    comparison_path = root / "plans/fictional-comparison-plan.json"
    vocabulary = {"schema_version": "functional-role-vocabulary-v1", "game_id": "magic",
        "vocabulary_id": "original-fictional-vocabulary", "roles": {"fixture_instruction": {
            "label": "Original fixture instruction", "definition": "Retain one authored fictional instruction.",
            "evidence_requirements": ["Complete original fictional source line."],
            "allowed_bases": ["direct_mechanical"]}}}
    save(vocabulary_path, vocabulary)
    plan = {"schema_version": "functional-role-pilot-plan-v1", "game_id": "magic",
        "canonical_snapshot_id": mechanical.snapshot_id,
        "vocabulary_id": vocabulary["vocabulary_id"], "prepared_at": "2026-10-16T00:00:00Z",
        "comparison_card_ids": list(CARD_IDS), "coverage_limitations": ["Fictional pending proposals only."],
        "cards": []}
    for card_id in sorted(mechanical.cards):
        dossier = mechanical.dossier(card_id).to_dict()
        plan["cards"].append({"card_id": card_id, "name": dossier["card_identity"]["name"],
            "mechanical_dossier_id": dossier["dossier_id"],
            "oracle_text": dossier["fields"]["oracle_text"]["value"],
            "selection_reason": "Original fictional bounded integration subject.",
            "roles": [{"role_id": "fixture_instruction", "basis": "direct_mechanical",
                "state": "known", "function": "Original fictional fixture instruction.",
                "explanation": "Authored fictional interpretation; review pending.",
                "evidence_lines": [0], "costs": [], "conditions": [], "restrictions": [],
                "timing": {"status": "unknown", "description": "No verified legal timing."},
                "context_dependencies": [], "limitations": ["No interaction or strength claim."],
                "supersedes": []}]})
    save(role_path, plan)
    roles = FunctionalRolePilot(catalog / "data", plan_path=role_path,
                                vocabulary_path=vocabulary_path)
    context = {"kind": "hypothetical_deck_context", "description": "Original fictional illustration.",
        "objective": "Compare fictional supplied instructions without selecting a winner.",
        "format_legality": {"status": "unknown", "value": None},
        "assumptions": [{"assumption_id": "resolved_instructions", "state": "supplied_assumption",
            "value": True, "description": "Illustrative instruction arithmetic only; no verified legal state."}],
        "constraints": ["No scoring or strategic selection."], "unknowns": ["Human context review."]}
    comparison = {"schema_version": "contextual-card-comparison-plan-v1", "game_id": "magic",
        # The existing retained comparison schema requires a SHA-shaped field.
        # Zero is an explicit fictional sentinel, never a real Git revision.
        "canonical_main_baseline": "0" * 40, "canonical_snapshot_id": mechanical.snapshot_id,
        "prepared_at": "2026-10-16T01:00:00Z", "context": context,
        "criteria": [{"criterion_id": "review", "category": "unknown", "description": "Human review absent.",
                      "selection_weight": None}], "cards": []}
    for card_id in CARD_IDS:
        dossier = mechanical.dossier(card_id).to_dict()
        comparison["cards"].append({"card_id": card_id, "name": dossier["card_identity"]["name"],
            "mechanical_dossier_id": dossier["dossier_id"], "role_dossier_id": roles.dossier(card_id)["dossier_id"],
            "oracle_text": dossier["fields"]["oracle_text"]["value"],
            "literal_instruction_annotation": {"draw_count": 1, "mandatory_discard_count": 0,
                                                "draw_parameter_assumption": None},
            "strategic_hypotheses": [], "counterarguments": ["No verified strategic suitability."]})
    save(comparison_path, comparison)
    fixture.update(role_plan=role_path, vocabulary=vocabulary_path, comparison_plan=comparison_path)
    return fixture
