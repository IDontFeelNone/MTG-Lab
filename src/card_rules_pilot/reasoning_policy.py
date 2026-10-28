"""Closed conditional review policy, independent of Card names and proposal labels.

This unit accepts only criterion readings and retained rule-reference bindings.
It does not validate real provenance: the public report API supplies these inputs
only from the freshly verified, privately owned fixed-pilot snapshot. Synthetic
policy fixtures may exercise the algebra without impersonating real candidates.
"""
from __future__ import annotations

import json

from .contract import PilotError, owned, seal

POLICY_VERSION = 'card-rules-mana-reasoning-policy-v1'
_ACTIVATED = ('activated_kind', 'no_target', 'potential_mana', 'not_loyalty',
              'no_library_cost_movement', 'no_library_effect_movement')
_METHOD = ('self_replacement_considered', 'other_replacements_disregarded')
_TRIGGERED = ('triggered_kind', 'trigger_no_target', 'trigger_potential_mana',
              'qualifying_trigger_relationship')
_DEFINITIONS = (
    ('activated_kind', ('605.1a',)),
    ('no_target', ('605.1a', '115.6')),
    ('potential_mana', ('605.1a', '605.2')),
    ('not_loyalty', ('605.1a', '606.1', '606.2')),
    ('no_library_cost_movement', ('605.1a',)),
    ('no_library_effect_movement', ('605.1a',)),
    ('self_replacement_considered', ('605.1a',)),
    ('other_replacements_disregarded', ('605.1a',)),
    ('triggered_kind', ('605.1b',)),
    ('trigger_no_target', ('605.1b', '115.6')),
    ('trigger_potential_mana', ('605.1b', '605.2')),
    ('qualifying_trigger_relationship', ('605.1b', '605.1a')),
)
_STATES = ('proposed_satisfied', 'proposed_not_satisfied', 'unknown',
           'unsupported', 'inapplicable', 'conflicting')
_RULE_ALLOWLIST = ('605.1', '605.1a', '605.1b', '605.2', '605.3',
                   '605.3a', '605.3b', '605.3c', '605.4', '605.4a', '605.5', '605.5a',
                   '605.5b', '115.6', '606.1', '606.2', '405.6c')
_KINDS = (('proposed_activated_ability', 'activated'),
          ('proposed_triggered_ability', 'triggered'),
          ('proposed_spell_instruction', 'spell'))

SATISFIED = 'SATISFIED_UNDER_AUTHORED_READINGS'
NOT_SATISFIED = 'NOT_SATISFIED_UNDER_AUTHORED_READINGS'
INDETERMINATE = 'INDETERMINATE_UNDER_AUTHORED_READINGS'
ELIGIBLE = 'CONDITIONALLY_ELIGIBLE_UNDER_AUTHORED_READINGS'
EXCLUDED = 'CONDITIONALLY_EXCLUDED_UNDER_AUTHORED_READINGS'
INCOMPLETE = 'INCOMPLETE_ASSESSMENT_UNDER_AUTHORED_READINGS'

