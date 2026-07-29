"""Normalization orchestration for validated intermediate artifacts."""
from __future__ import annotations
from dataclasses import replace
from .candidate_validation import validate_candidate_artifact
from .candidates import ArtifactStatus, CandidateNormalizationResult, CandidateValidationState, ParsedArtifact
from .errors import ParserMismatch
from .intermediate_storage import IntermediateArtifactStorage
from .normalizers import CandidateNormalizer

class CandidateNormalizationService:
    def __init__(self,storage:IntermediateArtifactStorage,normalizers:tuple[CandidateNormalizer,...]=())->None:
        self._storage=storage;self._normalizers=normalizers
    def normalize(self,parsed:ParsedArtifact,*,normalizer:CandidateNormalizer|None=None)->CandidateNormalizationResult:
        parsed_document=parsed.to_dict(); self._storage.store_parsed(parsed_document)
        selected=normalizer or next((n for n in self._normalizers if n.supports(parsed)),None)
        if selected is None or not selected.supports(parsed): raise ParserMismatch("Normalizer does not support parsed record types")
        try: result=selected.normalize(parsed)
        except Exception as e:return CandidateNormalizationResult(None,ArtifactStatus.FAILED,(f"{type(e).__name__}: {e}",))
        if result.artifact is None:return result
        artifact=result.artifact
        validation=validate_candidate_artifact(artifact.to_dict(),parsed_document)
        if validation.state is CandidateValidationState.INVALID:
            return CandidateNormalizationResult(artifact,ArtifactStatus.FAILED,validation.errors,result.warnings)
        validated=replace(artifact,candidates=tuple(replace(c,validation_state=CandidateValidationState.VALID) for c in artifact.candidates))
        self._storage.store_candidates(validated.to_dict())
        return CandidateNormalizationResult(validated,result.status,result.errors,result.warnings)
