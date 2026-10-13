#!/usr/bin/env python3
"""Build or check an isolated, compressed, fictional collection audit."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from card_intelligence.mechanics import content_identity, stable_json
from card_intelligence.roles import FunctionalRolePilot
from collection.intelligence import CanonicalCollectionResolver, digest, read_import
from reasoning import ReasoningContextRequest
from semantic import SemanticRequest

REVIEW = ROOT / "data/review/collection-audit-pilot"
IMPORT = ROOT / "data/collections/imports/fictional-collection-audit-pilot.json"
ASSESSMENTS = ROOT / "data/collections/assessments/fictional-collection-audit-pilot"
PREPARED_AT = "2026-10-12T21:26:30Z"
COLLECTION_ID = "fictional-collection-audit-pilot"
MAXIMUM_STDOUT_BYTES = 65536
NOTICE = (
    "SYNTHETIC ONLY: this compressed fixture declares 360 fictional copies using twelve "
    "positive-quantity lots. Quantities, ownership, storage, physical attributes and personal "
    "review history are fictional. This is not a reconstruction of real MB2 pulls, a full-set "
    "inventory or an assertion that these copies are owned by the user. The six retained pack "
    "reports (90 reported positions) are evidence leads only and are not converted into ownership."
)
TARGETS = (
    ("Ponder", "02090581-61aa-4348-ad57-451be8ee91c2", "5c8d3bc4-32fc-5b26-84bf-9921e5884d43"),
    ("Faithless Looting", "3d6fa57a-aa53-4b5c-b8af-a7612c823117", "72783a15-4847-5448-8f1d-0c40379594d3"),
    ("Greater Good", "dc0593c2-ccb4-4648-a592-c5bcd121dc72", "46c0ae9f-b64a-528f-aab6-f1ceff9f0ade"),
    ("Sol Ring", "6ad8011d-3471-4369-9d68-b264cc027487", "b43c646f-797d-5b5f-8ade-142486708c88"),
    ("Counterspell", "cc187110-1148-4090-bbb8-e205694a39f5", "d5bfe686-da3c-5a8d-9dd5-4a1fe5aaef3d"),
    ("Veil of Summer", "002965be-a36f-4a09-9ce0-c6535bca1703", "e930c78d-2ef1-5853-83e5-571d8efb6f51"),
)


def compact_payload(value: Any) -> bytes:
    raw = (stable_json(value) + "\n").encode("utf-8")
    if len(raw) > MAXIMUM_STDOUT_BYTES:
        raise ValueError("collection audit payload exceeds 65,536 bytes including trailing LF")
    return raw


def retained_payload(value: Any) -> bytes:
    """Full retained results may exceed the bounded manual delivery envelope."""
    return (stable_json(value) + "\n").encode("utf-8")


def _reference(path: Path, raw: bytes) -> dict:
    return {"relative_path": path.relative_to(ROOT).as_posix(),
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def fixture_document() -> dict:
    """A compressed fictional declaration; never infer actual pulls from reference data."""
    printings = {name: pid for name, _, pid in TARGETS}
    def lot(name, suffix, quantity, location, classification, *, finish="nonfoil",
            language="English", condition="near_mint"):
        return {"printing_id": printings[name], "card_name": name, "quantity": quantity,
            "finish": finish, "language": language, "condition": condition,
            "acquisition_price": None, "acquisition_date": None,
            "storage_location": location, "notes": "Explicit fictional lot; no price or actual pull claim.",
            "provenance": {"owned_lot_id": "fictional-" + suffix,
                "source_type": "synthetic_fixture", "captured_at": PREPARED_AT,
                "organization": {"schema_version": "collection-organization-v1",
                                 "storage_classification": classification}}}
    rows = [
        lot("Ponder", "ponder-main", 80, "fictional-blue-binder", "binder"),
        lot("Ponder", "ponder-archive", 20, None, None, condition=None),
        lot("Faithless Looting", "faithless-bulk", 75, "fictional-unsorted-box", "bulk"),
        lot("Greater Good", "greater-nonfoil", 20, "fictional-green-binder", "binder"),
        lot("Greater Good", "greater-foil", 5, "fictional-display", "sleeved", finish="foil"),
        lot("Sol Ring", "sol-ring-main", 70, "fictional-artifact-binder", "binder"),
        lot("Sol Ring", "sol-ring-foil", 10, "fictional-unsorted-box", "bulk", finish="foil", condition=None),
        lot("Counterspell", "counterspell-main", 40, "fictional-blue-binder", "binder"),
        lot("Counterspell", "counterspell-unknown", 5, "fictional-unsorted-box", "bulk", finish=None,
            language=None, condition=None),
        lot("Veil of Summer", "veil-main", 5, "fictional-green-binder", "separated"),
        {"card_name": "Sol Ring", "quantity": 15, "finish": None, "language": None,
         "condition": None, "storage_location": None,
         "provenance": {"owned_lot_id": "fictional-name-ambiguous", "source_type": "synthetic_fixture",
            "organization": {"schema_version": "collection-organization-v1", "storage_classification": None}}},
        {"printing_id": "fictional-unresolved-printing-label", "quantity": 15,
         "finish": None, "language": None, "condition": None, "storage_location": None,
         "provenance": {"owned_lot_id": "fictional-unresolved-lot", "source_type": "synthetic_fixture",
            "organization": {"schema_version": "collection-organization-v1", "storage_classification": None}}},
    ]
    rows.extend([copy.deepcopy(rows[0]), {"printing_id": printings["Ponder"], "quantity": 0,
        "provenance": {"owned_lot_id": "fictional-invalid-zero", "source_type": "synthetic_fixture"}}])
    return {"schema_version": "collection-import-v1", "collection_id": COLLECTION_ID,
        "source": {"type": "synthetic_fixture", "name": "compressed fictional 360-copy audit",
            "captured_at": PREPARED_AT, "notice": NOTICE, "mode": "synthetic_demonstration",
            "expected_nonduplicate_quantity": 360, "real_user_inventory": False}, "entries": rows}


def load_inputs() -> tuple[dict, CanonicalCollectionResolver, dict]:
    from collection.audit import build_snapshot
    expected = retained_payload(fixture_document())
    if IMPORT.read_bytes() != expected:
        raise ValueError("fictional import differs from its complete retained fixture declaration")
    imported = read_import(IMPORT)
    resolver = CanonicalCollectionResolver("magic", ROOT / "data")
    for name, cid, pid in TARGETS:
        if resolver.cards[cid]["name"] != name or resolver.printings[pid]["card_id"] != cid:
            raise ValueError("exact production fixture Card/Printing identity changed")
    resolution = resolver.resolve(imported)
    snapshot = build_snapshot(imported, resolution, None)
    return imported, resolver, snapshot


def _assessment_documents(snapshot: dict) -> dict[str, bytes]:
    """Retain every mock review claim before referencing its immutable source bytes."""
    documents = {}
    previous = {}
    def make(name, label, status, outcome, moment, *, prior=None, trigger=None):
        cid = next(cid for n, cid, _ in TARGETS if n == name)
        earlier = previous.get(prior)
        claim = {"collection_id": COLLECTION_ID, "card_id": cid,
            "purpose": "personal_collection_organization", "status": status, "outcome": outcome,
            "reason": "Fictional personal review example; no strategic importance or canonical fact is established.",
            "assessed_at": earlier["assessed_at"] if earlier else moment, "recorded_at": moment,
            "assessment_version": earlier["assessment_version"] if earlier else "fictional-personal-review-v1",
            "prior_assessment_id": earlier["assessment_id"] if earlier else None,
            "supersedes": [earlier["assessment_id"]] if earlier else [],
            "manual_reassessment_trigger": trigger,
            "human_review": copy.deepcopy(earlier["human_review"]) if earlier else {
                "kind": "synthetic_mock", "approved": False, "reviewer": None, "review_reference": None},
            "snapshot_binding": {"snapshot_id": snapshot["snapshot_id"],
                "snapshot_digest": snapshot["snapshot_digest"],
                "source_import_digest": snapshot["source_import_digest"],
                "source_import_reference": {"relative_path": IMPORT.relative_to(ROOT).as_posix(),
                    "sha256": snapshot["source_import_digest"]},
                "canonical_snapshot_id": snapshot["canonical_snapshot_id"],
                "resolved_printing_ids": sorted({h["printing_id"] for h in snapshot["resolved_holdings"]
                                                if h["card_id"] == cid})},
            "evidence_references": [{"source_id": "fictional-review-" + label,
                "source_type": "synthetic_fixture", "reference": "fictional retained review claim: " + label,
                "observed_at": moment, "claim": "Mock personal review only; no real human approval."}]}
        source_path = ASSESSMENTS / "sources" / (label + ".json")
        source_raw = retained_payload({"kind": "synthetic_fixture", "mode": "synthetic_demonstration", "synthetic": True,
            "notice": "Fictional personal assessment. Human approval is false.", "claim": claim})
        documents[source_path.relative_to(ROOT).as_posix()] = source_raw
        record = {"schema_version": "collection-assessment-v1", **claim,
            "source": {"relative_path": source_path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(source_raw).hexdigest(), "json_pointer": "/claim"}}
        record["assessment_id"] = "sha256:" + digest(record)
        documents[(ASSESSMENTS / "records" / (record["assessment_id"].removeprefix("sha256:") + ".json"))
                  .relative_to(ROOT).as_posix()] = retained_payload(record)
        previous[label] = record
    make("Ponder", "ponder-already-processed", "reviewed", "already_processed", "2026-10-10T10:00:00Z")
    make("Greater Good", "greater-formerly-reviewed", "reviewed", "stored_after_personal_review", "2026-10-10T11:00:00Z")
    make("Greater Good", "greater-manual-reassessment", "reassessment_needed", "stored_after_personal_review",
         PREPARED_AT, prior="greater-formerly-reviewed", trigger="Fictional owner requested another personal inspection.")
    make("Sol Ring", "sol-ring-reviewed", "reviewed", "stored_after_personal_review", "2026-10-10T12:00:00Z")
    make("Counterspell", "counterspell-pending", "pending", None, "2026-10-10T13:00:00Z")
    make("Veil of Summer", "veil-reviewed", "reviewed", "stored_after_personal_review", "2026-10-10T14:00:00Z")
    return documents


def _load_assessments(snapshot: dict):
    from collection.assessments import CollectionAssessment
    documents = _assessment_documents(snapshot)
    records = []
    for relative, expected in sorted(documents.items()):
        actual = (ROOT / relative).read_bytes()
        if actual != expected:
            raise ValueError("fictional assessment source/record differs from full input replay")
        if "/records/" in relative:
            records.append(CollectionAssessment(json.loads(actual), ROOT, snapshot=snapshot))
    return records


def _build_audit() -> tuple[dict, dict, dict]:
    from collection.audit import CollectionAudit
    imported, resolver, snapshot = load_inputs()
    snapshot_path = ROOT / "data/collections/snapshots" / (snapshot["snapshot_id"] + ".json")
    if snapshot_path.read_bytes() != retained_payload(snapshot):
        raise ValueError("retained fictional snapshot differs from complete source resolution replay")
    assessments = _load_assessments(snapshot)
    audit = CollectionAudit(resolver).build(snapshot, source_path=IMPORT, source_root=ROOT,
        assessments=assessments, expected_total=360,
        candidate_printing_ids=tuple(pid for _, _, pid in TARGETS[:3])).as_dict()
    return imported, snapshot, audit


def _audit_projection(audit: dict) -> dict:
    """Preserve every calculation; reference repeated rows and lineage losslessly."""
    raw = retained_payload(audit)
    projected = copy.deepcopy(audit)
    projected["schema_version"] = "collection-audit-projection-v1"
    projected["validated_audit_reference"] = _reference(REVIEW / "audit-result.json", raw)
    for holding in projected["holdings"]:
        row = holding.pop("row")
        holding["physical_attributes"] = {key: row.get(key) for key in ("finish", "language", "condition")}
        holding["unknown_fields"] = row["unknown_fields"]
        holding["source_row_pointer"] = "/entries/" + str(row["row_number"] - 1)
        holding.pop("canonical_reference")
        holding.pop("identity_evidence")
    for card in projected["cards"]:
        card.pop("canonical_reference")
    projected["omissions"] = {"holdings_omitted": 0, "cards_omitted": 0, "quantities_omitted": 0,
        "assessment_records_omitted": 0, "normalized_source_rows_referenced": len(audit["holdings"]),
        "holding_canonical_references_referenced": sum(h["canonical_reference"] is not None for h in audit["holdings"]),
        "card_canonical_references_referenced": len(audit["cards"]),
        "identity_evidence_referenced": sum(len(h["identity_evidence"]) for h in audit["holdings"]),
        "policy": "The full source-bound audit result retains every normalized row, canonical lineage and identity evidence. This projection keeps all quantities, identities/candidates, physical unknowns, exclusions, storage, review history and ownership coverage. Repeated row and lineage payloads are referenced by exact full-result digest and source-row pointers."}
    projected["projection_id"] = content_identity(projected)
    return projected


def build_pilot_dossier() -> dict:
    imported, snapshot, audit = _build_audit()
    audit = _audit_projection(audit)
    roles = FunctionalRolePilot(ROOT / "data")
    if roles.mechanical.snapshot_id != snapshot["canonical_snapshot_id"]:
        raise ValueError("mechanical and collection canonical snapshot disagree")
    subjects = []
    for name, cid, pid in TARGETS:
        mechanical = roles.mechanical.dossier(cid).to_dict()
        role_dossier = roles.dossier(cid)
        subjects.append({"card_id": cid, "card_name": name, "printing_id": pid,
            "mechanical_dossier_id": mechanical["dossier_id"],
            "mechanical_reference": "data/review/mechanical-card-cohort/dossiers.jsonl",
            "pending_role_dossier_id": role_dossier["dossier_id"],
            "pending_role_candidate_count": len(role_dossier["role_candidates"]),
            "role_review_status": "requires_review", "human_role_approval": False,
            "omissions": {"mechanical_payload": "Complete unchanged dossier retained by identity in companion JSONL.",
                "functional_roles": "Pending proposal payloads retained in original role dossier; no classification inferred."}})
    payload = {"schema_version": "collection-audit-pilot-v1", "prepared_at": PREPARED_AT,
        "mode": "synthetic_demonstration", "notice": NOTICE,
        "collection_id": imported["collection_id"], "audit": audit, "subjects": subjects,
        "snapshot_reference": _reference(ROOT / "data/collections/snapshots" /
            (snapshot["snapshot_id"] + ".json"), retained_payload(snapshot)),
        "real_inventory": {"status": "not_retained", "complete_360_copy_inventory": False,
            "partial_observation_pack_count": 6, "partial_observation_position_count": 90,
            "partial_observation_reference": "data/observations/magic/mystery_booster_2/boxes/box_001/manifest.json",
            "observation_to_ownership_conversion": False},
        "acquisition_boundary": {"actual_purchase_advice": False,
            "candidate_printing_ids": [pid for _, _, pid in TARGETS[:3]],
            "status": "informational_ownership_counts_only",
            "required_real_inputs": ["exhaustive current ownership declaration", "scoped buyer source review",
                "desired acceptable copies", "buyer context", "budget and currency", "objective and personal priority",
                "current reviewed offers and availability", "complete transaction costs"]},
        "review": {"status": "requires_review", "human_attestation": None, "canonical_admission": False},
        "protection_boundary": {"canonical_write": False, "market_admission": False, "knowledge_admission": False,
            "role_approval": False, "external_acquisition": False, "purchase_execution": False}}
    payload["dossier_id"] = content_identity(payload)
    compact_payload(payload)
    return payload


def _validate_pilot(dossier: dict) -> None:
    # Reject altered caller projections cheaply, then independently reproduce the
    # matching retained projection from all original inputs. Retained bytes alone
    # never replace the complete source/result replay below.
    if (REVIEW / "audit-dossier.json").read_bytes() != compact_payload(dossier):
        raise ValueError("collection audit pilot contradicts complete bound input/result replay")
    if stable_json(dossier) != stable_json(build_pilot_dossier()):
        raise ValueError("collection audit pilot contradicts complete bound input/result replay")
    reference = dossier["audit"]["validated_audit_reference"]
    raw = (ROOT / reference["relative_path"]).read_bytes()
    if len(raw) != reference["bytes"] or hashlib.sha256(raw).hexdigest() != reference["sha256"]:
        raise ValueError("retained full audit result differs from bound input/result replay")


def canonical_contexts(dossier: dict) -> list[dict]:
    _validate_pilot(dossier)
    return _canonical_contexts(dossier)


def _canonical_contexts(dossier: dict) -> list[dict]:
    mechanical = FunctionalRolePilot(ROOT / "data").mechanical
    contexts = [mechanical.context_builder.build(ReasoningContextRequest(
        SemanticRequest("find_identifier", {"identifier": s["card_id"], "entity_type": "card"}),
        requested_entity_types=("card",), maximum_entities=0, maximum_relationships=0,
        maximum_evidence_items=0)).to_dict() for s in dossier["subjects"]]
    if any(c["canonical_snapshot_id"] != dossier["audit"]["bindings"]["canonical_snapshot_id"] for c in contexts):
        raise ValueError("collection handoff canonical context drift")
    return contexts


def pilot_reasoning_context(dossier: dict, *, contexts: list[dict] | None = None) -> dict:
    _validate_pilot(dossier)
    expected = _canonical_contexts(dossier)
    if contexts is not None and stable_json(contexts) != stable_json(expected):
        raise ValueError("collection handoff contexts contradict canonical replay")
    if (REVIEW / "canonical-contexts.json").read_bytes() != compact_payload(expected):
        raise ValueError("retained collection canonical contexts contradict canonical replay")
    return _pilot_reasoning_context(dossier, expected)


def _pilot_reasoning_context(dossier: dict, contexts: list[dict]) -> dict:
    raw = compact_payload(contexts)
    payload = {"schema_version": "collection-audit-pilot-handoff-v1", "dossier": dossier,
        "instruction": "Explain the synthetic inventory and repository-produced counts, organization and personal history. Preserve unknowns, ambiguities, unresolved identities, prior review and manual reassessment. Never present fictional copies as actual pulls or ownership. Pending roles do not establish importance or strategic strength. No purchase advice or real human approval.",
        "canonical_contexts": [{"card_id": dossier["subjects"][i]["card_id"], "context_id": c["context_id"],
            "canonical_snapshot_id": c["canonical_snapshot_id"], "omitted_item_counts": c["omitted_item_counts"]}
            for i, c in enumerate(contexts)],
        "canonical_contexts_reference": {**_reference(REVIEW / "canonical-contexts.json", raw),
            "schema_version": "canonical-reasoning-context-v1", "contract_count": len(contexts)},
        "omissions": {"audit_holdings": 0, "audit_cards": 0, "audit_census": 0,
            "canonical_contexts": [c["omitted_item_counts"] for c in contexts],
            "mechanical_and_role_payloads": "Original immutable dossiers referenced by identity; no source facts or pending role approvals synthesized."},
        "delivery": "bounded manual handoff; no model execution or live transport",
        "maximum_serialized_bytes_including_trailing_lf": MAXIMUM_STDOUT_BYTES}
    payload["handoff_id"] = content_identity(payload)
    compact_payload(payload)
    return payload


def pilot_explanation(dossier: dict) -> str:
    _validate_pilot(dossier)
    return _pilot_explanation(dossier)


def _pilot_explanation(dossier: dict) -> str:
    audit = dossier["audit"]
    lines = ["# Collection Audit & Organization Pilot", "", NOTICE, "",
        "Dossier: `" + dossier["dossier_id"] + "`. This manual review remains pending.", "",
        "## Quantity census", ""]
    for key, value in sorted(audit["quantity_census"].items()):
        lines.append("- " + key.replace("_", " ") + ": " + ("unknown" if value is None else str(value)) + ".")
    lines.extend(["", "## Exact production identities", ""])
    for subject in dossier["subjects"]:
        lines.append("- " + subject["card_name"] + ": Card `" + subject["card_id"] + "`; Printing `" +
                     subject["printing_id"] + "`. Mechanical dossier `" + subject["mechanical_dossier_id"] +
                     "`; " + str(subject["pending_role_candidate_count"]) + " role proposals remain pending.")
    lines.extend(["", "## Personal review and organization", "",
        "Personal review state is separate from storage and card mechanics. Every review in this demonstration is a synthetic mock; actual human approval remains false.", "",
        "| Card | Resolved fictional copies | Current personal review | Previously reviewed | Eligible for unreviewed bulk inspection |",
        "|---|---:|---|---|---|"])
    for card in audit["cards"]:
        lines.append("| " + card["card_name"] + " | " + str(card["quantity"]) + " | " +
            card["review_status"].replace("_", " ") + " | " + ("yes" if card["ever_reviewed"] else "no") +
            " | " + ("yes" if card["unreviewed_bulk_eligible"] else "no") + " |")
    lines.extend(["", "Ponder's retained fictional outcome is already_processed. Greater Good retains its earlier personal review and a separate manual reassessment request. Previously reviewed cards stay outside new-discovery candidates; a manual request does not run another review automatically.", "",
        "The organization census includes known quantities whose exact identity is still ambiguous or unresolved.", "",
        "| Storage classification | Fictional location | Declared copies |", "|---|---|---:|"])
    for group in audit["organization"]["groups"]:
        lines.append("| " + (group["storage_classification"] or "unknown") + " | " +
                     (group["storage_location"] or "unknown") + " | " + str(group["reported_quantity"]) + " |")
    lines.extend(["", "## Ownership query boundary", "",
        "The Ponder, Faithless Looting and Greater Good queries are informational counts. Real acquisition advice still requires:", ""])
    lines.extend("- " + item + "." for item in dossier["acquisition_boundary"]["required_real_inputs"])
    lines.extend(["", "The retained six-pack, 90-position report is partial opening evidence only. No real 360-copy inventory is present or reconstructed.", "",
        "No prices, ranking, competitive strength, inferred functional classification, verified combo, role approval, purchase or canonical admission is produced.", ""])
    return "\n".join(lines)


def protected_inventory() -> dict[str, str]:
    def owned(path):
        return path == IMPORT or path.is_relative_to(ASSESSMENTS) or path.is_relative_to(REVIEW) or (
            path.is_relative_to(ROOT / "data/collections/snapshots") and path.name in _snapshot_names())
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT / "data").rglob("*")) if p.is_file() and not owned(p)}


def _snapshot_names() -> set[str]:
    if not IMPORT.exists():
        return set()
    return {load_inputs()[2]["snapshot_id"] + ".json"}


def build_artifacts() -> dict[str, bytes]:
    dossier = build_pilot_dossier()
    contexts = _canonical_contexts(dossier)
    artifacts = {"audit-result.json": retained_payload(_build_audit()[2]),
        "audit-dossier.json": compact_payload(dossier),
        "canonical-contexts.json": compact_payload(contexts),
        "reasoning-context.json": compact_payload(_pilot_reasoning_context(dossier, contexts)),
        "explanation.md": _pilot_explanation(dossier).encode("utf-8")}
    inputs = {IMPORT.relative_to(ROOT).as_posix(): retained_payload(fixture_document())}
    snapshot = load_inputs()[2]
    inputs.update(_assessment_documents(snapshot))
    inputs[dossier["snapshot_reference"]["relative_path"]] = retained_payload(snapshot)
    inventory = protected_inventory()
    manifest = {"schema_version": "collection-audit-pilot-manifest-v1", "prepared_at": PREPARED_AT,
        "mode": "synthetic_demonstration", "dossier_id": dossier["dossier_id"], "review": dossier["review"],
        "canonical_snapshot_id": snapshot["canonical_snapshot_id"],
        "source_and_snapshot_files": {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for name, raw in sorted(inputs.items())},
        "protected_inventory": {"file_count": len(inventory), "content_identity": content_identity(inventory),
            "scope": "All prior data files; excludes only this fixture's explicit import, snapshot, assessment and review artifacts."},
        "files": {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for name, raw in sorted(artifacts.items())}}
    artifacts["manifest.json"] = compact_payload(manifest)
    return artifacts


def _publish_immutable(documents: dict[str, bytes], *, check: bool) -> None:
    for relative, raw in documents.items():
        path = ROOT / relative
        if path.exists() and path.read_bytes() != raw:
            raise ValueError("refusing to overwrite conflicting collection pilot artifact: " + relative)
        if check and not path.exists():
            raise ValueError("missing retained collection pilot artifact: " + relative)
    if not check:
        for relative, raw in documents.items():
            path = ROOT / relative
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(raw)


def _check_scoped_inventory(documents: dict[str, bytes]) -> None:
    """An extra file cannot become an undocumented source or derived result."""
    expected = set(documents)
    for scope in (ASSESSMENTS, REVIEW):
        if scope.exists():
            actual = {p.relative_to(ROOT).as_posix() for p in scope.rglob("*") if p.is_file()}
            extra = actual - expected
            if extra:
                raise ValueError("unexpected file in isolated collection pilot: " + sorted(extra)[0])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="read-only exact replay of source, snapshot, history and review artifacts")
    args = parser.parse_args(argv)
    before = protected_inventory()
    _publish_immutable({IMPORT.relative_to(ROOT).as_posix(): retained_payload(fixture_document())}, check=args.check)
    snapshot = load_inputs()[2]
    snapshot_path = ROOT / "data/collections/snapshots" / (snapshot["snapshot_id"] + ".json")
    _publish_immutable({snapshot_path.relative_to(ROOT).as_posix(): retained_payload(snapshot)}, check=args.check)
    assessments = _assessment_documents(snapshot)
    _publish_immutable(assessments, check=args.check)
    artifacts = build_artifacts()
    outputs = {(REVIEW / name).relative_to(ROOT).as_posix(): raw for name, raw in artifacts.items()}
    _check_scoped_inventory({**assessments, **outputs})
    _publish_immutable(outputs, check=args.check)
    if before != protected_inventory():
        raise ValueError("protected prior data changed during collection pilot generation")
    print(stable_json({"schema_version": "collection-audit-pilot-build-v1", "artifact_count": len(artifacts),
        "fictional_copies": 360, "production_cards": len(TARGETS), "verified": args.check}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
