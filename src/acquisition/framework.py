"""Immutable acquisition, normalization, and evidence-assertion stages.

Nothing in this module imports a canonical repository or promotion service.  That
dependency boundary is deliberate: successful retrieval is evidence, not truth.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_TYPES = {"application/json", "application/x-ndjson", "text/csv", "text/plain"}
_SECRET_KEYS = {"authorization", "api_key", "apikey", "password", "secret", "token"}
SNAPSHOT_SCHEMA = "raw-snapshot-v1"
NORMALIZED_SCHEMA = "normalized-source-record-v1"
RUN_SCHEMA = "acquisition-run-v1"
ASSERTION_SCHEMA = "v3"


class AcquisitionError(ValueError):
    """A safe, auditable acquisition-stage failure."""


def _json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _identifier(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise AcquisitionError(f"{label} must be a stable lowercase identifier")
    return value


def _timestamp(value: str, label: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise AcquisitionError(f"{label} must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise AcquisitionError(f"{label} must include a timezone")
    return value


def _reject_secrets(value: Any, location: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in _SECRET_KEYS:
                raise AcquisitionError(f"credentials are forbidden in {location}")
            _reject_secrets(child, location)
    elif isinstance(value, (list, tuple)):
        for child in value: _reject_secrets(child, location)


def _atomic_create(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".partial-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != content:
                raise AcquisitionError(f"immutable artifact already exists with different content: {path}")
        finally:
            os.unlink(temporary)
    except Exception:
        if os.path.exists(temporary): os.unlink(temporary)
        raise


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    dataset: str
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    payload: bytes
    content_type: str
    content_encoding: str = "identity"
    publication_timestamp: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    rate_limit: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    status: str = "succeeded"


class AcquisitionProvider(ABC):
    """Source-specific boundary used by the generic engine."""

    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    def discover(self) -> Sequence[str]: return ()

    def build_request(self, dataset: str, parameters: Mapping[str, Any]) -> ProviderRequest:
        return ProviderRequest(dataset, dict(parameters))

    @abstractmethod
    def retrieve(self, request: ProviderRequest) -> ProviderResponse: ...

    def validate_response(self, response: ProviderResponse) -> None: return None

    @abstractmethod
    def emit_records(self, payload: bytes, content_type: str) -> Iterable[Mapping[str, Any]]: ...


class FixtureProvider(AcquisitionProvider):
    """Deterministic JSON provider for network-free tests and demonstrations."""

    provider_id = "fixture"

    def __init__(self, datasets: Mapping[str, bytes | Sequence[Mapping[str, Any]]], *,
                 fail_datasets: Iterable[str] = ()) -> None:
        self._datasets = dict(datasets); self._fail = frozenset(fail_datasets)

    def discover(self) -> Sequence[str]: return tuple(sorted(self._datasets))

    def retrieve(self, request: ProviderRequest) -> ProviderResponse:
        if request.dataset in self._fail: raise AcquisitionError(f"fixture failure: {request.dataset}")
        if request.dataset not in self._datasets: raise AcquisitionError(f"unknown fixture dataset: {request.dataset}")
        value = self._datasets[request.dataset]
        payload = value if isinstance(value, bytes) else _json(list(value))
        return ProviderResponse(payload, "application/json", metadata={"offline": True},
                                provenance={"fixture_dataset": request.dataset})

    def emit_records(self, payload: bytes, content_type: str) -> Iterable[Mapping[str, Any]]:
        try: value = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error: raise AcquisitionError("malformed JSON payload") from error
        rows = value if isinstance(value, list) else value.get("records") if isinstance(value, dict) else None
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise AcquisitionError("fixture payload must contain a JSON record list")
        return rows


@dataclass(frozen=True, slots=True)
class SnapshotRef:
    snapshot_id: str
    provider_id: str
    dataset: str
    path: Path
    checksum: str
    unchanged: bool = False


class RawSnapshotStore:
    """Byte-preserving immutable storage at provider/dataset/checksum paths."""

    def __init__(self, root: Path | str = "data/raw", max_payload_bytes: int = 100_000_000) -> None:
        self.root = Path(root); self.max_payload_bytes = max_payload_bytes
        if self.max_payload_bytes <= 0: raise AcquisitionError("max_payload_bytes must be positive")
        project = Path(__file__).resolve().parents[2]
        if self.root.resolve().is_relative_to((project / "data" / "canonical").resolve()):
            raise AcquisitionError("raw snapshots cannot use the canonical data directory")

    def store(self, provider_id: str, request: ProviderRequest, response: ProviderResponse,
              acquired_at: str, *, license_reference: str | None = None,
              parent_snapshot_id: str | None = None) -> SnapshotRef:
        provider_id = _identifier(provider_id, "provider_id"); dataset = _identifier(request.dataset, "dataset")
        _timestamp(acquired_at, "acquired_at")
        if response.content_type not in _TYPES: raise AcquisitionError(f"unsupported content type: {response.content_type}")
        if not isinstance(response.payload, bytes): raise AcquisitionError("provider payload must be bytes")
        if len(response.payload) > self.max_payload_bytes: raise AcquisitionError("payload exceeds configured size limit")
        if response.publication_timestamp: _timestamp(response.publication_timestamp, "publication_timestamp")
        _reject_secrets(request.parameters, "request parameters")
        _reject_secrets(response.metadata, "provider metadata")
        _reject_secrets(response.provenance, "provider provenance")
        checksum = hashlib.sha256(response.payload).hexdigest(); snapshot_id = checksum
        base = self.root.resolve(); directory = base / provider_id / dataset / snapshot_id
        if not directory.resolve().is_relative_to(base): raise AcquisitionError("snapshot path escapes raw root")
        payload_path = directory / "payload.bin"; existed = payload_path.exists()
        if existed and hashlib.sha256(payload_path.read_bytes()).hexdigest() != checksum:
            raise AcquisitionError("checksum mismatch in existing snapshot")
        manifest = {
            "schema_version": SNAPSHOT_SCHEMA, "snapshot_id": snapshot_id,
            "provider_id": provider_id, "dataset": dataset, "acquired_at": acquired_at,
            "publication_timestamp": response.publication_timestamp,
            "request_parameters": dict(request.parameters), "content_type": response.content_type,
            "content_encoding": response.content_encoding, "raw_payload_location": "payload.bin",
            "payload_byte_length": len(response.payload), "checksum": {"algorithm": "sha256", "value": checksum},
            "acquisition_status": response.status, "license_reference": license_reference,
            "parent_snapshot_id": parent_snapshot_id,
        }
        metadata = {"provider": dict(response.metadata), "rate_limit": dict(response.rate_limit),
                    "provenance": dict(response.provenance)}
        result = {"schema_version": SNAPSHOT_SCHEMA, "status": response.status,
                  "snapshot_id": snapshot_id, "byte_length": len(response.payload)}
        # A checksum-addressed duplicate retains its original immutable manifest.
        _atomic_create(payload_path, response.payload)
        _atomic_create(directory / "manifest.json", _json(manifest))
        _atomic_create(directory / "checksum.sha256", f"{checksum}  payload.bin\n".encode())
        _atomic_create(directory / "provider-metadata.json", _json(metadata))
        _atomic_create(directory / "acquisition-result.json", _json(result))
        return SnapshotRef(snapshot_id, provider_id, dataset, directory, checksum, existed)

    def load(self, snapshot: Path | str) -> tuple[dict[str, Any], bytes]:
        directory = Path(snapshot); manifest = json.loads((directory / "manifest.json").read_text())
        if manifest.get("schema_version") != SNAPSHOT_SCHEMA: raise AcquisitionError("invalid raw snapshot schema version")
        payload = (directory / manifest["raw_payload_location"]).read_bytes()
        checksum = hashlib.sha256(payload).hexdigest()
        if checksum != manifest["checksum"]["value"] or len(payload) != manifest["payload_byte_length"]:
            raise AcquisitionError("raw snapshot checksum or length mismatch")
        return manifest, payload


def normalize_snapshot(provider: AcquisitionProvider, store: RawSnapshotStore, snapshot: Path | str,
                       destination: Path | str) -> dict[str, Any]:
    """Emit deterministic provider records with complete snapshot lineage."""
    manifest, payload = store.load(snapshot)
    if manifest["provider_id"] != provider.provider_id: raise AcquisitionError("provider identity collision")
    provider.validate_response(ProviderResponse(payload, manifest["content_type"], manifest["content_encoding"]))
    output = []
    seen = set()
    for index, source in enumerate(provider.emit_records(payload, manifest["content_type"])):
        source_id = str(source.get("id", index))
        if source_id in seen: raise AcquisitionError(f"duplicate source record id: {source_id}")
        seen.add(source_id)
        mapped = dict(source.get("normalized", {})) if isinstance(source.get("normalized", {}), dict) else {}
        unmapped = {key: value for key, value in source.items() if key not in {"normalized"}}
        record_id = hashlib.sha256(f"{provider.provider_id}\0{source_id}\0{manifest['snapshot_id']}".encode()).hexdigest()
        output.append({"schema_version": NORMALIZED_SCHEMA, "id": record_id,
                       "provider_id": provider.provider_id, "source_record_id": source_id,
                       "raw_snapshot_id": manifest["snapshot_id"], "raw_snapshot_path": str(Path(snapshot)),
                       "source_values": mapped, "canonical_values": {}, "unmapped_source_fields": unmapped,
                       "validation_errors": []})
    output.sort(key=lambda row: (row["source_record_id"], row["id"]))
    document = {"schema_version": NORMALIZED_SCHEMA, "provider_id": provider.provider_id,
                "dataset": manifest["dataset"], "raw_snapshot_id": manifest["snapshot_id"], "records": output}
    _atomic_create(Path(destination), _json(document))
    return document


@dataclass(frozen=True, slots=True)
class ProviderTrustPolicy:
    evidence_class: str = "unknown"
    confidence: float = 0.0
    verification_status: str = "unverified"
    source_type: str = "external_dataset"

    def __post_init__(self) -> None:
        allowed = {"official", "authoritative_structured", "verified_community", "direct_observation", "derived", "inferred", "unknown", "conflicting"}
        if self.evidence_class not in allowed or not 0 <= self.confidence <= 1:
            raise AcquisitionError("invalid provider trust policy")


def assertions_from_normalized(document: Mapping[str, Any], policy: ProviderTrustPolicy,
                               timestamp: str) -> list[dict[str, Any]]:
    """Create candidate v3 assertions; never invoke promotion."""
    _timestamp(timestamp, "timestamp")
    if document.get("schema_version") != NORMALIZED_SCHEMA: raise AcquisitionError("invalid normalized schema version")
    assertions = []
    for record in document.get("records", []):
        subject = _identifier(str(record["source_record_id"]), "source_record_id")
        for field_path, value in sorted(record["source_values"].items()):
            path = field_path if field_path.startswith("/") else f"/{field_path}"
            identity = _json([document["provider_id"], subject, path, value, record["raw_snapshot_id"]])
            aid = "src-" + hashlib.sha256(identity).hexdigest()
            assertions.append({"schema_version": ASSERTION_SCHEMA, "id": aid, "subject_id": subject,
                "path": path, "asserted_value": value, "source_id": document["provider_id"],
                "source_type": policy.source_type, "evidence_class": policy.evidence_class,
                "timestamp": timestamp, "confidence": policy.confidence,
                "verification_status": policy.verification_status, "status": "candidate",
                "notes": f"raw_snapshot_id={record['raw_snapshot_id']}; source_path=/normalized{path}",
                "supersedes": [], "conflicts_with": []})
    return sorted(assertions, key=lambda row: row["id"])


def compare_assertions(previous: Iterable[Mapping[str, Any]], current: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Report additions, removals, and value changes without replacing evidence."""
    def index(rows): return {(r["source_id"], r["subject_id"], r["path"]): r for r in rows}
    old, new = index(previous), index(current); changes, conflicts = [], []
    for key in sorted(old.keys() | new.keys()):
        if key not in old: changes.append({"kind": "added", "current_id": new[key]["id"]})
        elif key not in new: changes.append({"kind": "removed", "previous_id": old[key]["id"]})
        elif old[key]["asserted_value"] != new[key]["asserted_value"]:
            item = {"kind": "changed", "previous_id": old[key]["id"], "current_id": new[key]["id"],
                    "path": key[2], "previous_value": old[key]["asserted_value"], "current_value": new[key]["asserted_value"]}
            changes.append(item); conflicts.append(item)
    return {"changes": changes, "conflicts": conflicts}


