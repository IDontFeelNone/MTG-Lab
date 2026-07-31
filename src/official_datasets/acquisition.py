"""Fail-closed download, verification, and non-canonical registration."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Callable
from urllib.request import Request, urlopen

from evidence import (AcquisitionMetadata, EvidenceArtifact, EvidenceDataset,
                      ReferenceDatasetRegistry)
from providers.mtgjson.provider import ENTITY_TYPES, LICENSE
from providers.mtgjson.parser import parse_dataset

from .configuration import DatasetDefinition, definitions, get_definition


class AcquisitionError(RuntimeError):
    """An artifact did not pass every required acquisition gate."""


class OfficialDatasetAcquisition:
    def __init__(self, data_root: Path | str = "data", *, opener: Callable[..., Any] = urlopen,
                 now: Callable[[], datetime] | None = None) -> None:
        self.data_root = Path(data_root)
        self.local_root = self.data_root / "local"
        self.opener = opener
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.registry = ReferenceDatasetRegistry(self.local_root / "reference-datasets" / "registry")

    def _paths(self, definition: DatasetDefinition) -> tuple[Path, Path, Path]:
        directory = self.local_root / definition.local_storage_path
        artifact = directory / definition.expected_filename
        return artifact, artifact.with_suffix(artifact.suffix + ".part"), directory / "acquisition.json"

    @staticmethod
    def _digest(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _remote_checksum(self, definition: DatasetDefinition) -> str | None:
        if not definition.checksum_url:
            return None
        try:
            with self.opener(Request(definition.checksum_url, headers={"User-Agent": "mtg-lab/1"})) as response:
                value = response.read().decode("ascii", errors="strict")
        except Exception as error:
            raise AcquisitionError(f"checksum acquisition failed: {error}") from error
        match = re.search(r"\b[0-9a-fA-F]{64}\b", value)
        if not match:
            raise AcquisitionError("checksum response does not contain a SHA-256 digest")
        return match.group(0).lower()

    def download(self, name: str) -> dict[str, Any]:
        definition = get_definition(name)
        if definition.expected_compression != "none":
            raise AcquisitionError(f"unsupported configured compression: {definition.expected_compression}")
        artifact, partial, _ = self._paths(definition)
        if artifact.exists():
            result = self.verify(name)
            if not result["valid"]:
                raise AcquisitionError("existing artifact failed verification: " + "; ".join(result["errors"]))
            return {**result, "status": "already_downloaded", "resumed": False}
        artifact.parent.mkdir(parents=True, exist_ok=True)
        offset = partial.stat().st_size if partial.exists() else 0
        request = Request(definition.official_url, headers={"User-Agent": "mtg-lab/1"})
        if offset:
            request.add_header("Range", f"bytes={offset}-")
        try:
            with self.opener(request) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                append = bool(offset and status == 206)
                if status not in (200, 206):
                    raise AcquisitionError(f"download returned HTTP status {status}")
                with partial.open("ab" if append else "wb") as output:
                    while True:
                        block = response.read(1024 * 1024)
                        if not block:
                            break
                        output.write(block)
                    output.flush()
                    os.fsync(output.fileno())
        except AcquisitionError:
            raise
        except Exception as error:
            raise AcquisitionError(f"download interrupted: {error}") from error
        if partial.stat().st_size <= 0:
            raise AcquisitionError("downloaded artifact is empty")
        expected = self._remote_checksum(definition)
        actual = self._digest(partial)
        if expected is not None and actual != expected:
            raise AcquisitionError("downloaded artifact SHA-256 does not match official checksum")
        try:
            document = parse_dataset(partial)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise AcquisitionError(f"downloaded artifact validation failed: {error}") from error
        if not document["meta"]["version"].startswith(definition.schema_version.removesuffix("x")):
            raise AcquisitionError("downloaded artifact schema does not match configured schema version")
        partial.replace(artifact)
        return self._register(definition, artifact, document, actual, expected, resumed=bool(offset))

    def _register(self, definition: DatasetDefinition, artifact: Path, document: dict[str, Any],
                  digest: str, expected: str | None, *, resumed: bool) -> dict[str, Any]:
        timestamp = self.now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        artifact_id = f"{definition.provider}-all-printings-{digest[:16]}"
        dataset_id = f"{definition.name}-{digest[:16]}"
        acquisition = AcquisitionMetadata(timestamp, document["meta"]["date"], "official-url-download",
                                          definition.official_url)
        artifact_record = EvidenceArtifact(definition.provider, dataset_id, artifact_id, digest,
                                           "application/json", artifact.stat().st_size, acquisition, LICENSE)
        dataset_record = EvidenceDataset(definition.provider, dataset_id, document["meta"]["version"],
                                         timestamp, LICENSE,
                                         (("official_url", definition.official_url),
                                          ("local_path", str(artifact))), ENTITY_TYPES,
                                         (artifact_id,))
        self.registry.register_artifact(artifact_record)
        self.registry.register_dataset(dataset_record)
        manifest = {"schema_version": "1.0.0", "definition": definition.to_dict(),
                    "artifact": artifact_record.to_dict(), "dataset": dataset_record.to_dict(),
                    "official_checksum": expected}
        manifest_path = self._paths(definition)[2]
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {"dataset": definition.name, "status": "downloaded", "valid": True,
                "resumed": resumed, "path": str(artifact), "byte_length": artifact.stat().st_size,
                "sha256": digest, "schema_version": document["meta"]["version"],
                "checksum_verified": expected is not None, "canonical_write": False}

    def verify(self, name: str) -> dict[str, Any]:
        definition = get_definition(name)
        artifact, _, manifest_path = self._paths(definition)
        errors: list[str] = []
        digest = None
        document = None
        if not artifact.is_file() or artifact.stat().st_size <= 0:
            errors.append("artifact is missing or empty")
        else:
            digest = self._digest(artifact)
            try:
                document = parse_dataset(artifact)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                errors.append(f"JSON or schema validation failed: {error}")
        manifest = None
        if not manifest_path.is_file():
            errors.append("acquisition registration is missing")
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest.get("definition") != definition.to_dict():
                    errors.append("registered dataset definition does not match configuration")
                if digest and manifest.get("artifact", {}).get("sha256") != digest:
                    errors.append("artifact SHA-256 does not match registration")
                if artifact.exists() and manifest.get("artifact", {}).get("byte_length") != artifact.stat().st_size:
                    errors.append("artifact file size does not match registration")
                expected = manifest.get("official_checksum")
                if expected and digest != expected:
                    errors.append("artifact SHA-256 does not match official checksum")
                if document and manifest.get("dataset", {}).get("dataset_version") != document["meta"]["version"]:
                    errors.append("schema metadata does not match registration")
                if document and not document["meta"]["version"].startswith(
                        definition.schema_version.removesuffix("x")):
                    errors.append("schema metadata does not match configured schema version")
            except (OSError, ValueError) as error:
                errors.append(f"registration is invalid: {error}")
        registry_result = self.registry.validate()
        errors.extend(registry_result["errors"])
        return {"dataset": name, "valid": not errors, "status": "ready" if not errors else "invalid",
                "path": str(artifact), "byte_length": artifact.stat().st_size if artifact.exists() else 0,
                "sha256": digest, "errors": sorted(set(errors)), "canonical_write": False}

    def status(self, name: str) -> dict[str, Any]:
        definition = get_definition(name)
        artifact, partial, _ = self._paths(definition)
        if artifact.exists():
            return self.verify(name)
        return {"dataset": name, "status": "partial" if partial.exists() else "not_downloaded",
                "valid": False, "path": str(artifact), "partial_bytes": partial.stat().st_size if partial.exists() else 0,
                "canonical_write": False}

    def list(self) -> dict[str, Any]:
        return {"schema_version": "1.0.0", "datasets": [
            {**definition.to_dict(), "status": self.status(definition.name)["status"]}
            for definition in definitions()], "canonical_write": False}
