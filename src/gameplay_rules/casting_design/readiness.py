"""Deterministic Madness readiness analysis; no casting or payment execution."""
from dataclasses import dataclass

from .common import DesignRecord, _exact, _hash, _strings, _json, _fail
from .evidence import RETAINED_BINDING, EXISTING_UNPROJECTED_REFERENCES
from .frontier import OUTSIDE_CANDIDATE_REFERENCES, ProjectionFrontierDesign
from .anchors import MultiLineSourceAnchorDesign
from .stages import CastingSubprocedureDesign
from .costs import CostModelDesign

_DIMENSION_SCOPES = (
    ("discard_replacement_semantics", ["702.35a"], [], ["discard_replacement", "discard_execution"]),
    ("exile_semantics", ["702.35a"], [], ["exile_zone_movement"]),
    ("madness_trigger_semantics", ["702.35a"], [], ["trigger_detection", "trigger_resolution"]),
    ("casting_permission", ["702.35a"], [], ["casting_permission_prohibition", "timing_and_priority"]),
    ("alternative_cost_selection", ["702.35a", "702.35b"], ["601.2b", "118.9"], ["alternative_cost_choice", "choice_restrictions"]),
    ("total_cost_determination", ["702.35b"], ["601.2f"], ["total_cost_expression", "cost_modifiers", "cost_locking"]),
    ("mana_ability_window", ["702.35b"], ["601.2g", "605"], ["mana_ability_opportunity", "real_mana_abilities"]),
    ("payment", ["702.35b"], ["601.2h"], ["locked_cost_payment", "mana_payment", "nonmana_payment", "random_and_library_payment_groups"]),
    ("full_spell_casting_legality", [], [], ["spell_proposal", "targets", "legality", "casting_completion", "stack", "priority", "illegal_action_rollback"]),
    ("public_zone_fallback_if_not_cast", ["702.35a", "702.35c"], [], ["uncast_choice", "graveyard_movement", "public_zone_tracking"]),
    ("zone_change_lookup", ["702.35c", "400.7k"], [], ["discarded_card_result_lookup", "object_history_execution"]),
)


