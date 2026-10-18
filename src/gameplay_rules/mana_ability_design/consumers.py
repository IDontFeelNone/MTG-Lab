"""Read-only consumer requirements; dependency flow grants no runtime authority."""
from dataclasses import dataclass
from typing import ClassVar

from .common import DesignRecord, _json, _exact, _keys, _hash, _strings, _fail
from .classification import ManaAbilityClassificationDesign
from .behavior import ManaAbilityBehaviorDesign
from .controller import ManaAbilityControllerDesign
from .evidence import RETAINED_BINDING


def _consumer_body(binding, classification_id, behavior_id, controller_id, notes):
    _exact(binding, RETAINED_BINDING, "retained_evidence_binding")
    return {
        "retained_evidence_binding": _json(binding),
        "classification_design_id": classification_id,
        "behavior_design_id": behavior_id, "controller_design_id": controller_id,
        "consumer_bindings": [
            {"consumer_reference": "601.2g", "consumer_evidence": binding["consumers"]["601.2g"],
             "relationship_kind": "EXISTING_DIRECT_CR_DEPENDENCY",
             "unresolved_target": "605",
             "required_capabilities": ["mana_ability_classification",
                 "activated_mana_ability_activation_window", "mana_payment_opportunity",
                 "activated_mana_ability_immediate_resolution"],
             "later_capabilities": ["triggered_mana_ability_immediate_resolution",
                 "mana_production_semantics", "mana_pool_semantics", "payment_integration"],
             "execution_readiness": "BLOCKED", "required_primitives_available": False},
            {"consumer_reference": "109.4a", "consumer_evidence": binding["consumers"]["109.4a"],
             "relationship_kind": "EXISTING_DIRECT_CR_DEPENDENCY",
             "unresolved_target": "605",
             "required_capabilities": ["mana_ability_classification", "mana_ability_controller_attribution"],
             "later_capabilities": ["activated_and_triggered_subtype_knowledge",
                                    "general_ability_controller_semantics"],
             "execution_readiness": "BLOCKED", "required_primitives_available": False},
        ],
        "indirect_dependency_flows": [{
            "flow_id": "madness_casting_mana_frontier", "relationship_kind": "INDIRECT_DEPENDENCY_FLOW",
            "retained_madness_rule": next(row for row in binding["madness_rules"] if row["rule_reference"] == "702.35b"),
            "path": ["702.35b", "bounded_casting_projection", "601.2g", "605"],
            "selected_casting_stages": ["601.2b", "601.2f", "601.2g", "601.2h"],
            "new_direct_madness_to_605_citation": False, "execution_readiness": "BLOCKED",
        }],
        "authority_boundary": {
            "finding": "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605",
            "allowed_evidence": ["RETAINED_CONSUMER_PROJECTION_IDENTITIES", "EXPLICITLY_LABELED_PM_DESIGN_INPUT"],
            "fictional_runtime_authority_inherited": False, "fictional_mana_satisfies_real_605": False,
            "classification_implies_execution": False, "one_consumer_satisfies_other_consumer": False,
            "controller_attribution_distinct_from_casting_opportunity": True,
        },
        "design_notes": notes,
    }


@dataclass(frozen=True)
class ManaAbilityConsumerMatrix(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-rules-mana-ability-consumer-matrix-v1"
    ID_FIELD: ClassVar[str] = "consumer_matrix_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "retained_evidence_binding", "classification_design_id", "behavior_design_id",
        "controller_design_id", "consumer_bindings", "indirect_dependency_flows", "authority_boundary", "design_notes",
    })

    @staticmethod
    def _validate_body(body):
        _keys(body, ManaAbilityConsumerMatrix.BODY_FIELDS)
        for field in ("classification_design_id", "behavior_design_id", "controller_design_id"):
            _hash(body[field], field)
        _strings(body["design_notes"], "design_notes")
        _exact(body, _consumer_body(body["retained_evidence_binding"], body["classification_design_id"],
            body["behavior_design_id"], body["controller_design_id"], body["design_notes"]), "consumer_matrix")


def build_consumer_matrix(binding, classification, behavior, controller, *, design_notes=None):
    for record, expected in ((classification, ManaAbilityClassificationDesign),
                             (behavior, ManaAbilityBehaviorDesign), (controller, ManaAbilityControllerDesign)):
        if type(record) is not expected:
            _fail("concrete immutable design inputs required")
        record.verify()
    _exact(controller.to_dict()["consumer_binding"], binding["consumers"]["109.4a"], "controller_consumer_binding")
    return ManaAbilityConsumerMatrix.create(_consumer_body(_json(binding), classification.identity,
        behavior.identity, controller.identity, [] if design_notes is None else design_notes))