_POLICY_BYTES = owned(seal(POLICY_VERSION, {
    'schema_version': POLICY_VERSION,
    'domain': 'Card-Rules pending interpretation review',
    'kind_branches': [{'proposed_kind': kind, 'branch': branch} for kind, branch in _KINDS],
    'rule_allowlist': list(_RULE_ALLOWLIST),
    'criterion_definitions': [{'criterion_id': key, 'rule_refs': list(refs)}
                              for key, refs in _DEFINITIONS],
    'criterion_states': list(_STATES),
    'input_rule': 'Exactly twelve ordered unique criteria with closed criterion_id/state/rule_refs fields and exact definition rule bindings; closed unique kind evidence references; required applicable kind evidence.',
    'activated_substantive': list(_ACTIVATED),
    'activated_method_obligations': list(_METHOD),
    'triggered_substantive': list(_TRIGGERED),
    'spell_exclusion': {'kind': 'proposed_spell_instruction',
                        'required_evidence_refs': ['type_line', 'rule:605.5b']},
    'substantive_rule': 'A negative witness decides the conjunction; retain all unresolved inputs. Otherwise unresolved inputs make it indeterminate; only all proposed_satisfied inputs satisfy it.',
    'method_rule': 'Conflicting takes precedence over unmet, then incomplete; preserve all findings. Only all proposed_satisfied obligations complete the activated assessment. Other branches have no activated method obligations.',
    'overall_rule': 'Incomplete, unmet or conflicting applicable methods block a conditional classification. Otherwise propagate the substantive result; spells use the explicit 605.5b exclusion.',
    'inapplicable_rule': 'Required inapplicable readings are unresolved and never satisfied. Every inactive-family row must be inapplicable.',
    'authority': 'CONDITIONAL_CALCULATION_OVER_PENDING_AUTHORED_READINGS_ONLY',
    'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
    'review': {'status': 'requires_review', 'human_attestation': None,
               'canonical_admission': False},
    'execution_authority': 'BLOCKED',
}, 'policy_id'), limit=16_384)
POLICY_ID = json.loads(_POLICY_BYTES)['policy_id']


def policy_document():
    """Return an independent decoded view of the privately owned policy bytes."""
    return json.loads(_POLICY_BYTES)


