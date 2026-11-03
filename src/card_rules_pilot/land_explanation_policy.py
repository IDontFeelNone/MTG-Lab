"""Small deterministic presentation policy over already admitted land premises.

This is not an admission API. The public service first validates the current
owner decision and its complete retained evidence, then supplies the unchanged
classification, behavior and effect composition. Names, subject selectors and
text searches never choose a finding here.
"""
from __future__ import annotations

import json

from . import contract as c

POLICY_VERSION = 'card-rules-accepted-land-explanation-policy-v1'
_PATTERNS = (
    'fixed_colorless', 'unrestricted_color_choice', 'targeted_land_tapping_utility',
    'damage_trigger_without_mana_output', 'swamp_count_dependent',
    'commander_color_context_dependent',
)
_DEPENDENCIES = {
    'controlled_swamp_count': 'Output depends on the controlled Swamp count, which is unknown. Potential production establishes neither actual nor net output.',
    'available_payment': 'Available payment is unknown; the written cost does not establish payment feasibility.',
    'commander_color_identity': "The written color choice is restricted by commander color identity. No commander, color identity or permitted palette is supplied; unknown is not an empty palette.",
    'legal_target_land': 'The selected utility instruction requires a target land. A legal target and strategic impact are not established.',
    'actual_trigger_event': 'Whether the described trigger event occurs is unknown; no event or actual damage is established.',
    'ordinary_trigger_procedure_603': 'General triggered placement, ordering, priority and response procedure require additional rule evidence at the unresolved broad-603 frontier.',
}
_PROCEDURE = {
    'CONDITIONAL_ACTIVATED_MANA': 'activated_no_stack',
    'CONDITIONAL_ORDINARY_ACTIVATED': 'ordinary_activated_placement_context',
    'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER': 'ordinary_triggered_route_only',
}
_OWNERSHIP = (
    'same_ability_additional_effect', 'no_additional_effect', 'separate_triggered_ability',
)
_POLICY_RAW = c.owned(c.seal(POLICY_VERSION, {
    'schema_version': POLICY_VERSION,
    'input_scope': 'Already admitted exact owner decision, retained candidate and original recomputed classification, behavior and additional-effect composition only.',
    'patterns': list(_PATTERNS), 'dependency_templates': _DEPENDENCIES,
    'procedure_consequence_selection': _PROCEDURE, 'ownership_states': list(_OWNERSHIP),
    'templates': {
        'written_capability': 'Retained written capability: {instruction}',
        'potential_mana': 'Accepted premises conditionally support potential mana production; current or net output is not established.',
        'written_cost': 'Written activation cost: {cost}. Payment feasibility remains unknown.',
        'trigger_no_activation_cost': 'No activation cost is authored for this separately selected triggered ability.',
        'no_additional_effect': 'The accepted complete-subject reading assigns no additional effect to this selected ability. Costs, targets, output and damage from other abilities do not transfer.',
        'same_ability_effect': 'Additional effect owned by this same ability: {clause} If the qualifying mana ability resolves, both instructions share its immediate-resolution context; fine-grained ordering remains unestablished.',
        'separate_trigger_effect': 'Damage belongs to this separately selected triggered ability: {clause} It is not an additional effect of the separate mana ability, and that ability supplies no mana output to this subject.',
        'procedure': 'Conditional procedure: {computed_explanation}',
        'priority_unknown': 'Pre-activation priority is unknown, so applicability of the conditional priority-return implication remains unknown.',
        'unknown': '{retained_unknown}',
        'bounded_conclusion': 'This is a capability explanation within accepted historical retained-text scope. It establishes no current legal action, completed payment, actual output, damage, or strategic advantage.',
    },
    'premise_reference_rule': 'Every finding identifies exact candidate or original assessment JSON Pointer paths; the enclosing report binds their identities and detailed evidence route.',
    'comparison_rule': 'Compare explicit capabilities, written costs, output dependencies, computed procedure and effect ownership. Equal capability premises support a shared capability; unequal premises support a difference, never a strategic ranking.',
    'excluded': ['Card-name routing', 'subject-ID routing', 'substring inference',
                 'game execution', 'strategic ranking', 'new semantic interpretation'],
}, 'policy_id'), limit=16_384)
POLICY_ID = json.loads(_POLICY_RAW)['policy_id']


