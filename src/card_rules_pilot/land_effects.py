"""Conditional same-ability composition over explicit pending ownership readings.

No Card labels or text recognition select a consequence. The caller admits real
evidence and candidate bindings; this pure composition additionally recomputes
the unchanged classification/behavior calculations and owns every input first.
"""
from __future__ import annotations

import hashlib
import json
import re

from . import behavior_policy
from .contract import PilotError, canonical, exact, identity, owned, seal


POLICY_VERSION = 'card-rules-land-effect-ownership-policy-v1'
RESULT_VERSION = 'card-rules-land-effect-ownership-composition-v1'
CANDIDATE_VERSION = 'card-rules-land-mana-utility-pending-interpretation-v1'
LIMIT = 262_144
RESULT_LIMIT = 65_536
_STATES = ('same_ability_additional_effect', 'no_additional_effect',
           'separate_triggered_ability', 'unknown', 'conflicting')
_AUTHORITY = {
    'authority': 'CONDITIONAL_COMPOSITION_FROM_PENDING_EFFECT_OWNERSHIP_ONLY',
    'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
    'review': {'status': 'requires_review', 'human_attestation': None,
               'canonical_admission': False},
    'execution_authority': 'BLOCKED',
}
_POLICY_RAW = owned(seal(POLICY_VERSION, {
    'schema_version': POLICY_VERSION,
    'behavior_policy_id': behavior_policy.POLICY_ID,
    'ownership_states': list(_STATES),
    'same_ability_rule': 'A recomputed qualifying mana branch, explicit source-bound pending same-ability ownership, and exact 405.6c evidence jointly support conditional shared immediate-resolution context.',
    'interpretation_binding_rule': 'Reproduce the complete pending candidate own identity in its exact domain; bind its complete subject, effect-ownership reading, kind and criterion inputs exactly to this composition. An expressly authored effect clause must occur uniquely within that selected passage; offsets express correspondence only.',
    'separate_ability_rule': 'A separately owned triggered subject retains its actual recomputed behavior and unresolved procedure frontier. Another subject supplies it neither mana output nor an additional-effect relationship.',
    'baseline_rule': 'The unchanged calculation received no effect-ownership input. Its lack of an additional-effect assertion is retained separately and is not evidence that the selected subject lacks an additional effect.',
    'uncertainty_rule': 'Missing, conflicting or incompatible ownership and classification premises yield no same-ability consequence.',
    'runtime': 'No event detection, text parsing, damage calculation, sequencing or game-state execution.',
    **_AUTHORITY,
}, 'policy_id'), limit=16_384)
POLICY_ID = json.loads(_POLICY_RAW)['policy_id']


def policy_document():
    return json.loads(_POLICY_RAW)


def _identity(value):
    return type(value) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', value) is not None


def _strings(value, *, allow_empty=False):
    return (type(value) is list and len(value) <= 32
            and (allow_empty or bool(value))
            and all(type(item) is str and item for item in value)
            and len(set(value)) == len(value))


def _subject(value):
    keys = {'subject_id', 'identity_scope', 'card_id', 'mechanical_dossier_id',
        'owner', 'source_field_pointer', 'source_record_pointer',
        'source_field_identity', 'complete_field_value', 'selected_passage',
        'passage_start', 'passage_end', 'surrounding_before', 'surrounding_after',
        'unselected_context_assessment', 'ownership_and_context_limitations', 'type_line'}
    if type(value) is not dict or set(value) != keys:
        raise PilotError('complete closed source-bound local subject required')
    for key in keys - {'passage_start', 'passage_end', 'type_line'}:
        if type(value[key]) is not str or (not value[key] and key not in ('surrounding_before', 'surrounding_after')):
            raise PilotError('exact subject string fields required')
    start, end = value['passage_start'], value['passage_end']
    if (type(start) is not int or type(end) is not int or not 0 <= start < end
            or value['identity_scope'] != 'local_review_subject_only'
            or not _identity(value['mechanical_dossier_id'])
            or not _identity(value['source_field_identity'])
            or value['complete_field_value'] != value['surrounding_before'] + value['selected_passage'] + value['surrounding_after']
            or start != len(value['surrounding_before'])
            or end != start + len(value['selected_passage'])
            or value['complete_field_value'][start:end] != value['selected_passage']):
        raise PilotError('complete subject ownership, field or offsets mismatch')
    field = {'source_pointer': value['source_field_pointer'],
             'status': 'known', 'value': value['complete_field_value']}
    field_id = 'sha256:' + hashlib.sha256(canonical(field)[:-1]).hexdigest()
    if field_id != value['source_field_identity']:
        raise PilotError('subject complete field identity mismatch')
    type_line = value['type_line']
    if (type(type_line) is not dict or set(type_line) != {'source_pointer', 'status', 'value', 'field_identity'}
            or any(type(type_line[key]) is not str for key in type_line)
            or type_line['status'] != 'known' or type_line['source_pointer'] != '/type_line'
            or not type_line['value']
            or type_line['field_identity'] != 'sha256:' + hashlib.sha256(canonical({
                key: child for key, child in type_line.items() if key != 'field_identity'})[:-1]).hexdigest()
            or value['source_field_pointer'] != '/oracle_text'
            or re.fullmatch(r'/[0-9]+/oracle_text', value['source_record_pointer']) is None):
        raise PilotError('complete exact retained field bindings required')
    return value


