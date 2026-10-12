#!/usr/bin/env python3
"""Replay one isolated acquisition demonstration; never admit evidence or buy."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from card_intelligence.acquisition import CardAcquisitionAdapter, CardAcquisitionDossier
from card_intelligence.mechanics import content_identity, stable_json
from card_intelligence.roles import FunctionalRolePilot
from reasoning import ReasoningContextRequest
from semantic import SemanticRequest

REVIEW = ROOT / "data/review/card-acquisition-pilot"
MAXIMUM_STDOUT_BYTES = 65536


def compact_payload(value: Any) -> bytes:
    """The byte bound includes the one documented CLI/retained trailing LF."""
    raw = (stable_json(value) + "\n").encode("utf-8")
    if len(raw) > MAXIMUM_STDOUT_BYTES:
        raise ValueError("acquisition pilot payload exceeds 65,536 bytes including trailing LF")
    return raw


def load_inputs() -> tuple[dict, dict, bytes]:
    plan = json.loads((REVIEW / "plan.json").read_bytes())
    raw = (ROOT / plan["source_reference"]).read_bytes()
    if (len(raw) != plan["synthetic_source_bytes"] or
            hashlib.sha256(raw).hexdigest() != plan["synthetic_source_sha256"]):
        raise ValueError("synthetic retained source integrity mismatch")
    source = json.loads(raw)
    if source["schema_version"] != "card-acquisition-synthetic-fixture-v1":
        raise ValueError("unsupported synthetic source contract")
    return plan, source, raw


def build_packets() -> tuple[dict, dict]:
    """Bind every fictional supplied object to retained, digest-verified bytes."""
    plan, source, raw = load_inputs()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    source_id = "synthetic-" + digest
    binding = lambda pointer: {"source_id": source_id, "pointer": pointer}
    source_reference = {"source_id": source_id, "relative_path": plan["source_reference"],
        "content_digest": digest, "kind": "synthetic_fixture", "captured_at": plan["prepared_at"],
        "provider_identity": "mtg-lab-fictional-test-fixture", "seller_identity": "fictional-seller-01",
        "review": {"status": "not_applicable", "reviewer": None, "reviewed_at": None,
                   "content_digest": digest}}
    synthetic = {"schema_version": "card-acquisition-input-v1", "mode": "synthetic_demonstration",
        "as_of": plan["synthetic_as_of"], "canonical_snapshot_id": plan["canonical_snapshot_id"],
        "sources": [source_reference],
        "context": {"value": source["context"], "binding": binding("/context")},
        "ownership": {"value": source["ownership"], "binding": binding("/ownership")},
        "candidates": [{**requirement, "requirements_binding": binding("/requirements/" + str(i)),
            "offer": {"value": source["offers"][i], "binding": binding("/offers/" + str(i))},
            "eligibility": None} for i, requirement in enumerate(source["requirements"])]}
    real = {"schema_version": "card-acquisition-input-v1", "mode": "real_world",
        "as_of": plan["prepared_at"], "canonical_snapshot_id": plan["canonical_snapshot_id"],
        "sources": [], "context": {"value": None, "binding": None},
        "ownership": {"value": None, "binding": None},
        "candidates": [{"card_id": target["card_id"], "printing_id": target["printing_id"],
            "acceptable_printing_ids": [target["printing_id"]], "desired_quantity": None,
            "preferred_dimensions": {"finish": "nonfoil", "language": "English", "treatment": None},
            "requirements_binding": None, "offer": None, "eligibility": None}
            for target in plan["targets"]]}
    return synthetic, real


def _subjects(roles: FunctionalRolePilot, plan: dict, validated_result: dict) -> list[dict]:
    subjects = []
    printings = {p.canonical_identity: p for p in roles.mechanical.query.entities(entity_type="printing")}
    for target in plan["targets"]:
        mechanical = roles.mechanical.dossier(target["card_id"]).to_dict()
        printing = printings.get(target["printing_id"])
        if (printing is None or printing.canonical_values.get("card_id") != target["card_id"] or
                printing.canonical_values.get("uuid") != target["printing_id"] or
                mechanical["card_identity"]["name"] != target["name"]):
            raise ValueError("authorized exact production Card/Printing binding changed")
        role_dossier = roles.dossier(target["card_id"])
        subjects.append({"card_identity": mechanical["card_identity"],
            "printing_identity": {"printing_id": target["printing_id"],
                "set_id": printing.canonical_values["set_id"],
                "collector_number": printing.canonical_values["collector_number"],
                "canonical_language": printing.canonical_values["language"],
                "supported_finishes": printing.canonical_values["finish_ids"],
                "canonical_treatment": {"status": "unknown", "reason": "canonical_field_absent"}},
            "mechanical_dossier_id": mechanical["dossier_id"],
            "mechanical_fields": {key: mechanical["fields"][key] for key in
                ("oracle_text", "mana_cost", "mana_value", "type_line")},
            "source": mechanical["source"], "canonical_provenance": mechanical["canonical_provenance"],
            "canonical_printing_provenance": next(row["canonical_printing_provenance"]
                for row in validated_result["candidates"] if row["printing_id"] == target["printing_id"]),
            "pending_role_evidence": {"dossier_id": role_dossier["dossier_id"],
                "review_status": role_dossier["review_status"],
                "candidates": [{"candidate_id": role["candidate_id"],
                    "role_id": role["role_reference"]["role_id"],
                    "value_state": role["value"]["status"], "review": role["review"]}
                    for role in role_dossier["role_candidates"]]},
            "omissions": {"mechanical_fields_omitted": len(mechanical["fields"]) - 4,
                "role_candidate_count_omitted": 0,
                "role_candidate_details": "Only identities, value states and review status are copied; exact original role dossier is content-bound and unchanged.",
                "raw_source": "No artwork, provider prices or nonmechanical fields copied; full source and record digests retained."}})
    return subjects


def _build_pilot() -> tuple[dict, dict, dict, FunctionalRolePilot]:
    plan, source, _ = load_inputs()
    roles = FunctionalRolePilot(ROOT / "data")
    if roles.mechanical.snapshot_id != plan["canonical_snapshot_id"]:
        raise ValueError("acquisition pilot canonical snapshot changed")
    synthetic_packet, real_packet = build_packets()
    adapter = CardAcquisitionAdapter(ROOT / "data")
    synthetic_result = adapter.evaluate(synthetic_packet, source_root=ROOT).to_dict()
    real_result = adapter.evaluate(real_packet, source_root=ROOT).to_dict()
    synthetic = _scenario_projection(synthetic_result, "synthetic-result.json")
    real = _scenario_projection(real_result, "real-result.json")
    subjects = _subjects(roles, plan, synthetic_result)
    common_keys = {"provider", "dataset", "acquisition_run_id", "source_url", "manifest_reference",
        "manifest_bytes_sha256", "acquisition_canonical_snapshot_identity", "normalized_source_sha256",
        "upstream_bulk_sha256", "original_bulk_bytes"}
    shared_source = {key: subjects[0]["source"][key] for key in sorted(common_keys)}
    if any({key: subject["source"][key] for key in common_keys} != shared_source for subject in subjects):
        raise ValueError("pilot subjects do not share the declared mechanical acquisition")
    shared_source_identity = content_identity(shared_source)
    for subject in subjects:
        subject["source"] = {key: value for key, value in subject["source"].items() if key not in common_keys}
        subject["source"]["shared_source_identity"] = shared_source_identity
    document = {"schema_version": "card-acquisition-pilot-v1",
        "canonical_main_baseline": plan["canonical_main_baseline"],
        "canonical_snapshot_id": plan["canonical_snapshot_id"], "prepared_at": plan["prepared_at"],
        "question": "Which one missing copy should I acquire first, given my budget, ownership, declared objectives, and verified acquisition costs?",
        "subjects": subjects, "mechanical_source": {**shared_source, "content_identity": shared_source_identity},
        "synthetic_demonstration": synthetic, "real_evidence_assessment": real,
        "real_input_inventory": plan["real_evidence_status"], "notices": plan["notices"] + [source["notice"]],
        "review": {"status": "requires_review", "human_attestation": None,
                   "canonical_admission": False, "actual_purchase_advice": False},
        "unsupported_dimensions": ["competitive_strength", "format_legality", "net_card_advantage",
            "verified_synergy_or_combo", "universal_efficiency", "investment_value", "future_prices",
            "actual_buyer_suitability", "live_chatgpt_integration"],
        "protection_boundary": {"canonical_write": False, "market_admission": False,
            "knowledge_admission": False, "functional_role_approval": False,
            "purchase_execution": False, "external_acquisition": False},
        "decision_conditions": ["Changing the supplied personal preference order can change the synthetic result.",
            "Owning an acceptable copy removes that candidate's missing-copy need.",
            "An unaffordable candidate cannot be selected; complete costs and budget are required.",
            "Missing or stale decision-critical evidence requires abstention.",
            "Pending role evidence cannot establish approved strategic eligibility."]}
    document["dossier_id"] = content_identity(document)
    compact_payload(document)
    return document, synthetic_result, real_result, roles


def build_pilot_dossier() -> dict:
    return _build_pilot()[0]


def _scenario_projection(validated: dict, artifact_name: str) -> dict:
    """Keep all decision values; common subjects carry repeated canonical data."""
    validated = CardAcquisitionDossier(validated).to_dict()
    retained_bytes = compact_payload(validated)
    reconstruction = validated["reconstruction"]
    omitted = {"printing_values", "source", "canonical_printing_provenance"}
    document = {key: value for key, value in validated.items() if key not in
        {"schema_version", "dossier_id", "candidates", "evidence", "reconstruction"}}
    document.update(schema_version="card-acquisition-scenario-projection-v1",
        validated_acquisition_dossier_id=validated["dossier_id"],
        validated_acquisition_reference={"relative_path": (REVIEW / artifact_name).relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(retained_bytes).hexdigest(), "bytes": len(retained_bytes)},
        candidates=[{key: value for key, value in row.items() if key not in omitted}
                    for row in validated["candidates"]],
        omissions={"candidate_count_omitted": 0, "decision_values_omitted": 0,
            "candidate_field_omissions": [{"printing_id": row["printing_id"],
                "field_names": sorted(set(row) & omitted)} for row in validated["candidates"]],
            "repeated_evidence_reference_count": len(validated["evidence"]),
            "reconstruction_proof": {"retained_field": "reconstruction",
                "schema_version": reconstruction["schema_version"],
                "content_identity": content_identity(reconstruction),
                "input_id": validated["input_id"],
                "decision_request_id": validated["decision_request_id"],
                "analysis_count": len(reconstruction["analyses"]),
                "analysis_content_identities": [content_identity({**reconstruction["analysis_shared"], **analysis})
                    for analysis in reconstruction["analyses"]],
                "source_snapshot_count": len(reconstruction["sources"]),
                "canonical_snapshot_id": reconstruction["canonical"]["snapshot_id"],
                "canonical_card_count": len(reconstruction["canonical"]["cards"]),
                "canonical_printing_count": len(reconstruction["canonical"]["printings"])},
            "policy": "Common subjects retain canonical Printing identity, provenance and mechanical source; recommendation retains complete evidence references. The fully validated reconstruction proof is omitted only from this projection and retained under reconstruction in the full acquisition result, bound by validated_acquisition_reference, validated_acquisition_dossier_id and the proof identity and counts above."})
    document["projection_id"] = content_identity(document)
    return document


def canonical_contexts(dossier: dict, roles: FunctionalRolePilot) -> list[dict]:
    contexts = [roles.mechanical.context_builder.build(ReasoningContextRequest(
        SemanticRequest("find_identifier", {"identifier": card["card_identity"]["card_id"], "entity_type": "card"}),
        requested_entity_types=("card",), maximum_entities=0, maximum_relationships=0,
        maximum_evidence_items=0)).to_dict() for card in dossier["subjects"]]
    if any(c["canonical_snapshot_id"] != dossier["canonical_snapshot_id"] for c in contexts):
        raise ValueError("acquisition reasoning-context snapshot mismatch")
    return contexts


def _validate_pilot_aggregate(dossier: dict) -> None:
    if stable_json(dossier) != stable_json(_build_pilot()[0]):
        raise ValueError("acquisition pilot aggregate contradicts bound input/result replay")


def pilot_reasoning_context(dossier: dict, *, roles: FunctionalRolePilot | None = None,
                            contexts: list[dict] | None = None) -> dict:
    """Retain unchanged retrieval contracts separately; avoid repeated envelopes."""
    _validate_pilot_aggregate(dossier)
    contexts = contexts or canonical_contexts(dossier, roles or FunctionalRolePilot(ROOT / "data"))
    context_bytes = compact_payload(contexts)
    context = {"schema_version": "card-acquisition-pilot-handoff-v1",
        "instruction": "Explain the repository-produced synthetic demonstration and real-input abstention separately. Preserve outcomes. Synthetic prices, buyer context, ownership and priorities are fictional; no actual purchase advice, competitive facts or pending-role approval may be added.",
        "dossier": dossier, "canonical_contexts": [{"context_id": c["context_id"],
            "canonical_snapshot_id": c["canonical_snapshot_id"],
            "card_id": dossier["subjects"][i]["card_identity"]["card_id"],
            "omitted_item_counts": c["omitted_item_counts"]} for i, c in enumerate(contexts)],
        "canonical_contexts_reference": {"relative_path": (REVIEW / "canonical-contexts.json").relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(context_bytes).hexdigest(), "bytes": len(context_bytes),
            "schema_version": "canonical-reasoning-context-v1", "contract_count": len(contexts)},
        "omissions": {"pilot_subjects_omitted": 0, "scenario_outcomes_omitted": 0,
            "canonical_contexts": [c["omitted_item_counts"] for c in contexts],
            "policy": "The three unchanged retrieval envelopes are retained in a digest-bound companion artifact, with their exact context identities, snapshot and omissions copied here. Generic entity and evidence copies are omitted to avoid audit duplication. The dossier retains exact identities, compact lineage, source and record identities, complete scenario decision values, and digest-bound full result and reconstruction references."},
        "delivery": "read-only manual handoff; no live model execution or transport",
        "maximum_serialized_bytes_including_trailing_lf": MAXIMUM_STDOUT_BYTES}
    context["handoff_id"] = content_identity(context)
    compact_payload(context)
    return context


def _recommendation(scenario: dict) -> dict:
    # The domain owns validated calculations; the existing Decision Engine owns
    # the recommendation. No outcome is reconstructed in this renderer.
    return scenario["decision"]["recommendation"]


def pilot_explanation(dossier: dict) -> str:
    _validate_pilot_aggregate(dossier)
    lines = ["# Collection-aware Card acquisition — manual explanation example", "",
        "Dossier: `" + dossier["dossier_id"] + "`. Human review remains pending. No actual purchase advice or live ChatGPT integration.", "",
        "## Evidence boundary", ""]
    lines.extend("- " + notice for notice in dossier["notices"])
    lines.extend(["", "## Verified retained mechanics", ""])
    for card in dossier["subjects"]:
        fields = card["mechanical_fields"]
        lines.extend(["### " + card["card_identity"]["name"], "",
            "Exact production Card: `" + card["card_identity"]["card_id"] + "`; Printing: `" + card["printing_identity"]["printing_id"] + "`.",
            "Retained mana cost: `" + fields["mana_cost"]["value"] + "`; type: `" + fields["type_line"]["value"] + "`.",
            "Source observation: `" + card["source"]["source_timestamp"] + "`; source retrieval: `" + card["source"]["retrieved_at"] + "`.", ""])
        lines.extend("> " + line for line in fields["oracle_text"]["value"].splitlines())
        lines.extend(["", "Functional-role candidates remain pending and do not establish strategic suitability.", ""])
    for key, label in (("synthetic_demonstration", "Synthetic selection demonstration"),
                       ("real_evidence_assessment", "Real-evidence abstention")):
        scenario = dossier[key]; recommendation = _recommendation(scenario)
        lines.extend(["## " + label, "", "Repository outcome: **" + recommendation["outcome"].upper() + "**.", ""])
        if recommendation["selected_alternative_id"]:
            lines.append("Selected synthetic alternative: `" + recommendation["selected_alternative_id"] + "`.")
        context = scenario["context"]
        if context:
            lines.extend(["", "Supplied personal collecting order: " +
                " > ".join(next(c["card_name"] for c in scenario["candidates"]
                    if c["printing_id"] == identity) for identity in context["priority_order"]) + ".",
                "Fictional budget: " + context["budget"] + " " + context["currency"] + ".",
                "This declared preference is not a mechanical superiority or competitive ranking.", ""])
        for candidate in scenario["candidates"]:
            display = lambda value: "unknown" if value is None else str(value)
            lines.append("- " + candidate["card_name"] + ": desired " + display(candidate["desired_quantity"]) +
                "; acceptable owned " + display(candidate["owned_acceptable_quantity"]) +
                "; missing " + display(candidate["missing_quantity"]) +
                "; complete acquisition cost " + display(candidate["complete_cost"]) +
                (" " + candidate["currency"] if candidate.get("currency") else "") +
                "; remaining budget " + display(candidate["remaining_budget"]) + ".")
            if candidate.get("costs"):
                costs = candidate["costs"]
                lines.append("  Exact quote arithmetic: " + " + ".join(costs[k]["amount"] for k in
                    ("unit_price", "shipping", "taxes", "fees")) + " - " + costs["discounts"]["amount"] +
                    " = " + candidate["complete_cost"] + " " + candidate["currency"] + ".")
            lines.extend("  Exclusion: " + reason for reason in candidate["exclusion_reasons"])
        for factor in recommendation["supporting_factors"]:
            lines.append("- Supporting factor: " + factor["statement"])
        for factor in recommendation["counterarguments"]:
            lines.append("- Counterargument: " + factor["statement"])
        for reason in recommendation["abstention_reasons"]:
            lines.append("- Abstention reason: " + reason)
        lines.extend("- Limitation: " + limitation for limitation in recommendation["limitations"])
        if key == "synthetic_demonstration" and recommendation["selected_alternative_id"]:
            selected = next(c for c in scenario["candidates"] if c["printing_id"] == recommendation["selected_alternative_id"])
            for rival in scenario["candidates"]:
                if rival["acquisition_eligible"] and rival["complete_cost_units"] < selected["complete_cost_units"]:
                    lines.append("- Cost counterargument: " + rival["card_name"] + " has a lower complete fictional cost (" +
                        rival["complete_cost"] + " " + rival["currency"] + ") than " + selected["card_name"] +
                        " (" + selected["complete_cost"] + " " + selected["currency"] +
                        "). The supplied personal priority precedes cost in this policy; changing that priority can change the demonstration.")
        if key == "real_evidence_assessment":
            lines.extend("- Missing input: " + name + " — " + state for name, state in dossier["real_input_inventory"].items())
        lines.append("")
    lines.extend(["## Conditions that change the decision", ""])
    lines.extend("- " + condition for condition in dossier["decision_conditions"])
    lines.extend(["", "## Unsupported conclusions", "",
        "No competitive ranking, format-legality conclusion, net card advantage, verified combo, forecast or actual acquisition recommendation is established.", ""])
    return "\n".join(lines)


def protected_inventory() -> dict[str, str]:
    files = [p for p in (ROOT / "data").rglob("*") if p.is_file() and not p.is_relative_to(REVIEW)]
    files.append(ROOT / "docs/ARCHITECTURE.md")
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def build_artifacts() -> dict[str, bytes]:
    plan, _, _ = load_inputs()
    dossier, synthetic_result, real_result, roles = _build_pilot()
    synthetic, real = build_packets()
    contexts = canonical_contexts(dossier, roles)
    artifacts = {"packet-synthetic.json": compact_payload(synthetic),
        "packet-real.json": compact_payload(real), "acquisition-dossier.json": compact_payload(dossier),
        "synthetic-result.json": compact_payload(synthetic_result),
        "real-result.json": compact_payload(real_result),
        "canonical-contexts.json": compact_payload(contexts),
        "reasoning-context.json": compact_payload(pilot_reasoning_context(dossier, contexts=contexts)),
        "explanation.md": pilot_explanation(dossier).encode("utf-8")}
    subjects = dossier["subjects"]
    inputs = [REVIEW / "plan.json", REVIEW / "synthetic-inputs.json"]
    for subject in subjects:
        inputs.append(ROOT / subject["source"]["retained_source_reference"])
    inputs.append(ROOT / dossier["mechanical_source"]["manifest_reference"])
    inventory = protected_inventory()
    manifest = {"schema_version": "card-acquisition-pilot-manifest-v1",
        "canonical_main_baseline": plan["canonical_main_baseline"],
        "canonical_snapshot_id": plan["canonical_snapshot_id"], "prepared_at": plan["prepared_at"],
        "dossier_id": dossier["dossier_id"], "review": dossier["review"],
        "synthetic_outcome": _recommendation(dossier["synthetic_demonstration"])["outcome"],
        "real_outcome": _recommendation(dossier["real_evidence_assessment"])["outcome"],
        "protected_inventory": {"file_count": len(inventory), "content_identity": content_identity(inventory),
            "scope": "Every pre-existing data file plus Architecture v12; only this isolated review directory excluded."},
        "input_files": {p.relative_to(ROOT).as_posix(): {"bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(set(inputs))},
        "files": {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for name, raw in sorted(artifacts.items())}}
    artifacts["manifest.json"] = (stable_json(manifest) + "\n").encode("utf-8")
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="read-only byte-identical replay")
    args = parser.parse_args()
    artifacts = build_artifacts()
    actual = {p.name: p.read_bytes() for p in REVIEW.iterdir()
              if p.is_file() and p.name not in {"plan.json", "synthetic-inputs.json"}}
    if actual and actual != artifacts:
        raise ValueError("refusing to overwrite conflicting retained acquisition review artifacts")
    if args.check:
        if actual != artifacts:
            raise ValueError("acquisition pilot does not replay byte-identically")
    elif not actual:
        for name, raw in artifacts.items():
            (REVIEW / name).write_bytes(raw)
    manifest = json.loads(artifacts["manifest.json"])
    print(stable_json({"artifact_count": len(artifacts) + 2, "card_count": 3,
        "synthetic_outcome": manifest["synthetic_outcome"],
        "real_outcome": manifest["real_outcome"], "verified": args.check}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
