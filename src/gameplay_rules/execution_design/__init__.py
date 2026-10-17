"""Inactive real-rules design and review metadata, separate from the kernel."""
from .contracts import (FoundationalProjectionReview, RealRulesCapabilityMatrix,
    RealRulesExecutionProfileDesign, RealRulesActivationGateDesign, RealRulesExecutionReadiness)
from .builder import build_design_package
from .package import load_design_package

__all__ = ["FoundationalProjectionReview", "RealRulesCapabilityMatrix",
           "RealRulesExecutionProfileDesign", "RealRulesActivationGateDesign",
           "RealRulesExecutionReadiness", "build_design_package", "load_design_package"]
