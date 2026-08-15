"""Versioned, immutable contracts for game-neutral fixed-content products."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from decision_intelligence import EvidenceReference
from market.intelligence import MarketObservation

MANIFEST_SCHEMA = "fixed-content-product-manifest-v1"
OFFER_SCHEMA = "product-acquisition-offer-v1"
VALUATION_SCHEMA = "component-valuation-input-v1"


class ProductValidationError(ValueError): pass


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value:
        raise ProductValidationError(f"{name} must be non-empty single-line text")
    return value.strip()


def _decimal(value: Any, name: str) -> Decimal:
    try: result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ProductValidationError(f"{name} must be a finite decimal") from error
    if not result.is_finite() or result < 0: raise ProductValidationError(f"{name} must be non-negative")
    return result


def _stamp(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None: raise ProductValidationError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping): return {str(k): _plain(v) for k, v in sorted(value.items())}
    if isinstance(value, (tuple, list)): return [_plain(v) for v in value]
    if isinstance(value, Decimal): return format(value, "f")
    if isinstance(value, (date, datetime)): return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, (str, int, bool, type(None))): return value
    raise ProductValidationError(f"unsupported contract value: {type(value).__name__}")


def _freeze(value: Any) -> Any:
    value = _plain(value)
    if isinstance(value, dict): return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list): return tuple(_freeze(v) for v in value)
    return value


def _identity(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded=json.dumps(_plain(payload),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return prefix + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class GuaranteedComponent:
    component_id: str
    component_type: str
    quantity: int
    printing_id: str | None = None
    finish: str | None = None
    language: str | None = None
    treatment: str | None = None
    evidence_ids: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()

    def __post_init__(self):
        for name in ("component_id", "component_type"): object.__setattr__(self,name,_text(getattr(self,name),name))
        if isinstance(self.quantity,bool) or not isinstance(self.quantity,int) or self.quantity <= 0: raise ProductValidationError("quantity must be a positive integer")
        for name in ("printing_id","finish","language","treatment"):
            if getattr(self,name) is not None: object.__setattr__(self,name,_text(getattr(self,name),name))
        object.__setattr__(self,"evidence_ids",tuple(sorted(_text(x,"evidence_id") for x in self.evidence_ids)))
        object.__setattr__(self,"unknowns",tuple(sorted(_text(x,"unknown") for x in self.unknowns)))

    @property
    def identity(self): return (self.component_id,self.printing_id,self.finish,self.language,self.treatment)
    def to_dict(self): return {"component_id":self.component_id,"component_type":self.component_type,"quantity":self.quantity,"printing_id":self.printing_id,"finish":self.finish,"language":self.language,"treatment":self.treatment,"evidence_ids":list(self.evidence_ids),"unknowns":list(self.unknowns)}


@dataclass(frozen=True)
class FixedContentProductManifest:
    product_id: str
    game_id: str
    product_type: str
    components: tuple[GuaranteedComponent, ...]
    completeness: str
    evidence: tuple[EvidenceReference, ...]
    release_date: date | None = None
    effective_at: datetime | None = None
    unknowns: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    schema_version: str = MANIFEST_SCHEMA

    def __post_init__(self):
        if self.schema_version != MANIFEST_SCHEMA: raise ProductValidationError("unsupported manifest schema")
        for name in ("product_id","game_id","product_type"): object.__setattr__(self,name,_text(getattr(self,name),name))
        if self.completeness not in {"complete","incomplete","unknown"}: raise ProductValidationError("invalid completeness")
        components=tuple(sorted(self.components,key=lambda x:tuple(v or "" for v in x.identity)))
        if not components: raise ProductValidationError("manifest requires guaranteed components")
        if len({x.identity for x in components}) != len(components): raise ProductValidationError("duplicate component identity")
        evidence=tuple(sorted(self.evidence,key=lambda x:x.evidence_id)); known={x.evidence_id for x in evidence}
        if len(known)!=len(evidence): raise ProductValidationError("duplicate evidence identity")
        if any(not set(x.evidence_ids)<=known for x in components): raise ProductValidationError("component references absent evidence")
        object.__setattr__(self,"components",components); object.__setattr__(self,"evidence",evidence)
        if self.effective_at is not None: object.__setattr__(self,"effective_at",_stamp(self.effective_at,"effective_at"))
        for name in ("unknowns","assumptions","limitations"): object.__setattr__(self,name,tuple(sorted(_text(x,name[:-1]) for x in getattr(self,name))))

    def content_dict(self): return {"schema_version":self.schema_version,"product_id":self.product_id,"game_id":self.game_id,"product_type":self.product_type,"release_date":_plain(self.release_date),"effective_at":_plain(self.effective_at),"completeness":self.completeness,"components":[x.to_dict() for x in self.components],"evidence":[x.to_dict() for x in self.evidence],"unknowns":list(self.unknowns),"assumptions":list(self.assumptions),"limitations":list(self.limitations)}
    @property
    def manifest_id(self): return _identity("manifest-sha256:",self.content_dict())
    def to_dict(self): return {"manifest_id":self.manifest_id,**self.content_dict()}
    def to_json(self): return json.dumps(self.to_dict(),sort_keys=True,separators=(",",":"),ensure_ascii=False)


@dataclass(frozen=True)
class ProductAcquisitionOffer:
    offer_id: str
    product_id: str
    provider: str
    observed_at: datetime
    currency: str
    listed_price: Decimal
    evidence: tuple[EvidenceReference, ...]
    shipping: Decimal = Decimal(0)
    tax: Decimal = Decimal(0)
    transaction_fees: Decimal = Decimal(0)
    discounts: Decimal = Decimal(0)
    effective_at: datetime | None = None
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    schema_version: str = OFFER_SCHEMA

    def __post_init__(self):
        if self.schema_version != OFFER_SCHEMA: raise ProductValidationError("unsupported offer schema")
        for name in ("offer_id","product_id","provider"): object.__setattr__(self,name,_text(getattr(self,name),name))
        currency=_text(self.currency,"currency").upper()
        if len(currency)!=3 or not currency.isalpha(): raise ProductValidationError("currency must be a three-letter code")
        object.__setattr__(self,"currency",currency); object.__setattr__(self,"observed_at",_stamp(self.observed_at,"observed_at"))
        if self.effective_at is not None: object.__setattr__(self,"effective_at",_stamp(self.effective_at,"effective_at"))
        for name in ("listed_price","shipping","tax","transaction_fees","discounts"): object.__setattr__(self,name,_decimal(getattr(self,name),name))
        if self.discounts > self.listed_price+self.shipping+self.tax+self.transaction_fees: raise ProductValidationError("discounts exceed supplied costs")
        evidence=tuple(sorted(self.evidence,key=lambda x:x.evidence_id))
        if not evidence or len({x.evidence_id for x in evidence})!=len(evidence): raise ProductValidationError("offer requires unique evidence")
        object.__setattr__(self,"evidence",evidence)
        for name in ("assumptions","limitations"): object.__setattr__(self,name,tuple(sorted(_text(x,name[:-1]) for x in getattr(self,name))))
    @property
    def effective_cost(self): return self.listed_price+self.shipping+self.tax+self.transaction_fees-self.discounts
    def to_dict(self): return {"schema_version":self.schema_version,"offer_id":self.offer_id,"product_id":self.product_id,"provider":self.provider,"observed_at":_plain(self.observed_at),"effective_at":_plain(self.effective_at),"currency":self.currency,"listed_price":_plain(self.listed_price),"shipping":_plain(self.shipping),"tax":_plain(self.tax),"transaction_fees":_plain(self.transaction_fees),"discounts":_plain(self.discounts),"effective_cost":_plain(self.effective_cost),"evidence":[x.to_dict() for x in self.evidence],"assumptions":list(self.assumptions),"limitations":list(self.limitations)}


@dataclass(frozen=True)
class ComponentValuationInput:
    component_id: str
    observation: MarketObservation
    printing_id: str | None = None
    finish: str | None = None
    language: str | None = None
    treatment: str | None = None
    schema_version: str = VALUATION_SCHEMA

    def __post_init__(self):
        if self.schema_version != VALUATION_SCHEMA: raise ProductValidationError("unsupported valuation schema")
        object.__setattr__(self,"component_id",_text(self.component_id,"component_id"))
        if not isinstance(self.observation,MarketObservation): raise ProductValidationError("observation must be a MarketObservation")
        if self.observation.entity_type not in {"card","printing"}: raise ProductValidationError("component valuation requires card or printing observation")
        for name in ("printing_id","finish","language","treatment"):
            if getattr(self,name) is not None: object.__setattr__(self,name,_text(getattr(self,name),name))
        if self.printing_id is not None and (self.observation.entity_type!="printing" or self.observation.entity_id!=self.printing_id): raise ProductValidationError("printing identity conflicts with market observation")
        if self.finish != self.observation.finish: raise ProductValidationError("finish conflicts with market observation")
        observed_language=self.observation.provenance.get("language")
        if self.language != observed_language: raise ProductValidationError("language conflicts with market observation")
    @property
    def valuation_id(self): return _identity("valuation-sha256:",self.to_dict())
    def to_dict(self): return {"schema_version":self.schema_version,"component_id":self.component_id,"printing_id":self.printing_id,"finish":self.finish,"language":self.language,"treatment":self.treatment,"market_observation":self.observation.to_dict()}
