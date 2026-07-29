"""Evidence-preserving ingestion infrastructure for MTG Lab."""
from .errors import (
    ConflictingStoredContent,
    EvidenceStorageError,
    HashingError,
    IngestionError,
    InvalidEvidencePath,
    ParserMismatch,
    SourceTargetMismatch,
    UnknownAcquisitionTarget,
    UnknownSourceReference,
    UnsupportedContentType,
)
from .hashing import hash_bytes, hash_file
from .card_printing_wave import CardPrintingWave, ingest_card_printing_wave
from .models import (
    AcquisitionRequest,
    ArtifactValidationResult,
    NormalizationResult,
    ParseResult,
    PipelineResult,
    RawEvidenceArtifact,
    TransformationStatus,
    ValidationStatus,
)
from .pipeline import IngestionPipeline
from .storage import FileSystemEvidenceStorage

__all__ = [
    "AcquisitionRequest", "ArtifactValidationResult", "CardPrintingWave", "ConflictingStoredContent",
    "EvidenceStorageError", "FileSystemEvidenceStorage", "HashingError",
    "IngestionError", "IngestionPipeline", "InvalidEvidencePath",
    "NormalizationResult", "ParseResult", "ParserMismatch", "PipelineResult",
    "RawEvidenceArtifact", "SourceTargetMismatch", "TransformationStatus",
    "UnknownAcquisitionTarget", "UnknownSourceReference", "UnsupportedContentType",
    "ValidationStatus", "hash_bytes", "hash_file", "ingest_card_printing_wave",
]
