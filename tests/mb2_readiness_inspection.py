"""Read-only reproduction of the MB2 readiness matrix, not an admission path.

Only the writer's pure record adapter is called. No engine execution, authority,
production payload, checkpoint or proposed canonical store is created. Policy
classifications are reviewed evidence dispositions, never execution clearance.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from production_evidence.automatic_updates import AutomaticCanonicalUpdate, TargetDescriptor

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "reference-reviews/mb2-reference-coverage/structured-2026-10-13"
READINESS = ROOT / "reference-reviews/mb2-810-production-readiness/2026-10-14"
POLICY = ROOT / "reference-reviews/mb2-810-source-policy/2026-10-14"
DIGEST = "f63585f4a023e2b81656a4cca0c6811a7d598e45f065633c3a11d9a9a2b5d500"
PACKET_SHA = "158440b59b45c0d50e81f4d8345f4ea637e6d5bbef6d77400a3a2300738c11b8"
ROLES = {
    "REQUIRED_FOR_CANONICAL_IDENTITY", "REQUIRED_FOR_RELATIONSHIP_INTEGRITY",
    "USEFUL_BUT_OPTIONAL", "SOURCE_PROVENANCE_ONLY",
    "EXCLUDABLE_FROM_PUBLIC_CANONICAL_OUTPUT",
}
PERMISSIONS = {"ESTABLISHED", "NOT_ESTABLISHED", "NOT_APPLICABLE"}


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def selected_candidates():
    ids = read(ROOT / "tests/fixtures/catalog_admission/mb2-recommended-candidate-ids.json")
    assert sha(encoded(ids).rstrip(b"\n")) == DIGEST
    raw = (PACKET / "candidate-preparation.json").read_bytes()
    assert sha(raw) == PACKET_SHA
    candidates = read(PACKET / "candidate-preparation.json")["candidates"]
    by_id = {row["payload"]["candidate_identifier"]: row for row in candidates}
    assert len(candidates) == len(by_id) == 819
    selected = [by_id[identifier] for identifier in ids]
    assert len(ids) == len(set(ids)) == 810
    assert Counter(row["entity_type"] for row in selected) == {"card": 270, "printing": 270, "identifier": 270}
    assert all(row["payload"]["review_status"] == "pending" for row in candidates)
    return selected, sorted(set(by_id) - set(ids))


def parsed_context(candidate):
    context = {
        "field_provenance": deepcopy(candidate["field_provenance"]),
        "retained_candidate_id": candidate["id"],
        "retained_candidate_validation_state": candidate["validation_state"],
        "retained_candidate_packet_sha256": PACKET_SHA,
    }
    for key in ("parsed_artifact_id", "parsed_record_id", "source_id", "raw_evidence_hash"):
        values = {item[key] for item in candidate["field_provenance"] if key in item}
        assert len(values) == 1
        context[key] = values.pop()
    return context


def inspect_record(candidate, basis):
    # A pure adapter call cannot establish authorization or whole-workflow success.
    adapter = SimpleNamespace(config={"canonical_identity_fields": basis["canonical_identity_fields"]},
                              descriptor=TargetDescriptor(**basis["target"]))
    return AutomaticCanonicalUpdate._canonical_record(adapter, candidate["payload"], parsed_context(candidate))


def paths(value, prefix=""):
    """Inspect every container and leaf; array positions become one field path."""
    yield prefix or "/", type(value).__name__
    if isinstance(value, dict):
        for key, child in sorted(value.items()):
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from paths(child, prefix + "/" + escaped)
    elif isinstance(value, list):
        for child in value:
            yield from paths(child, prefix + "/[]")


def classify(kind, path):
    """Field roles and permission evidence; no inference from field brevity."""
    parts = path.strip("/").split("/")
    root, field = parts[0], parts[1] if len(parts) > 1 else ""
    source_copy = root == "source_values"
    if path == "/$canonical_identity":
        status = {"card": "NOT_ESTABLISHED", "printing": "ESTABLISHED", "identifier": "NOT_APPLICABLE"}[kind]
        origin = {"card": "Scryfall Oracle UUID", "printing": "MTGJSON-generated Printing UUID",
                  "identifier": "Internal deterministic candidate hash; raw Scryfall alias is still required"}[kind]
        return "REQUIRED_FOR_CANONICAL_IDENTITY", status, origin
    if root in {"unknown_fields", "unknown_values"}:
        if parts[-1] == "uuid" or parts[-1] == "mtgjsonV4Id":
            return "USEFUL_BUT_OPTIONAL", "ESTABLISHED", "MTGJSON-generated UUID; only the isolated identifier has an established MTGJSON-controlled layer"
        origin = "Underlying Magic content or provider/upstream material; complete rights chain not established"
        if field in {"edhrecRank", "edhrecSaltiness"}: origin = "EDHREC metric carried by MTGJSON; no upstream reuse grant retained"
        if field in {"purchaseUrls", "skuIds", "artistIds"}: origin = "Provider link/identifier metadata; issuer and complete permission chain require review"
        return "EXCLUDABLE_FROM_PUBLIC_CANONICAL_OUTPUT", "NOT_ESTABLISHED", origin
    if root in {"values", "source_values"} and field:
        role = "SOURCE_PROVENANCE_ONLY" if source_copy else "USEFUL_BUT_OPTIONAL"
        status, origin = "NOT_ESTABLISHED", "Provider-derived card/product field; no complete upstream grant retained"
        if field in {"uuid", "printing_uuid"}:
            role = "SOURCE_PROVENANCE_ONLY" if source_copy else (
                "REQUIRED_FOR_CANONICAL_IDENTITY" if field == "uuid" else "REQUIRED_FOR_RELATIONSHIP_INTEGRITY")
            status, origin = "ESTABLISHED", "MTGJSON-generated UUID; MTGJSON-controlled MIT layer only"
        elif field in {"card_reference", "card_id"}:
            role = "SOURCE_PROVENANCE_ONLY" if source_copy else (
                "REQUIRED_FOR_CANONICAL_IDENTITY" if kind == "card" else "REQUIRED_FOR_RELATIONSHIP_INTEGRITY")
            origin = "Scryfall Oracle UUID, also embedded in Card-to-Printing relationship"
        elif kind == "card" and field in {"name", "normalized_name", "layout"}:
            role = "SOURCE_PROVENANCE_ONLY" if source_copy else (
                "REQUIRED_FOR_CANONICAL_IDENTITY" if field == "name" else "USEFUL_BUT_OPTIONAL")
            origin = "Wizards name/content or provider layout encoding; name is required by the supported writer, normalized_name/layout by typed v3; requiredness is not a grant"
        elif kind == "printing" and field in {"set_id", "set_code", "collector_number", "language", "finish_ids", "finishes"}:
            role = "SOURCE_PROVENANCE_ONLY" if source_copy else "REQUIRED_FOR_RELATIONSHIP_INTEGRITY"
        elif kind == "identifier" and field in {"namespace", "value"}:
            role = "SOURCE_PROVENANCE_ONLY" if source_copy else "REQUIRED_FOR_CANONICAL_IDENTITY"
            origin = "Scryfall Printing alias; local-bulk guidance does not establish public redistribution"
            if field == "namespace": status, origin = "NOT_APPLICABLE", "Internal mapper namespace label; does not license identifier value"
        if field == "mana_cost" and parts[-1] == "status":
            status, origin = "NOT_APPLICABLE", "Internal explicit missing-value marker; no mechanical fact asserted"
        if field == "identifiers" and parts[-1] == "mtgjsonV4Id":
            status, origin = "ESTABLISHED", "MTGJSON-generated historical UUID represented in current MTGJSON data; MIT notice retained"
        elif field == "identifiers" and parts[-1].startswith("scryfall"):
            origin = "Scryfall-generated identifier namespace; complete public reuse permission not established"
        return role, status, origin
    if root in {"values", "source_values"} or path == "/":
        return "SOURCE_PROVENANCE_ONLY", "NOT_ESTABLISHED", "Mixed container; individual descendants must be evaluated"
    role = "SOURCE_PROVENANCE_ONLY"
    if root in {"entity_type", "uncertainty_state", "confidence"}: role = "USEFUL_BUT_OPTIONAL"
    return role, "NOT_APPLICABLE", "Internal construction/acquisition observation; does not license bound source content"


def build_matrix(basis):
    selected, held = selected_candidates()
    occurrences, types = Counter(), defaultdict(Counter)
    record_bindings = []
    for candidate in selected:
        kind, identity, record = inspect_record(candidate, basis)
        found = {path for path, _ in paths(record)} | {"/$canonical_identity"}
        for path in found: occurrences[(kind, path)] += 1
        for path, typ in paths(record): types[(kind, path)][typ] += 1
        types[(kind, "/$canonical_identity")]["str"] += 1
        record_bindings.append({"candidate_id": candidate["payload"]["candidate_identifier"],
                               "entity_type": kind, "canonical_identity_sha256": sha(identity.encode()),
                               "adapted_record_sha256": sha(encoded(record).rstrip(b"\n"))})
    entries = []
    for (kind, path), count in sorted(occurrences.items()):
        role, permission, origin = classify(kind, path)
        entries.append({"entity_type": kind, "path": path, "record_count": count,
                        "observed_value_types": dict(sorted(types[(kind, path)].items())),
                        "admission_role": role, "public_retention_evidence": permission,
                        "origin_or_rights_layer": origin,
                        "evidence": ["reference-reviews/mb2-810-source-policy/2026-10-14/source-records/mtgjson-license-current.json"]
                            if permission == "ESTABLISHED" else
                            ["reference-reviews/mb2-810-source-policy/2026-10-14/source-receipts.json"]
                            if permission == "NOT_ESTABLISHED" else ["Internal transformation in the reviewed writer; no provider-content permission asserted"],
                        "proposed_action": "withhold_and_block_required_field" if permission == "NOT_ESTABLISHED" and role.startswith("REQUIRED_")
                            else "withhold" if permission == "NOT_ESTABLISHED" else "eligible_for_review_only"})
    return {"reviewed_main": basis["reviewed_main"], "inspection_only": True,
            "workflow_executed": False, "permission_clearance": False,
            "selection": {"count": 810, "counts_by_type": {"card": 270, "printing": 270, "identifier": 270},
                          "ordered_candidate_digest": DIGEST, "held_candidate_ids": held},
            "canonical_pre_state": basis["canonical_pre_state"],
            "record_hash_recipe": "SHA-256 of UTF-8 canonical JSON, sorted keys, compact separators, ensure_ascii=False, no trailing LF",
            "inspection_context": "Pure existing adapter, retained payloads and uniquely source-bound parsed context; hashes are inspection bindings, not execution inputs or writer acceptance.",
            "canonical_identity_path": "/$canonical_identity is an inspection pseudo-path for the returned identity, not a stored record field",
            "role_scope": "Roles describe the supported promoted-state writer/query representation. Typed v3 additionally requires normalized_name/layout; typed materialization is not claimed complete.",
            "record_bindings": record_bindings, "fields": entries,
            "absent_categories": ["price values", "image/artwork bytes", "direct image URLs", "mechanical-source activation"],
            "limitations": ["MTGJSON-only grant does not establish upstream rights.",
                            "Definition URLs are explanatory citations, not retained origin policy captures.",
                            "Short facts, identifiers and names are not assumed to share one rights status.",
                            "Source metadata and hashes are not approval or a source-policy clearance."]}
