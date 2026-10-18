"""Build review-only records from retained knowledge and labeled design input."""
from .evidence import load_retained_evidence
from .classification import build_classification_design
from .behavior import build_behavior_design
from .controller import build_controller_design
from .consumers import build_consumer_matrix
from .frontier import build_projection_frontier
from .readiness import build_readiness


def build_design_package(*, review_root):
    binding = load_retained_evidence(review_root)
    classification = build_classification_design()
    behavior = build_behavior_design()
    controller = build_controller_design(binding)
    consumers = build_consumer_matrix(binding, classification, behavior, controller)
    frontier = build_projection_frontier(classification, behavior, controller)
    readiness = build_readiness(binding, classification, behavior, controller, consumers, frontier)
    return {"classification-design.json": classification, "behavior-design.json": behavior,
            "controller-design.json": controller, "consumer-bindings.json": consumers,
            "projection-frontier.json": frontier, "readiness.json": readiness}