def policy_document():
    """Return an independent decoded policy view."""
    return json.loads(_POLICY_RAW)


def _strings(value):
    return (type(value) is list and all(type(item) is str and item for item in value)
            and len(set(value)) == len(value))


def compute(*, readings, classification, behavior, composition, unknowns):
    """Present admitted structured premises without choosing by labels or text.

    Evidence admission and recomputation belong to the enclosing public consumer.
    These checks ensure that its original structured result relationships remain
    intact; this function cannot establish semantic acceptance on its own.
    """
    value = json.loads(c.owned(dict(readings=readings, classification=classification,
        behavior=behavior, composition=composition, unknowns=unknowns)))
    readings, classification, behavior, composition, unknowns = (
        value[key] for key in ('readings', 'classification', 'behavior', 'composition', 'unknowns'))
    if type(readings) is not dict or set(readings) != {'cost', 'output', 'conditions', 'effect_ownership'}:
        raise c.PilotError('closed admitted explanation readings required')
    expected = {
        'cost': {'written_cost', 'payment_feasibility', 'evidence_refs', 'rationale'},
        'output': {'pattern', 'written_instruction', 'actual_output', 'dependencies', 'evidence_refs', 'rationale'},
        'conditions': {'dependencies', 'supplied_game_inputs', 'evidence_refs', 'rationale'},
        'effect_ownership': {'state', 'owner_subject_id', 'card_id', 'damage_clause', 'other_subject_ids', 'evidence_refs', 'rationale', 'counterevidence', 'unresolved'},
    }
    for key, fields in expected.items():
        if type(readings[key]) is not dict or set(readings[key]) != fields:
            raise c.PilotError('closed explanation premise fields required')
    cost, output, conditions, ownership = (readings[key] for key in expected)
    if (type(output['pattern']) is not str or output['pattern'] not in _PATTERNS
            or type(output['written_instruction']) is not str or not output['written_instruction']
            or not _strings(output['dependencies']) or not _strings(conditions['dependencies'])
            or any(key not in _DEPENDENCIES for key in output['dependencies'])
            or output['dependencies'] != conditions['dependencies']
            or conditions['supplied_game_inputs'] != []
            or output['actual_output'] != 'unknown'
            or cost['payment_feasibility'] != 'unknown'
            or cost['written_cost'] is not None and (type(cost['written_cost']) is not str or not cost['written_cost'])
            or type(ownership['state']) is not str or ownership['state'] not in _OWNERSHIP
            or not _strings(ownership['other_subject_ids']) or not _strings(unknowns)):
        raise c.PilotError('unsupported or ill-typed structured explanation premise')
    if any(type(row) is not dict for row in (classification, behavior, composition)):
        raise c.PilotError('original computed explanation results required')
    c.exact(behavior.get('classification'), classification)
    c.exact(composition.get('pending_effect_ownership'), ownership)
    if (composition.get('behavior_calculation_id') != behavior.get('calculation_id')
            or composition.get('classification_policy_id') != classification.get('policy_id')
            or composition.get('classification_assessment') != classification.get('overall_assessment')
            or type(behavior.get('branch')) is not str or behavior['branch'] not in _PROCEDURE
            or type(behavior.get('consequences')) is not list
            or not _strings(classification.get('satisfied_requirements'))):
        raise c.PilotError('original computed result relationships required')
    findings = []
    templates = json.loads(_POLICY_RAW)['templates']

    def emit(category, template, paths, refs=(), **values):
        findings.append({'category': category, 'template_id': template,
            'text': templates[template].format(**values), 'premise_paths': list(paths),
            'rule_refs': list(refs)})

    emit('capability', 'written_capability', ['/candidate/descriptive_readings/output/written_instruction'],
         instruction=output['written_instruction'])
    if set(classification['satisfied_requirements']) & {'potential_mana', 'trigger_potential_mana'}:
        emit('capability', 'potential_mana', ['/assessment/classification/satisfied_requirements',
            '/candidate/descriptive_readings/output/actual_output'], ('605.2',))
    if cost['written_cost'] is None:
        if classification.get('branch') != 'triggered':
            raise c.PilotError('null activation cost requires the admitted triggered kind')
        emit('cost', 'trigger_no_activation_cost', ['/candidate/descriptive_readings/cost/written_cost',
             '/assessment/classification/branch'])
    else:
        emit('cost', 'written_cost', ['/candidate/descriptive_readings/cost/written_cost',
             '/candidate/descriptive_readings/cost/payment_feasibility'], cost=cost['written_cost'])
    for index, dependency in enumerate(output['dependencies']):
        findings.append({'category': 'restriction', 'template_id': 'dependency_' + dependency,
            'text': _DEPENDENCIES[dependency], 'premise_paths': [
                '/candidate/descriptive_readings/output/dependencies/' + str(index),
                '/candidate/descriptive_readings/conditions/supplied_game_inputs'],
            'rule_refs': []})
    state = ownership['state']
    effect_path = '/assessment/additional_effect_composition'
    if state == 'no_additional_effect':
        if composition.get('status') != 'PENDING_NO_ADDITIONAL_EFFECT_IN_SELECTED_SUBJECT':
            raise c.PilotError('original no-additional-effect composition required')
        emit('additional_effect', 'no_additional_effect', [
            '/candidate/descriptive_readings/effect_ownership/state', effect_path + '/status'])
    elif state == 'same_ability_additional_effect':
        if (composition.get('status') != 'CONDITIONAL_SAME_ABILITY_ADDITIONAL_EFFECT'
                or type(composition.get('conditional_relationship')) is not dict):
            raise c.PilotError('original same-ability composition required')
        emit('additional_effect', 'same_ability_effect', [
            '/candidate/descriptive_readings/effect_ownership/damage_clause',
            effect_path + '/conditional_relationship'], ('405.6c',), clause=ownership['damage_clause'])
    else:
        if composition.get('status') != 'SEPARATE_TRIGGERED_SUBJECT':
            raise c.PilotError('original separate-trigger composition required')
        emit('additional_effect', 'separate_trigger_effect', [
            '/candidate/descriptive_readings/effect_ownership/damage_clause', effect_path + '/status'],
            clause=ownership['damage_clause'])
    required = _PROCEDURE[behavior['branch']]
    selected = [(index, row) for index, row in enumerate(behavior['consequences'])
                if type(row) is dict and row.get('consequence_id') == required]
    if len(selected) != 1:
        raise c.PilotError('one original computed procedure consequence required')
    index, row = selected[0]
    conclusion = row.get('conditional_consequence')
    if (type(conclusion) is not dict or type(conclusion.get('explanation')) is not str
            or not _strings(row.get('rule_refs'))):
        raise c.PilotError('original computed procedure explanation required')
    emit('procedure', 'procedure', ['/assessment/behavior/consequences/' + str(index)],
         row['rule_refs'], computed_explanation=conclusion['explanation'])
    for index, row in enumerate(behavior['consequences']):
        if row.get('consequence_id') == 'activated_priority_implication':
            implication = row.get('conditional_consequence', {})
            if implication.get('status') != 'APPLICABILITY_UNKNOWN':
                raise c.PilotError('no actual or hypothetical priority premise authorized')
            emit('unknown', 'priority_unknown', ['/assessment/behavior/consequences/' + str(index)], ('405.6c',))
    for index, unknown in enumerate(unknowns):
        emit('unknown', 'unknown', ['/candidate/unresolved/' + str(index)], retained_unknown=unknown)
    emit('limitation', 'bounded_conclusion', ['/candidate/classification_present_usability_distinct',
        '/candidate/limitations', '/assessment/behavior/scope_restrictions'])
    return json.loads(c.owned(findings, limit=32_768))
