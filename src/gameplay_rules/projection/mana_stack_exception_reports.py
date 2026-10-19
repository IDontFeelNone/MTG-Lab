"""Authored source correspondence and readiness records for one bounded child.

These records preserve evidence provenance. They provide no executable stack,
priority, ability, mana, or effect semantics.
"""
from .contracts import _json
from .bounded_mana_contracts import SOURCE_BINDING, BOUNDARY_FLAGS
from .mana_stack_exception_pins import VERIFIED_ANCHORS
from .mana_stack_exception_source import SELECTED_REFERENCES
from evidence.contracts import sha256_identity

CANONICAL_MAIN = 'c9f46a2768cdee5e32f72e27d0255c6d4efbe175'
STATUS = 'BOUNDED_MANA_STACK_EXCEPTION_PROJECTED'
UNPROJECTED = [
    '405.6', '405.6a', '405.6b', '405.6d', '405.6e', '405.6f', '405.6g', '405.6h',
    '602.2', '603', '603.7d', '603.7e', '603.7f', '606', '606.3', '606.4', '606.5',
    '606.6', '114', '901.6', '902.6', '904.7', '905.5', '613', '601.2a', '601.2c',
    '601.2d', '601.2e', '601.2i', '601.3', '733', '700.2', '702.47', '118.8',
    '118.9', '107.3',
]
MISSING = [
    'real_activated_ability_semantics', 'real_triggered_ability_semantics',
    'ability_classification', 'real_effect_semantics', 'mana_production',
    'priority_semantics', 'general_stack_semantics',
]
MANA_REFERENCES = [
    '605.1', '605.1a', '605.1b', '605.2', '605.3', '605.3a', '605.3b',
    '605.3c', '605.4', '605.4a', '605.5', '605.5a', '605.5b',
]
GENERAL_STACK_BOUNDARIES = [
    'stack_object_model', 'object_ordering', 'stack_push_pop', 'spell_stack_placement',
    'activated_ability_stack_placement', 'triggered_ability_stack_placement',
    'resolution_queue', 'response_windows', 'countering', 'priority_sequencing',
    'APNAP_stack_ordering',
]
GENERAL_PRIORITY_BOUNDARIES = [
    'priority_ownership', 'priority_passing', 'APNAP_priority', 'response_windows',
    'step_phase_progression',
]


def seal(kind, body):
    content = {
        'schema_version': 'gameplay-bounded-mana-stack-exception-' + kind + '-v1',
        'canonical_base': CANONICAL_MAIN, 'source_binding': _json(SOURCE_BINDING),
        'boundary_flags': _json(BOUNDARY_FLAGS), **body,
    }
    field = 'projection_id' if kind == 'projection' else 'review_id'
    return {**content, field: 'sha256:' + sha256_identity({
        'domain': content['schema_version'], 'content': content})}


def projection():
    rule = {
        'rule_reference': '405.6c', 'source_anchor': _json(VERIFIED_ANCHORS)[0],
        'knowledge_kind': 'MANA_ABILITY_IMMEDIATE_RESOLUTION_CONTEXT',
        'immediate_resolution': {
            'applicability': 'MANA_ABILITIES', 'behavior': 'IMMEDIATE_RESOLUTION',
            'knowledge_only': True, 'resolver_created': False,
        },
        'mana_plus_additional_effect': {
            'condition': 'MANA_ABILITY_HAS_MANA_PRODUCTION_AND_ADDITIONAL_EFFECT',
            'mana_production': 'IMMEDIATE_AS_PART_OF_MANA_ABILITY_RESOLUTION',
            'additional_effect': 'IMMEDIATE_AS_PART_OF_MANA_ABILITY_RESOLUTION',
            'relationship': 'BOTH_PARTS_SHARE_IMMEDIATE_RESOLUTION_BEHAVIOR',
            'fine_grained_ordering': 'NOT_ESTABLISHED',
            'mana_before_additional_effect_inferred': False,
            'additional_effect_before_mana_inferred': False,
            'event_sequencing_implemented': False,
        },
        'post_mana_activation_priority_return_context': {
            'applicability': 'ACTIVATED_MANA_ABILITY_ONLY',
            'condition': 'PLAYER_HELD_PRIORITY_IMMEDIATELY_BEFORE_ACTIVATION',
            'recipient': 'THAT_PRE_ACTIVATION_PRIORITY_HOLDER',
            'return_context': 'AFTER_MANA_ABILITY_RESOLUTION',
            'applied_to_triggered_mana_abilities': False,
            'general_priority_semantics_supplied': False,
            'priority_runtime_implemented': False,
        },
        'no_stack_evidence_provenance': {
            'activated_direct_evidence': ['605.3b'],
            'triggered_direct_evidence': ['605.4a'],
            '405.6c_role': 'IMMEDIATE_RESOLUTION_AND_ACTIVATED_PRIORITY_CONTEXT',
            'parent_reference': '405.6',
            'parent_observation': 'STRUCTURAL_PARENT_OBSERVED_NOT_PROJECTED',
            'general_non_stack_event_semantics_supplied': False,
        },
        'direct_dependency_references': ['605'],
        'dependency_frontier': 'SECTION_REFERENCE_REQUIRES_CONCRETE_FAMILY_BINDING',
        'direct_117_dependency_created': False,
        'general_stack_semantics_supplied': False,
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
    }
    rule['rule_id'] = 'sha256:' + sha256_identity({
        'domain': 'bounded-mana-stack-exception-rule-v1', 'content': rule})
    return seal('projection', {
        'status': STATUS, 'projection_kind': 'NON_EXECUTABLE',
        'review_state': 'PROJECTED_FOR_REVIEW',
        'selected_references': list(SELECTED_REFERENCES), 'selected_rule_count': 1,
        'new_source_units_projected': 1, 'total_projected_rule_count': 85,
        'additional_rules_projected': [], 'rules': [rule],
    })