def compute(*, proposed_kind, criteria, kind_evidence_refs):
    """Calculate a conditional result after complete closed-input validation.

    Each criterion is exactly ``criterion_id``, ``state`` and ``rule_refs``.
    Authored prose, source text, display names, subject identifiers and proposed
    classification labels cannot enter this calculation. All twelve rows are
    inspected before any decisive logical premise is used.
    """
    # Own an exact JSON view first. This also rejects floats, non-JSON values,
    # excessive structure and Boolean/integer coercions before calculation.
    value = json.loads(owned({'proposed_kind': proposed_kind, 'criteria': criteria,
                             'kind_evidence_refs': kind_evidence_refs}, limit=16_384))
    proposed_kind, criteria, kind_evidence_refs = (
        value[key] for key in ('proposed_kind', 'criteria', 'kind_evidence_refs'))
    kinds = dict(_KINDS)
    if type(proposed_kind) is not str or proposed_kind not in kinds:
        raise PilotError('closed proposed kind required')
    if type(criteria) is not list or len(criteria) != len(_DEFINITIONS):
        raise PilotError('complete twelve-row policy layout required')
    for row, (identifier, refs) in zip(criteria, _DEFINITIONS):
        if type(row) is not dict or set(row) != {'criterion_id', 'state', 'rule_refs'}:
            raise PilotError('closed policy criterion fields required')
        if row['criterion_id'] != identifier or type(row['criterion_id']) is not str:
            raise PilotError('complete ordered unique policy criterion IDs required')
        if type(row['state']) is not str or row['state'] not in _STATES:
            raise PilotError('closed criterion state required')
        if type(row['rule_refs']) is not list or row['rule_refs'] != list(refs):
            raise PilotError('exact criterion rule bindings required')
    allowed_evidence = ('selected_passage', 'full_oracle_field', 'type_line') + tuple(
        'rule:' + ref for ref in _RULE_ALLOWLIST)
    if (type(kind_evidence_refs) is not list or not kind_evidence_refs
            or any(type(ref) is not str or ref not in allowed_evidence
                   for ref in kind_evidence_refs)
            or len(set(kind_evidence_refs)) != len(kind_evidence_refs)):
        raise PilotError('closed unique kind evidence references required')
    branch = kinds[proposed_kind]
    required = _ACTIVATED if branch == 'activated' else _TRIGGERED if branch == 'triggered' else ()
    methods = _METHOD if branch == 'activated' else ()
    readings = {row['criterion_id']: row['state'] for row in criteria}
    for identifier in readings:
        if identifier not in required + methods and readings[identifier] != 'inapplicable':
            raise PilotError('inactive branch criterion must be inapplicable')
    required_kind_refs = (('type_line', 'rule:605.5b') if branch == 'spell'
                          else ('selected_passage', 'rule:605.1a' if branch == 'activated'
                                else 'rule:605.1b'))
    if not set(required_kind_refs).issubset(kind_evidence_refs):
        raise PilotError('proposed branch kind lacks applicable evidence bindings')

    satisfied = [identifier for identifier in required
                 if readings[identifier] == 'proposed_satisfied']
    negative = [identifier for identifier in required
                if readings[identifier] == 'proposed_not_satisfied']
    unresolved = [{'criterion_id': identifier, 'state': readings[identifier]}
                  for identifier in required if readings[identifier] not in
                  ('proposed_satisfied', 'proposed_not_satisfied')]
    spell = ({'proposed_kind': proposed_kind, 'evidence_refs': list(required_kind_refs),
              'rule_refs': ['605.5b']} if branch == 'spell' else None)
    substantive = (NOT_SATISFIED if spell or negative else INDETERMINATE if unresolved
                   else SATISFIED)
    method_findings = [{'criterion_id': identifier, 'state': readings[identifier]}
                       for identifier in methods]
    method_states = [row['state'] for row in method_findings]
    method_status = ('NOT_APPLICABLE' if not methods else
                     'CONFLICTING' if 'conflicting' in method_states else
                     'UNMET' if 'proposed_not_satisfied' in method_states else
                     'INCOMPLETE' if any(state != 'proposed_satisfied' for state in method_states)
                     else 'PROPOSED_SATISFIED')
    overall = (INCOMPLETE if method_status not in ('PROPOSED_SATISFIED', 'NOT_APPLICABLE')
               else EXCLUDED if substantive == NOT_SATISFIED else
               INDETERMINATE if substantive == INDETERMINATE else ELIGIBLE)
    active_rule = '605.5b' if branch == 'spell' else '605.1a' if branch == 'activated' else '605.1b'
    trace = [
        {'step': 'branch_selection', 'premise_ids': ['proposed_kind'],
         'rule_refs': [active_rule], 'outcome': branch,
         'explanation': 'Use the explicit pending kind reading and its applicable retained rule bindings.'},
        {'step': 'spell_exclusion' if spell else 'substantive_conjunction',
         'premise_ids': ['proposed_kind'] if spell else list(required),
         'rule_refs': [active_rule], 'outcome': substantive,
         'explanation': ('The pending spell-kind reading and retained type-line evidence invoke 605.5b; inapplicable ability rows do not form a vacuously successful conjunction.' if spell else
                         'Preserve every satisfied, negative and unresolved substantive reading; a negative witness decides the conditional conjunction without erasing unresolved inputs.')},
        {'step': 'assessment_method', 'premise_ids': list(methods),
         'rule_refs': ['605.1a'] if methods else [], 'outcome': method_status,
         'explanation': ('Assess the two methodological obligations separately. Failure or uncertainty is not a negative Card property and does not independently establish category exclusion.' if methods else
                         'Activated assessment-method obligations do not apply to this branch; no activated priority-return context is transferred.')},
        {'step': 'bounded_conclusion', 'premise_ids': list(required + methods) if not spell else ['proposed_kind'],
         'rule_refs': [active_rule], 'outcome': overall,
         'explanation': 'Applicable methods must be proposed satisfied before any conditional eligibility or exclusion conclusion. Semantic review remains pending in every case.'},
    ]
    return {'policy_version': POLICY_VERSION, 'policy_id': POLICY_ID, 'branch': branch,
            'substantive_result': substantive, 'method_status': method_status,
            'overall_assessment': overall, 'satisfied_requirements': satisfied,
            'negative_witnesses': negative, 'unresolved_requirements': unresolved,
            'method_findings': method_findings, 'spell_exclusion': spell, 'trace': trace}
