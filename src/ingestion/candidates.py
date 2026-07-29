"""Immutable models for parsed and normalized intermediate artifacts."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

class ArtifactStatus(StrEnum):
    SUCCEEDED="succeeded"; PARTIAL="partial"; FAILED="failed"
class CandidateValidationState(StrEnum):
    UNVALIDATED="unvalidated"; VALID="valid"; INVALID="invalid"; REQUIRES_REVIEW="requires_review"

@dataclass(frozen=True,slots=True)
class ParsedRecord:
    id:str; record_type:str; raw_fields:Mapping[str,Any]; source_location:str|int|None=None
    source_excerpt:Mapping[str,Any]|None=None; errors:tuple[str,...]=(); warnings:tuple[str,...]=()
    def to_dict(self)->dict[str,Any]:
        return {"id":self.id,"record_type":self.record_type,"raw_fields":deepcopy(self.raw_fields),
                "source_location":self.source_location,"source_excerpt":deepcopy(self.source_excerpt),
                "errors":list(self.errors),"warnings":list(self.warnings)}

@dataclass(frozen=True,slots=True)
class ParsedArtifact:
    id:str; product_id:str; source_id:str; acquisition_target_id:str; raw_evidence_hash:str
    parser_id:str; parser_version:str; parsed_at:str; input_content_type:str; status:ArtifactStatus
    records:tuple[ParsedRecord,...]=(); errors:tuple[str,...]=(); warnings:tuple[str,...]=(); artifact_version:str="1"
    def to_dict(self)->dict[str,Any]:
        return {"id":self.id,"schema_version":"v1","artifact_version":self.artifact_version,
                "product_id":self.product_id,"source_id":self.source_id,"acquisition_target_id":self.acquisition_target_id,
                "raw_evidence_hash":self.raw_evidence_hash,"parser_id":self.parser_id,"parser_version":self.parser_version,
                "parsed_at":self.parsed_at,"input_content_type":self.input_content_type,"parse_status":self.status.value,
                "record_count":len(self.records),"records":[record.to_dict() for record in self.records],
                "errors":list(self.errors),"warnings":list(self.warnings)}

@dataclass(frozen=True,slots=True)
class FieldProvenance:
    field_path:str; value_origin:str; source_id:str; acquisition_target_id:str; raw_evidence_hash:str
    parsed_artifact_id:str; parsed_record_id:str; transformation_id:str; transformation_version:str
    provenance_classification:str; confidence:float; notes:str|None=None
    def to_dict(self)->dict[str,Any]:
        d={"field_path":self.field_path,"value_origin":self.value_origin,"source_id":self.source_id,
           "acquisition_target_id":self.acquisition_target_id,"raw_evidence_hash":self.raw_evidence_hash,
           "parsed_artifact_id":self.parsed_artifact_id,"parsed_record_id":self.parsed_record_id,
           "transformation_id":self.transformation_id,"transformation_version":self.transformation_version,
           "provenance_classification":self.provenance_classification,"confidence":self.confidence}
        if self.notes is not None:d["notes"]=self.notes
        return d

@dataclass(frozen=True,slots=True)
class NormalizedCandidate:
    id:str; entity_type:str; payload:Mapping[str,Any]; parsed_record_ids:tuple[str,...]
    field_provenance:tuple[FieldProvenance,...]; confidence:float
    validation_state:CandidateValidationState=CandidateValidationState.UNVALIDATED
    errors:tuple[str,...]=(); warnings:tuple[str,...]=()
    def to_dict(self)->dict[str,Any]:
        return {"id":self.id,"entity_type":self.entity_type,"payload":deepcopy(self.payload),
                "parsed_record_ids":list(self.parsed_record_ids),
                "field_provenance":[provenance.to_dict() for provenance in self.field_provenance],
                "confidence":self.confidence,"validation_state":self.validation_state.value,
                "errors":list(self.errors),"warnings":list(self.warnings)}

@dataclass(frozen=True,slots=True)
class NormalizedCandidateArtifact:
    id:str; product_id:str; source_id:str; acquisition_target_id:str; raw_evidence_hash:str; parsed_artifact_id:str
    normalizer_id:str; normalizer_version:str; normalized_at:str; candidate_type:str; status:ArtifactStatus
    candidates:tuple[NormalizedCandidate,...]=(); errors:tuple[str,...]=(); warnings:tuple[str,...]=(); artifact_version:str="1"
    def to_dict(self)->dict[str,Any]:
        return {"id":self.id,"schema_version":"v1","artifact_version":self.artifact_version,
                "product_id":self.product_id,"source_id":self.source_id,"acquisition_target_id":self.acquisition_target_id,
                "raw_evidence_hash":self.raw_evidence_hash,"parsed_artifact_id":self.parsed_artifact_id,
                "normalizer_id":self.normalizer_id,"normalizer_version":self.normalizer_version,
                "normalized_at":self.normalized_at,"candidate_type":self.candidate_type,
                "normalization_status":self.status.value,"candidate_count":len(self.candidates),
                "candidates":[candidate.to_dict() for candidate in self.candidates],
                "errors":list(self.errors),"warnings":list(self.warnings)}

@dataclass(frozen=True,slots=True)
class CandidateValidationResult:
    state:CandidateValidationState; errors:tuple[str,...]=(); warnings:tuple[str,...]=()

@dataclass(frozen=True,slots=True)
class CandidateNormalizationResult:
    artifact:NormalizedCandidateArtifact|None; status:ArtifactStatus; errors:tuple[str,...]=(); warnings:tuple[str,...]=()
