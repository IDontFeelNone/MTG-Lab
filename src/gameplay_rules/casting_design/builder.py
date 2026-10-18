"""Reproduce a design package from retained repository evidence alone."""
from .anchors import MultiLineSourceAnchorDesign, build_source_anchor_design
from .stages import CastingSubprocedureDesign, build_casting_subprocedure_design
from .costs import CostModelDesign, build_cost_design
from .frontier import ProjectionFrontierDesign, build_projection_frontier_design
from .readiness import MadnessCastingReadiness, build_madness_readiness
from .evidence import load_retained_evidence


def build_design_package(*, review_root):
    """No artifact parameter, network, source parser, runtime, or side effects."""
    binding = load_retained_evidence(review_root)
    anchor = build_source_anchor_design()
    casting = build_casting_subprocedure_design()
    cost = build_cost_design(casting)
    frontier = build_projection_frontier_design()
    readiness = build_madness_readiness(binding, casting, cost, anchor, frontier)
    return {"source-anchor-design.json": anchor, "casting-subprocedure-design.json": casting,
            "cost-design.json": cost, "madness-readiness.json": readiness,
            "projection-frontier.json": frontier}
