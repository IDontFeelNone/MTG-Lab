"""Unverified source-scoping candidate; no source parser, anchors or projection."""
from dataclasses import dataclass
from typing import ClassVar

from .common import DesignRecord, PM_INPUT, _json, _keys, _exact, _hash, _strings, _fail
from .classification import ManaAbilityClassificationDesign
from .behavior import ManaAbilityBehaviorDesign
from .controller import ManaAbilityControllerDesign

CANDIDATE_FAMILY = (
    "605.1", "605.1a", "605.1b", "605.2", "605.3", "605.3a", "605.3b", "605.3c",
    "605.4", "605.4a", "605.5", "605.5a", "605.5b",
)
CANDIDATE_DIRECT_REFERENCES = ("115.6", "606", "602.2", "405.6c", "603")
_GROUPS = {
    "605.1": ("classification", "Preserve the candidate classification parent and both proposed classification branches."),
    "605.2": ("classification_persistence", "Retain the proposed persistence context separating classification from current outcome."),
    "605.3": ("activated_behavior", "Keep the proposed activated-behavior parent together with every supplied subrule."),
    "605.4": ("triggered_behavior", "Keep the proposed triggered-behavior parent and its supplied subrule together."),
    "605.5": ("non_mana_exclusions", "Keep the proposed exclusion parent and both supplied exclusion branches together."),
}


def _candidate_family():
    rows = []
    for reference in CANDIDATE_FAMILY:
        parent = reference[:-1] if reference[-1].isalpha() else None
        group, reason = _GROUPS[parent or reference]
        rows.append({
            "rule_reference": reference, "candidate_parent": parent, "conceptual_group": group,
            "scope_rationale": reason if parent is None else
                f"Retain {reference} within the complete proposed {parent} branch; removing a supplied sibling would leave its scope unreviewed.",
            "rationale_authority": "DESIGN_SCOPING_JUDGMENT_FROM_PM_CANDIDATE_FAMILY",
            "exact_source_body_and_role": "REQUIRES_FUTURE_SOURCE_VERIFICATION",
            "evidence_status": PM_INPUT, "source_verified": False, "coverage_state": "UNPROJECTED",
        })
    return rows


def _candidate_references():
    details = (
        ("115.6", "TARGETING_DEFINITION", "POTENTIALLY_BOUNDED", "Classification requires target knowledge; exact outgoing citation awaits source verification."),
        ("606", "LOYALTY_ABILITY_CLASSIFICATION", "POTENTIALLY_BOUNDED", "Loyalty status can affect classification without being relevant to every activation."),
        ("602.2", "GENERAL_ACTIVATED_ABILITY_PROCEDURE", "LARGE_CORE_SUBSYSTEM", "Ordinary activation procedure cannot be closed by a mana-only design."),
        ("405.6c", "STACK_EXCEPTION_CONTEXT", "POTENTIALLY_BOUNDED_WITH_STACK_INTERACTIONS", "A stack exception does not supply general stack execution."),
        ("603", "GENERAL_TRIGGERED_ABILITY_SUBSYSTEM", "LARGE_CORE_SUBSYSTEM", "Trigger detection and resolution require a separate broad semantic review."),
    )
    return [{"rule_reference": ref, "concern": concern, "subsystem_size": size,
             "scope_assessment": reason, "relationship_status": "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION",
             "evidence_status": PM_INPUT, "source_verified": False, "coverage_state": "UNPROJECTED",
             "recursive_design_authorized": False}
            for ref, concern, size, reason in details]


def _frontier_body(classification_id, behavior_id, controller_id, notes):
    return {
        "classification_design_id": classification_id, "behavior_design_id": behavior_id,
        "controller_design_id": controller_id, "evidence_status": PM_INPUT,
        "candidate_family": _candidate_family(), "candidate_source_unit_count": 13,
        "coherence_review": {
            "finding": "PROVISIONALLY_SMALLEST_COHERENT_PM_CANDIDATE_FAMILY",
            "basis": "Complete proposed classification, persistence, activated, triggered and exclusion branches are retained.",
            "independently_verified_minimal_source_scope": False,
            "minimum_scope_requires_future_source_verification": True,
            "madness_specific_cherry_picking": False, "automatically_expand_scope": False,
            "source_shape_or_scope_discrepancy_action": "STOP_FOR_SEPARATE_REVIEW",
        },
        "candidate_direct_references": _candidate_references(),
        "deferred_semantic_boundaries": ["general_activated_abilities", "general_triggered_abilities",
            "general_controller_semantics", "stack", "priority", "mana_production", "mana_pool",
            "payment_integration", "real_card_and_effect_semantics", "replacement_effect_execution"],
        "next_milestone": {
            "candidate": "Bounded Mana Ability Rules Projection", "exact_proposed_source_allowlist": list(CANDIDATE_FAMILY),
            "proposed_source_unit_count": 13, "candidate_outgoing_dependencies": list(CANDIDATE_DIRECT_REFERENCES),
            "deliberately_deferred_numbered_dependencies": list(CANDIDATE_DIRECT_REFERENCES),
            "verified_txt_required": True, "source_release_concept": "2026-09-25",
            "expected_anchor_type": "MULTI_LINE_RULE_BLOCK_ANCHOR",
            "expected_span_policy": "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR",
            "anchor_design_id": "sha256:c42c8dd774a263f182c08e66135aca4e5668d4f5f70af480a6c0d281b187ee19",
            "one_line_blocks_permitted": True, "example_ownership_required": "UNAMBIGUOUS_OR_STOP",
            "internal_terminators": "PRESERVE_RAW_BYTES", "final_terminator": "EXCLUDED",
            "rationale": "Project the complete proposed family for coherent shared-consumer knowledge; unresolved large subsystems and primitives still prevent execution.",
            "source_coverage_implies_execution": False, "authorized": False, "started": False,
        },
        "design_notes": notes,
    }


@dataclass(frozen=True)
class ManaAbilityProjectionFrontier(DesignRecord):
    SCHEMA: ClassVar[str] = "gameplay-rules-mana-ability-projection-frontier-v1"
    ID_FIELD: ClassVar[str] = "projection_frontier_id"
    BODY_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "classification_design_id", "behavior_design_id", "controller_design_id", "evidence_status",
        "candidate_family", "candidate_source_unit_count", "coherence_review", "candidate_direct_references",
        "deferred_semantic_boundaries", "next_milestone", "design_notes",
    })

    @staticmethod
    def _validate_body(body):
        _keys(body, ManaAbilityProjectionFrontier.BODY_FIELDS)
        for field in ("classification_design_id", "behavior_design_id", "controller_design_id"):
            _hash(body[field], field)
        _strings(body["design_notes"], "design_notes")
        _exact(body, _frontier_body(body["classification_design_id"], body["behavior_design_id"],
            body["controller_design_id"], body["design_notes"]), "projection_frontier")


def build_projection_frontier(classification, behavior, controller, *, design_notes=None):
    for record, expected in ((classification, ManaAbilityClassificationDesign),
                             (behavior, ManaAbilityBehaviorDesign), (controller, ManaAbilityControllerDesign)):
        if type(record) is not expected:
            _fail("concrete immutable designs required")
        record.verify()
    return ManaAbilityProjectionFrontier.create(_frontier_body(classification.identity, behavior.identity,
        controller.identity, [] if design_notes is None else design_notes))
