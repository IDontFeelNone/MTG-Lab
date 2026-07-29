"""Immutable models for parsed and normalized intermediate artifacts."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
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
    def to_dict(self)->dict[str,Any]: return asdict(self)

@dataclass(frozen=True,slots=True)
class ParsedArtifact:
    id:str; product_id:str; source_id:str; acquisition_target_id:str; raw_evidence_hash:str
    parser_id:str; parser_version:str; parsed_at:str; input_content_type:str; status:ArtifactStatus
    records:tuple[ParsedRecord,...]=(); errors:tuple[str,...]=(); warnings:tuple[str,...]=(); artifact_version:str="1"
    def to_dict(self)->dict[str,Any]:
        d=asdict(self);d["schema_version"]="v1";d["parse_status"]=d.pop("status");d["record_count"]=len(self.records);return d

@dataclass(frozen=True,slots=True)
class FieldProvenance:
    field_path:str; value_origin:str; source_id:str; acquisition_target_id:str; raw_evidence_hash:str
    parsed_artifact_id:str; parsed_record_id:str; transformation_id:str; transformation_version:str
    provenance_classification:str; confidence:float; notes:str|None=None
    def to_dict(self)->dict[str,Any]:
        return {k:v for k,v in asdict(self).items() if v is not None}

@dataclass(frozen=True,slots=True)
class NormalizedCandidate:
    id:str; entity_type:str; payload:Mapping[str,Any]; parsed_record_ids:tuple[str,...]
    field_provenance:tuple[FieldProvenance,...]; confidence:float
    validation_state:CandidateValidationState=CandidateValidationState.UNVALIDATED
    errors:tuple[str,...]=(); warnings:tuple[str,...]=()
    def to_dict(self)->dict[str,Any]:
        d=asdict(self);d["validation_state"]=self.validation_state.value;return d

@dataclass(frozen=True,slots=True)
class NormalizedCandidateArtifact:
    id:str; product_id:str; source_id:str; acquisition_target_id:str; raw_evidence_hash:str; parsed_artifact_id:str
    normalizer_id:str; normalizer_version:str; normalized_at:str; candidate_type:str; status:ArtifactStatus
    candidates:tuple[NormalizedCandidate,...]=(); errors:tuple[str,...]=(); warnings:tuple[str,...]=(); artifact_version:str="1"
    def to_dict(self)->dict[str,Any]:
        d=asdict(self);d["schema_version"]="v1";d["normalization_status"]=d.pop("status");d["candidate_count"]=len(self.candidates);return d

@dataclass(frozen=True,slots=True)
class CandidateValidationResult:
    state:CandidateValidationState; errors:tuple[str,...]=(); warnings:tuple[str,...]=()

@dataclass(frozen=True,slots=True)
class CandidateNormalizationResult:
    artifact:NormalizedCandidateArtifact|None; status:ArtifactStatus; errors:tuple[str,...]=(); warnings:tuple[str,...]=()