def reports(prior_manifest, mana_projection, prior_composite, projection_record, prior_rules):
    """Produce eight append-only reviews without mutating historical inputs."""
    projection_id = projection_record['projection_id']
    new_rule = projection_record['rules'][0]
    prior_id = prior_manifest['package_id']
    mana_rules = {r['rule_reference']: r for r in mana_projection['rules']}
    assert list(mana_rules) == MANA_REFERENCES

    def review(kind, findings):
        return seal(kind, {
            'status': 'APPEND_ONLY_REASSESSMENT',
            'projection_id_binding': projection_id,
            'prior_design_package_id': prior_id,
            'prior_design_record_ids': _json(prior_manifest['record_ids']),
            'historical_design_mutated': False, 'findings': findings,
        })

    def identity(ref):
        r = prior_rules[ref]
        return {
            'rule_reference': ref, 'historical_rule_id': r['rule_id'],
            'historical_direct_dependency_references': _json(r.get('direct_dependency_references', [])),
            'historical_dependency_array_rewritten': False,
            'historical_rule_mutated': False, 'historical_anchor_changed': False,
        }

    observations = [
        ('child_only_scope_coherence', 'VERIFIED', 'RETAINED_605.3b_SUPPLIES_DIRECT_ACTIVATED_NO_STACK_CONTEXT'),
        ('parent_405.6_structural_context', 'VERIFIED', 'STRUCTURAL_PARENT_OBSERVED_NOT_PROJECTED'),
        ('immediate_mana_ability_resolution', 'VERIFIED', 'MANA_ABILITY_IMMEDIATE_RESOLUTION_CONTEXT'),
        ('mana_plus_additional_effect', 'VERIFIED_WITH_REFINEMENT', 'BOTH_IMMEDIATE_WITHOUT_FINE_GRAINED_ORDERING'),
        ('post_activation_priority_return', 'VERIFIED_WITH_REFINEMENT', 'ACTIVATED_CASE_WITH_PRE_ACTIVATION_PRIORITY_CONDITION_ONLY'),
        ('direct_broad_605_citation', 'VERIFIED', 'SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY'),
        ('general_stack_semantics_not_supplied', 'VERIFIED', 'GENERAL_STACK_BOUNDARY_OPEN'),
        ('general_priority_semantics_not_supplied', 'VERIFIED', 'PRIORITY_SEMANTICS_BOUNDARY_OPEN'),
        ('semantic_overlap_with_605.4a', 'VERIFIED_WITH_REFINEMENT', 'SEMANTIC_OVERLAP_WITHOUT_DIRECT_CR_CITATION'),
        ('parent_not_necessary_for_bounded_consumer_scope', 'VERIFIED', 'RETAINED_CONSUMER_CONTEXT_AND_CHILD_ADDITIONAL_KNOWLEDGE_ARE_COHERENT'),
        ('direct_no_stack_provenance', 'VERIFIED_WITH_REFINEMENT', 'ACTIVATED_605.3b_TRIGGERED_605.4a_PARENT_UNPROJECTED'),
        ('triggered_priority_return', 'FOUND_ADDITIONAL_BOUNDARY', 'ACTIVATED_PRIORITY_SENTENCE_DOES_NOT_ESTABLISH_TRIGGERED_RETURN'),
    ]
    correspondence = review('design-source-correspondence', {
        'prior_authority': 'PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED',
        'new_authority': 'EXACT_SELECTED_SOURCE_BLOCK_VERIFIED',
        'observations': [dict(rule_reference='405.6c', observation=o, result=s, finding=f)
                         for o, s, f in observations],
        'contradictions': [], 'discrepancies': [], 'additional_rule_required': False,
        'source_verified_selected_count': 1, 'historical_design_rewritten': False,
    })
    parent = review('parent-scope-review', {
        'rule_reference': '405.6c', 'parent_reference': '405.6',
        'parent_observation': 'STRUCTURAL_PARENT_OBSERVED_NOT_PROJECTED',
        'parent_observed': True, 'parent_projected': False,
        'parent_anchor_retained': False, 'parent_prose_retained': False,
        'parent_required_for_this_bounded_consumer_scope': False,
        'scope_coherence': 'CHILD_ONLY_COHERENT_WITH_RETAINED_605.3b_CONTEXT',
        'direct_consumer': identity('605.3b'),
        'retained_consumer_knowledge': ['ACTIVATED_MANA_NO_STACK', 'ACTIVATED_MANA_IMMEDIATE_RESOLUTION'],
        'new_child_knowledge': ['MANA_ABILITY_IMMEDIATE_RESOLUTION_CONTEXT',
            'MANA_AND_ADDITIONAL_EFFECT_IMMEDIATE_BEHAVIOR', 'ACTIVATED_MANA_PRIORITY_RETURN_CONTEXT'],
        'general_parent_semantics': 'UNPROJECTED',
        'siblings_inspected_as_transient_source_shape_only': True,
        'sibling_rules_projected': [], 'automatic_parent_admission': False,
        'broad_405.6_family_represented': False,
        'general_non_stack_event_semantics_supplied': False,
        'local_source_shape': 'RELEASE_SPECIFIC_405.6c_BLOCK_WITH_EXACT_405.6d_TERMINATION',
        'source_prose_retained': False,
    })
    direct = {
        'from_reference': '605.3b', 'target_reference': '405.6c',
        'reference_state': 'DIRECT_REFERENCE_RESOLVED',
        'historical_rule_id': mana_rules['605.3b']['rule_id'],
        'target_rule_id': new_rule['rule_id'],
        'historical_direct_dependency_references': _json(mana_rules['605.3b']['direct_dependency_references']),
        'historical_dependency_array_rewritten': False,
        'source_coverage_state': 'IMPROVED', 'semantic_closure': 'OPEN',
        'execution_readiness': 'BLOCKED', 'source_reference_resolution_implies_execution': False,
    }
    family_bindings = [{
        'rule_reference': ref, 'rule_id': mana_rules[ref]['rule_id'],
        'source_anchor': _json(mana_rules[ref]['source_anchor']),
    } for ref in MANA_REFERENCES]
    section = {
        'from_reference': '405.6c', 'source_citation': '605',
        'citation_kind': 'BROAD_SECTION_REFERENCE',
        'state': 'SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY',
        'concrete_family_references': list(MANA_REFERENCES),
        'concrete_family_count': 13, 'concrete_family_bindings': family_bindings,
        'family_projection_id': mana_projection['projection_id'],
        'synthetic_605_rule_created': False, 'historical_605_family_mutated': False,
        'family_source_units_reprojected': 0, 'semantic_closure': 'OPEN',
        'execution_readiness': 'BLOCKED',
    }
    semantic_overlap = {
        **identity('605.4a'), 'related_reference': '405.6c',
        'relationship': 'SEMANTIC_OVERLAP_WITHOUT_DIRECT_CR_CITATION',
        'direct_405.6c_citation': False, 'new_direct_cr_citations': [],
        'triggered_no_stack_evidence': ['605.4a'],
        'triggered_immediate_resolution_evidence': ['605.4a'],
        '405.6c_role': 'SEMANTIC_FAMILY_OVERLAP',
        'priority_return_from_405.6c_applied_to_triggered': False,
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
    }
    dependency = review('section-dependency-review', {
        'exact_outgoing_numbered_references': ['605'],
        'section_reference': section,
        'direct_reference_reassessments': [direct],
        'semantic_overlap': semantic_overlap,
        'invented_direct_numbered_references': [],
        'direct_117_dependency_created': False,
        'source_reference_resolution_implies_semantic_closure': False,
        'source_reference_resolution_implies_general_stack_support': False,
        'source_reference_resolution_implies_priority_implementation': False,
        'remaining_unprojected_references': list(UNPROJECTED),
    })
    activated = {
        **identity('605.3b'), 'direct_405.6c_reference': 'DIRECT_REFERENCE_RESOLVED',
        'resolved_target_rule_id': new_rule['rule_id'],
        'source_coverage_state': 'IMPROVED',
        'no_stack_evidence': ['605.3b'],
        'immediate_resolution_evidence': ['605.3b', '405.6c'],
        'post_activation_priority_evidence': ['405.6c'],
        'remaining_semantic_dependencies': list(MISSING),
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
    }
    casting = {
        **identity('601.2g'), 'new_direct_cr_citations': [],
        'new_direct_405.6c_citation': False,
        'path': ['601.2g', '605', 'activated_mana_behavior'],
        'relationship': 'INDIRECT_SOURCE_COVERAGE_IMPROVEMENT',
        '605_section': 'SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY',
        'source_coverage_state': 'IMPROVED_INDIRECTLY',
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
    }
    madness = {
        'consumer': 'Madness', 'path': ['702.35b', 'bounded_casting', '601.2g', '605'],
        'relationship': 'INDIRECT', 'new_direct_cr_citations': [],
        'new_direct_405.6c_citation': False,
        'source_coverage_state': 'IMPROVED_INDIRECTLY',
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
    }
    controller = {
        **identity('109.4a'), 'new_direct_cr_citations': [],
        'new_direct_405.6c_dependency': False,
        'controller_attribution': 'SEPARATE_UNRESOLVED_SEMANTIC_BOUNDARY',
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
    }
    consumers = review('consumer-reassessment', {
        'direct_reference_reassessments': [direct],
        'consumers': [activated, semantic_overlap, casting, madness, controller],
        'new_direct_cr_citations_invented': [],
        'source_coverage_implies_execution': False,
    })
    stack = review('stack-exception-readiness', {
        'capability': 'mana_ability_stack_exception_context',
        'source_coverage': ['605.3b', '605.4a', '405.6c'],
        'source_coverage_state': 'IMPROVED',
        'state': 'REPRESENTED_WITH_OPEN_DEPENDENCIES',
        'activated_mana_abilities': {
            'no_stack_evidence': ['605.3b'],
            'immediate_resolution_evidence': ['605.3b', '405.6c'],
            'post_activation_priority_evidence': ['405.6c'],
            'direct_reference_relationship': '605.3b_TO_405.6c_RESOLVED',
        },
        'triggered_mana_abilities': {
            'no_stack_evidence': ['605.4a'],
            'immediate_resolution_evidence': ['605.4a'],
            '405.6c_relationship': 'SEMANTIC_OVERLAP_WITHOUT_DIRECT_CR_CITATION',
            'direct_405.6c_citation': False,
            'post_activation_priority_return_inferred': False,
        },
        'general_405.6_parent_projected': False,
        'general_stack_semantics': 'OPEN',
        'unrepresented_general_stack_boundaries': list(GENERAL_STACK_BOUNDARIES),
        'response_windows': 'OPEN', 'countering': 'OPEN', 'resolution_queue': 'OPEN',
        'source_coverage_implies_general_stack_support': False,
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
        'runtime_implemented': False,
    })
    priority = review('priority-readiness', {
        'capability': 'post_mana_activation_priority_return_context',
        'source_coverage': ['405.6c'],
        'state': 'REPRESENTED_WITH_OPEN_DEPENDENCIES',
        'condition': 'PLAYER_HELD_PRIORITY_IMMEDIATELY_BEFORE_MANA_ABILITY_ACTIVATION',
        'post_resolution_context': 'SAME_PLAYER_RECEIVES_PRIORITY',
        'applicability': 'ACTIVATED_MANA_ABILITY_ONLY',
        'triggered_priority_return_inferred': False,
        'general_priority_semantics': 'OPEN',
        'general_priority_source_coverage': 'UNPROJECTED',
        'unrepresented_general_priority_boundaries': list(GENERAL_PRIORITY_BOUNDARIES),
        'direct_117_dependency_created': False, 'rule_117_projected': False,
        'priority_runtime_implemented': False,
        'source_coverage_implies_general_priority_support': False,
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
    })
    next_milestone = {
        'candidate': 'Activated Ability Procedure Design',
        'exact_proposed_design_scope': ['602.2', '602.2a', '602.2b'],
        'scope_kind': 'DEDICATED_SUBSYSTEM_DESIGN_BEFORE_ANY_SOURCE_PROJECTION',
        'provisional_input': 'EXISTING_602.2_602.2a_602.2b_CLUSTER_IS_DESIGN_INPUT_ONLY',
        'future_source_allowlist': [],
        'target_consumers': ['605.3', '605.3b', '601.2g', 'bounded_casting', 'Madness'],
        'deliberately_unresolved': ['603', 'priority_semantics', 'general_stack_semantics',
            'target_recognition', 'real_card_semantics', 'real_effect_semantics',
            'mana_production', 'controller_attribution', '613'],
        'rationale': 'The one-unit stack-context reference is resolved; the large activation procedure remains a direct blocker for retained activated mana behavior and its casting consumers.',
        'source_txt_required': True, 'authorized': False,
    }
    readiness = review('overall-readiness', {
        'capability': 'mana_ability_stack_exception_context',
        'source_coverage_state': 'IMPROVED',
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
        'real_execution_profile': 'magic-comprehensive-rules-20260925-v1',
        'profile_status': 'DESIGN_ONLY / NOT EXECUTABLE',
        'readiness_code': 'REAL_EXECUTION_PROFILE_NOT_READY',
        'blocked_consumers': ['mana_abilities', 'casting', 'object_control', 'Madness'],
        'missing_semantic_evidence': list(MISSING),
        'general_stack_semantics': 'OPEN', 'priority_semantics': 'OPEN',
        'original_mana_direct_dependency_frontier': {
            'resolved_source_units': ['115.6', '405.6c'],
            'bounded_classification_evidence': ['606.1', '606.2'],
            'broad_606': 'PARTIALLY_REPRESENTED_NOT_SECTION_COMPLETE',
            'major_unresolved_direct_subsystem_targets': ['602.2', '603'],
            'original_five_target_frontier_fully_solved': False,
        },
        'large_unprojected_frontiers': [
            {'reference': '602.2', 'classification': 'LARGE_CORE_SUBSYSTEM', 'projected': False},
            {'reference': '603', 'classification': 'LARGE_SHARED_CORE_SUBSYSTEM', 'projected': False},
            {'references': ['603.7d', '603.7e', '603.7f'], 'classification': 'DELAYED_TRIGGER_CONTROLLER_FRONTIER', 'projected': False},
            {'reference': '606', 'classification': 'PARTIAL_CLASSIFICATION_ONLY', 'section_complete': False},
            {'reference': '613', 'classification': 'CONTINUOUS_EFFECTS', 'projected': False},
        ],
        'remaining_unprojected_references': list(UNPROJECTED),
        'fictional_mana_satisfies_real_605': False,
        'next_milestone_recommendation_count': 1, 'next_milestone': next_milestone,
    })
    components = _json(prior_composite['projection_components'])
    components.append({
        'name': 'bounded_mana_stack_exception', 'projection_id': projection_id,
        'package_binding': 'THIS_ENCLOSING_PACKAGE',
        'projected_references': list(SELECTED_REFERENCES),
    })
    refs = [ref for c in components for ref in c['projected_references']]
    assert len(components) == len({c['projection_id'] for c in components}) == 9
    assert [len(c['projected_references']) for c in components] == [20, 12, 7, 12, 12, 5, 13, 3, 1]
    assert len(refs) == len(set(refs)) == 85
    assert not set(refs).intersection(UNPROJECTED)
    assert '605' not in refs
    composite = review('composite-coverage', {
        'view_kind': 'READ_ONLY_NINE_PROJECTION_COMPOSITE',
        'projection_components': components, 'projected_references': refs,
        'previous_count': 84, 'new_count': 1, 'total_projected_rule_count': 85,
        'projection_identities_preserved': True,
        'monolithic_projection_created': False,
    })
    return {name + '.json': value for name, value in [
        ('design-source-correspondence', correspondence), ('parent-scope-review', parent),
        ('section-dependency-review', dependency), ('consumer-reassessment', consumers),
        ('stack-exception-readiness', stack), ('priority-readiness', priority),
        ('overall-readiness', readiness), ('composite-coverage', composite),
    ]}
