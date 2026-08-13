"""Immutable, versioned, game-neutral Decision Intelligence contracts."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping

STATES = frozenset({"known", "unknown", "incomplete", "unsupported"})


def freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): freeze(v) for k, v in sorted(value.items())})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numbers are not deterministic JSON values")
    if isinstance(value, (str, int, float, bool, type(None))): return value
    raise TypeError(f"unsupported contract value: {type(value).__name__}")


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping): return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, tuple): return [thaw(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(thaw(value), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def identity(prefix: str, value: Any) -> str:
    return prefix + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip(): raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    source_identity: str
    content_digest: str
    recorded_at: str | None = None
    locator: str | None = None

    def __post_init__(self):
        for n in ("evidence_id", "source_identity", "content_digest"): _text(getattr(self, n), n)
        if not self.content_digest.startswith("sha256:"): raise ValueError("content_digest must be sha256-prefixed")
    def to_dict(self): return {k:v for k,v in {"evidence_id":self.evidence_id,"source_identity":self.source_identity,"content_digest":self.content_digest,"recorded_at":self.recorded_at,"locator":self.locator}.items() if v is not None}


@dataclass(frozen=True)
class DecisionAlternative:
    alternative_id: str
    action: str
    subject_references: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = MappingProxyType({})
    schema_version: str = "decision-alternative-v1"
    def __post_init__(self):
        if self.schema_version != "decision-alternative-v1": raise ValueError("unsupported alternative schema")
        _text(self.alternative_id, "alternative_id"); _text(self.action, "action")
        object.__setattr__(self, "subject_references", tuple(sorted(self.subject_references)))
        object.__setattr__(self, "attributes", freeze(self.attributes))
    def to_dict(self): return {"schema_version":self.schema_version,"alternative_id":self.alternative_id,"action":self.action,"subject_references":list(self.subject_references),"attributes":thaw(self.attributes)}


@dataclass(frozen=True)
class AnalysisMetric:
    metric_id: str
    state: str
    value: Any = None
    unit: str | None = None
    uncertainty: Mapping[str, Any] = MappingProxyType({})
    evidence_ids: tuple[str, ...] = ()
    def __post_init__(self):
        _text(self.metric_id, "metric_id")
        if self.state not in STATES: raise ValueError(f"unsupported metric state: {self.state}")
        if self.state != "known" and self.value is not None: raise ValueError("non-known metric value must be null")
        if self.state == "known" and self.value is None: raise ValueError("known metric requires value")
        object.__setattr__(self, "value", freeze(self.value)); object.__setattr__(self,"uncertainty",freeze(self.uncertainty)); object.__setattr__(self,"evidence_ids",tuple(sorted(self.evidence_ids)))
    def to_dict(self): return {"metric_id":self.metric_id,"state":self.state,"value":thaw(self.value),"unit":self.unit,"uncertainty":thaw(self.uncertainty),"evidence_ids":list(self.evidence_ids)}


@dataclass(frozen=True)
class Factor:
    factor_id: str
    alternative_id: str
    metric_id: str
    statement: str
    evidence_ids: tuple[str, ...] = ()
    def __post_init__(self):
        for n in ("factor_id","alternative_id","metric_id","statement"): _text(getattr(self,n),n)
        object.__setattr__(self,"evidence_ids",tuple(sorted(self.evidence_ids)))
    def to_dict(self): return {"factor_id":self.factor_id,"alternative_id":self.alternative_id,"metric_id":self.metric_id,"statement":self.statement,"evidence_ids":list(self.evidence_ids)}


@dataclass(frozen=True)
class DomainAnalysisEnvelope:
    domain_id: str
    domain_version: str
    alternative_id: str
    metrics: tuple[AnalysisMetric, ...]
    evidence: tuple[EvidenceReference, ...] = ()
    state: str = "known"
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    uncertainty: Mapping[str, Any] = MappingProxyType({})
    sensitivity_inputs: Mapping[str, Any] = MappingProxyType({})
    input_snapshot_ids: tuple[str, ...] = ()
    schema_version: str = "decision-analysis-v1"
    def __post_init__(self):
        if self.schema_version != "decision-analysis-v1": raise ValueError("unsupported analysis schema")
        for n in ("domain_id","domain_version","alternative_id"): _text(getattr(self,n),n)
        if self.state not in STATES: raise ValueError(f"unsupported analysis state: {self.state}")
        metrics=tuple(sorted(self.metrics,key=lambda x:x.metric_id)); evidence=tuple(sorted(self.evidence,key=lambda x:x.evidence_id))
        if len({m.metric_id for m in metrics}) != len(metrics): raise ValueError("duplicate metric identity")
        if len({e.evidence_id for e in evidence}) != len(evidence): raise ValueError("duplicate evidence identity")
        known={e.evidence_id for e in evidence}
        if any(not set(m.evidence_ids)<=known for m in metrics): raise ValueError("metric references absent evidence")
        object.__setattr__(self,"metrics",metrics); object.__setattr__(self,"evidence",evidence)
        for n in ("assumptions","limitations","input_snapshot_ids"): object.__setattr__(self,n,tuple(sorted(getattr(self,n))))
        object.__setattr__(self,"uncertainty",freeze(self.uncertainty)); object.__setattr__(self,"sensitivity_inputs",freeze(self.sensitivity_inputs))
    def to_dict(self): return {"schema_version":self.schema_version,"domain_id":self.domain_id,"domain_version":self.domain_version,"alternative_id":self.alternative_id,"state":self.state,"metrics":[m.to_dict() for m in self.metrics],"evidence":[e.to_dict() for e in self.evidence],"assumptions":list(self.assumptions),"limitations":list(self.limitations),"uncertainty":thaw(self.uncertainty),"sensitivity_inputs":thaw(self.sensitivity_inputs),"input_snapshot_ids":list(self.input_snapshot_ids)}


@dataclass(frozen=True)
class DecisionRequest:
    objective: str
    alternatives: tuple[DecisionAlternative, ...]
    constraints: Mapping[str, Any]
    preferences: Mapping[str, Any]
    domain_inputs: Mapping[str, Any]
    evidence_references: tuple[EvidenceReference, ...]
    policy_id: str
    policy_version: str
    uncertainty: Mapping[str, Any]
    input_snapshot_ids: tuple[str, ...]
    schema_version: str = "decision-request-v1"
    def __post_init__(self):
        if self.schema_version != "decision-request-v1": raise ValueError("unsupported request schema")
        for n in ("objective","policy_id","policy_version"): _text(getattr(self,n),n)
        alternatives=tuple(sorted(self.alternatives,key=lambda x:x.alternative_id))
        if not alternatives or len({a.alternative_id for a in alternatives}) != len(alternatives): raise ValueError("request requires uniquely identified alternatives")
        object.__setattr__(self,"alternatives",alternatives); object.__setattr__(self,"evidence_references",tuple(sorted(self.evidence_references,key=lambda x:x.evidence_id)))
        for n in ("constraints","preferences","domain_inputs","uncertainty"): object.__setattr__(self,n,freeze(getattr(self,n)))
        object.__setattr__(self,"input_snapshot_ids",tuple(sorted(self.input_snapshot_ids)))
    def content_dict(self): return {"schema_version":self.schema_version,"objective":self.objective,"alternatives":[a.to_dict() for a in self.alternatives],"constraints":thaw(self.constraints),"preferences":thaw(self.preferences),"domain_inputs":thaw(self.domain_inputs),"evidence_references":[e.to_dict() for e in self.evidence_references],"policy":{"policy_id":self.policy_id,"policy_version":self.policy_version},"uncertainty":thaw(self.uncertainty),"input_snapshot_ids":list(self.input_snapshot_ids)}
    @property
    def request_id(self): return identity("request-sha256:",self.content_dict())
    def to_dict(self): return {"request_id":self.request_id,**self.content_dict()}
    def to_json(self,*,indent=None): return json.dumps(self.to_dict(),sort_keys=True,ensure_ascii=False,indent=indent,separators=(",", ":") if indent is None else None)


@dataclass(frozen=True)
class StructuredRecommendation:
    request_id: str; outcome: str; selected_alternative_id: str | None
    policy_id: str; policy_version: str; rationale: tuple[Mapping[str, Any], ...]
    evidence_references: tuple[EvidenceReference, ...]; supporting_factors: tuple[Factor, ...]
    counterarguments: tuple[Factor, ...]; uncertainties: tuple[Mapping[str, Any], ...]
    assumptions: tuple[str, ...]; limitations: tuple[str, ...]
    decision_change_conditions: tuple[Mapping[str, Any], ...]; input_snapshot_ids: tuple[str, ...]
    abstention_reasons: tuple[str, ...] = (); schema_version: str = "recommendation-v1"
    def __post_init__(self):
        if self.schema_version != "recommendation-v1" or self.outcome not in {"selected","abstain"}: raise ValueError("invalid recommendation outcome/schema")
        if (self.outcome == "selected") != (self.selected_alternative_id is not None): raise ValueError("selected alternative must agree with outcome")
        for n in ("rationale","uncertainties","decision_change_conditions"): object.__setattr__(self,n,tuple(freeze(v) for v in getattr(self,n)))
    def content_dict(self): return {"schema_version":self.schema_version,"request_id":self.request_id,"outcome":self.outcome,"selected_alternative_id":self.selected_alternative_id,"policy":{"policy_id":self.policy_id,"policy_version":self.policy_version},"rationale":[thaw(x) for x in self.rationale],"evidence_references":[x.to_dict() for x in self.evidence_references],"supporting_factors":[x.to_dict() for x in self.supporting_factors],"counterarguments":[x.to_dict() for x in self.counterarguments],"uncertainties":[thaw(x) for x in self.uncertainties],"assumptions":list(self.assumptions),"limitations":list(self.limitations),"decision_change_conditions":[thaw(x) for x in self.decision_change_conditions],"input_snapshot_ids":list(self.input_snapshot_ids),"abstention_reasons":list(self.abstention_reasons)}
    @property
    def recommendation_id(self): return identity("recommendation-sha256:",self.content_dict())
    def to_dict(self): return {"recommendation_id":self.recommendation_id,**self.content_dict()}
    def to_json(self,*,indent=None): return json.dumps(self.to_dict(),sort_keys=True,ensure_ascii=False,indent=indent,separators=(",", ":") if indent is None else None)
