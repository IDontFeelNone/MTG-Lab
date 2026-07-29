"""Generic normalization contract for parsed intermediate records."""
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Collection
from .candidates import CandidateNormalizationResult, ParsedArtifact

class CandidateNormalizer(ABC):
    """Transforms compatible parsed artifacts into non-canonical candidates."""
    normalizer_id: str
    normalizer_version: str
    supported_record_types: Collection[str]
    output_candidate_type: str

    def supports(self, artifact: ParsedArtifact) -> bool:
        return all(record.record_type in self.supported_record_types for record in artifact.records)

    @abstractmethod
    def normalize(self, artifact: ParsedArtifact) -> CandidateNormalizationResult:
        """Return structured candidates; implementations must not promote canonical data."""
