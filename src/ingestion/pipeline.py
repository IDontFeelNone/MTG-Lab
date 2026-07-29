"""Generic orchestration from acquired bytes to parsed intermediate artifacts."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from repository import SourceLoadError, load_acquisition_manifest, load_source_record

from .errors import (
    ParserMismatch,
    SourceTargetMismatch,
    UnknownAcquisitionTarget,
    UnknownSourceReference,
    UnsupportedContentType,
)
from .models import AcquisitionRequest, ParseResult, PipelineResult, TransformationStatus
from .parsers.base import EvidenceParser
from .storage import FileSystemEvidenceStorage


class IngestionPipeline:
    """Validates source references, stores immutable evidence, then invokes a parser."""

    def __init__(
        self,
        evidence_storage: FileSystemEvidenceStorage,
        parsers: Iterable[EvidenceParser] = (),
        *,
        games_root: Path | None = None,
    ) -> None:
        self._storage = evidence_storage
        self._parsers = tuple(parsers)
        self._games_root = games_root

    def ingest(
        self,
        request: AcquisitionRequest,
        content: bytes,
        *,
        parser: EvidenceParser | None = None,
    ) -> PipelineResult:
        self._verify_references(request)
        evidence = self._storage.store_bytes(request, content)
        selected_parser = parser or self._select_parser(request.content_type)
        if not selected_parser.supports(request.content_type):
            raise ParserMismatch(
                "Parser does not support the requested content type",
                context={"parser_id": selected_parser.parser_id, "content_type": request.content_type},
            )
        try:
            parse_result = selected_parser.parse(content, evidence)
        except Exception as error:
            parse_result = ParseResult(
                parser_id=selected_parser.parser_id,
                parser_version=selected_parser.parser_version,
                status=TransformationStatus.FAILED,
                errors=(f"{type(error).__name__}: {error}",),
            )
        return PipelineResult(
            request=request,
            evidence=evidence,
            parse_result=parse_result,
            errors=parse_result.errors,
            warnings=parse_result.warnings,
        )

    def _verify_references(self, request: AcquisitionRequest) -> None:
        try:
            load_source_record(
                request.game, request.product_id, request.source_id, games_root=self._games_root
            )
        except SourceLoadError as error:
            raise UnknownSourceReference(
                "Unknown source reference",
                context={"source_id": request.source_id, "product_id": request.product_id},
            ) from error
        try:
            manifest = load_acquisition_manifest(
                request.game,
                request.product_id,
                request.acquisition_target_id,
                games_root=self._games_root,
            )
        except SourceLoadError as error:
            raise UnknownAcquisitionTarget(
                "Unknown acquisition target",
                context={"target_id": request.acquisition_target_id, "product_id": request.product_id},
            ) from error
        if request.source_id not in manifest["source_ids"]:
            raise SourceTargetMismatch(
                "Acquisition target does not reference the requested source",
                context={"source_id": request.source_id, "target_id": request.acquisition_target_id},
            )
        expected_type = manifest.get("expected_content_type")
        if expected_type is not None and request.content_type != expected_type:
            raise UnsupportedContentType(
                "Requested content type does not match acquisition target",
                context={"requested": request.content_type, "expected": expected_type},
            )

    def _select_parser(self, content_type: str) -> EvidenceParser:
        for parser in self._parsers:
            if parser.supports(content_type):
                return parser
        raise UnsupportedContentType(
            "No parser supports the requested content type",
            context={"content_type": content_type},
        )
