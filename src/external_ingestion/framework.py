"""Fail-closed ingestion of supplied files into the governed acquisition pipeline.

This module establishes byte integrity and prepares a Knowledge Review Package.  It
deliberately has no dependency on canonical repositories or promotion services.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from acquisition import (AcquisitionEngine, AcquisitionError, AcquisitionProvider,
                         ProviderPolicy, ProviderRequest, ProviderResponse,
                         ProviderTrustPolicy, RawSnapshotStore,
                         assertions_from_normalized, build_review_package,
                         normalize_snapshot)

MANIFEST_SCHEMA = "external-dataset-manifest-v1"
REGISTRATION_SCHEMA = "external-dataset-registration-v1"
_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ExternalDatasetError(ValueError):
    """Integrity or ingestion could not be established safely."""


def _json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _atomic(path: Path, value: Any) -> None:
    content = _json(value); path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".partial-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream: stream.write(content)
        os.replace(temporary, path)
    except Exception:
        if os.path.exists(temporary): os.unlink(temporary)
        raise


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    dataset_name: str
    logical_identity: str
    version: str
    provider: str
    publication_date: str
    source_attribution: str
    license: str
    expected_entity_types: tuple[str, ...]
    schema_version: str
    checksum: str
    data_file: str
    notes: str | None = None
    manifest_schema: str = MANIFEST_SCHEMA

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "DatasetManifest":
        required = ("dataset_name", "logical_identity", "version", "provider",
                    "publication_date", "source_attribution", "license",
                    "expected_entity_types", "schema_version", "checksum", "data_file")
        missing = [key for key in required if not value.get(key)]
        if missing: raise ExternalDatasetError("manifest missing required fields: " + ", ".join(missing))
        if value.get("manifest_schema", MANIFEST_SCHEMA) != MANIFEST_SCHEMA:
            raise ExternalDatasetError("unsupported manifest schema")
        logical = str(value["logical_identity"])
        if not _ID.fullmatch(logical): raise ExternalDatasetError("logical_identity must be a stable lowercase identifier")
        try: date.fromisoformat(str(value["publication_date"]))
        except ValueError as error: raise ExternalDatasetError("publication_date must be ISO 8601") from error
        checksum = str(value["checksum"])
        if not _SHA256.fullmatch(checksum): raise ExternalDatasetError("checksum must be a lowercase sha256 digest")
        entity_types = value["expected_entity_types"]
        if not isinstance(entity_types, list) or not entity_types or not all(isinstance(x, str) and x for x in entity_types):
            raise ExternalDatasetError("expected_entity_types must be a non-empty string list")
        data_file = str(value["data_file"]); pure = PurePosixPath(data_file)
        if pure.is_absolute() or ".." in pure.parts or data_file.endswith("/"):
            raise ExternalDatasetError("data_file must be a safe relative path")
        return cls(str(value["dataset_name"]), logical, str(value["version"]), str(value["provider"]),
                   str(value["publication_date"]), str(value["source_attribution"]), str(value["license"]),
                   tuple(entity_types), str(value["schema_version"]), checksum, data_file,
                   str(value["notes"]) if value.get("notes") is not None else None)

    def as_dict(self) -> dict[str, Any]:
        result = {"manifest_schema": self.manifest_schema, "dataset_name": self.dataset_name,
                  "logical_identity": self.logical_identity, "version": self.version,
                  "provider": self.provider, "publication_date": self.publication_date,
                  "source_attribution": self.source_attribution, "license": self.license,
                  "expected_entity_types": list(self.expected_entity_types),
                  "schema_version": self.schema_version, "checksum": self.checksum,
                  "data_file": self.data_file}
        if self.notes is not None: result["notes"] = self.notes
        return result


class FormatAdapter(ABC):
    extensions: tuple[str, ...] = ()
    content_type = "application/octet-stream"

    @abstractmethod
    def records(self, payload: bytes) -> Iterable[Mapping[str, Any]]: ...


class JsonAdapter(FormatAdapter):
    extensions = (".json",); content_type = "application/json"
    def records(self, payload: bytes) -> Iterable[Mapping[str, Any]]:
        try: value = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error: raise ExternalDatasetError("invalid JSON dataset") from error
        rows = value if isinstance(value, list) else value.get("records") if isinstance(value, dict) else None
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ExternalDatasetError("JSON dataset must be a record list or an object containing records")
        return rows


class CsvAdapter(FormatAdapter):
    extensions = (".csv",); content_type = "text/csv"
    def records(self, payload: bytes) -> Iterable[Mapping[str, Any]]:
        try: text = payload.decode("utf-8-sig")
        except UnicodeDecodeError as error: raise ExternalDatasetError("CSV dataset must be UTF-8") from error
        try:
            reader = csv.DictReader(io.StringIO(text, newline=""))
            if not reader.fieldnames or any(not name for name in reader.fieldnames):
                raise ExternalDatasetError("CSV dataset requires a non-empty header")
            return [dict(row) for row in reader]
        except csv.Error as error: raise ExternalDatasetError("invalid CSV dataset") from error


class AdapterRegistry:
    """Extension point for formats; the ingestion core does not branch by provider."""
    def __init__(self, *, include_defaults: bool = True) -> None:
        self._adapters: dict[str, FormatAdapter] = {}
        if include_defaults:
            self.register(JsonAdapter()); self.register(CsvAdapter())
    def register(self, adapter: FormatAdapter) -> None:
        for extension in adapter.extensions:
            if extension in self._adapters: raise ExternalDatasetError(f"adapter already registered: {extension}")
            self._adapters[extension] = adapter
    def resolve(self, filename: str) -> FormatAdapter:
        adapter = self._adapters.get(PurePosixPath(filename).suffix.lower())
        if not adapter: raise ExternalDatasetError(f"unsupported dataset format: {filename}")
        return adapter


class _SuppliedFileProvider(AcquisitionProvider):
    provider_id = "external-file"
    def __init__(self, dataset: str, payload: bytes, adapter: FormatAdapter, manifest: DatasetManifest) -> None:
        self.dataset = dataset; self.payload = payload; self.adapter = adapter; self.manifest = manifest
    def discover(self): return (self.dataset,)
    def retrieve(self, request: ProviderRequest) -> ProviderResponse:
        if request.dataset != self.dataset: raise AcquisitionError("external dataset identity mismatch")
        return ProviderResponse(self.payload, self.adapter.content_type,
            publication_timestamp=self.manifest.publication_date + "T00:00:00+00:00",
            metadata={"external_provider": self.manifest.provider},
            provenance={"source_attribution": self.manifest.source_attribution})
    def emit_records(self, payload: bytes, content_type: str):
        output = []
        for index, source in enumerate(self.adapter.records(payload)):
            row = dict(source)
            supplied_id = str(row.get("id", ""))
            row["id"] = supplied_id if _ID.fullmatch(supplied_id) else f"record-{index}"
            if not isinstance(row.get("normalized"), dict):
                row = {"id": row["id"], "normalized": {key: value for key, value in row.items() if key != "id"}}
            output.append(row)
        return output


class ExternalDatasetIngestor:
    def __init__(self, root: Path | str = "data", adapters: AdapterRegistry | None = None) -> None:
        self.root = Path(root); self.adapters = adapters or AdapterRegistry()

    def _load(self, source: Path | str, manifest_path: Path | str | None = None) -> tuple[DatasetManifest, bytes, FormatAdapter]:
        path = Path(source)
        if not path.is_file(): raise ExternalDatasetError("external dataset file is missing")
        if path.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(path) as archive:
                    names = archive.namelist()
                    if names.count("manifest.json") != 1: raise ExternalDatasetError("ZIP archive requires exactly one manifest.json")
                    if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
                        raise ExternalDatasetError("ZIP archive contains unsafe paths")
                    manifest = DatasetManifest.from_dict(json.loads(archive.read("manifest.json")))
                    if names.count(manifest.data_file) != 1: raise ExternalDatasetError("manifest data_file is missing or duplicated in ZIP archive")
                    payload = archive.read(manifest.data_file)
            except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, UnicodeDecodeError) as error:
                raise ExternalDatasetError("invalid ZIP dataset") from error
        else:
            if manifest_path is None: raise ExternalDatasetError("non-ZIP datasets require --manifest")
            try: manifest = DatasetManifest.from_dict(json.loads(Path(manifest_path).read_text()))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error: raise ExternalDatasetError("invalid manifest file") from error
            if Path(manifest.data_file).name != path.name: raise ExternalDatasetError("manifest data_file does not match supplied file")
            payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != manifest.checksum:
            raise ExternalDatasetError("dataset checksum verification failed")
        adapter = self.adapters.resolve(manifest.data_file)
        list(adapter.records(payload))  # parse now: registration never precedes format validation
        return manifest, payload, adapter

    def validate(self, source: Path | str, manifest: Path | str | None = None) -> dict[str, Any]:
        description, payload, adapter = self._load(source, manifest)
        records = list(adapter.records(payload))
        return {"valid": True, "manifest": description.as_dict(), "format": PurePosixPath(description.data_file).suffix[1:].lower(),
                "byte_length": len(payload), "record_count": len(records)}

    def inspect(self, source: Path | str, manifest: Path | str | None = None) -> dict[str, Any]:
        result = self.validate(source, manifest)
        result["registered"] = (self.root / "external-datasets" / result["manifest"]["logical_identity"] /
                                f'{result["manifest"]["version"]}.json').exists()
        return result

    def list(self) -> list[dict[str, Any]]:
        return [json.loads(path.read_text()) for path in sorted((self.root / "external-datasets").glob("*/*.json"))]

    def ingest(self, source: Path | str, manifest: Path | str | None = None, *,
               timestamp: str) -> dict[str, Any]:
        description, payload, adapter = self._load(source, manifest)
        registration_path = self.root / "external-datasets" / description.logical_identity / f"{description.version}.json"
        identity = hashlib.sha256(_json(description.as_dict())).hexdigest()
        if registration_path.exists():
            existing = json.loads(registration_path.read_text())
            if existing.get("manifest") != description.as_dict():
                raise ExternalDatasetError("duplicate dataset identity/version has different content")
            return existing
        provider = _SuppliedFileProvider(description.logical_identity, payload, adapter, description)
        store = RawSnapshotStore(self.root / "raw")
        engine = AcquisitionEngine(store, self.root / "acquisition-runs"); engine.register(provider)
        run_id = "ingest-" + identity
        run = engine.acquire(provider.provider_id, description.logical_identity, started_at=timestamp,
                             run_id=run_id, license_reference=description.license)
        if run["status"] != "succeeded": raise ExternalDatasetError("governed raw acquisition failed")
        snapshot_path = Path(run["downloaded_snapshots"][0]["path"])
        snapshot = json.loads((snapshot_path / "manifest.json").read_text())
        normalized = normalize_snapshot(provider, store, snapshot_path,
                                         self.root / "external-ingestion" / identity / "normalized.json")
        assertions = assertions_from_normalized(normalized, ProviderTrustPolicy(), timestamp)
        policy = ProviderPolicy(provider.provider_id, "unknown", 0, (description.license,),
                                description.source_attribution, description.expected_entity_types)
        review = build_review_package(run, [snapshot], [normalized], assertions, policy, description.version)
        review_path = self.root / "external-ingestion" / identity / "review-package.json"
        _atomic(review_path, review)
        registration = {"schema_version": REGISTRATION_SCHEMA, "registration_id": "external-dataset-" + identity,
                        "manifest": description.as_dict(), "snapshot_id": snapshot["snapshot_id"],
                        "acquisition_run_id": run["run_id"], "review_package_id": review["review_package_id"],
                        "review_package_path": str(review_path), "status": "awaiting_human_review"}
        _atomic(registration_path, registration)
        return registration
