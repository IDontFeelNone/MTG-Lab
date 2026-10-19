"""Project-authored correspondence and readiness findings; no executable semantics."""
from .contracts import _json
from .bounded_mana_contracts import SOURCE_BINDING, BOUNDARY_FLAGS
from .mana_classification_pins import VERIFIED_ANCHORS
from .mana_classification_source import SELECTED_REFERENCES
from evidence.contracts import sha256_identity

CANONICAL_MAIN = '7082d7c048ef764d5e5ec8d5ea42e2ab9d3dbb28'
STATUS = 'BOUNDED_MANA_CLASSIFICATION_DEPENDENCIES_PROJECTED'
UNPROJECTED = ['606', '606.3', '606.4', '606.5', '606.6', '405.6c', '602.2', '603',
    '603.7d', '603.7e', '603.7f', '114', '901.6', '902.6', '904.7', '905.5', '613',
    '601.2a', '601.2c', '601.2d', '601.2e', '601.2i', '601.3', '733', '700.2',
    '702.47', '118.8', '118.9', '107.3']
MISSING = ['general_target_recognition', 'real_activated_ability_semantics',
    'real_triggered_ability_semantics', 'loyalty_symbol_parsing', 'library_movement_semantics',
    'replacement_effect_semantics', 'potential_mana_output_semantics', 'real_card_effect_semantics']
RULE_CONTENT = {
    '115.6': {
        'knowledge_kind': 'TARGET_REQUIREMENT_DISTINCTION',
        'target_requirement': 'MAY_PERSIST_WHEN_ZERO_TARGETS_ARE_CHOSEN',
        'chosen_target_count': 'ACTUAL_SELECTION_COUNT_SEPARATE_FROM_REQUIREMENT',
        'targeted_status': 'UNDER_THIS_RULE_REQUIRES_ONE_OR_MORE_ACTUALLY_CHOSEN_TARGETS',
        'zero_selected_implies_no_target_requirement': False,
        'target_requirement_distinct_from_legality': True,
        'recognizes_arbitrary_ability_target_requirements': False,
    },
    '606.1': {'knowledge_kind': 'LOYALTY_CATEGORY_CONTEXT',
        'category': 'SOME_ACTIVATED_ABILITIES_ARE_LOYALTY_ABILITIES_SUBJECT_TO_SPECIAL_RULES',
        'timing_or_cost_rule': False},
    '606.2': {'knowledge_kind': 'LOYALTY_CLASSIFICATION_CRITERION',
        'criterion': 'ACTIVATED_ABILITY_WITH_LOYALTY_SYMBOL_IN_ACTIVATION_COST',
        'planeswalker_context': 'NORMAL_ASSOCIATION_ONLY',
        'only_planeswalkers_can_have_loyalty_abilities': False,
        'loyalty_symbol_parser_supplied': False},
}


def seal(kind, body):
    content = {'schema_version': 'gameplay-bounded-mana-classification-'+kind+'-v1',
        'canonical_base': CANONICAL_MAIN, 'source_binding': _json(SOURCE_BINDING),
        'boundary_flags': _json(BOUNDARY_FLAGS), **body}
    field = 'projection_id' if kind == 'projection' else 'review_id'
    return {**content, field: 'sha256:'+sha256_identity({'domain': content['schema_version'], 'content': content})}


def projection():
    rules = []
    for ref, anchor in zip(SELECTED_REFERENCES, _json(VERIFIED_ANCHORS)):
        rule = {'rule_reference': ref, 'source_anchor': anchor, **RULE_CONTENT[ref],
            'direct_dependency_references': [],
            'dependency_frontier': 'NO_EXPLICIT_OUTGOING_NUMBERED_REFERENCES',
            'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED'}
        rule['rule_id'] = 'sha256:'+sha256_identity({'domain': 'bounded-mana-classification-rule-v1', 'content': rule})
        rules.append(rule)
    return seal('projection', {'status': STATUS, 'projection_kind': 'NON_EXECUTABLE',
        'review_state': 'PROJECTED_FOR_REVIEW', 'selected_references': list(SELECTED_REFERENCES),
        'selected_rule_count': 3, 'new_source_units_projected': 3, 'total_projected_rule_count': 84,
        'additional_rules_projected': [], 'rules': rules})


