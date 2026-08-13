"""Thin stateless orchestration; domain metrics remain opaque except to policy criteria."""
from __future__ import annotations
from numbers import Real
from typing import Iterable

from .models import (DecisionRequest, DomainAnalysisEnvelope, Factor,
                     StructuredRecommendation, thaw)
from .policy import DecisionPolicy


class AcquisitionDecisionOrchestrator:
    """Validate, evaluate an explicit policy, and assemble a recommendation."""
    def evaluate(self, request: DecisionRequest, analyses: Iterable[DomainAnalysisEnvelope],
                 policy: DecisionPolicy) -> StructuredRecommendation:
        envelopes=tuple(sorted(analyses,key=lambda x:(x.alternative_id,x.domain_id,x.domain_version)))
        reasons=[]
        if (request.policy_id,request.policy_version)!=(policy.policy_id,policy.version): reasons.append("policy_identity_mismatch")
        alternative_ids={a.alternative_id for a in request.alternatives}
        if any(x.alternative_id not in alternative_ids for x in envelopes): reasons.append("analysis_for_unknown_alternative")
        by_alt={aid:{} for aid in alternative_ids}; contradiction=set()
        for envelope in envelopes:
            if policy.require_analysis_state_known and envelope.state != "known": reasons.append(f"analysis_{envelope.state}:{envelope.alternative_id}:{envelope.domain_id}")
            for metric in envelope.metrics:
                prior=by_alt.get(envelope.alternative_id,{}).get(metric.metric_id)
                if prior is not None and prior.to_dict()!=metric.to_dict(): contradiction.add((envelope.alternative_id,metric.metric_id))
                else: by_alt.get(envelope.alternative_id,{})[metric.metric_id]=metric
        reasons.extend(f"contradictory_evidence:{a}:{m}" for a,m in sorted(contradiction))
        for aid in sorted(alternative_ids):
            for criterion in policy.criteria:
                metric=by_alt[aid].get(criterion.metric_id)
                if criterion.required and metric is None: reasons.append(f"missing_required_metric:{aid}:{criterion.metric_id}")
                elif criterion.required and metric.state != "known": reasons.append(f"required_metric_{metric.state}:{aid}:{criterion.metric_id}")
                elif metric is not None and metric.state == "known" and (isinstance(metric.value,bool) or not isinstance(metric.value,Real)):
                    reasons.append(f"non_numeric_policy_metric:{aid}:{criterion.metric_id}")
        evidence_by_id={}
        for item in (e for x in envelopes for e in x.evidence):
            if item.evidence_id in evidence_by_id and evidence_by_id[item.evidence_id] != item:
                reasons.append(f"conflicting_evidence_reference:{item.evidence_id}")
            evidence_by_id[item.evidence_id]=item
        evidence=tuple(sorted(evidence_by_id.values(),key=lambda x:x.evidence_id))
        uncertainty=tuple({"alternative_id":x.alternative_id,"domain_id":x.domain_id,"analysis":thaw(x.uncertainty),"metrics":[{"metric_id":m.metric_id,"state":m.state,"uncertainty":thaw(m.uncertainty)} for m in x.metrics if m.state != "known" or m.uncertainty]} for x in envelopes if x.uncertainty or any(m.state != "known" or m.uncertainty for m in x.metrics))
        assumptions=tuple(sorted({v for x in envelopes for v in x.assumptions})); limitations=tuple(sorted({v for x in envelopes for v in x.limitations}))
        snapshots=tuple(sorted(set(request.input_snapshot_ids)|{v for x in envelopes for v in x.input_snapshot_ids}))
        if reasons: return self._result(request,policy,None,(),(),uncertainty,assumptions,limitations,(),evidence,snapshots,tuple(sorted(set(reasons))))

        # Ordered criteria are a transparent lexicographic policy; no hidden weights or inferred utility.
        active_criteria=tuple(c for c in policy.criteria if all(
            (m:=by_alt[aid].get(c.metric_id)) is not None and m.state=="known"
            for aid in alternative_ids))
        if not active_criteria:
            return self._result(request,policy,None,(),(),uncertainty,assumptions,limitations,(),evidence,snapshots,("no_comparable_policy_criteria",))
        def score(aid):
            values=[]
            for c in active_criteria:
                value=by_alt[aid][c.metric_id].value
                values.append(value if c.direction=="maximize" else -value)
            return tuple(values)
        scores={aid:score(aid) for aid in sorted(alternative_ids)}; best=max(scores.values())
        winners=[aid for aid,value in scores.items() if value==best]
        if len(winners)!=1:
            return self._result(request,policy,None,(),(),uncertainty,assumptions,limitations,(),evidence,snapshots,("policy_tie",))
        winner=winners[0]; supporting=[]; counter=[]; rationale=[]; conditions=[]
        for index,c in enumerate(active_criteria):
            value=by_alt[winner].get(c.metric_id)
            rationale.append({"criterion_order":index,"metric_id":c.metric_id,"direction":c.direction,"selected_value":value.value if value else None})
            supporting.append(Factor(f"criterion-{index}-selected",winner,c.metric_id,"Selected alternative value under the ordered policy criterion.",value.evidence_ids if value else ()))
            rivals=[]
            for aid in sorted(alternative_ids-{winner}):
                metric=by_alt[aid].get(c.metric_id)
                if metric:
                    rivals.append(metric.value)
                    better=(c.direction=="maximize" and metric.value>value.value) or (c.direction=="minimize" and metric.value<value.value)
                    if better: counter.append(Factor(f"criterion-{index}-counter-{aid}",aid,c.metric_id,"A non-selected alternative is stronger on this criterion.",metric.evidence_ids))
            if rivals: conditions.append({"metric_id":c.metric_id,"alternative_id":winner,"condition":"selection may change if ordered comparison changes","selected_value":value.value,"comparison_values":rivals})
        return self._result(request,policy,winner,tuple(rationale),tuple(counter),uncertainty,assumptions,limitations,tuple(conditions),evidence,snapshots,(),tuple(supporting))

    @staticmethod
    def _result(request,policy,winner,rationale,counter,uncertainty,assumptions,limitations,conditions,evidence,snapshots,reasons,supporting=()):
        return StructuredRecommendation(request.request_id,"selected" if winner else "abstain",winner,policy.policy_id,policy.version,rationale,evidence,supporting,counter,uncertainty,assumptions,limitations,conditions,snapshots,reasons)
