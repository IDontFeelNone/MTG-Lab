"""Normalize native MTGJSON workflow artifacts for the Phase 111 intake API."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from .repository import EvidenceError, ProductionEvidenceRepository


ADAPTER_VERSION = "mtgjson-workflow-artifact-v2"
SCHEMA_VERSION = "2.0.0"


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return _sha(encoded)


def _object(data: bytes, path: str) -> dict:
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"invalid JSON file {path}: {error}") from error
    if not isinstance(value, dict):
        raise EvidenceError(f"JSON object required: {path}")
    return value


class WorkflowArtifactAdapter:
    """Fail-closed, deterministic bridge; it grants no review or write authority."""

    def normalize(self, archive: Path | str, *, run_id: str, artifact_name: str,
                  output: Path | str, archive_sha256: str | None = None,
                  repository: str = "unknown/unknown", commit_sha: str = "0" * 40) -> dict:
        archive, output = Path(archive), Path(output)
        source_bytes = archive.read_bytes()
        source_digest = _sha(source_bytes)
        if archive_sha256 and source_digest != archive_sha256.lower():
            raise EvidenceError("archive SHA-256 mismatch")
        if not re.fullmatch(r"[1-9][0-9]*", str(run_id)):
            raise EvidenceError("workflow run ID must be a positive decimal value")
        if artifact_name != f"mtgjson-ingestion-{run_id}":
            raise EvidenceError("artifact name does not match workflow run identity")
        if not repository or not re.fullmatch(r"[0-9a-f]{40}", commit_sha.lower()):
            raise EvidenceError("incomplete authenticated workflow lineage")
        members = ProductionEvidenceRepository._members(archive)
        source_inventory = [self._record(path, data) for path, data in sorted(members.items())]
        self._forbid_source_dataset(members)

        run_paths = [path for path in members if PurePosixPath(path).name == "run-result.json"]
        if len(run_paths) != 1:
            raise EvidenceError("missing or ambiguous run-result.json")
        run_result = _object(members[run_paths[0]], run_paths[0])
        manifest = run_result.get("manifest")
        if (run_result.get("mode") != "dry-run" or run_result.get("valid") is False
                or not isinstance(manifest, dict)
                or manifest.get("status") != "awaiting_independent_review"):
            raise EvidenceError("run-result.json is not a successful dry run")
        self._require_false(run_result, "canonical_write")
        self._require_false(run_result, "promotion_performed")
        self._require_false(manifest, "canonical_write")
        self._require_false(manifest, "promotion_performed")

        source_hash = manifest.get("artifact_sha256")
        dataset_id = manifest.get("dataset_identifier")
        if not isinstance(source_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", source_hash):
            raise EvidenceError("invalid source lineage SHA-256")
        if not dataset_id or not str(dataset_id).endswith(source_hash[:12]):
            raise EvidenceError("source lineage is inconsistent")
        streaming = self._unique_streaming_root(members, source_hash)
        retained_manifest_path = f"{streaming}/manifest.json"
        ledger_path = f"{streaming}/completed-sets.json"
        for required in (retained_manifest_path, ledger_path, f"{streaming}/batch-index.json"):
            if required not in members:
                raise EvidenceError(f"missing required retained evidence: {required}")
        retained_manifest = _object(members[retained_manifest_path], retained_manifest_path)
        if retained_manifest != manifest:
            raise EvidenceError("run-result and retained streaming manifest differ")
        ledger = _object(members[ledger_path], ledger_path)
        if ledger.get("source_sha256") != source_hash:
            raise EvidenceError("completed-set ledger source lineage mismatch")
        sets = ledger.get("sets")
        if not isinstance(sets, dict) or not sets:
            raise EvidenceError("completed-set ledger is empty or invalid")
        for unit, entry in sets.items():
            shard_path = f"{streaming}/candidate-shards/{unit}.json"
            if not isinstance(entry, dict) or shard_path not in members:
                raise EvidenceError(f"candidate shard reference does not resolve: {unit}")
            if _sha(members[shard_path]) != entry.get("sha256"):
                raise EvidenceError(f"internal hash mismatch: completed-set shard {unit}")
        self._verify_delivery_reports(members, source_hash, dataset_id)

        normalized: dict[str, bytes] = {}
        batches = manifest.get("batches")
        if not isinstance(batches, list) or not batches:
            raise EvidenceError("streaming manifest contains no review batches")
        batch_records, targets = [], {}
        for batch in sorted(batches, key=lambda item: str(item.get("batch_id", ""))):
            record, bundle, dependencies, payload = self._bundle(
                members, streaming, source_hash, batch)
            bundle_path = f"review_batches/{record['target_product'].lower()}/{record['batch_id']}.json"
            payload_path = f"review_payloads/{record['target_product'].lower()}/{record['batch_id']}.json"
            payload_bytes = _canonical(payload)
            normalized[payload_path] = payload_bytes
            bundle["review_payload"] = self._record(payload_path, payload_bytes)
            bundle_bytes = _canonical(bundle)
            normalized[bundle_path] = bundle_bytes
            dependency_path = f"dependency_reports/{record['target_product'].lower()}/{record['batch_id']}.json"
            normalized[dependency_path] = dependencies
            record.update(bundle_path=bundle_path, bundle_sha256=_sha(bundle_bytes),
                          payload_path=payload_path, payload_sha256=_sha(payload_bytes),
                          payload_size=len(payload_bytes),
                          retained_payload_count=len(payload["candidate_payloads"]),
                          retained_payload_bytes=len(payload_bytes))
            batch_records.append(record)
            identity = bundle["review_package"]["target_set_name"]
            previous = targets.setdefault(record["target_product"], identity)
            if previous != identity:
                raise EvidenceError("target identity is ambiguous")

        # Preserve bounded reports, findings, quarantine, lineage, and diagnostics verbatim.
        copied = []
        for path, data in sorted(members.items()):
            relative = self._permitted_relative(path, streaming)
            if relative:
                destination = relative
                if destination in normalized:
                    raise EvidenceError(f"normalized path collision: {destination}")
                normalized[destination] = data
                copied.append({"operation": "copy", "source_path": path,
                               "destination_path": destination, **self._size_hash(data)})

        normalized["metadata.json"] = _canonical({
            "adapter_version": ADAPTER_VERSION, "artifact_name": artifact_name,
            "canonical_write": False, "original_archive_sha256": source_digest,
            "promotion_performed": False, "run_id": str(run_id),
            "source_dataset_id": dataset_id, "source_sha256": source_hash,
        })
        normalized["lineage/source.json"] = _canonical({
            "dataset_id": dataset_id, "sha256": source_hash,
            "native_manifest_path": retained_manifest_path,
        })
        normalized["batch_index.json"] = _canonical({"batches": batch_records,
            "retained_payload_count": sum(x["retained_payload_count"] for x in batch_records),
            "retained_payload_bytes": sum(x["retained_payload_bytes"] for x in batch_records)})
        content_inventory = [self._record(path, data) for path, data in sorted(normalized.items())]
        normalized_digest = _sha(_canonical(content_inventory))
        dispositions = {item["source_path"]: item for item in copied}
        transformations = [dispositions.get(path, {"operation": "verify-source-only",
                            "source_path": path, "source_sha256": _sha(data),
                            "source_size": len(data)})
                           for path, data in sorted(members.items())]
        transformations.extend({"operation": "construct-review-bundle",
                "source_path": item["native_bundle_path"], "destination_path": item["bundle_path"]}
                for item in batch_records)
        top_manifest = {
            "schema_version": SCHEMA_VERSION,
            "workflow": {"run_id": str(run_id), "workflow_name": "MTGJSON production ingestion",
                         "repository": repository, "commit_sha": commit_sha.lower()},
            "source": {"dataset_id": dataset_id, "sha256": source_hash},
            "artifact_name": artifact_name, "original_archive_sha256": source_digest,
            "internal_member_inventory": source_inventory,
            "target_set_identities": [{"code": code, "name": targets[code]}
                                      for code in sorted(targets)],
            "review_bundle_paths": [item["bundle_path"] for item in batch_records],
            "canonical_write": False, "promotion_performed": False,
            "adapter_version": ADAPTER_VERSION,
            "revision_policy": "derived-production-evidence-identity",
            "evidence_identity": f"{run_id}-review-payload-v2",
            "retained_payload_count": sum(x["retained_payload_count"] for x in batch_records),
            "retained_payload_bytes": sum(x["retained_payload_bytes"] for x in batch_records),
            "normalized_archive_sha256": normalized_digest,
            "normalized_digest_scope": "canonical inventory of all normalized members except manifest.json",
            "transformations": transformations,
            "files": content_inventory,
        }
        normalized["manifest.json"] = _canonical(top_manifest)
        output.mkdir(parents=True, exist_ok=True)
        for path in sorted(normalized):
            destination = output / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(normalized[path])
        zip_path = output / "normalized-intake.zip"
        self._write_zip(zip_path, normalized)
        (output / "normalized-inventory.json").write_bytes(_canonical({
            "schema_version": SCHEMA_VERSION, "files": content_inventory,
            "normalized_archive_sha256": normalized_digest}))
        report = {"schema_version": SCHEMA_VERSION, "valid": True, "adapter_version": ADAPTER_VERSION,
                  "run_id": str(run_id), "artifact_name": artifact_name,
                  "evidence_identity": f"{run_id}-review-payload-v2",
                  "retained_payload_count": sum(x["retained_payload_count"] for x in batch_records),
                  "retained_payload_bytes": sum(x["retained_payload_bytes"] for x in batch_records),
                  "original_archive_sha256": source_digest,
                  "normalized_archive_sha256": normalized_digest,
                  "normalized_zip_sha256": _sha(zip_path.read_bytes()),
                  "normalized_archive": "normalized-intake.zip", "canonical_write": False,
                  "promotion_performed": False}
        (output / "adapter-report.json").write_bytes(_canonical(report))
        return {**report, "normalized_archive": str(zip_path)}

    @staticmethod
    def _record(path: str, data: bytes) -> dict:
        return {"path": path, "sha256": _sha(data), "size": len(data)}

    @staticmethod
    def _size_hash(data: bytes) -> dict:
        return {"source_sha256": _sha(data), "source_size": len(data)}

    @staticmethod
    def _require_false(value: dict, field: str) -> None:
        if value.get(field) is not False:
            raise EvidenceError(f"{field} must be false")

    @staticmethod
    def _forbid_source_dataset(members: dict[str, bytes]) -> None:
        for path in members:
            lower = path.casefold()
            if "allprintings.json" in lower or lower.endswith((".sqlite", ".sqlite3", ".db")):
                raise EvidenceError(f"full MTGJSON source artifact is forbidden: {path}")

    @staticmethod
    def _unique_streaming_root(members: dict[str, bytes], source_hash: str) -> str:
        suffix = f"streaming/{source_hash}/manifest.json"
        paths = [path[:-len("/manifest.json")] for path in members
                 if path == suffix or path.endswith("/" + suffix)]
        if len(paths) != 1:
            raise EvidenceError("missing or ambiguous retained streaming manifest")
        return paths[0]

    def _bundle(self, members: dict[str, bytes], root: str, source_hash: str,
                batch: dict) -> tuple[dict, dict, bytes, dict]:
        batch_id, code = batch.get("batch_id"), batch.get("target_set_code")
        if not batch_id or not code:
            raise EvidenceError("target identity is ambiguous")
        native = f"{root}/review-batches/{code}/{batch_id}"
        paths = {name: f"{native}/{name}.json" for name in
                 ("manifest", "candidate-ids", "dependency-closure", "review-package")}
        for name, path in paths.items():
            if path not in members:
                label = {"candidate-ids": "candidate IDs", "dependency-closure": "dependency closure",
                         "review-package": "review package"}.get(name, "batch manifest")
                raise EvidenceError(f"missing {label}: {path}")
        native_manifest = _object(members[paths["manifest"]], paths["manifest"])
        ids = _object(members[paths["candidate-ids"]], paths["candidate-ids"])
        closure = _object(members[paths["dependency-closure"]], paths["dependency-closure"])
        package = _object(members[paths["review-package"]], paths["review-package"])
        for value in (native_manifest, ids, closure, package):
            if value.get("target_set_code") != code:
                raise EvidenceError("cross-target contamination in review bundle")
        if package.get("review_status") != "pending":
            raise EvidenceError("review status must be pending")
        self._require_false(package, "canonical_write")
        self._require_false(package, "promotion_performed")
        self._require_false(native_manifest, "canonical_write")
        self._require_false(native_manifest, "promotion_performed")
        candidate_ids = ids.get("candidate_ids")
        if not isinstance(candidate_ids, list) or candidate_ids != package.get("candidate_ids") \
                or candidate_ids != closure.get("candidate_ids") or candidate_ids != batch.get("candidate_ids"):
            raise EvidenceError("candidate-ID lists differ across retained evidence")
        candidate_digest = _identity(candidate_ids)
        if candidate_digest != batch.get("candidate_id_digest") or candidate_digest != ids.get("candidate_id_digest"):
            raise EvidenceError("internal hash mismatch: candidate IDs")
        if not closure.get("valid") or closure.get("dependency_closure_digest") != batch.get("dependency_closure_digest"):
            raise EvidenceError("dependency closure is invalid or inconsistent")
        if _sha(members[paths["review-package"]]) != native_manifest.get("review_package_sha256"):
            raise EvidenceError("internal hash mismatch: review package")
        lineage = package.get("source_lineage", {})
        if lineage.get("source_sha256") != source_hash or lineage.get("dataset_identifier") is None:
            raise EvidenceError("source lineage is inconsistent")
        payloads = package.get("candidate_payload_references")
        if not isinstance(payloads, list) or not payloads:
            raise EvidenceError("missing candidate shard reference")
        payload_refs = []
        payload_by_id, payload_codes = {}, set()
        for reference in payloads:
            unit = PurePosixPath(str(reference.get("path", ""))).stem
            matches = [path for path in members if path == f"{root}/candidate-shards/{unit}.json"]
            if len(matches) != 1:
                raise EvidenceError("candidate shard reference does not resolve uniquely")
            data = members[matches[0]]
            referenced_size = reference.get("byte_length", reference.get("size"))
            if _sha(data) != reference.get("sha256") or len(data) != referenced_size:
                raise EvidenceError("internal hash mismatch: candidate shard")
            shard = _object(data, matches[0])
            payload_codes.add(shard.get("set_code"))
            candidates = shard.get("candidates")
            if not isinstance(candidates, list):
                raise EvidenceError("candidate shard candidates list is required")
            for item in candidates:
                if not isinstance(item, dict) or not item.get("candidate_identifier"):
                    raise EvidenceError("candidate payload identity is missing")
                identifier = item["candidate_identifier"]
                if identifier in payload_by_id:
                    raise EvidenceError("duplicate candidate payload")
                payload_by_id[identifier] = item
            payload_refs.append({"source_path": matches[0], "sha256": _sha(data), "size": len(data)})
        if payload_codes != {code}:
            raise EvidenceError("cross-target contamination in candidate payload")
        missing = [identifier for identifier in candidate_ids if identifier not in payload_by_id]
        if missing:
            raise EvidenceError("candidate ID lacks a payload")
        selected = [payload_by_id[identifier] for identifier in candidate_ids]
        if [item["candidate_identifier"] for item in selected] != candidate_ids:
            raise EvidenceError("candidate payload order or identity differs from candidate-ID list")
        selected_ids = set(candidate_ids)
        if len(selected_ids) != len(candidate_ids):
            raise EvidenceError("duplicate candidate ID")
        card_refs = {item.get("mapped_fields", {}).get("card_reference") for item in selected
                     if item.get("entity_type") == "card"}
        for item in selected:
            if item.get("entity_type") == "printing" and item.get("mapped_fields", {}).get(
                    "card_reference") not in card_refs:
                raise EvidenceError("Card-to-Printing reference cannot be resolved")
        if not isinstance(package.get("provenance"), dict) or not package["provenance"]:
            raise EvidenceError("payload provenance is missing")
        payload_digest = _identity(selected)
        payload = {"schema_version": SCHEMA_VERSION, "batch_id": batch_id,
            "target_set_code": code, "target_set_name": package.get("target_set_name"),
            "candidate_ids": candidate_ids, "candidate_id_digest": candidate_digest,
            "candidate_payloads": selected,
            "candidate_payload_digest": payload_digest,
            "candidate_id_to_payload_index": {identifier: index for index, identifier in enumerate(candidate_ids)},
            "source_candidate_shards": payload_refs, "source_lineage": lineage,
            "provenance": package["provenance"], "dependency_references": closure,
            "canonical_write": False, "promotion_performed": False}
        bundle = {"review_package": package, "candidate_ids": candidate_ids,
                  "dependency_closure": closure, "payload_references": payload_refs,
                  "provenance": package.get("provenance", {}),
                  "findings": package.get("identifier_findings", []),
                  "lineage": lineage, "deterministic_digests": {
                      "candidate_ids_sha256": candidate_digest,
                      "candidate_payloads_sha256": payload_digest,
                      "dependency_closure_sha256": batch.get("dependency_closure_digest"),
                      "review_package_sha256": _sha(members[paths["review-package"]])},
                  "native_paths": paths}
        record = {"batch_id": batch_id, "target_product": code,
                  "candidate_ids_sha256": candidate_digest, "native_bundle_path": native}
        return record, bundle, members[paths["dependency-closure"]], payload

    @staticmethod
    def _permitted_relative(path: str, streaming: str) -> str | None:
        name = PurePosixPath(path).name
        if path.startswith(streaming + "/finding-shards/"):
            return "findings/" + path[len(streaming) + 1:]
        if path.startswith(streaming + "/quarantine/"):
            return "findings/" + path[len(streaming) + 1:]
        if name == "identifier_quarantine.json":
            return "findings/identifier-quarantine.json"
        if path.startswith(streaming + "/performance-checkpoints/"):
            return "summaries/performance-checkpoints/" + name
        if path in {f"{streaming}/manifest.json", f"{streaming}/completed-sets.json",
                    f"{streaming}/batch-index.json"}:
            return "summaries/native-" + name
        if "/reports/" in "/" + path or path.startswith("reports/"):
            return "summaries/reports/" + name
        if "diagnostic" in path.casefold():
            return "summaries/diagnostics/" + name
        if name == "run-result.json":
            return "summaries/run-result.json"
        return None

    @staticmethod
    def _verify_delivery_reports(members: dict[str, bytes], source_hash: str,
                                 dataset_id: str) -> None:
        checksums = [path for path in members if PurePosixPath(path).name ==
                     "checksum-verification.json"]
        if len(checksums) != 1:
            raise EvidenceError("missing or ambiguous checksum verification report")
        checksum = _object(members[checksums[0]], checksums[0])
        if (checksum.get("valid") is not True or checksum.get("actual_sha256") != source_hash
                or checksum.get("expected_sha256", source_hash) != source_hash):
            raise EvidenceError("checksum report source lineage mismatch")
        summaries = [path for path in members if PurePosixPath(path).name == "dataset-summary.json"]
        if len(summaries) != 1:
            raise EvidenceError("missing or ambiguous dataset summary report")
        summary = _object(members[summaries[0]], summaries[0])
        if (summary.get("artifact_sha256") != source_hash
                or summary.get("dataset_identifier") != dataset_id):
            raise EvidenceError("dataset report source lineage mismatch")

    @staticmethod
    def _write_zip(path: Path, members: dict[str, bytes]) -> None:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
            for name in sorted(members):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                target.writestr(info, members[name])