def reports(prior_manifest, mana_projection, mana_composite, projection_record):
    projection_id = projection_record['projection_id']
    prior_id = prior_manifest['package_id']
    def review(kind, findings):
        return seal(kind, {'status': 'APPEND_ONLY_REASSESSMENT', 'projection_id_binding': projection_id,
            'prior_design_package_id': prior_id, 'prior_design_record_ids': prior_manifest['record_ids'],
            'historical_design_mutated': False, 'findings': findings})
    observed = [
        ('115.6', 'target_requirement_distinct_from_chosen_count', 'VERIFIED'),
        ('115.6', 'targeted_status_depends_on_actual_chosen_targets', 'VERIFIED'),
        ('115.6', 'narrow_standalone_coherence', 'VERIFIED'),
        ('115.6', 'target_legality_not_supplied', 'VERIFIED'),
        ('115.6', 'target_parser_not_supplied', 'VERIFIED'),
        ('115.6', 'zero_count_does_not_negate_requirement', 'VERIFIED_WITH_REFINEMENT'),
        ('606.1', 'loyalty_category_context', 'VERIFIED'),
        ('606.2', 'loyalty_symbol_classification_criterion', 'VERIFIED'),
        ('606.2', 'contextual_planeswalker_statement_not_exclusivity', 'VERIFIED_WITH_REFINEMENT'),
        ('606.2', 'symbol_and_cost_recognition_remain_absent', 'FOUND_ADDITIONAL_BOUNDARY'),
    ]
    correspondence = review('design-source-correspondence', {
        'prior_authority': 'PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED',
        'new_authority': 'EXACT_SELECTED_SOURCE_BLOCKS_VERIFIED',
        'observations': [dict(rule_reference=r, observation=o, result=s) for r,o,s in observed],
        'contradictions': [], 'discrepancies': [], 'additional_rule_required': False})
    mana_rules = {r['rule_reference']: r for r in mana_projection['rules']}
    def consumer(ref, missing, improved):
        r = mana_rules[ref]
        return {'rule_reference': ref, 'historical_rule_id': r['rule_id'],
            'historical_direct_dependency_references': r['direct_dependency_references'],
            'historical_dependency_array_rewritten': False, 'historical_rule_mutated': False,
            'improved': improved, 'remaining_semantic_dependencies': missing,
            'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED'}
    activated = consumer('605.1a', MISSING, ['115.6_target_requirement_distinction', '606.1_606.2_loyalty_classification'])
    activated['criteria'] = {
        'target': {'direct_115.6_reference': 'DIRECT_REFERENCE_RESOLVED', 'requirement_recognition': 'OPEN'},
        'loyalty': {'classification_relationship': 'REPRESENTED', 'broad_606_section': 'OPEN',
            'section_state': 'SECTION_DEPENDENCY_PARTIALLY_REPRESENTED_FOR_CLASSIFICATION'},
        'library_movement': 'DESCRIPTIVE_ONLY_CARD_EFFECT_SEMANTICS_ABSENT',
        'potential_mana_output': 'DESCRIPTIVE_ONLY', 'replacement_effect_distinction': 'DESCRIPTIVE_ONLY'}
    triggered = consumer('605.1b', ['triggered_target_requirement_recognition', 'general_trigger_semantics',
        'trigger_relationship_evaluation', 'potential_mana_output_semantics', 'real_card_effect_semantics'], ['115.6_target_requirement_distinction'])
    triggered['direct_115.6_reference'] = 'DIRECT_REFERENCE_RESOLVED'
    direct = [{'from_reference': ref, 'target_reference': '115.6', 'reference_state': 'DIRECT_REFERENCE_RESOLVED',
        'ability_target_requirement_semantic_closure': 'OPEN', 'real_classification_execution': 'BLOCKED',
        'historical_rule_id': mana_rules[ref]['rule_id']} for ref in ('605.1a','605.1b')]
    dependency = review('classification-dependency-review', {'direct_reference_reassessments': direct,
        'section_reassessment': {'from_reference': '605.1a', 'source_citation': '606',
            'state': 'SECTION_DEPENDENCY_PARTIALLY_REPRESENTED_FOR_CLASSIFICATION',
            'broad_606_section_resolution': 'OPEN', 'classification_specific_relationship': 'REPRESENTED',
            'execution_behavior_scope': 'UNPROJECTED', 'historical_dependency_array_rewritten': False,
            'historical_605.1a_rule_mutated': False},
        'derived_classification_evidence': {'consumer': '605.1a', 'source_citation': '606',
            'evidence_references': ['606.1','606.2'], 'relationship_kind': 'DERIVED_CLASSIFICATION_RELATIONSHIP',
            'new_direct_cr_citations': [], 'purpose': 'LOYALTY_EXCLUSION_CATEGORY_EVIDENCE'},
        'activated_classification': activated, 'triggered_classification': triggered,
        'remaining_unprojected_references': UNPROJECTED})
    consumers = review('consumer-reassessment', {'consumers': [activated, triggered,
        {'rule_reference': '601.2g', 'new_direct_source_dependency': False,
         '605_section': 'SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY',
         'execution_blockers': ['real_mana_classification', 'activation_semantics'], 'execution_readiness': 'BLOCKED'},
        {'consumer': 'Madness', 'path': ['702.35b','bounded_casting','601.2g','605'],
         'relationship': 'INDIRECT', 'new_direct_cr_citations': [], 'execution_readiness': 'BLOCKED'}]})
    target = review('target-readiness', {'capability': 'target_requirement_semantics',
        'source_coverage': ['115.6'], 'dimensions': {
            'requirement_vs_selected_count_distinction': 'BOUNDED_SOURCE_COVERAGE',
            **{key:'BLOCKED_UNPROJECTED' for key in ['target_grammar_recognition','keyword_defined_targets',
                'legal_target_determination','target_selection','target_change_reselection']}},
        'semantic_boundaries': ['activated_ability_target_grammar','triggered_ability_target_grammar',
            'keyword_defined_targeting','aura_targeting','general_target_recognition','target_legality',
            'target_selection','real_card_effect_semantics'],
        'general_targeting_supported': False, 'runtime_implemented': False,
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED'})
    loyalty = review('loyalty-readiness', {'capabilities': [
        {'capability': 'loyalty_ability_classification', 'source_coverage': ['606.1','606.2'],
         'state': 'REPRESENTED_WITH_OPEN_SEMANTIC_DEPENDENCIES', 'semantic_closure': 'OPEN',
         'missing': ['loyalty_symbol_parsing','activation_cost_parsing','ability_semantics'], 'execution_readiness': 'BLOCKED'},
        {'capability': 'loyalty_ability_execution', 'source_coverage': 'INCOMPLETE',
         'unprojected_references': ['606.3','606.4','606.5','606.6'], 'execution_readiness': 'BLOCKED',
         'missing': ['activation_timing','stack_state','main_phase_state','prior_activation_history',
            'loyalty_counter_addition_removal','modified_loyalty_costs','combined_loyalty_costs',
            'negative_cost_sufficiency','cost_payment']}],
        'classification_implies_execution': False, 'broad_606_section_resolution': 'OPEN', 'runtime_implemented': False})
    readiness = review('overall-readiness', {'capability': 'mana_ability_classification',
        'source_coverage': ['605.1','605.1a','605.1b','605.2','605.5','605.5a','605.5b',*SELECTED_REFERENCES],
        'source_coverage_state': 'IMPROVED', 'missing_semantic_evidence': MISSING,
        'semantic_closure': 'OPEN', 'execution_readiness': 'BLOCKED',
        'real_execution_profile': 'magic-comprehensive-rules-20260925-v1',
        'profile_status': 'DESIGN_ONLY / NOT EXECUTABLE', 'readiness_code': 'REAL_EXECUTION_PROFILE_NOT_READY',
        'blocked_consumers': ['mana_abilities','casting','object_control','Madness'],
        'fictional_mana_satisfies_real_605': False, 'remaining_unprojected_references': UNPROJECTED,
        'next_milestone': {'candidate': 'Bounded Mana Stack-Exception Projection',
            'exact_proposed_scope': ['405.6c'], 'parent_review_only': '405.6',
            'parent_admission': 'REQUIRES_FUTURE_SOURCE_VERIFICATION_AND_SEPARATE_SCOPE_AUTHORIZATION_IF_NECESSARY',
            'rationale': 'Small immediate consumer frontier for 605.3b; preserves shared activation and trigger subsystem boundaries.',
            'source_txt_required': True, 'authorized': False}})
    components = mana_composite['projection_components']
    components.append({'name':'bounded_mana_classification_dependencies', 'projection_id':projection_id,
        'package_binding':'THIS_ENCLOSING_PACKAGE', 'projected_references':list(SELECTED_REFERENCES)})
    refs = [ref for c in components for ref in c['projected_references']]
    assert len(components) == len({c['projection_id'] for c in components}) == 8
    assert [len(c['projected_references']) for c in components] == [20,12,7,12,12,5,13,3]
    assert len(refs) == len(set(refs)) == 84
    assert not set(refs).intersection(UNPROJECTED)
    composite = review('composite-coverage', {'view_kind':'READ_ONLY_EIGHT_PROJECTION_COMPOSITE',
        'projection_components':components, 'projected_references':refs, 'previous_count':81,
        'new_count':3, 'total_projected_rule_count':84, 'projection_identities_preserved':True})
    return {name+'.json': value for name,value in [
        ('design-source-correspondence',correspondence),('classification-dependency-review',dependency),
        ('consumer-reassessment',consumers),('target-readiness',target),('loyalty-readiness',loyalty),
        ('overall-readiness',readiness),('composite-coverage',composite)]}
