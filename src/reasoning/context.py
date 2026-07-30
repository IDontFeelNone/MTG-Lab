"""Deterministic evidence-package assembly over public semantic contracts only."""
import hashlib
import json

from semantic import CanonicalSemanticQueryEngine, SemanticQueryError, SemanticRequest
from .errors import InvalidReasoningRequest, ReasoningSnapshotError
from .models import ReasoningContextRequest, ReasoningContextResult


class ReasoningContextBuilder:
    ANALYTICS = frozenset({"analytics_summary", "dataset_statistics", "provenance_statistics", "validation_statistics"})

    def __init__(self, semantic: CanonicalSemanticQueryEngine): self._semantic = semantic

    def build(self, request: ReasoningContextRequest) -> ReasoningContextResult:
        self._validate(request)
        try: response = self._semantic.execute(request.semantic_request)
        except (SemanticQueryError, ValueError) as error: raise InvalidReasoningRequest(str(error)) from error
        raw = response.to_dict()["result"]
        entities = list(raw if isinstance(raw, list) else [])
        entities = [x for x in entities if self._matches(x, request)]
        entities.sort(key=lambda x: (str(x.get("entity_type", "")), str(x.get("canonical_identity", ""))))
        relationships = self._relationships(entities)
        provenance = {str(x["canonical_identity"]): x.get("provenance_summary", response.to_dict()["provenance_references"].get(str(x["canonical_identity"]), {})) for x in entities}
        evidence = self._evidence(entities, provenance, response.canonical_snapshot_id)
        totals = {"entities": len(entities), "relationships": len(relationships), "evidence": len(evidence)}
        entities = entities[:request.maximum_entities]; relationships = relationships[:request.maximum_relationships]
        evidence = dict(list(sorted(evidence.items()))[:request.maximum_evidence_items])
        omitted = {"entities": totals["entities"]-len(entities), "relationships": totals["relationships"]-len(relationships), "evidence": totals["evidence"]-len(evidence)}
        selected_ids = {x["canonical_identity"] for x in entities}; provenance = {k:v for k,v in provenance.items() if k in selected_ids}
        analytics, analytics_id = [], None
        if request.include_analytics:
            try: report = self._semantic.execute(SemanticRequest(request.analytics_operation, {}))
            except (SemanticQueryError, ValueError) as error: raise InvalidReasoningRequest(str(error)) from error
            if report.canonical_snapshot_id != response.canonical_snapshot_id: raise ReasoningSnapshotError("semantic and analytics canonical snapshots differ")
            analytics, analytics_id = [report.to_dict()["result"]], report.analytics_snapshot_id
        validation = {x["canonical_identity"]: x.get("uncertainty") for x in entities}
        confidence = {x["canonical_identity"]: x.get("confidence") for x in entities}
        truncation = {"occurred": any(omitted.values()), "policy": request.truncation_policy, "limits": {"entities": request.maximum_entities, "relationships": request.maximum_relationships, "evidence": request.maximum_evidence_items}}
        warnings = tuple(f"{k} truncated: {v} omitted" for k,v in sorted(omitted.items()) if v)
        content = {"canonical_snapshot_id": response.canonical_snapshot_id, "analytics_snapshot_id": analytics_id,
                   "request": request.to_dict(), "entities": entities, "relationships": relationships, "analytics": analytics,
                   "provenance": provenance, "evidence": evidence, "omitted": omitted, "truncation": truncation, "warnings": warnings}
        identity = "sha256:" + hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        return ReasoningContextResult(identity, response.canonical_snapshot_id, request.to_dict(), entities, relationships, analytics,
            provenance, evidence, validation, confidence, omitted, truncation, warnings, analytics_snapshot_id=analytics_id)

    def _validate(self, r):
        if r.semantic_request.operation not in self._semantic.OPERATIONS: raise InvalidReasoningRequest(f"unsupported semantic operation: {r.semantic_request.operation}")
        for name in ("maximum_entities", "maximum_relationships", "maximum_evidence_items"):
            value=getattr(r,name)
            if isinstance(value,bool) or not isinstance(value,int) or value < 0: raise InvalidReasoningRequest(f"{name} must be a non-negative integer")
        if r.truncation_policy != "canonical-order-prefix": raise InvalidReasoningRequest("unsupported truncation policy")
        lo, hi = r.minimum_confidence, r.maximum_confidence
        if any(x is not None and (isinstance(x,bool) or not isinstance(x,(int,float)) or not 0 <= x <= 1) for x in (lo,hi)) or (lo is not None and hi is not None and lo > hi): raise InvalidReasoningRequest("confidence bounds must satisfy 0 <= minimum <= maximum <= 1")
        if r.include_analytics and r.analytics_operation not in self.ANALYTICS: raise InvalidReasoningRequest("unsupported analytics operation")
        if r.semantic_request.operation.startswith("analytics_") or r.semantic_request.operation.endswith("_statistics"): raise InvalidReasoningRequest("primary semantic request must select entities")

    @staticmethod
    def _matches(x, r):
        prov=x.get("provenance_summary",{}); datasets={d.get("dataset_id") for d in prov.get("dataset_identity",[]) if isinstance(d,dict)}; sources=set(prov.get("source_ids",[]))
        if r.requested_entity_types and x.get("entity_type") not in r.requested_entity_types: return False
        if r.requested_datasets and not datasets.intersection(r.requested_datasets): return False
        if r.requested_provenance_sources and not sources.intersection(r.requested_provenance_sources): return False
        uncertainty=str(x.get("uncertainty","unknown"))
        if r.validation_states and not any(uncertainty.startswith(s) for s in r.validation_states): return False
        confidence=x.get("confidence")
        if (r.minimum_confidence is not None or r.maximum_confidence is not None) and confidence is None: return False
        return (r.minimum_confidence is None or confidence >= r.minimum_confidence) and (r.maximum_confidence is None or confidence <= r.maximum_confidence)

    @staticmethod
    def _relationships(entities):
        found=[]
        for x in entities:
            for key,value in sorted(x.get("canonical_values",{}).items()):
                if key.endswith("_id") and isinstance(value,str): found.append({"relationship_type":key,"source":x["canonical_identity"],"target":value,"status":x.get("lifecycle_status","unknown")})
        return sorted(found,key=lambda x:(x["relationship_type"],x["source"],x["target"]))

    @staticmethod
    def _evidence(entities, provenance, snapshot):
        result={}
        for x in entities:
            identity=str(x["canonical_identity"]); p=provenance.get(identity,{})
            assertions=p.get("evidence_assertions",[]) or []
            if not assertions: assertions=[{"source_id":s} for s in p.get("source_ids",[])]
            for index,a in enumerate(assertions):
                eid=f"{identity}#{index}"
                result[eid]={"canonical_identity":identity,"entity_type":x.get("entity_type"),"source_dataset":p.get("dataset_identity",[]),"provenance":a,"validation_state":x.get("uncertainty","unknown"),"confidence":x.get("confidence"),"canonical_snapshot_id":snapshot,"lifecycle_status":x.get("lifecycle_status","unknown")}
        return result