class AcquisitionEngine:
    """Coordinates retrieval and run auditing while leaving later stages explicit."""

    def __init__(self, store: RawSnapshotStore, run_root: Path | str = "data/acquisition-runs") -> None:
        self.store = store; self.run_root = Path(run_root); self._providers: dict[str, AcquisitionProvider] = {}

    def register(self, provider: AcquisitionProvider) -> None:
        provider_id = _identifier(provider.provider_id, "provider_id")
        if provider_id in self._providers and self._providers[provider_id] is not provider:
            raise AcquisitionError(f"provider identity collision: {provider_id}")
        self._providers[provider_id] = provider

    def acquire(self, provider_id: str, datasets: str | Sequence[str], *, started_at: str,
                completed_at: str | None = None, parameters: Mapping[str, Any] | None = None,
                run_id: str | None = None, license_reference: str | None = None) -> dict[str, Any]:
        _timestamp(started_at, "started_at"); completed_at = completed_at or started_at; _timestamp(completed_at, "completed_at")
        provider = self._providers.get(provider_id)
        if not provider: raise AcquisitionError(f"provider is not registered: {provider_id}")
        requested = [datasets] if isinstance(datasets, str) else list(datasets)
        for dataset in requested: _identifier(dataset, "dataset")
        rid = run_id or hashlib.sha256(_json([provider_id, requested, dict(parameters or {}), started_at])).hexdigest()
        _identifier(rid, "run_id")
        report = {"schema_version": RUN_SCHEMA, "run_id": rid, "provider_id": provider_id,
                  "requested_datasets": requested, "started_at": started_at, "completed_at": completed_at,
                  "status": "succeeded", "discovered_records": len(provider.discover()),
                  "downloaded_snapshots": [], "unchanged_snapshots": [], "failures": [],
                  "normalization_counts": {}, "assertion_counts": {}, "warnings": [],
                  "report_location": str(self.run_root / rid / "report.json"), "resumable": True}
        for dataset in requested:
            try:
                request = provider.build_request(dataset, parameters or {})
                response = provider.retrieve(request); provider.validate_response(response)
                snapshot = self.store.store(provider_id, request, response, started_at,
                                             license_reference=license_reference)
                target = "unchanged_snapshots" if snapshot.unchanged else "downloaded_snapshots"
                report[target].append({"dataset": dataset, "snapshot_id": snapshot.snapshot_id, "path": str(snapshot.path)})
            except (AcquisitionError, OSError) as error:
                report["failures"].append({"dataset": dataset, "error": str(error)})
        if report["failures"]: report["status"] = "partial" if report["downloaded_snapshots"] or report["unchanged_snapshots"] else "failed"
        path = self.run_root / rid / "report.json"; _atomic_create(path, _json(report))
        return report

    def report(self, run_id: str) -> dict[str, Any]:
        _identifier(run_id, "run_id"); path = self.run_root / run_id / "report.json"
        result = json.loads(path.read_text())
        if result.get("schema_version") != RUN_SCHEMA or result.get("run_id") != run_id:
            raise AcquisitionError("invalid acquisition run report")
        return result
