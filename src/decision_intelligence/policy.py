"""Explicit deterministic multi-alternative policy configuration."""
from dataclasses import dataclass

@dataclass(frozen=True)
class MetricCriterion:
    metric_id: str
    direction: str
    required: bool = True
    def __post_init__(self):
        if not self.metric_id.strip() or self.direction not in {"maximize","minimize"}: raise ValueError("invalid metric criterion")

@dataclass(frozen=True)
class DecisionPolicy:
    policy_id: str
    version: str
    criteria: tuple[MetricCriterion, ...]
    tie_behavior: str = "abstain"
    require_analysis_state_known: bool = True
    schema_version: str = "decision-policy-v1"
    def __post_init__(self):
        if self.schema_version != "decision-policy-v1" or not self.policy_id.strip() or not self.version.strip(): raise ValueError("invalid policy identity/schema")
        if not self.criteria or len({x.metric_id for x in self.criteria}) != len(self.criteria): raise ValueError("policy requires unique criteria")
        if self.tie_behavior != "abstain": raise ValueError("only fail-closed tie behavior is supported")
        object.__setattr__(self,"criteria",tuple(self.criteria))
    def to_dict(self): return {"schema_version":self.schema_version,"policy_id":self.policy_id,"version":self.version,"criteria":[{"metric_id":x.metric_id,"direction":x.direction,"required":x.required} for x in self.criteria],"tie_behavior":self.tie_behavior,"require_analysis_state_known":self.require_analysis_state_known}
