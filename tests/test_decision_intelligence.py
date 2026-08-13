"""Synthetic-only proof of the shared, game-neutral decision substrate."""
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

from decision_intelligence import (AcquisitionDecisionOrchestrator, AnalysisMetric,
 DecisionAlternative, DecisionPolicy, DecisionRequest, DomainAnalysisEnvelope,
 EvidenceReference, MetricCriterion, recommendation_reasoning_context)

E=EvidenceReference("synthetic-evidence","synthetic-fixture","sha256:"+"a"*64)

def request(order=("option-b","option-a")):
 return DecisionRequest("Select a synthetic alternative",tuple(DecisionAlternative(x,"SYNTHETIC_ACTION_"+x[-1].upper()) for x in order),
  {"synthetic_constraint":True},{"synthetic_preference":"explicit"},{"semantics":"synthetic dimensionless test signal"},(E,),"synthetic-policy","1.0.0",{"state":"explicitly supplied"},("synthetic-input-snapshot",))
def analysis(a,value,state="known",**kwargs):
 return DomainAnalysisEnvelope("synthetic-domain","1.0.0",a,(AnalysisMetric("synthetic.signal",state,value if state=="known" else None,evidence_ids=("synthetic-evidence",),uncertainty=kwargs.pop("metric_uncertainty",{})),),(E,),input_snapshot_ids=("synthetic-analysis-snapshot",),**kwargs)
def policy(): return DecisionPolicy("synthetic-policy","1.0.0",(MetricCriterion("synthetic.signal","maximize"),))
def evaluate(analyses): return AcquisitionDecisionOrchestrator().evaluate(request(),analyses,policy())

def test_serialization_selection_provenance_context_and_replay():
 r1=request(); r2=request(("option-a","option-b"))
 assert r1.to_json()==r2.to_json() and r1.request_id==r2.request_id
 result=evaluate((analysis("option-b",2,assumptions=("synthetic assumption",),limitations=("synthetic limitation",),uncertainty={"kind":"synthetic range"},sensitivity_inputs={"synthetic.signal":"caller supplied"}),analysis("option-a",1)))
 replay=evaluate(reversed((analysis("option-b",2,assumptions=("synthetic assumption",),limitations=("synthetic limitation",),uncertainty={"kind":"synthetic range"},sensitivity_inputs={"synthetic.signal":"caller supplied"}),analysis("option-a",1))))
 assert result.outcome=="selected" and result.selected_alternative_id=="option-b"
 assert result.to_json()==replay.to_json() and result.recommendation_id==replay.recommendation_id
 assert result.evidence_references==(E,) and "synthetic assumption" in result.assumptions
 assert result.decision_change_conditions and result.uncertainties
 context=recommendation_reasoning_context(result)
 assert context["recommendation"]==result.to_dict() and "without changing" in context["instruction"]

def test_missing_unsupported_incomplete_and_tie_abstain_closed():
 missing=evaluate((analysis("option-a",1),DomainAnalysisEnvelope("synthetic-domain","1","option-b",(),(E,))))
 unsupported=evaluate((analysis("option-a",1),analysis("option-b",None,"unsupported")))
 tie=evaluate((analysis("option-a",1),analysis("option-b",1)))
 assert all(x.outcome=="abstain" and x.selected_alternative_id is None for x in (missing,unsupported,tie))
 assert "missing_required_metric" in missing.abstention_reasons[0]
 assert any("unsupported" in x for x in unsupported.abstention_reasons)

def test_contradiction_abstains_and_uncertainty_is_preserved():
 result=evaluate((analysis("option-a",1),analysis("option-a",2),analysis("option-b",3,metric_uncertainty={"range":[2,4]})))
 assert result.outcome=="abstain"
 assert any(x.startswith("contradictory_evidence") for x in result.abstention_reasons)
 assert result.to_dict()["uncertainties"][0]["metrics"][0]["uncertainty"]=={"range":[2,4]}

def test_counterargument_preserved_for_later_criterion():
 p=DecisionPolicy("synthetic-policy","1.0.0",(MetricCriterion("synthetic.primary","maximize"),MetricCriterion("synthetic.secondary","maximize")))
 def a(aid,x,y): return DomainAnalysisEnvelope("synthetic-domain","1",aid,(AnalysisMetric("synthetic.primary","known",x),AnalysisMetric("synthetic.secondary","known",y)))
 result=AcquisitionDecisionOrchestrator().evaluate(request(),(a("option-a",2,1),a("option-b",1,9)),p)
 assert result.selected_alternative_id=="option-a" and result.counterarguments[0].alternative_id=="option-b"

def test_schema_validation_and_fail_closed_models():
 root=Path("src/schemas/v1")
 pairs=((request().to_dict(),"decision-request-v1"),(policy().to_dict(),"decision-policy-v1"),(analysis("option-a",1).to_dict(),"decision-analysis-v1"),(evaluate((analysis("option-a",1),analysis("option-b",2))).to_dict(),"recommendation-v1"))
 for instance,name in pairs: Draft202012Validator(json.loads((root/f"{name}.schema.json").read_text())).validate(instance)
 with pytest.raises(ValueError): AnalysisMetric("x","unknown",0)
 with pytest.raises(ValueError): DecisionAlternative("x","",attributes={})

def test_domain_isolation_and_no_mutation(tmp_path):
 before={p:p.read_bytes() for p in Path("data").rglob("*") if p.is_file()}
 result=evaluate((analysis("option-a",1),analysis("option-b",2)))
 after={p:p.read_bytes() for p in Path("data").rglob("*") if p.is_file()}
 assert result.outcome=="selected" and before==after
 shared="\n".join(p.read_text() for p in Path("src/decision_intelligence").glob("*.py")).lower()
 forbidden=("booster","secret lair","commander","tournament","sealed","singles","deck","card","product","magic")
 assert not any(word in shared for word in forbidden)