def _reading(value, subject):
    keys = {'state', 'owner_subject_id', 'card_id', 'damage_clause',
            'other_subject_ids', 'evidence_refs', 'rationale', 'counterevidence', 'unresolved'}
    if type(value) is not dict or set(value) != keys:
        raise PilotError('complete closed pending ownership reading required')
    if (type(value['state']) is not str or value['state'] not in _STATES
            or type(value['owner_subject_id']) is not str
            or value['owner_subject_id'] != subject['subject_id']
            or type(value['card_id']) is not str or value['card_id'] != subject['card_id']):
        raise PilotError('foreign or unsupported effect ownership rejected')
    if (not _strings(value['other_subject_ids'], allow_empty=True)
            or subject['subject_id'] in value['other_subject_ids']
            or not _strings(value['evidence_refs'])
            or not {'selected_passage', 'full_oracle_field'} <= set(value['evidence_refs'])
            or not _strings(value['counterevidence'])
            or not _strings(value['unresolved'], allow_empty=True)
            or type(value['rationale']) is not str or not value['rationale']
            or value['damage_clause'] is not None and (type(value['damage_clause']) is not str or not value['damage_clause'])):
        raise PilotError('complete exact ownership evidence and rationale required')
    allowed = {'selected_passage', 'full_oracle_field', 'type_line', 'rule:405.6c'} | {
        'subject:' + sid for sid in value['other_subject_ids']}
    if not set(value['evidence_refs']) <= allowed:
        raise PilotError('foreign ownership evidence reference rejected')
    if value['state'] in ('same_ability_additional_effect', 'separate_triggered_ability') and value['damage_clause'] is None:
        raise PilotError('explicit owned effect clause required')
    if value['state'] == 'no_additional_effect' and value['damage_clause'] is not None:
        raise PilotError('conflicting effect must be represented as conflicting')
    if value['state'] == 'same_ability_additional_effect' and 'rule:405.6c' not in value['evidence_refs']:
        raise PilotError('same-ability reading must bind 405.6c explicitly')
    if value['damage_clause'] is not None and subject['selected_passage'].count(value['damage_clause']) != 1:
        raise PilotError('authored effect clause must correspond uniquely within selected owned passage')
    return value


