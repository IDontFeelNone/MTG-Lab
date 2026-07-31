"""Verified intake and deterministic lookup for production evidence archives."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


class EvidenceError(ValueError):
    """An evidence archive failed a closed verification boundary."""


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"invalid JSON file {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise EvidenceError(f"JSON object required: {path.name}")
    return value


class ProductionEvidenceRepository:
    """Repository-owned immutable evidence, deliberately separate from canonical data."""

    SCHEMA_VERSION = "1.0.0"
    REQUIRED = {"metadata.json", "batch_index.json", "lineage/source.json"}
    ALLOWED_TOP_LEVEL = {
        "metadata.json", "batch_index.json", "review_batches", "findings",
        "dependency_reports", "lineage", "summaries",
    }

    def __init__(self, data_root: Path | str = Path("data")):
        self.root = Path(data_root) / "production_runs"

    @staticmethod
    def _members(archive: Path) -> dict[str, bytes]:
        try:
            with zipfile.ZipFile(archive) as source:
                result = {}
                for item in source.infolist():
                    if item.is_dir():
                        continue
                    path = PurePosixPath(item.filename)
                    if path.is_absolute() or ".." in path.parts or not path.parts:
                        raise EvidenceError(f"unsafe archive path: {item.filename}")
                    name = path.as_posix()
                    if name in result:
                        raise EvidenceError(f"duplicate archive member: {name}")
                    result[name] = source.read(item)
                return result
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            raise EvidenceError(f"invalid evidence archive: {error}") from error

    def intake(self, archive: Path | str, archive_sha256: str, run_id: str) -> dict:
        archive = Path(archive)
        actual_archive_hash = _digest(archive.read_bytes())
        if actual_archive_hash != archive_sha256.lower():
            raise EvidenceError("archive SHA-256 mismatch")
        members = self._members(archive)
        if "manifest.json" not in members:
            raise EvidenceError("missing required file: manifest.json")
        try:
            manifest = json.loads(members["manifest.json"])
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise EvidenceError(f"invalid manifest: {error}") from error
        if not isinstance(manifest, dict) or manifest.get("schema_version") != self.SCHEMA_VERSION:
            raise EvidenceError("unsupported or missing evidence manifest schema_version")
        workflow = manifest.get("workflow")
        if not isinstance(workflow, dict) or str(workflow.get("run_id")) != str(run_id):
            raise EvidenceError("workflow run identity mismatch")
        if not workflow.get("workflow_name") or not workflow.get("repository") or not workflow.get("commit_sha"):
            raise EvidenceError("incomplete workflow identity")
        source = manifest.get("source")
        if not isinstance(source, dict) or not source.get("dataset_id") or not source.get("sha256"):
            raise EvidenceError("incomplete source lineage")
        declared = manifest.get("files")
        if not isinstance(declared, list):
            raise EvidenceError("manifest files inventory is required")
        inventory = {}
        for record in declared:
            if not isinstance(record, dict) or set(record) != {"path", "sha256", "size"}:
                raise EvidenceError("invalid manifest file record")
            path = str(record["path"])
            if path in inventory or path == "manifest.json":
                raise EvidenceError(f"duplicate or invalid manifest path: {path}")
            inventory[path] = record
        if set(members) != set(inventory) | {"manifest.json"}:
            raise EvidenceError("archive members do not match manifest inventory")
        if not self.REQUIRED <= set(inventory):
            missing = sorted(self.REQUIRED - set(inventory))
            raise EvidenceError("missing required file: " + ", ".join(missing))
        for path, record in inventory.items():
            pure = PurePosixPath(path)
            if pure.is_absolute() or ".." in pure.parts or pure.parts[0] not in self.ALLOWED_TOP_LEVEL:
                raise EvidenceError(f"disallowed evidence path: {path}")
            content = members[path]
            if len(content) != record["size"] or _digest(content) != record["sha256"]:
                raise EvidenceError(f"internal hash or size mismatch: {path}")
            lower = path.casefold()
            if "allprintings" in lower or lower.endswith((".tar", ".tar.gz", ".zip", ".sqlite")):
                raise EvidenceError(f"full dataset or transient artifact forbidden: {path}")

        with tempfile.TemporaryDirectory(dir=self.root.parent if self.root.parent.exists() else None) as temporary:
            staging = Path(temporary)
            for name, content in members.items():
                target = staging / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            metadata = _read_json(staging / "metadata.json")
            batches = _read_json(staging / "batch_index.json")
            lineage = _read_json(staging / "lineage/source.json")
            if str(metadata.get("run_id")) != str(run_id):
                raise EvidenceError("metadata workflow run identity mismatch")
            if metadata.get("source_dataset_id") != source["dataset_id"] or metadata.get("source_sha256") != source["sha256"]:
                raise EvidenceError("metadata source lineage mismatch")
            if lineage.get("dataset_id") != source["dataset_id"] or lineage.get("sha256") != source["sha256"]:
                raise EvidenceError("source lineage record mismatch")
            entries = batches.get("batches")
            if not isinstance(entries, list):
                raise EvidenceError("batch index batches list is required")
            for batch in entries:
                required = {"batch_id", "target_product", "candidate_ids_sha256", "bundle_path", "bundle_sha256"}
                if not isinstance(batch, dict) or not required <= set(batch):
                    raise EvidenceError("incomplete retained review batch")
                bundle_path = str(batch["bundle_path"])
                if not bundle_path.startswith("review_batches/") or bundle_path not in members:
                    raise EvidenceError(f"missing review bundle: {bundle_path}")
                if _digest(members[bundle_path]) != batch["bundle_sha256"]:
                    raise EvidenceError(f"review bundle digest mismatch: {bundle_path}")
                try:
                    bundle = json.loads(members[bundle_path])
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise EvidenceError(f"invalid review bundle: {bundle_path}") from error
                bundle_fields = {"review_package", "candidate_ids", "dependency_closure",
                    "payload_references", "provenance", "findings", "lineage",
                    "deterministic_digests"}
                if not isinstance(bundle, dict) or not bundle_fields <= set(bundle):
                    raise EvidenceError(f"incomplete review bundle: {bundle_path}")

            destination = self.root / str(run_id)
            tree_digest = self._tree_digest(staging)
            if destination.exists():
                if self._tree_digest(destination) == tree_digest:
                    raise EvidenceError(f"duplicate production run: {run_id}")
                raise EvidenceError(f"production run identity collision: {run_id}")
            self.root.mkdir(parents=True, exist_ok=True)
            os.replace(staging, destination)
        self.rebuild_index()
        return self.inspect(str(run_id))

    @staticmethod
    def _tree_digest(root: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            relative = path.relative_to(root).as_posix()
            digest.update(relative.encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest())
        return digest.hexdigest()

    def runs(self) -> dict:
        index = self.rebuild_index()
        return {"schema_version": self.SCHEMA_VERSION, "runs": index["runs"]}

    def inspect(self, run_id: str) -> dict:
        run = self.root / str(run_id)
        if not run.is_dir():
            raise EvidenceError(f"unknown production run: {run_id}")
        manifest, metadata, batches = (_read_json(run / name) for name in
                                       ("manifest.json", "metadata.json", "batch_index.json"))
        return {"schema_version": self.SCHEMA_VERSION, "run_id": str(run_id),
                "manifest": manifest, "metadata": metadata, "batches": batches["batches"],
                "tree_sha256": self._tree_digest(run)}

    def batches(self, run_id: str) -> dict:
        inspected = self.inspect(run_id)
        return {"schema_version": self.SCHEMA_VERSION, "run_id": str(run_id),
                "batches": inspected["batches"]}

    def verify(self, run_id: str) -> dict:
        run = self.root / str(run_id)
        inspected = self.inspect(run_id)
        manifest = inspected["manifest"]
        expected = {record["path"]: record for record in manifest["files"]}
        actual = {path.relative_to(run).as_posix() for path in run.rglob("*") if path.is_file()}
        if actual != set(expected) | {"manifest.json"}:
            raise EvidenceError("retained files do not match manifest inventory")
        for path, record in expected.items():
            content = (run / path).read_bytes()
            if len(content) != record["size"] or _digest(content) != record["sha256"]:
                raise EvidenceError(f"retained file hash mismatch: {path}")
        return {"schema_version": self.SCHEMA_VERSION, "run_id": str(run_id),
                "valid": True, "tree_sha256": inspected["tree_sha256"]}

    def rebuild_index(self) -> dict:
        self.root.mkdir(parents=True, exist_ok=True)
        records = []
        for run in sorted((path for path in self.root.iterdir() if path.is_dir()), key=lambda p: p.name):
            manifest, metadata, batches = (_read_json(run / name) for name in
                                           ("manifest.json", "metadata.json", "batch_index.json"))
            records.append({"run_id": run.name, "workflow": manifest["workflow"],
                "source": manifest["source"], "target_products": sorted({
                    item["target_product"] for item in batches["batches"]}),
                "batch_ids": sorted(item["batch_id"] for item in batches["batches"]),
                "tree_sha256": self._tree_digest(run)})
        index = {"schema_version": self.SCHEMA_VERSION, "runs": records,
                 "by_source_sha256": {}, "by_target_product": {}, "by_workflow_identity": {}}
        for record in records:
            index["by_source_sha256"].setdefault(record["source"]["sha256"], []).append(record["run_id"])
            for target in record["target_products"]:
                index["by_target_product"].setdefault(target, []).append(record["run_id"])
            workflow = record["workflow"]
            key = f'{workflow["repository"]}:{workflow["workflow_name"]}:{workflow["commit_sha"]}'
            index["by_workflow_identity"].setdefault(key, []).append(record["run_id"])
        encoded = json.dumps(index, indent=2, sort_keys=True) + "\n"
        target = self.root / "index.json"
        if not target.exists() or target.read_text() != encoded:
            target.write_text(encoded)
        return index
