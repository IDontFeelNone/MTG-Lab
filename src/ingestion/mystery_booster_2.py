"""Mystery Booster 2 parsing and normalization for the official product page."""
from __future__ import annotations

from html.parser import HTMLParser

from .candidates import (
    ArtifactStatus,
    CandidateNormalizationResult,
    FieldProvenance,
    NormalizedCandidate,
    NormalizedCandidateArtifact,
    ParsedArtifact,
    ParsedRecord,
)
from .models import ParseResult, RawEvidenceArtifact, TransformationStatus
from .normalizers import CandidateNormalizer
from .parsers import EvidenceParser

PRODUCT_ID = "mystery_booster_2"
SOURCE_ID = "official_product_page"
TARGET_ID = "mystery_booster_2_product_overview"
RECORD_TYPE = "mystery_booster_2.product_overview"


class _ProductPageHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title_parts: list[str] = []
        self.open_graph_title: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "title":
            self.in_title = True
        if tag.casefold() != "meta":
            return
        attributes = {name.casefold(): value for name, value in attrs}
        if attributes.get("property", "").casefold() == "og:title":
            self.open_graph_title = attributes.get("content")

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


class MysteryBooster2ProductPageParser(EvidenceParser):
    """Extracts only explicit product-page title evidence; it makes no domain inferences."""

    parser_id = "mystery_booster_2.product_page"
    parser_version = "1"
    supported_content_types = ("text/html",)

    def parse(self, content: bytes, evidence: RawEvidenceArtifact) -> ParseResult:
        artifact = self.parse_artifact(content, evidence)
        return ParseResult(
            parser_id=self.parser_id,
            parser_version=self.parser_version,
            status={
                ArtifactStatus.SUCCEEDED: TransformationStatus.SUCCEEDED,
                ArtifactStatus.PARTIAL: TransformationStatus.SUCCEEDED,
                ArtifactStatus.FAILED: TransformationStatus.FAILED,
            }[artifact.status],
            records=tuple(record.to_dict() for record in artifact.records),
            errors=artifact.errors,
            warnings=artifact.warnings,
        )

    def parse_artifact(self, content: bytes, evidence: RawEvidenceArtifact) -> ParsedArtifact:
        self._verify_evidence(evidence)
        artifact_id = f"mb2-product-overview-{evidence.content_hash[:16]}"
        common = dict(
            id=artifact_id,
            product_id=evidence.product_id,
            source_id=evidence.source_id,
            acquisition_target_id=evidence.acquisition_target_id,
            raw_evidence_hash=evidence.content_hash,
            parser_id=self.parser_id,
            parser_version=self.parser_version,
            parsed_at=evidence.acquired_at,
            input_content_type=evidence.content_type,
        )
        try:
            document = content.decode("utf-8", errors="strict")
            parser = _ProductPageHTMLParser()
            parser.feed(document)
            parser.close()
        except (UnicodeDecodeError, ValueError) as error:
            return ParsedArtifact(
                **common,
                status=ArtifactStatus.FAILED,
                errors=(f"Invalid HTML evidence: {type(error).__name__}",),
            )

        title = " ".join("".join(parser.title_parts).split()) or None
        fields = {"document_title": title, "open_graph_title": parser.open_graph_title}
        present_fields = {key: value for key, value in fields.items() if value}
        if not present_fields:
            return ParsedArtifact(
                **common,
                status=ArtifactStatus.FAILED,
                errors=("Product page contains no supported title fields",),
            )
        missing = tuple(f"Missing {name.replace('_', ' ')}" for name, value in fields.items() if not value)
        record = ParsedRecord(
            id=f"mb2-product-overview-record-{evidence.content_hash[:16]}",
            record_type=RECORD_TYPE,
            raw_fields=present_fields,
            source_location="HTML head",
            source_excerpt=present_fields,
            warnings=missing,
        )
        return ParsedArtifact(
            **common,
            status=ArtifactStatus.PARTIAL if missing else ArtifactStatus.SUCCEEDED,
            records=(record,),
            warnings=missing,
        )

    @staticmethod
    def _verify_evidence(evidence: RawEvidenceArtifact) -> None:
        expected = (PRODUCT_ID, SOURCE_ID, TARGET_ID, "text/html")
        actual = (
            evidence.product_id,
            evidence.source_id,
            evidence.acquisition_target_id,
            evidence.content_type,
        )
        if actual != expected:
            raise ValueError("Evidence does not belong to the approved Mystery Booster 2 target")


class MysteryBooster2ProductOverviewNormalizer(CandidateNormalizer):
    """Normalizes explicit official titles into a reviewable product candidate."""

    normalizer_id = "mystery_booster_2.product_overview"
    normalizer_version = "1"
    supported_record_types = (RECORD_TYPE,)
    output_candidate_type = "product"

    def normalize(self, artifact: ParsedArtifact) -> CandidateNormalizationResult:
        if artifact.status is ArtifactStatus.FAILED or not artifact.records:
            return CandidateNormalizationResult(
                artifact=None,
                status=ArtifactStatus.FAILED,
                errors=("No parsed product overview is available",),
            )
        record = artifact.records[0]
        title_field = "open_graph_title" if record.raw_fields.get("open_graph_title") else "document_title"
        title = str(record.raw_fields[title_field]).strip()
        name_provenance = FieldProvenance(
            field_path="name",
            value_origin=title_field,
            source_id=artifact.source_id,
            acquisition_target_id=artifact.acquisition_target_id,
            raw_evidence_hash=artifact.raw_evidence_hash,
            parsed_artifact_id=artifact.id,
            parsed_record_id=record.id,
            transformation_id=self.normalizer_id,
            transformation_version=self.normalizer_version,
            provenance_classification="official",
            confidence=1.0,
            notes="Copied verbatim after trimming surrounding whitespace.",
        )
        identifier_provenance = FieldProvenance(
            field_path="id",
            value_origin="acquisition_target.product_id",
            source_id=artifact.source_id,
            acquisition_target_id=artifact.acquisition_target_id,
            raw_evidence_hash=artifact.raw_evidence_hash,
            parsed_artifact_id=artifact.id,
            parsed_record_id=record.id,
            transformation_id=self.normalizer_id,
            transformation_version=self.normalizer_version,
            provenance_classification="internal",
            confidence=1.0,
            notes="Copied from the approved acquisition target product identifier.",
        )
        candidate = NormalizedCandidate(
            id=f"mb2-product-candidate-{artifact.raw_evidence_hash[:16]}",
            entity_type="product",
            payload={"id": PRODUCT_ID, "name": title},
            parsed_record_ids=(record.id,),
            field_provenance=(identifier_provenance, name_provenance),
            confidence=1.0,
            warnings=record.warnings,
        )
        normalized = NormalizedCandidateArtifact(
            id=f"mb2-product-candidates-{artifact.raw_evidence_hash[:16]}",
            product_id=artifact.product_id,
            source_id=artifact.source_id,
            acquisition_target_id=artifact.acquisition_target_id,
            raw_evidence_hash=artifact.raw_evidence_hash,
            parsed_artifact_id=artifact.id,
            normalizer_id=self.normalizer_id,
            normalizer_version=self.normalizer_version,
            normalized_at=artifact.parsed_at,
            candidate_type=self.output_candidate_type,
            status=artifact.status,
            candidates=(candidate,),
            warnings=artifact.warnings,
        )
        return CandidateNormalizationResult(normalized, artifact.status, warnings=artifact.warnings)
