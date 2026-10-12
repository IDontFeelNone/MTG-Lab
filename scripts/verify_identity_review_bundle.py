#!/usr/bin/env python3
"""Replay a pending identity bundle without acquiring, approving or writing data."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from acquisition import RawSnapshotStore
from dataset_import.framework import EntityResolver
from decision_intelligence import EvidenceReference
from ingestion.candidate_validation import validate_candidate_artifact
from product_intelligence import FixedContentProductManifest, GuaranteedComponent
from providers.mtgjson.validator import IDENTIFIER_POLICY
from validation import validate_document


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _path(root, relative):
    relative = Path(relative)
    result = (root / relative).resolve()
    _require(not relative.is_absolute() and ".." not in relative.parts
             and result.is_relative_to(root.resolve()), "unsafe bundle path")
    return result


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _pointer(value, pointer):
    _require(pointer.startswith("/"), "record requires a JSON pointer")
    for part in pointer[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def _contains(value, expected):
    return value == expected or (isinstance(value, dict) and
        any(_contains(child, expected) for child in value.values())) or (
        isinstance(value, list) and any(_contains(child, expected) for child in value))


def _coordinate(payload):
    language = str(payload.get("language", "")).casefold()
    return (str(payload.get("set_id", payload.get("set_code", ""))).casefold(),
            "en" if language == "english" else language,
            payload.get("collector_number_namespace", "default"),
            payload.get("collector_number"))


def _resolver_record(kind, identifier, payload):
    aliases = []
    provider_ids = payload.get("metadata", {}).get("provider_identifiers", {})
    external = payload.get("external_identifiers", {})
    if isinstance(external, dict) and "status" not in external:
        provider_ids = {**external, **provider_ids}
    for namespace, value in sorted(provider_ids.items()):
        policy = IDENTIFIER_POLICY.get(namespace, {})
        if kind == "product" or policy.get("uniqueness") == "strict" or (
                kind == "card" and policy.get("scope") == "card") or namespace in {"uuid", "mtgjson_uuid"}:
            aliases.append(f"{kind}:{namespace}:{value}")
    if kind == "card" and payload.get("card_reference"):
        aliases.append(f"card:scryfallOracleId:{payload['card_reference']}")
    if kind == "printing" and payload.get("uuid"):
        aliases.append(f"printing:uuid:{payload['uuid']}")
    return {"id": f"{kind}:{identifier}", "entity_type": kind, "identifiers": {
        "canonical_identifier": f"{kind}:{identifier}", "external_identifiers": aliases}}


def _verify_bundle(bundle_path, data_root):
    """Validate retained evidence and relationships; return a deterministic pending report."""
    bundle_path, data_root = Path(bundle_path).resolve(), Path(data_root).resolve()
    if bundle_path.is_dir():
        bundle_path = bundle_path / "bundle.json"
    root, bundle = bundle_path.parent, _load(bundle_path)
    pinned_paths = {bundle[field] for field in ("manifest_path", "existing_references_path", "unresolved_path")}
    for entry in bundle["parsed_artifacts"]:
        pinned_paths.add(entry["path"])
        pinned_paths.update(entry["candidate_artifacts"])
    pins = bundle.get("artifact_sha256", {})
    _require(pinned_paths <= pins.keys(), "prepared artifact integrity pins missing")
    for relative, digest in sorted(pins.items()):
        _require(_sha(_path(root, relative).read_bytes()) == digest, "prepared artifact integrity mismatch")
    for field in ("human_approved", "promotion_performed", "market_admission_performed"):
        _require(bundle.get(field) is False, f"pending bundle must declare {field}=false")
    sources, raw = {}, {}
    for entry in bundle["raw_sources"]:
        source_id = entry["source_id"]
        _require(source_id not in sources, "duplicate source identifier")
        snapshot_path = _path(root, entry["snapshot_directory"])
        snapshot = _load(snapshot_path / "manifest.json")
        _require(snapshot.get("raw_payload_location") == "payload.bin", "unsafe raw payload path")
        snapshot, payload = RawSnapshotStore(root / "raw").load(snapshot_path)
        digest = _sha(payload)
        blob = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
        _require(digest == entry["raw_sha256"] and len(payload) == entry["byte_count"]
                 and blob == entry["git_blob_sha1"], "source bytes/hash/blob mismatch")
        _require(snapshot["snapshot_id"] == digest and snapshot["checksum"]["value"] == digest
                 and snapshot["raw_payload_location"] == "payload.bin", "snapshot identity mismatch")
        _require(snapshot["acquired_at"] == entry["retrieved_at"]
                 and snapshot["publication_timestamp"] == entry["publication_timestamp"]
                 and snapshot["request_parameters"]["source_url"] == entry["source_url"]
                 and snapshot["request_parameters"]["git_commit"] == entry["git_commit"],
                 "snapshot acquisition provenance mismatch")
        _require(_path(root, entry["license_path"]).is_file(), "license notice missing")
        source = _load(_path(root, entry["source_record_path"]))
        validate_document(source, "source-record")
        _require(source["id"] == source_id and source["content_hash"] == "sha256:" + digest
                 and source["source_location"] == entry["source_url"]
                 and source["access_date"] == entry["retrieved_at"][:10]
                 and source["record_version"] == entry["git_commit"]
                 and _path(root, source["archival_location"]) == snapshot_path / "payload.bin",
                 "source record provenance mismatch")
        metadata = _load(snapshot_path / "provider-metadata.json")
        _require(metadata["provider"]["git_blob_sha1"] == blob
                 and metadata["provider"]["provider"] == source["provider"]
                 and metadata["provider"]["git_commit"] == entry["git_commit"]
                 and metadata["provider"]["license"] == entry["license"]
                 and metadata["provenance"]["source_url"] == entry["source_url"],
                 "provider identity mismatch")
        _require((snapshot_path / "checksum.sha256").read_text() == f"{digest}  payload.bin\n",
                 "snapshot checksum record mismatch")
        acquisition = _load(snapshot_path / "acquisition-result.json")
        _require(acquisition["snapshot_id"] == digest and acquisition["byte_length"] == len(payload)
                 and acquisition["status"] == snapshot["acquisition_status"] == "succeeded",
                 "snapshot acquisition result mismatch")
        sources[source_id], raw[source_id] = source, (digest, payload)

    for entry in bundle["raw_sources"]:
        notice = _path(root, entry["license_path"])
        _require(any(notice == _path(root, other["snapshot_directory"]) / "payload.bin"
                     for other in bundle["raw_sources"]), "license is not a verified retained source")

    for reference in bundle.get("research_references", []):
        _require(_sha(_path(data_root, reference["path"]).read_bytes()) == reference["sha256"],
                 "research reference hash mismatch")
    candidates, parsed_count = [], 0
    for entry in bundle["parsed_artifacts"]:
        parsed = _load(_path(root, entry["path"]))
        validate_document(parsed, "parsed-record-artifact")
        digest, payload = raw[parsed["source_id"]]
        _require(parsed["raw_evidence_hash"] == digest and parsed["product_id"] == bundle["product_id"]
                 and parsed["record_count"] == len(parsed["records"]), "parsed source binding mismatch")
        records = {record["id"]: record for record in parsed["records"]}
        _require(len(records) == len(parsed["records"]), "duplicate parsed record identifier")
        for record in records.values():
            excerpt = record.get("source_excerpt")
            if excerpt and "raw_text" in excerpt:
                _require(excerpt["raw_text"].encode() in payload, "parsed excerpt not in source bytes")
            if parsed["input_content_type"] == "application/json":
                selected = _pointer(json.loads(payload), record["source_location"])
                _require(_contains(record["raw_fields"], selected), "parsed JSON record differs from source")
        parsed_count += len(records)
        for candidate_path in entry["candidate_artifacts"]:
            artifact = _load(_path(root, candidate_path))
            result = validate_candidate_artifact(artifact, parsed)
            _require(result.state.value == "valid", "candidate artifact: " + "; ".join(result.errors))
            _require(artifact["candidate_count"] == len(artifact["candidates"]), "candidate count mismatch")
            for candidate in artifact["candidates"]:
                kind, proposed = candidate["entity_type"], candidate["payload"]
                _require(kind in {"card", "printing", "product"} and kind == artifact["candidate_type"],
                         "candidate entity type mismatch")
                _require(candidate["validation_state"] == "requires_review", "candidate is not pending review")
                validate_document(proposed, kind)
                coverage = {p["field_path"] for p in candidate["field_provenance"]}
                _require(set(proposed) <= coverage, "candidate field provenance incomplete")
                for provenance in candidate["field_provenance"]:
                    for field in ("source_id", "raw_evidence_hash", "acquisition_target_id"):
                        _require(provenance[field] == parsed[field], "field provenance source mismatch")
                    _require(provenance["parsed_record_id"] in candidate["parsed_record_ids"],
                             "field provenance references unrelated record")
                    if provenance["value_origin"] == "source":
                        _require(_contains(records[provenance["parsed_record_id"]]["raw_fields"],
                                           proposed[provenance["field_path"]]), "source field differs from parsed value")
                    else:
                        _require(bool(provenance.get("notes")), "computed field lacks transformation explanation")
                for assertion in proposed.get("assertions", []):
                    _require(assertion["status"] == "candidate" and assertion["subject_id"] == proposed["id"]
                             and assertion["source_id"] in sources
                             and assertion["asserted_value"] == _pointer(proposed, assertion["path"]),
                             "assertion does not match pending payload")
                if kind == "product":
                    _require(proposed["game"] == bundle["game_id"] and proposed["lifecycle_status"] == "draft",
                             "Product is not an unpromoted draft")
                    _require(all(p["source_id"] in sources for p in proposed["provenance"]),
                             "Product provenance source missing")
                candidates.append((kind, proposed))

    existing = {}
    state_path = data_root / "canonical/state.json"
    state = _load(state_path) if state_path.exists() else {}
    for kind in ("card", "printing", "product"):
        for identifier, record in state.get(kind, {}).items():
            existing[(kind, identifier)] = record["values"]
        native = data_root / "canonical/games" / bundle["game_id"] / (kind + "s")
        for path in sorted(native.glob(f"*/{kind}.json")):
            proposed = _load(path)
            _require((kind, proposed["id"]) not in existing, "canonical identity exists in two stores")
            existing[(kind, proposed["id"])] = proposed
    reused = _load(_path(root, bundle["existing_references_path"]))
    reused_keys = [(item["entity_type"], item["entity_id"]) for item in reused]
    _require(len(set(reused_keys)) == len(reused_keys), "duplicate reused canonical reference")
    for reference in reused:
        document = _load(_path(data_root, reference["canonical_path"]))
        record = _pointer(document, reference["json_pointer"])
        _require(_sha(_bytes(record)) == reference["record_sha256"]
                 and record.get("values", record) == reference["expected_values"]
                 and (reference["entity_type"], reference["entity_id"]) in existing,
                 "reused canonical reference changed")
    proposed_ids = [(kind, payload["id"]) for kind, payload in candidates]
    _require(len(set(proposed_ids)) == len(proposed_ids), "duplicate proposed identity")
    _require(not set(proposed_ids) & existing.keys(), "candidate recreates canonical identity")
    all_payloads = [(*key, payload) for key, payload in existing.items()] + [
        (kind, payload["id"], payload) for kind, payload in candidates]
    resolver_rows = {_resolver_record(*row)["id"]: _resolver_record(*row) for row in all_payloads}
    for record in state.get("identifier", {}).values():
        fields = record["values"]
        if IDENTIFIER_POLICY.get(fields.get("namespace"), {}).get("uniqueness") == "strict":
            identifier = "printing:" + fields["printing_uuid"]
            if identifier in resolver_rows:
                resolver_rows[identifier]["identifiers"]["external_identifiers"].append(
                    f"printing:{fields['namespace']}:{fields['value']}")
    resolution = EntityResolver().resolve(list(resolver_rows.values()))
    rejected = {row["source_id"] for row in resolution["rejected"] + resolution["unresolved"]}
    _require(not {f"{kind}:{identifier}" for kind, identifier in proposed_ids} & rejected,
             "proposed provider identifier collision")
    card_ids = {identifier for kind, identifier, _ in all_payloads if kind == "card"}
    coordinates = {}
    for kind, identifier, payload in all_payloads:
        if kind == "printing":
            if (kind, identifier) in proposed_ids:
                _require(payload["card_id"] in card_ids, "Printing references missing Card")
                _require(_coordinate(payload) not in coordinates, "collector coordinate collision")
            coordinates[_coordinate(payload)] = identifier
    printing_ids = {identifier for kind, identifier, _ in all_payloads if kind == "printing"}
    manifest = _load(_path(root, bundle["manifest_path"]))
    schema = _load(Path(__file__).resolve().parents[1] / "src/schemas/v1/fixed-content-product-manifest-v1.schema.json")
    schema_errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest))
    _require(not schema_errors, "manifest schema validation failed: " + "; ".join(error.message for error in schema_errors))
    research_hashes = {"sha256:" + value["sha256"] for value in bundle.get("research_references", [])}
    for evidence in manifest["evidence"]:
        if evidence["evidence_id"] in sources:
            source_id = evidence["evidence_id"]
            entry = next(value for value in bundle["raw_sources"] if value["source_id"] == source_id)
            _require(evidence["content_digest"] == "sha256:" + raw[source_id][0]
                     and evidence["source_identity"] == sources[source_id]["provider"]
                     and evidence.get("recorded_at") == entry["retrieved_at"]
                     and evidence.get("locator") == entry["source_url"], "manifest source provenance mismatch")
        else:
            _require(evidence["content_digest"] in research_hashes, "manifest evidence lacks retained source")
    document = {key: value for key, value in manifest.items() if key not in {"manifest_id", "components", "evidence"}}
    for field, constructor in (("release_date", date.fromisoformat), ("effective_at", datetime.fromisoformat)):
        if document.get(field): document[field] = constructor(document[field].replace("Z", "+00:00"))
    model = FixedContentProductManifest(**document,
        components=tuple(GuaranteedComponent(**value) for value in manifest["components"]),
        evidence=tuple(EvidenceReference(**value) for value in manifest["evidence"]))
    _require(model.to_dict() == manifest, "manifest deterministic identity/serialization mismatch")
    _require(manifest["product_id"] == bundle["product_id"] and manifest["game_id"] == bundle["game_id"],
             "manifest Product/game mismatch")
    unresolved = _load(_path(root, bundle["unresolved_path"]))
    component_ids = {value["component_id"] for value in manifest["components"]}
    unresolved_ids = {item["component_id"] for item in unresolved}
    _require(len(unresolved_ids) == len(unresolved), "duplicate unresolved component")
    _require(all(item["status"] == "unresolved" and item["missing_fields"]
                 and item["component_id"] in component_ids
                 and item.get("canonical_card_id") is None and item.get("canonical_printing_id") is None
                 for item in unresolved), "unresolved identity claims an unsupported admission")
    for component in manifest["components"]:
        _require(component["printing_id"] is None or component["printing_id"] in printing_ids,
                 "manifest references missing Printing")
        if component["printing_id"] is None:
            _require(bool(component["unknowns"]), "unbound manifest identity lacks explicit unknowns")
            _require(any(item["component_id"] == component["component_id"] for item in unresolved),
                     "unbound component is absent from unresolved inventory")
    _require(not unresolved or manifest["completeness"] != "complete", "unresolved manifest claims completeness")
    _require(unresolved_ids == {component["component_id"] for component in manifest["components"]
                               if component["printing_id"] is None}, "unresolved inventory/manifest mismatch")
    counts = Counter(kind for kind, _ in candidates)
    _require(counts["card"] == counts["printing"], "Card/Printing candidate pairs are incomplete")
    scope = bundle.get("expected_scope", {})
    _require(len(component_ids) == scope.get("physical_components", len(component_ids))
             and counts["product"] == scope.get("new_product_candidates", counts["product"])
             and counts["card"] + len(unresolved) == scope.get("new_card_printing_pairs", counts["card"] + len(unresolved))
             and sum(kind == "printing" for kind, _ in reused_keys) == scope.get("reused_printings", sum(kind == "printing" for kind, _ in reused_keys)),
             "declared scope census mismatch")
    return {"schema_version": "pending-identity-bundle-validation-v1", "baseline_commit": bundle["baseline_commit"],
        "product_id": bundle["product_id"], "valid": True, "source_count": len(sources),
        "validation_scope": "retained_artifact_integrity_schemas_references_and_replay",
        "bundle_sha256": _sha(bundle_path.read_bytes()),
        "parsed_record_count": parsed_count, "candidate_counts": {kind: counts[kind] for kind in ("card", "printing", "product")},
        "verified_candidates": sorted([{"entity_type": kind, "entity_id": payload["id"],
            "validation_state": "requires_review"} for kind, payload in candidates], key=lambda x: (x["entity_type"], x["entity_id"])),
        "source_evidence": [{key: entry[key] for key in ("source_id", "source_url", "raw_sha256", "git_commit",
            "git_blob_sha1", "retrieved_at", "license", "license_path")} for entry in sorted(bundle["raw_sources"], key=lambda x: x["source_id"])],
        "unresolved_identities": sorted([{key: item[key] for key in ("component_id", "name", "missing_fields", "reason")}
            for item in unresolved], key=lambda x: x["component_id"]),
        "reused_canonical_references": [{key: item[key] for key in ("entity_type", "entity_id", "record_sha256")}
            for item in sorted(reused, key=lambda x: (x["entity_type"], x["entity_id"]))],
        "unresolved_identity_count": len(unresolved), "reused_printing_count": sum(x["entity_type"] == "printing" for x in reused),
        "manifest_id": model.manifest_id, "manifest_completeness": model.completeness,
        "source_extraction_semantically_approved": False,
        "extraction_semantics": "manual_preparation_requires_human_review",
        "human_approved": False, "promotion_performed": False, "market_admission_performed": False,
        "readiness": "NOT_READY_FOR_EVALUATION", "blockers": sorted({"independent_human_review_required", "source_extraction_semantic_review_required",
            "market_evidence_not_acquired", *(["unresolved_exact_component_identities"] if unresolved else []),
            *(["guaranteed_content_manifest_incomplete"] if model.completeness != "complete" else [])})}


def verify_bundle(bundle_path, data_root):
    """Fail closed on malformed inputs while retaining a read-only verification boundary."""
    try:
        return _verify_bundle(bundle_path, data_root)
    except (OSError, KeyError, TypeError, IndexError) as error:
        raise ValueError(f"incomplete or malformed identity bundle: {error}") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_bundle(args.bundle, args.data_root), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
