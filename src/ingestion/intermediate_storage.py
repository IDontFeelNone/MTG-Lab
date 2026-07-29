"""Immutable filesystem storage for validated intermediate artifacts."""
from __future__ import annotations
import json, os, re, tempfile
from pathlib import Path
from typing import Any, Mapping
from validation import SchemaValidationError, validate_document
from .errors import ConflictingStoredContent, EvidenceStorageError, InvalidEvidencePath

_ID=re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_ROOT=Path(__file__).resolve().parents[2]/"data"/"intermediate"

class IntermediateArtifactStorage:
    """Stores parsed and candidate artifacts outside canonical repository data."""
    def __init__(self, root:Path|None=None)->None: self._root=Path(root) if root else _ROOT
    def store_parsed(self, document:Mapping[str,Any])->Path: return self._store("parsed","parsed-record-artifact",document)
    def store_candidates(self, document:Mapping[str,Any])->Path: return self._store("candidates","normalized-candidate-artifact",document)
    def load_parsed(self, product_id:str, source_id:str, target_id:str, artifact_id:str)->dict[str,Any]:
        return self._load("parsed","parsed-record-artifact",product_id,source_id,target_id,artifact_id)
    def load_candidates(self, product_id:str, source_id:str, target_id:str, artifact_id:str)->dict[str,Any]:
        return self._load("candidates","normalized-candidate-artifact",product_id,source_id,target_id,artifact_id)
    def _store(self,kind:str,schema:str,d:Mapping[str,Any])->Path:
        try: validate_document(d,schema)
        except SchemaValidationError as e: raise EvidenceStorageError(str(e)) from e
        p=self._path(kind,d["product_id"],d["source_id"],d["acquisition_target_id"],d["id"])
        raw=(json.dumps(d,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode()
        p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():
            if p.read_bytes()!=raw: raise ConflictingStoredContent("Artifact identifier already stores different content",context={"path":str(p)})
            return p
        fd,tmp=tempfile.mkstemp(prefix=".artifact-",dir=p.parent)
        try:
            with os.fdopen(fd,"wb") as f:f.write(raw)
            os.replace(tmp,p)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        return p
    def _load(self,kind:str,schema:str,product:str,source:str,target:str,artifact:str)->dict[str,Any]:
        p=self._path(kind,product,source,target,artifact)
        try:d=json.loads(p.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError) as e: raise EvidenceStorageError(f"Cannot load artifact: {p}") from e
        try: validate_document(d,schema)
        except SchemaValidationError as e: raise EvidenceStorageError(str(e)) from e
        if d["id"]!=artifact: raise EvidenceStorageError("Artifact identifier does not match path")
        return d
    def _path(self,kind:str,product:str,source:str,target:str,artifact:str)->Path:
        if not all(_ID.fullmatch(x) for x in (kind,product,source,target,artifact)): raise InvalidEvidencePath("Artifact identifiers must be stable lowercase identifiers")
        root=self._root.resolve(); canonical=(Path(__file__).resolve().parents[2]/"data"/"canonical").resolve()
        if root.is_relative_to(canonical): raise InvalidEvidencePath("Intermediate storage cannot use canonical data")
        p=root/kind/product/source/target/f"{artifact}.json"
        if not p.resolve().is_relative_to(root): raise InvalidEvidencePath("Artifact path escapes storage root")
        return p
