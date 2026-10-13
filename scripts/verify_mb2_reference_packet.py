"""Offline replay of PR #171's bounded public reference packet; no promotion path."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from acquisition import RawSnapshotStore
from evidence import AcquisitionMetadata
from evidence.contracts import deterministic_json
from ingestion.candidates import (ArtifactStatus, CandidateValidationState, FieldProvenance,
    NormalizedCandidate, NormalizedCandidateArtifact, ParsedArtifact, ParsedRecord)
from ingestion.candidate_validation import validate_candidate_artifact
from production_evidence.bounded_promotion import _canonical_id
from providers.mtgjson.execution import MTGJSONImportExecution
from providers.mtgjson.mapper import map_dataset
from providers.mtgjson.parser import parse_dataset
from providers.mtgjson.validator import identifier_findings
from query.engine import CanonicalQueryEngine
from validation import validate_document

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "reference-reviews/mb2-reference-coverage"
HISTORICAL_PACKET_PREFIX = Path("reference-reviews/mb2-reference-coverage")
HISTORICAL_REPOSITORY_FILES = {"docs/MB2_REFERENCE_COVERAGE_REVIEW.md"}
REVISION = "structured-2026-10-13"
SNAPSHOT = "sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7"


def encoded(value):
    return (deterministic_json(value) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def bound_manifest_path(root, name):
    relative = Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts, "manifest path escape")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), "manifest path escape")
    return path


def check_manifest(root, manifest):
    for name, ref in manifest["files"].items():
        path = bound_manifest_path(root, name)
        require(path.is_file(), f"manifest-listed file missing: {name}")
        raw = path.read_bytes()
        require(len(raw) == ref["bytes"] and digest(raw) == ref["sha256"],
                f"manifest integrity mismatch: {name}")
        if "git_blob_sha" in ref:
            git_blob = b"blob " + str(len(raw)).encode() + b"\0" + raw
            require(hashlib.sha1(git_blob).hexdigest() == ref["git_blob_sha"],
                    f"manifest Git blob mismatch: {name}")


def check_original(packet=PACKET, root=ROOT):
    manifest = read(packet / "review-manifest.json")
    # The retained manifest uses repository-relative names. Rebase only its
    # packet entries to the actual supplied packet, never a checkout fallback.
    packet_files, repository_files = {}, {}
    for name, ref in manifest["files"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts, "manifest path escape")
        if relative.is_relative_to(HISTORICAL_PACKET_PREFIX):
            packet_files[relative.relative_to(HISTORICAL_PACKET_PREFIX).as_posix()] = ref
        else:
            require(name in HISTORICAL_REPOSITORY_FILES,
                    f"unexpected historical repository dependency: {name}")
            repository_files[name] = ref
    check_manifest(packet, {"files": packet_files})
    check_manifest(root, {"files": repository_files})
    require(manifest["review_status"] == "pending" and manifest["human_approvals"] == 0
            and manifest["new_entity_candidate_set"] == []
            and not manifest["entity_admission_ready"], "false historical approval claim")
    snapshot = next((packet / "raw").rglob("payload.bin")).parent
    _, raw = RawSnapshotStore(packet / "raw").load(snapshot)
    source = read(packet / "source-record.json")
    validate_document(source, "source-record")
    require(source["content_hash"] == digest(raw), "source record digest mismatch")
    upstream = json.loads(raw)
    require(upstream["upstream_html_bytes_retained"] is False
            and upstream["upstream_html_digest"] is None
            and manifest["upstream_HTML_digest"] is None, "unretained HTML falsely attested")
    parsed = read(packet / "parsed-records.json")
    validate_document(parsed, "parsed-record-artifact")
    require(parsed["record_count"] == len(parsed["records"]) == len(upstream["records"]) == 273,
            "membership count mismatch")
    for index, (row, original) in enumerate(zip(parsed["records"], upstream["records"])):
        require(row["raw_fields"] == original and row["source_location"] == f"/records/{index}"
                and row["source_excerpt"]["raw_text"] == original["exact_tool_rendered_line"],
                "membership source-to-parsed mismatch")
    candidate = read(packet / "candidate-preparation.json")
    require(validate_candidate_artifact(candidate, parsed).state == CandidateValidationState.VALID,
            "historical candidate envelope invalid")
    require(candidate["candidates"] == [] and candidate["candidate_count"] == 0,
            "historical pending boundary violated")
    state = read(root / "data/canonical/state.json")
    require(CanonicalQueryEngine(data_root=root / "data",
            games_root=root / "data/canonical/games").snapshot().snapshot_id == SNAPSHOT,
            "current query snapshot binding mismatch")
    reuse = read(packet / "existing-reference-reuse.json")
    require(reuse["canonical_snapshot_id"] == SNAPSHOT, "snapshot binding mismatch")
    require(len(reuse["references"]) == 60, "existing reference count mismatch")
    for ref in reuse["references"]:
        source_raw = bound_manifest_path(root, ref["source_reference"]).read_bytes()
        require(digest(source_raw) == ref["source_sha256"], "existing source digest mismatch")
        row = json.loads(source_raw)[ref["source_record_index"]]
        require("sha256:" + digest(deterministic_json(row).encode()) == ref["record_content_identity"],
                "existing source record identity mismatch")
        require(row["id"] == ref["provider_record_id"]
                and row["oracle_id"] == ref["canonical_card_id"]
                and ref["canonical_card_id"] in state["card"]
                and ref["canonical_printing_id"] in state["printing"]
                and state["printing"][ref["canonical_printing_id"]]["values"]["card_id"]
                    == ref["canonical_card_id"]
                and ref["query_snapshot_id"] == SNAPSHOT
                and ref["physical_copy_identity_established"] is False,
                "existing identity reference mismatch")
    emblem = read(packet / "nonordinary-provider-evidence.json")
    require(emblem["exact_retained_field_projection"]["layout"] == "emblem"
            and emblem["exact_retained_field_projection"]["type_line"] == "Emblem"
            and emblem["new_candidate"] is None and emblem["human_review_status"] == "pending",
            "emblem semantics changed")
    return state, parsed


def derive(packet=PACKET, root=ROOT):
    state, membership = check_original(packet, root)
    base = packet / REVISION
    receipts = read(base / "source-receipts.json")
    sources = {}
    for key, receipt in receipts.items():
        directory = (base / receipt["path"]).resolve()
        require(directory.is_relative_to((base / "raw").resolve()), "source path escape")
        manifest, raw = RawSnapshotStore(base / "raw").load(directory)
        validate_document(manifest, "raw-snapshot", "v1")
        require(digest(raw) == receipt["sha256"] and manifest["acquired_at"] == receipt["retrieved_at"],
                "source receipt mismatch")
        require(Path(receipt["path"]).name == receipt["sha256"]
                and (base / receipt["path"] / "checksum.sha256").read_text()
                    == receipt["sha256"] + "  payload.bin\n", "raw checksum identity mismatch")
        metadata = read(base / receipt["path"] / "provider-metadata.json")["provider"]
        require(metadata == {k: v for k, v in receipt.items()
                             if k not in {"path", "sha256", "source_url", "retrieved_at"}},
                "source metadata mismatch")
        sources[key] = json.loads(raw)
        require(receipt.get("upstream_git_retained") is False
                if "upstream_git_retained" in receipt else key == "provider-checksums",
                "false upstream retention claim")
    records = sources["plst-mb2-records"]["records"]
    require(len(records) == 273, "structured record count mismatch")
    receipt = receipts["plst-mb2-records"]
    source_text = (base / receipt["path"] / "payload.bin").read_bytes().decode()
    cursor = source_text.index('[') + 1
    decoder = json.JSONDecoder()
    slices = []
    while source_text[cursor] != ']':
        if source_text[cursor] == ',' or source_text[cursor].isspace():
            cursor += 1
            continue
        _, end = decoder.raw_decode(source_text, cursor)
        slices.append(source_text[cursor:end].encode())
        cursor = end
    require(len(slices) == len(receipt["record_locators"]) == 273,
            "source slice count mismatch")
    previous_end = 0
    for raw, locator in zip(slices, receipt["record_locators"]):
        require(digest(raw) == locator["record_bytes_sha256"] and len(raw) == locator["upstream_byte_length"]
                and previous_end <= locator["upstream_byte_offset"]
                and locator["upstream_byte_offset"] + len(raw) <= receipt["upstream_bytes"],
                "exact source record slice mismatch")
        previous_end = locator["upstream_byte_offset"] + len(raw)
    products = sources["mb2-products"]
    require(products["code"] == "MB2", "wrong product namespace")
    product_ids = {p["uuid"] for p in products["sealedProduct"]}
    checksums = sources["provider-checksums"]
    for code, key in (("PLST", "plst-mb2-records"), ("MB2", "mb2-products")):
        require(checksums[code]["exact_response"].strip() == receipts[key]["upstream_sha256"],
                "upstream checksum correspondence mismatch")
    require("Permission is hereby granted" in sources["mtgjson-license-notice"]["rendered_main_text"],
            "license evidence missing")
    scryfall_rows = sources["scryfall-printing-facts"]["records"]
    responses = {r["sha256"]: r for r in sources["scryfall-printing-facts"]["responses"]}
    for r in scryfall_rows:
        response = responses[r["response_sha256"]]
        require(r["fields"]["id"] in response["request_ids"] and response["not_found"] == []
                and r["retrieved_at"] == response["retrieved_at"], "Scryfall response lineage mismatch")
    scryfall = {r["fields"]["id"]: r["fields"] for r in scryfall_rows}
    require(len(scryfall) == len(scryfall_rows) == 273, "Scryfall count or duplicate mismatch")
    labels = {r["raw_fields"]["card_name"]: r["id"] for r in membership["records"]}
    correspondences = []
    for record, locator in zip(records, receipts["plst-mb2-records"]["record_locators"]):
        fields = record["identifiers"]
        sf = scryfall[fields["scryfallId"]]
        require(record["uuid"] == locator["uuid"] and record["setCode"] == "PLST"
                and sf["set"] == "plst" and sf["oracle_id"] == fields["scryfallOracleId"]
                and sf["collector_number"] == record["number"] and sf["name"] == record["name"]
                and {"English": "en", "Japanese": "ja"}.get(record["language"]) == sf["lang"]
                and sf["layout"] != "emblem", "provider identity correspondence mismatch")
        shared = sorted(product_ids.intersection(sum(record.get("sourceProducts", {}).values(), [])))
        require(shared, "missing MB2 product relationship")
        label = record["name"] if record["name"] in labels else record["name"].split(" // ")[0]
        require(label in labels, "unsupported catalog name mapping")
        correspondences.append({"membership_record_id": labels[label], "catalog_label": label,
            "provider_name": record["name"], "oracle_id": sf["oracle_id"],
            "mtgjson_uuid": record["uuid"], "scryfall_id": sf["id"],
            "collector_number": record["number"], "provider_set": "PLST",
            "language": record["language"], "provider_language": sf["lang"],
            "mb2_source_product_ids": shared, "upstream_locator": locator,
            "mapping": "exact name" if label == record["name"] else "explicit front-face catalog label",
            "owner_spelling_confirmation": False, "physical_copy_assignment": False})
    require({r["catalog_label"] for r in correspondences} == set(labels), "catalog coverage gap")
    aliases = {r["values"].get("identifiers", {}).get("scryfallId"): identity
               for identity, r in state["printing"].items()}
    for row in correspondences:
        require(row["scryfall_id"] not in aliases or aliases[row["scryfall_id"]] == row["mtgjson_uuid"],
                "existing Printing alias collision")
    doc = {"meta": receipts["plst-mb2-records"]["meta"], "data": {"PLST": {
        "code": "PLST", "name": "The List", "cards": records}}}
    parse_dataset(encoded(doc))
    mapped = map_dataset(doc)
    findings = identifier_findings(doc)
    require(not any(f["severity"] == "error" for f in findings), "fatal identifier collision")
    eligible = []
    reused = []
    deferred = Counter()
    for row in mapped:
        kind = row["entity_type"]
        if kind not in {"card", "printing", "finish", "identifier"}:
            deferred[kind] += 1
            continue
        # Only the Printing alias needed for Scryfall readback is proposed.
        # All other identifiers remain in the unmodified provider records/mapped fields.
        if kind == "identifier" and row["mapped_fields"]["namespace"] != "scryfallId":
            deferred["optional_identifier"] += 1
            continue
        identity = _canonical_id(row)
        if identity in state.get(kind, {}):
            reused.append({"entity_type": kind, "canonical_id": identity})
        else:
            eligible.append(row)
    at = receipts["plst-mb2-records"]["retrieved_at"]
    sha = receipts["plst-mb2-records"]["sha256"]
    source_id = "mtgjson-mb2-ordinary-plst-projection"
    target = "mb2-ordinary-structured-reference"
    parsed = ParsedArtifact(id="parsed-plst-" + sha[:16], product_id="mystery_booster_2",
        source_id=source_id, acquisition_target_id=target, raw_evidence_hash=sha,
        parser_id="bounded-mtgjson-record-projection", parser_version="1", parsed_at=at,
        input_content_type="application/json", status=ArtifactStatus.SUCCEEDED,
        records=tuple(ParsedRecord(id="record-" + c["uuid"], record_type="mtgjson_printing",
            raw_fields=c, source_location=f"/records/{i}") for i, c in enumerate(records))).to_dict()
    acquisition = AcquisitionMetadata(at, at, "https-exact-record-projection", "sha256:" + sha)
    exported = []
    normalized = []
    for row in eligible:
        candidate = MTGJSONImportExecution._candidate(row, source_id, source_id + "-" + sha, acquisition)
        exported.append(candidate)
        fields = row["mapped_fields"]
        matching = [r for r in records if (r["uuid"] == fields.get("uuid", fields.get("printing_uuid")))
                    or (row["entity_type"] == "card" and
                        r["identifiers"]["scryfallOracleId"] == fields["card_reference"])]
        require(matching, "candidate source correspondence missing")
        rid = "record-" + matching[0]["uuid"]
        provenance = tuple(FieldProvenance(field_path=k,
            value_origin=("MTGJSON mapper: " if k in {"mapped_fields", "unknown_fields"}
                          else "internal deterministic candidate construction: ") + k,
            source_id=source_id, acquisition_target_id=target, raw_evidence_hash=sha,
            parsed_artifact_id=parsed["id"], parsed_record_id=rid,
            transformation_id="existing-mtgjson-mapper", transformation_version="1",
            provenance_classification=("community" if k in {"mapped_fields", "unknown_fields"}
                                       else "internal"), confidence=1.0) for k in candidate)
        normalized.append(NormalizedCandidate(id="candidate-" + row["candidate_identifier"].rsplit(":", 1)[-1],
            entity_type=row["entity_type"], payload=candidate, parsed_record_ids=(rid,),
            field_provenance=provenance, confidence=1.0,
            validation_state=CandidateValidationState.REQUIRES_REVIEW))
    MTGJSONImportExecution._validate_candidates(tuple(exported))
    envelope = NormalizedCandidateArtifact(id="candidates-plst-" + sha[:16],
        product_id="mystery_booster_2", source_id=source_id, acquisition_target_id=target,
        raw_evidence_hash=sha, parsed_artifact_id=parsed["id"], normalizer_id="existing-mtgjson-mapper",
        normalizer_version="1", normalized_at=at, candidate_type="card-printing-dependencies",
        status=ArtifactStatus.SUCCEEDED, candidates=tuple(normalized)).to_dict()
    validate_document(parsed, "parsed-record-artifact")
    require(validate_candidate_artifact(envelope, parsed).state == CandidateValidationState.VALID,
            "candidate artifact validation failed")
    proposed_cards = {r["mapped_fields"]["card_reference"] for r in exported if r["entity_type"] == "card"}
    proposed_printings = {r["mapped_fields"]["uuid"] for r in exported if r["entity_type"] == "printing"}
    for row in exported:
        fields = row["mapped_fields"]
        if row["entity_type"] == "printing":
            require(fields["card_reference"] in proposed_cards | set(state["card"]), "missing Card dependency")
            require(set(fields["finishes"]) <= set(state["finish"]), "missing finish dependency")
        if row["entity_type"] == "identifier":
            require(fields["printing_uuid"] in proposed_printings | set(state["printing"]),
                    "missing Printing dependency")
    summary = {"review_status": "pending", "human_approvals": 0, "canonical_write": False,
        "promotion_performed": False, "production_coverage_increased": False,
        "canonical_snapshot_id": SNAPSHOT, "canonical_state_sha256": digest((root / "data/canonical/state.json").read_bytes()),
        "catalog_labels": 273, "source_printing_records": 273,
        "verified_distinct_oracle_ids": len({r["oracle_id"] for r in correspondences}),
        "candidate_counts": dict(sorted(Counter(r["entity_type"] for r in exported).items())),
        "candidate_ids": [r["candidate_identifier"] for r in exported], "reused_dependencies": reused,
        "deferred_metadata_counts": dict(deferred), "identifier_findings": findings,
        "current_production": {k: len(v) for k, v in state.items()},
        "conditional_production": {k: len(v) + sum(r["entity_type"] == k for r in exported)
                                   for k, v in state.items()},
        "catalog_card_coverage": {"current": len(set(state["card"]) & {r["oracle_id"] for r in correspondences}),
                                  "conditional": 273},
        "catalog_printing_coverage": {"current": len(set(state["printing"]) & {r["mtgjson_uuid"] for r in correspondences}),
                                      "conditional": 273},
        "dependency_closure_valid": True, "entity_admission_ready": False,
        "terms_review_required": True, "physical_copy_assignment": False,
        "mechanical_cohort_expansion_authorized": False}
    source_record = {"schema_version": "v1", "id": source_id, "record_version": "1",
        "title": "Bounded MB2 ordinary PLST structured reference projection", "provider": "MTGJSON",
        "source_classification": "community", "source_location": receipts["plst-mb2-records"]["source_url"],
        "access_date": at[:10], "publication_date": doc["meta"]["date"],
        "content_hash": sha, "archival_location": receipts["plst-mb2-records"]["path"] + "/payload.bin",
        "claims": ["Source-supported PLST Printing and Oracle identities with MB2 sourceProduct links."],
        "verification_status": "supported",
        "notes": "Exact bounded record bytes, not complete upstream bytes. MIT notice separately retained. "
                 "Candidates and third-party terms remain pending review; no physical-copy assignment or admission."}
    validate_document(source_record, "source-record")
    return {"source-record.json": encoded(source_record),
            "parsed-records.json": encoded(parsed), "candidate-preparation.json": encoded(envelope),
            "correspondence.json": encoded(correspondences), "review-summary.json": encoded(summary)}


def verify(packet=PACKET, root=ROOT):
    base = packet / REVISION
    manifest = read(base / "manifest.json")
    check_manifest(base, manifest)
    require(manifest["review_status"] == "pending" and manifest["human_approvals"] == 0
            and manifest["entity_admission_ready"] is False, "false approval claim")
    actual = {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()}
    require(actual == set(manifest["files"]) | {"manifest.json"}, "unmanifested evidence file")
    for name, raw in derive(packet, root).items():
        require((base / name).read_bytes() == raw, f"deterministic replay mismatch: {name}")
    return read(base / "review-summary.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        for name, raw in derive().items():
            path = PACKET / REVISION / name
            if path.exists():
                require(path.read_bytes() == raw, f"immutable preparation conflict: {name}")
            else:
                path.write_bytes(raw)
    result = verify() if args.check else derive()
    summary = result if args.check else json.loads(result["review-summary.json"])
    print(deterministic_json({"verified": args.check, "prepared_artifacts": 5,
                              "candidate_counts": summary["candidate_counts"]}))


if __name__ == "__main__":
    main()
