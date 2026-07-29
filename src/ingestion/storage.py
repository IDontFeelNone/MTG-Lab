"""Filesystem storage for immutable raw evidence artifacts."""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from .errors import ConflictingStoredContent, EvidenceStorageError, InvalidEvidencePath
from .hashing import hash_bytes, hash_file
from .models import AcquisitionRequest, RawEvidenceArtifact

_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CANONICAL_DATA_ROOT = _PROJECT_ROOT / "data" / "canonical"
_DEFAULT_RAW_EVIDENCE_ROOT = _PROJECT_ROOT / "data" / "raw" / "evidence"


class FileSystemEvidenceStorage:
    """Stores immutable evidence at deterministic, hash-addressed raw-data paths."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root) if root is not None else _DEFAULT_RAW_EVIDENCE_ROOT

    def store_bytes(self, request: AcquisitionRequest, content: bytes) -> RawEvidenceArtifact:
        self._validate_request(request)
        content_hash = hash_bytes(content)
        root = self._safe_root()
        artifact_path = root / request.game / request.product_id / request.source_id / request.acquisition_target_id / content_hash / "evidence.bin"
        self._ensure_within_root(root, artifact_path)
        try:
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            if artifact_path.exists():
                if hash_file(artifact_path) != content_hash:
                    raise ConflictingStoredContent("Stored evidence conflicts with its hash-addressed location", context={"path": str(artifact_path), "content_hash": content_hash})
            else:
                self._write_atomically(artifact_path, content)
        except ConflictingStoredContent:
            raise
        except OSError as error:
            raise EvidenceStorageError("Unable to store raw evidence", context={"path": str(artifact_path)}) from error
        return RawEvidenceArtifact(
            id=content_hash, source_id=request.source_id,
            acquisition_target_id=request.acquisition_target_id, product_id=request.product_id,
            content_type=request.content_type, acquired_at=request.acquired_at,
            content_hash=content_hash, storage_path=artifact_path,
            original_filename=request.original_filename,
        )

    def _safe_root(self) -> Path:
        try:
            root = self._root.resolve()
            if root.is_relative_to(_CANONICAL_DATA_ROOT.resolve()):
                raise InvalidEvidencePath("Raw evidence storage cannot use the canonical data layer", context={"path": str(root)})
            root.mkdir(parents=True, exist_ok=True)
            return root
        except InvalidEvidencePath:
            raise
        except OSError as error:
            raise EvidenceStorageError("Unable to prepare evidence storage", context={"path": str(self._root)}) from error

    @staticmethod
    def _ensure_within_root(root: Path, candidate: Path) -> None:
        if candidate.resolve().is_relative_to(root):
            return
        raise InvalidEvidencePath("Evidence path escapes the configured storage root", context={"path": str(candidate)})

    @staticmethod
    def _write_atomically(path: Path, content: bytes) -> None:
        descriptor, temporary_path = tempfile.mkstemp(prefix=".evidence-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as temporary_file:
                temporary_file.write(content)
            os.replace(temporary_path, path)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)

    @staticmethod
    def _validate_request(request: AcquisitionRequest) -> None:
        for label, value in (
            ("game", request.game), ("product_id", request.product_id),
            ("source_id", request.source_id), ("acquisition_target_id", request.acquisition_target_id),
        ):
            if not _IDENTIFIER.fullmatch(value):
                raise InvalidEvidencePath(f"{label} must be a stable lowercase identifier", context={label: value})