def _candidate(value, expected_id, subject, reading):
    keys = {'schema_version', 'prepared_at', 'plan_id', 'context_id', 'subject',
        'source_binding', 'proposed_kind', 'kind_evidence_refs', 'criteria',
        'descriptive_readings', 'counterevidence', 'unresolved',
        'classification_present_usability_distinct', 'limitations', 'authority',
        'semantic_review_status', 'review', 'execution_authority', 'candidate_id'}
    if (type(value) is not dict or set(value) != keys
            or type(value['schema_version']) is not str or value['schema_version'] != CANDIDATE_VERSION
            or value['candidate_id'] != expected_id
            or identity(CANDIDATE_VERSION, value, 'candidate_id') != expected_id
            or not _identity(value['plan_id']) or not _identity(value['context_id'])
            or type(value['prepared_at']) is not str or not value['prepared_at']
            or value['classification_present_usability_distinct'] is not True
            or value['authority'] != 'ENGINEER_AUTHORED_SOURCE_BOUND_PENDING_LAND_READINGS_ONLY'
            or value['semantic_review_status'] != 'PENDING_NOT_ESTABLISHED'
            or value['execution_authority'] != 'BLOCKED'):
        raise PilotError('complete pending candidate own identity and schema required')
    exact(value['review'], {'status': 'requires_review', 'human_attestation': None,
        'canonical_admission': False})
    exact(value['subject'], subject)
    descriptions = value['descriptive_readings']
    if (type(descriptions) is not dict or set(descriptions) != {'cost', 'output', 'conditions', 'effect_ownership'}
            or any(type(row) is not dict for row in descriptions.values())
            or not _strings(value['counterevidence'])
            or not _strings(value['unresolved'], allow_empty=True)
            or not _strings(value['limitations'])):
        raise PilotError('complete bounded candidate descriptive readings required')
    exact(descriptions['effect_ownership'], reading)
    source = value['source_binding']
    if (type(source) is not dict or set(source) != {'card_id', 'mechanical_dossier_id',
            'canonical_snapshot_id', 'provider_record_id', 'record_content_identity', 'source_field_identity'}
            or source['card_id'] != subject['card_id']
            or source['mechanical_dossier_id'] != subject['mechanical_dossier_id']
            or source['source_field_identity'] != subject['source_field_identity']
            or not _identity(source['canonical_snapshot_id'])
            or not _identity(source['record_content_identity'])
            or type(source['provider_record_id']) is not str or not source['provider_record_id']):
        raise PilotError('exact candidate source and subject binding required')
    rows = value['criteria']
    if type(rows) is not list or len(rows) != 12:
        raise PilotError('complete twelve candidate criterion readings required')
    inputs = []
    for row in rows:
        if (type(row) is not dict or set(row) != {'criterion_id', 'state', 'rule_refs',
                'evidence_refs', 'rationale', 'absence_scope', 'counterevidence', 'unresolved'}
                or not _strings(row['evidence_refs']) or not _strings(row['counterevidence'])
                or not _strings(row['unresolved'], allow_empty=True)
                or type(row['rationale']) is not str or not row['rationale']
                or type(row['absence_scope']) is not str or not row['absence_scope']):
            raise PilotError('complete exact candidate criterion evidence required')
        inputs.append({key: row[key] for key in ('criterion_id', 'state', 'rule_refs')})
    return {'proposed_kind': value['proposed_kind'], 'criteria': inputs,
        'kind_evidence_refs': value['kind_evidence_refs']}


