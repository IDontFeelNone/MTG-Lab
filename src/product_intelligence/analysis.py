"""Pure descriptive analytics over supplied fixed-content evidence."""
from dataclasses import dataclass
from decimal import Decimal
import json

from decision_intelligence import AnalysisMetric, DomainAnalysisEnvelope, EvidenceReference
from .models import FixedContentProductManifest, ProductAcquisitionOffer, ComponentValuationInput, ProductValidationError, _freeze, _identity, _plain

ANALYSIS_SCHEMA="fixed-content-product-analysis-v1"
DEFERRED_DIMENSIONS=("presale_scarcity_premium","post_release_price_compression_risk","sealed_collectible_premium","supply_trajectory","availability","listing_sales_depth","liquidity","playability_demand","collector_ip_demand","artwork_treatment_demand","reprint_risk","historical_comparable_product_behavior")

@dataclass(frozen=True)
class FixedContentProductAnalysis:
    payload: dict
    def __post_init__(self): object.__setattr__(self,"payload",_freeze(self.payload))
    @property
    def analysis_id(self): return _identity("product-analysis-sha256:",self.payload)
    def to_dict(self): return {"analysis_id":self.analysis_id,**_plain(self.payload)}
    def to_json(self): return json.dumps(self.to_dict(),sort_keys=True,separators=(",",":"),ensure_ascii=False)


def analyze_fixed_content(manifest, offer, valuations, *, top_n=3):
    if not isinstance(manifest,FixedContentProductManifest) or not isinstance(offer,ProductAcquisitionOffer): raise ProductValidationError("typed manifest and offer are required")
    if offer.product_id != manifest.product_id: raise ProductValidationError("offer product conflicts with manifest")
    if isinstance(top_n,bool) or not isinstance(top_n,int) or top_n <= 0: raise ProductValidationError("top_n must be positive")
    values=tuple(sorted(valuations,key=lambda x:(x.component_id,x.valuation_id)))
    if any(not isinstance(x,ComponentValuationInput) for x in values): raise ProductValidationError("typed valuations are required")
    if len({x.component_id for x in values})!=len(values): raise ProductValidationError("conflicting replay/input for component valuation")
    by_id={x.component_id:x for x in values}; components={x.component_id:x for x in manifest.components}
    if not set(by_id)<=set(components): raise ProductValidationError("valuation references unknown component")
    comparable=[]; issues=[]
    expected=None
    for cid,value in by_id.items():
        component=components[cid]; obs=value.observation
        dimension=(obs.provider,obs.currency,obs.price_type,obs.observed_at,value.printing_id,value.finish,value.language,value.treatment)
        shared=dimension[:4]
        if expected is None: expected=shared
        elif shared!=expected: issues.append("incompatible_market_dimensions")
        if obs.currency != offer.currency: issues.append("incompatible_currencies")
        if (component.printing_id,component.finish,component.language,component.treatment)!=(value.printing_id,value.finish,value.language,value.treatment): issues.append("component_comparable_dimensions_mismatch")
        if obs.price is not None: comparable.append((component,obs.price*component.quantity,value))
    issues=tuple(sorted(set(issues)))
    priced_ids={x[0].component_id for x in comparable}; total_quantity=sum(x.quantity for x in manifest.components)
    priced_quantity=sum(x.quantity for x,_,_ in comparable); unknown=[x for x in manifest.components if x.component_id not in priced_ids]
    exact=manifest.completeness=="complete" and not unknown and not issues
    total=sum((x[1] for x in comparable),Decimal(0)); ordered=sorted(comparable,key=lambda x:(-x[1],x[0].component_id))
    contribution=[{"component_id":x.component_id,"quantity":x.quantity,"total_value":_plain(amount),"percentage":_plain(amount*Decimal(100)/total) if total else None,"market_observation_id":v.observation.observation_id} for x,amount,v in ordered]
    sealed=offer.effective_cost; delta=sealed-total if exact else None
    evidence={x.evidence_id:x for x in (*manifest.evidence,*offer.evidence)}
    for value in values:
        obs=value.observation; eid="market-observation:"+obs.observation_id
        evidence[eid]=EvidenceReference(eid,obs.provider,"sha256:"+obs.observation_id,obs.recorded_at.isoformat().replace("+00:00","Z"))
    payload={"schema_version":ANALYSIS_SCHEMA,"state":"known" if exact else "incomplete","product_id":manifest.product_id,"game_id":manifest.game_id,"manifest_id":manifest.manifest_id,"offer_id":offer.offer_id,"currency":offer.currency,"sealed_acquisition_cost":_plain(sealed),"listed_price":_plain(offer.listed_price),"transaction_cost_impact":_plain(offer.shipping+offer.tax+offer.transaction_fees-offer.discounts),"total_guaranteed_component_acquisition_value":_plain(total) if exact else None,"known_component_value_subtotal":_plain(total),"sealed_minus_components":_plain(delta),"components_minus_sealed":_plain(-delta) if delta is not None else None,"component_contributions":contribution,"largest_value_driving_component":contribution[0] if contribution else None,"largest_component_percentage":contribution[0]["percentage"] if contribution else None,"top_n":top_n,"top_n_component_value":_plain(sum((x[1] for x in ordered[:top_n]),Decimal(0))),"top_n_percentage":_plain(sum((x[1] for x in ordered[:top_n]),Decimal(0))*Decimal(100)/total) if total else None,"coverage":{"valued_component_count":len(priced_ids),"guaranteed_component_count":len(manifest.components),"valued_quantity":priced_quantity,"guaranteed_quantity":total_quantity,"component_percentage":_plain(Decimal(len(priced_ids))*100/len(manifest.components)),"quantity_percentage":_plain(Decimal(priced_quantity)*100/total_quantity),"unknown_unpriced_component_count":len(unknown),"unknown_unpriced_quantity":sum(x.quantity for x in unknown)},"comparability_issues":list(issues),"unsupported_dimensions":{x:"not_evaluated" for x in DEFERRED_DIMENSIONS},"evidence":[x.to_dict() for x in sorted(evidence.values(),key=lambda x:x.evidence_id)],"assumptions":list(manifest.assumptions+offer.assumptions),"limitations":sorted(set(manifest.limitations+offer.limitations+(("exact comparison unavailable",) if not exact else ())))}
    return FixedContentProductAnalysis(payload)


def to_decision_analysis(analysis, alternative_id):
    d=analysis.to_dict(); evidence=tuple(EvidenceReference(**x) for x in d["evidence"]); eids=tuple(x.evidence_id for x in evidence); known=d["state"]=="known"
    metric=lambda mid,key,unit=None: AnalysisMetric(mid,"known" if known else "incomplete",d[key] if known else None,unit,evidence_ids=eids)
    metrics=(metric("product.components_acquisition_value","total_guaranteed_component_acquisition_value",d["currency"]),AnalysisMetric("product.sealed_acquisition_cost","known",d["sealed_acquisition_cost"],d["currency"],evidence_ids=eids),metric("product.sealed_minus_components","sealed_minus_components",d["currency"]),AnalysisMetric("product.anchor_concentration_percentage","known" if d["largest_component_percentage"] is not None else "unknown",d["largest_component_percentage"],"percent",evidence_ids=eids))
    return DomainAnalysisEnvelope("fixed-content-product-intelligence","1.0.0",alternative_id,metrics,evidence,state=d["state"],assumptions=tuple(d["assumptions"]),limitations=tuple(d["limitations"]),uncertainty={"unsupported_dimensions":d["unsupported_dimensions"]},input_snapshot_ids=(d["analysis_id"],d["manifest_id"],d["offer_id"]))
