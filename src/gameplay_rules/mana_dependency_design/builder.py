"""Build immutable dependency-grouping records using retained evidence only."""
from .evidence import load_retained_evidence
from .classification import build_classification_design
from .activated import build_activated_design
from .triggered import build_triggered_design
from .stack import build_stack_design
from .consumers import build_consumer_matrix
from .grouping import build_dependency_grouping
from .readiness import build_readiness


def build_design_package(*, review_root):
    binding = load_retained_evidence(review_root)
    classification = build_classification_design()
    activated = build_activated_design()
    triggered = build_triggered_design()
    stack = build_stack_design()
    consumers = build_consumer_matrix(binding, classification, activated, triggered, stack)
    grouping = build_dependency_grouping(classification, activated, triggered, stack, consumers)
    readiness = build_readiness(binding, classification, activated, triggered, stack, consumers, grouping)
    return {
        "classification-dependencies.json": classification,
        "activated-procedure-design.json": activated,
        "triggered-procedure-design.json": triggered,
        "stack-context-design.json": stack,
        "consumer-bindings.json": consumers,
        "dependency-groups.json": grouping,
        "readiness.json": readiness,
    }