def compute(*, subject, candidate_id, candidate, classification, behavior, reading, rule_facts):
    """Compose explicit ownership with actual recomputed pending calculations.

    Text is retained for exact evidence binding, never interpreted or searched
    for classification, effect ownership, trigger detection or branch selection.
    An explicitly authored clause is matched exactly for evidence correspondence.
    The real adapter additionally reproduces the exact admitted candidate.
    """
    value = json.loads(owned({'subject': subject, 'candidate_id': candidate_id, 'candidate': candidate,
        'classification': classification, 'behavior': behavior,
        'reading': reading, 'rule_facts': rule_facts}, limit=LIMIT))
    subject = _subject(value['subject'])
    reading = _reading(value['reading'], subject)
    if not _identity(value['candidate_id']):
        raise PilotError('exact candidate own identity required')
    candidate_inputs = _candidate(value['candidate'], value['candidate_id'], subject, reading)
    supplied = value['behavior']
    if type(supplied) is not dict or supplied.get('hypothetical_context') is not None:
        raise PilotError('actual baseline behavior without hypothetical required')
    try:
        inputs = supplied['input_readings']
        exact({'proposed_kind': supplied['proposed_kind'], **inputs}, candidate_inputs)
        actual = behavior_policy.compute(proposed_kind=supplied['proposed_kind'],
            criteria=inputs['criteria'], kind_evidence_refs=inputs['kind_evidence_refs'],
            rule_facts=value['rule_facts'])
    except (KeyError, TypeError):
        raise PilotError('complete behavior calculation inputs required') from None
    exact(supplied, actual, limit=LIMIT)
    exact(value['classification'], actual['classification'], limit=LIMIT)
    facts = behavior_policy._facts(value['rule_facts'])
    state = reading['state']
    qualified = actual['branch'] in ('CONDITIONAL_ACTIVATED_MANA', 'CONDITIONAL_TRIGGERED_MANA')
    status = 'UNRESOLVED_EFFECT_OWNERSHIP'
    consequence = None
    unknowns = list(reading['unresolved'])
    if state == 'same_ability_additional_effect' and qualified and '405.6c' in facts:
        status = 'CONDITIONAL_SAME_ABILITY_ADDITIONAL_EFFECT'
        relationship = facts['405.6c']['rule']['mana_plus_additional_effect']
        consequence = {
            'relationship': relationship['relationship'],
            'mana_production': relationship['mana_production'],
            'additional_effect': relationship['additional_effect'],
            'fine_grained_ordering': relationship['fine_grained_ordering'],
            'antecedents': ['The exact pending classification and effect-ownership readings are assumed within their retained-text scope.',
                'If this same qualifying mana ability resolves, both the mana instruction and the expressly owned additional effect share its immediate-resolution context.'],
            'actual_effect_executed': False,
        }
        unknowns += ['No actual mana, damage, prevention, life total or fine-grained ordering is calculated.']
    elif state == 'no_additional_effect':
        status = 'PENDING_NO_ADDITIONAL_EFFECT_IN_SELECTED_SUBJECT'
        unknowns += ['This authored absence finding concerns the complete selected retained subject only; another subject and external changed text are not assessed by this finding.']
    elif (state == 'separate_triggered_ability' and actual['classification']['branch'] == 'triggered'
            and any(row['criterion_id'] == 'triggered_kind' and row['state'] == 'proposed_satisfied'
                    for row in candidate_inputs['criteria'])):
        status = 'SEPARATE_TRIGGERED_SUBJECT'
        unknowns += actual['remaining_unresolved']
        unknowns += ['No actual event or trigger sequence is detected. Separately owned mana output is not imported into this triggered subject.']
    else:
        unknowns += ['The ownership or completed qualifying-mana premise remains unknown, conflicting or incompatible; no conditional shared additional-effect relationship follows.']
        if '405.6c' not in facts:
            unknowns += ['The required retained 405.6c binding is missing.']
    baseline = next((row['conditional_consequence'] for row in actual['consequences']
        if row['consequence_id'] == 'immediate_resolution_context'), None)
    binding = facts.get('405.6c')
    rule_evidence = [] if binding is None else [{
        'rule_reference': '405.6c', 'package': binding['package'],
        'package_id': binding['package_id'], 'projection_id': binding['projection_id'],
        'rule_id': binding['rule']['rule_id'], 'source_anchor': binding['rule']['source_anchor']}]
    result = seal(RESULT_VERSION, {
        'schema_version': RESULT_VERSION, 'policy_id': POLICY_ID,
        'candidate_id': value['candidate_id'], 'subject_id': subject['subject_id'],
        'candidate_schema_version': value['candidate']['schema_version'],
        'plan_id': value['candidate']['plan_id'], 'context_id': value['candidate']['context_id'],
        'card_id': subject['card_id'],
        'subject_binding': {key: subject[key] for key in ('mechanical_dossier_id',
            'source_field_identity', 'source_record_pointer', 'selected_passage',
            'passage_start', 'passage_end')},
        'classification_policy_id': actual['classification']['policy_id'],
        'classification_assessment': actual['classification']['overall_assessment'],
        'behavior_calculation_id': actual['calculation_id'],
        'behavior_branch': actual['branch'], 'pending_effect_ownership': reading,
        'owned_effect_clause_binding': None if reading['damage_clause'] is None else {
            'clause': reading['damage_clause'],
            'selected_passage_start': subject['selected_passage'].index(reading['damage_clause']),
            'selected_passage_end': subject['selected_passage'].index(reading['damage_clause']) + len(reading['damage_clause']),
            'source_field_identity': subject['source_field_identity'],
            'correspondence_method': 'EXPLICIT_AUTHORED_CLAUSE_UNIQUE_EXACT_CORRESPONDENCE_ONLY'},
        'status': status, 'conditional_relationship': consequence,
        'unchanged_baseline_additional_effect_context': baseline,
        'baseline_statement_scope': 'The unchanged baseline calculation receives no effect-ownership input. Its lack of an assertion does not prove absence; the separately versioned pending composition above uses the explicitly bound ownership reading.',
        'rule_evidence': rule_evidence,
        'remaining_unknowns': list(dict.fromkeys(unknowns)),
        'scope': ['Complete retained selected subject only; gained abilities, changed text, copies, external effects and arbitrary game states remain unassessed.',
            'No parsing, event detection, trigger engine, damage engine or game execution.'],
        **_AUTHORITY,
    }, 'composition_id')
    return json.loads(owned(result, limit=RESULT_LIMIT))
