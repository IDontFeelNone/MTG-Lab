"""Project-specific errors for safe, evidence-preserving ingestion."""
from __future__ import annotations

from typing import Mapping


class IngestionError(RuntimeError):
    """Base error containing concise, non-payload diagnostic context."""

    def __init__(self, message: str, *, context: Mapping[str, str] | None = None) -> None:
        super().__init__(message)
        self.context = dict(context or {})


class UnknownSourceReference(IngestionError): pass
class UnknownAcquisitionTarget(IngestionError): pass
class SourceTargetMismatch(IngestionError): pass
class UnsupportedContentType(IngestionError): pass
class ParserMismatch(IngestionError): pass
class EvidenceStorageError(IngestionError): pass
class HashingError(IngestionError): pass
class ParseFailure(IngestionError): pass
class InvalidEvidencePath(IngestionError): pass
class ConflictingStoredContent(EvidenceStorageError): pass