def _body(binding, casting_id, cost_id, anchor_id, frontier_id):
    dimensions = [{"dimension": name, "supporting_existing_projected_rules": projected,
                   "unprojected_design_reference_candidates": candidates,
                   "required_unimplemented_primitives": primitives,
                   "evidence_scope": "DESCRIPTIVE_ONLY" if projected else "UNREPRESENTED_COMPLETE_SUBSYSTEM",
                   "dependency_closure": "OPEN", "semantic_closure": "OPEN",
                   "implementation_available": False, "execution_supported": False,
                   "execution_status": "EXECUTION_BLOCKED"}
                  for name, projected, candidates, primitives in _DIMENSION_SCOPES]
    primitives = list(dict.fromkeys(item for _, _, _, items in _DIMENSION_SCOPES for item in items))
    return {
        "retained_evidence": binding,
        "casting_design_id": casting_id, "cost_design_id": cost_id,
        "source_anchor_design_id": anchor_id, "projection_frontier_id": frontier_id,
        "binding_policy": "IMMUTABLE_EXISTING_RULE_IDENTITIES_NO_REPROJECTION",
        "conceptual_madness_path": [
            "DISCARD_REPLACEMENT_AND_EXILE", "MADNESS_TRIGGER", "OWNER_OPTIONAL_CAST_CHOICE",
            "CANDIDATE_MADNESS_ALTERNATIVE_COST", "CASTING_CHOICES", "TOTAL_COST_DETERMINATION",
            "CONDITIONAL_MANA_ABILITY_WINDOW", "TOTAL_COST_PAYMENT", "LATER_CASTING_STAGES_OUTSIDE_DESIGN",
        ],
        "conceptual_path_execution": False,
        "dimensions": dimensions,
        "capabilities": [
            {"capability_id": "madness", "representation": "EXISTING_DESCRIPTIVE_EVIDENCE_AND_NEW_DESIGN",
             "dependency_closure": "OPEN", "semantic_closure": "OPEN", "execution_status": "EXECUTION_BLOCKED"},
            {"capability_id": "alternative_cost_casting_subprocedure", "representation": "FOUR_STAGE_DESIGN_ONLY",
             "complete_casting_implied": False, "satisfied_by_fictional_runtime": False,
             "requires_independent_source_projection_and_semantics": True, "execution_status": "EXECUTION_BLOCKED"},
            {"capability_id": "complete_spell_casting", "representation": "OUTSIDE_DESIGN",
             "satisfied_by_alternative_cost_subprocedure": False,
             "requires_independent_closure": True, "execution_status": "EXECUTION_BLOCKED"},
        ],
        "fictional_runtime_authority_inherited": False,
        "fictional_mana_satisfies_real_605": False,
        "605_status": "UNRESOLVED_UNPROJECTED",
        "required_future_semantic_primitives": primitives,
        "real_execution_primitives_available": [],
        "remaining_unprojected_numbered_boundaries": list(dict.fromkeys([*EXISTING_UNPROJECTED_REFERENCES, *OUTSIDE_CANDIDATE_REFERENCES])),
        "candidate_reference_authority": "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED",
        "source_projections_added": 0, "projected_rule_count_before": 63, "projected_rule_count_after": 63,
        "overall_readiness": "EXECUTION_BLOCKED",
        "real_execution_profile_readiness": "REAL_EXECUTION_PROFILE_NOT_READY",
        "blockers": ["SOURCE_PROJECTION_FRONTIER_OPEN", "COMPLETE_CASTING_SEMANTICS_OPEN",
                     "REQUIRED_PRIMITIVES_ABSENT", "REAL_CARD_EFFECT_SEMANTICS_ABSENT",
                     "DETERMINISTIC_RUNTIME_VECTORS_ABSENT", "OWNER_ACTIVATION_NOT_GRANTED"],
        "limitations": ["Design declarations do not perform casting, determine costs, pay costs, generate mana, or move objects.",
                        "An alternative-cost subprocedure never supplies complete casting authority.",
                        "Existing public-zone Madness lookup evidence does not implement fallback movement or object history.",
                        "Real 605 closure cannot be inherited from fictional mana behavior."],
        "design_notes": ["All three conceptual capabilities remain blocked despite the represented high-level Madness definition."],
    }


@dataclass(frozen=True)
class MadnessCastingReadiness(DesignRecord):
    SCHEMA = "madness-casting-readiness-design-v1"
    ID_FIELD = "madness_readiness_id"
    BODY_FIELDS = frozenset(_body({}, "", "", "", ""))

    @staticmethod
    def _validate_body(body):
        for field in ("casting_design_id", "cost_design_id", "source_anchor_design_id", "projection_frontier_id"):
            _hash(body[field], field)
        _exact(body["retained_evidence"], RETAINED_BINDING, "retained_evidence")
        expected = _body(body["retained_evidence"], body["casting_design_id"], body["cost_design_id"],
                         body["source_anchor_design_id"], body["projection_frontier_id"])
        for key, value in expected.items():
            if key != "design_notes":
                _exact(body[key], value, key)
        _strings(body["design_notes"], "design_notes", nonempty=True)


def build_madness_readiness(binding, casting, cost, anchor, frontier):
    for record, expected_type in ((casting, CastingSubprocedureDesign), (cost, CostModelDesign),
                                  (anchor, MultiLineSourceAnchorDesign), (frontier, ProjectionFrontierDesign)):
        if type(record) is not expected_type:
            _fail("typed non-executable design records required for readiness analysis")
        record.verify()
    _exact(cost.casting_design_id, casting.identity, "cost_casting_binding")
    return MadnessCastingReadiness.create(_body(_json(binding), casting.identity, cost.identity, anchor.identity, frontier.identity))
