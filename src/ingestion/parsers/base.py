"""Generic parser interface for acquired evidence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection

from ..models import ParseResult, RawEvidenceArtifact


class EvidenceParser(ABC):
    """Parses a supported raw-evidence format into traceable intermediate records."""

    parser_id: str
    parser_version: str
    supported_content_types: Collection[str]

    def supports(self, content_type: str) -> bool:
        return content_type in self.supported_content_types

    @abstractmethod
    def parse(self, content: bytes, evidence: RawEvidenceArtifact) -> ParseResult:
        """Return a structured result; parsers must not write canonical records."""
