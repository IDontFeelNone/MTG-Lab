"""Bounded real-rules reasoning from declared facts, not Card text or gameplay.

Evidence admission reuses the existing metadata-only 24-rule reader. The old
Card interpretation factories are deliberately not called: they require a
different source-use scope. Historical projection states are never promoted.
"""
from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import sys

from card_rules_pilot import contract as c
from card_rules_pilot.land_context import read_context
from .mana_window import hypothetical_context, evaluate_propositions

INPUT_VERSION = 'real-card-rules-reasoning-input-v1'
VERSION = 'real-card-rules-reasoning-report-v1'
QUESTION = 'ACTIVATED_MANA_PAYMENT_TIMING_EXCEPTION'
CONTEXT_ID = 'sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478'
INPUT_LIMIT = 8192
REPORT_LIMIT = 65536
TRUTH = ('YES', 'NO', 'UNKNOWN')
CHARACTERISTICS = {
    'ability_kind': ('ACTIVATED', 'TRIGGERED', 'SPELL', 'UNKNOWN'),
    'target_requirement': ('NONE', 'PRESENT', 'UNKNOWN'),
    'potential_mana': TRUTH,
    'loyalty_symbol_in_cost': TRUTH,
    'source_is_planeswalker': TRUTH,
    'cost_library_movement': TRUTH,
    'effect_library_movement': TRUTH,
    'self_replacement': ('ABSENT', 'PRESENT', 'UNKNOWN'),
    'other_replacement': ('ABSENT', 'PRESENT', 'UNKNOWN'),
}
PAYMENT_REQUESTS = ('SPELL_CASTING_MANA_PAYMENT', 'ABILITY_ACTIVATION_MANA_PAYMENT',
                    'RULE_REQUESTED_MANA_PAYMENT', 'EFFECT_REQUESTED_MANA_PAYMENT')
STATE = {'mana_payment_request': ('ABSENT', *PAYMENT_REQUESTS, 'UNKNOWN'),
         'priority': TRUTH, 'same_ability_unresolved': TRUTH,
         'current_mana_output': ('ZERO', 'NONZERO', 'UNKNOWN')}
REFERENCES = ('605.1a', '605.2', '605.3a', '605.3c', '606.2', '115.6', '614.15')
DECISIONS = {
    'PAYMENT_TIMING_EXCEPTION_APPLIES': 'Under these declarations, the selected mana-payment opportunity applies and the same-ability repeat restriction is absent. Priority is not required for this opportunity.',
    'NO_MANA_PAYMENT_EXCEPTION': 'The declared ability fails a required activated-mana criterion; this mana-specific timing exception does not apply. Other activation permissions are not decided.',
    'SAME_ABILITY_REACTIVATION_PROHIBITED': 'Under the declared same-ability state, reactivation is prohibited until that activation resolves.',
    'NO_DECLARED_MANA_PAYMENT_OPPORTUNITY': 'No mana-payment request is declared. This payment-specific opportunity is absent; ordinary-priority and other permissions are not decided.',
    'NEEDS_FACTS': 'Required declarations are unknown or outside the resolved target scope; no affirmative or negative answer is established.',
}


class RulesReasoningError(c.PilotError):
    def __init__(self, code, reason):
        self.code = code
        super().__init__(reason)

    def as_dict(self):
        return dict(schema_version=VERSION, status='REFUSED', code=self.code,
                    reason=str(self), legal_activation='NOT_ESTABLISHED', execution_authority='BLOCKED')


def _require(condition, reason, code='INVALID_INPUT'):
    if not condition:
        raise RulesReasoningError(code, reason)


def _input(value):
    try:
        value = json.loads(c.owned(value, limit=INPUT_LIMIT))
    except (c.PilotError, ValueError, TypeError, RecursionError):
        raise RulesReasoningError('INVALID_INPUT', 'bounded JSON input required') from None
    _require(type(value) is dict and set(value) == {'schema_version','question','scenario_id',
             'evidence_context_id','characteristics','state'}, 'closed reasoning input required')
    _require(value['schema_version'] == INPUT_VERSION, 'unsupported input version', 'UNSUPPORTED_VERSION')
    _require(value['question'] == QUESTION, 'unsupported rules question', 'UNSUPPORTED_QUESTION')
    _require(type(value['scenario_id']) is str and 0 < len(value['scenario_id']) <= 128
             and value['scenario_id'] == value['scenario_id'].strip() and value['scenario_id'].isprintable(),
             'bounded printable scenario identity required')
    _require(type(value['evidence_context_id']) is str, 'exact evidence context identity required')
    traits, state = value['characteristics'], value['state']
    _require(type(traits) is dict and set(traits) == set(CHARACTERISTICS) | {'chosen_targets'},
             'complete closed characteristics required')
    _require(type(state) is dict and set(state) == set(STATE), 'complete closed state required')
    for fields, supplied in ((CHARACTERISTICS, traits), (STATE, state)):
        for key, choices in fields.items():
            _require(type(supplied[key]) is str and supplied[key] in choices, 'invalid declared field: '+key)
    count = traits['chosen_targets']
    _require((type(count) is int and 0 <= count <= 16) or (type(count) is str and count == 'UNKNOWN'),
             'chosen targets must be an exact bounded integer or UNKNOWN')
    _require(not (traits['target_requirement'] == 'NONE' and type(count) is int and count > 0),
             'declared target absence contradicts chosen targets', 'CONFLICTING_FACTS')
    _require(traits['ability_kind'] not in ('TRIGGERED','SPELL'),
             'triggered abilities and spell instructions require a different rules scope', 'UNSUPPORTED_SCOPE')
    _require(traits['self_replacement'] != 'PRESENT',
             'self-replacement application is not implemented; 614.15 context alone does not supply it',
             'UNSUPPORTED_SELF_REPLACEMENT')
    return value


def _admit(root, expected_context_id):
    _require(expected_context_id == CONTEXT_ID, 'unsupported evidence context identity', 'EVIDENCE_VERSION_MISMATCH')
    try:
        context = read_context(root)
    except (c.PilotError, OSError, ValueError, KeyError, TypeError):
        raise RulesReasoningError('EVIDENCE_INTEGRITY', 'existing retained rules admission refused') from None
    retained = context['retained_rules']
    _require(retained['context_id'] == expected_context_id, 'retained context changed', 'EVIDENCE_VERSION_MISMATCH')
    rules = context['rule_facts']
    a = rules['605.1a']['rule']['semantic_distinctions']
    # These are checked content descriptors, not facts inferred from citations.
    expected = dict(ability_kind='ACTIVATED', all_criteria_required=True, requires_target=False,
        could_add_mana_to_player_pool_on_resolution=True, is_loyalty_ability=False,
        cost_moves_card_to_or_from_library=False, effect_moves_card_to_or_from_library=False,
        applicable_replacement_effects_considered='SELF_REPLACEMENT_ONLY',
        other_applicable_replacement_effects_ignored_for_classification=True)
    _require(all(type(a.get(k)) is type(v) and a[k] == v for k,v in expected.items()),
             'retained classification descriptors do not support this question', 'UNSUPPORTED_EVIDENCE')
    _require(rules['606.2']['rule']['criterion'] == 'ACTIVATED_ABILITY_WITH_LOYALTY_SYMBOL_IN_ACTIVATION_COST'
             and rules['606.2']['rule']['only_planeswalkers_can_have_loyalty_abilities'] is False,
             'retained loyalty distinction changed', 'UNSUPPORTED_EVIDENCE')
    _require(rules['115.6']['rule']['zero_selected_implies_no_target_requirement'] is False,
             'retained target distinction changed', 'UNSUPPORTED_EVIDENCE')
    windows = rules['605.3a']['rule']['semantic_distinctions']['activation_opportunity_categories']
    _require(set(windows) == {'ORDINARY_PRIORITY', *PAYMENT_REQUESTS},
             'retained opportunity categories changed', 'UNSUPPORTED_EVIDENCE')
    _require(rules['605.3c']['rule']['semantic_distinctions']['same_ability_reactivation_before_resolution'] is False
             and rules['605.2']['rule']['semantic_distinctions']['inability_to_produce_mana_alone_removes_classification'] is False,
             'retained restriction or persistence distinction changed', 'UNSUPPORTED_EVIDENCE')
    return retained, rules


def _classify(traits):
    findings = []
    def row(key, supplied, status, refs, explanation):
        findings.append(dict(criterion=key, supplied=supplied, status=status, rule_references=refs, explanation=explanation))
    def boolean(key, required, refs):
        value = traits[key]
        row(key, value, 'UNKNOWN' if value == 'UNKNOWN' else 'SATISFIED' if value == required else 'UNSATISFIED',
            refs, 'Compare the explicit characteristic with the retained criterion; do not interpret Card text.')
    row('activated_kind', traits['ability_kind'], 'SATISFIED' if traits['ability_kind']=='ACTIVATED' else 'UNKNOWN',
        ['605.1a'], 'The ability kind is declared, not recognized from a Card identity.')
    chosen, requirement = traits['chosen_targets'], traits['target_requirement']
    targeted = ('UNSATISFIED' if type(chosen) is int and chosen > 0 else
                'SATISFIED' if requirement == 'NONE' and chosen == 0 else 'UNKNOWN')
    row('no_target', dict(requirement=requirement, chosen_targets=chosen), targeted, ['605.1a','115.6'],
        'Positive chosen targets supply a negative witness. Zero chosen targets alone do not prove absent target requirements; optional/conditional targeting remains unresolved here.')
    boolean('potential_mana','YES',['605.1a','605.2'])
    boolean('loyalty_symbol_in_cost','NO',['605.1a','606.2'])
    boolean('cost_library_movement','NO',['605.1a'])
    boolean('effect_library_movement','NO',['605.1a'])
    row('self_replacement_assessment', traits['self_replacement'],
        'SATISFIED' if traits['self_replacement']=='ABSENT' else 'UNKNOWN', ['605.1a','614.15'],
        'V1 requires explicit absence of self-replacements; recognizing or applying one is unsupported.')
    row('other_replacements_disregarded', traits['other_replacement'], 'SATISFIED', ['605.1a'],
        'The classifier disregards other replacement effects, even when their presence is unknown. They may still affect actual output.')
    statuses = [r['status'] for r in findings]
    # Unknown branch/method facts prevent interpreting an unreplaced profile as
    # the required effective profile. No pending Card readings are fabricated.
    if findings[0]['status']=='UNKNOWN' or findings[-2]['status']=='UNKNOWN':
        result = 'UNRESOLVED'
    else:
        result = 'EXCLUDED' if 'UNSATISFIED' in statuses else 'UNRESOLVED' if 'UNKNOWN' in statuses else 'QUALIFIES'
    return dict(status=result, findings=findings,
                unresolved=[r['criterion'] for r in findings if r['status']=='UNKNOWN'])


def _calculate(value, retained, rules):
    traits, state = value['characteristics'], value['state']
    classification = _classify(traits)
    hypothetical = hypothetical_context(
        classification={'QUALIFIES':'ACTIVATED_MANA','EXCLUDED':'ACTIVATED_NONMANA','UNRESOLVED':'UNKNOWN'}[classification['status']],
        priority_opportunity=state['priority'], payment_opportunity=state['mana_payment_request'],
        same_ability_unresolved=state['same_ability_unresolved'])
    props = [dict(key=key, rule_reference=ref, rule_id=rules[ref]['rule']['rule_id'],
        conditions=[dict(field='classification',allowed=['ACTIVATED_MANA']),dict(field=field,allowed=allowed)],
        conditional_consequence=explanation) for key,ref,field,allowed,explanation in (
            ('payment','605.3a','payment_opportunity',list(PAYMENT_REQUESTS), 'The declared mana-payment opportunity category applies.'),
            ('repeat','605.3c','same_ability_unresolved',['YES'], 'The same unresolved mana ability cannot be reactivated.'))]
    opportunities = evaluate_propositions(props, hypothetical)['findings']
    findings = {r['key']:r for r in opportunities}
    missing = list(classification['unresolved'])
    if classification['status']=='EXCLUDED': decision='NO_MANA_PAYMENT_EXCEPTION'
    elif classification['status']=='UNRESOLVED': decision='NEEDS_FACTS'
    elif findings['repeat']['status']=='APPLICABLE': decision='SAME_ABILITY_REACTIVATION_PROHIBITED'
    elif findings['payment']['status']=='INAPPLICABLE': decision='NO_DECLARED_MANA_PAYMENT_OPPORTUNITY'
    elif findings['payment']['status']=='UNKNOWN' or findings['repeat']['status']=='UNKNOWN':
        decision='NEEDS_FACTS'
        if state['mana_payment_request']=='UNKNOWN':missing.append('mana_payment_request')
        if state['same_ability_unresolved']=='UNKNOWN':missing.append('same_ability_unresolved')
    else: decision='PAYMENT_TIMING_EXCEPTION_APPLIES'
    refs = [dict(reference=ref, rule_id=rules[ref]['rule']['rule_id'], package_id=rules[ref]['package_id'],
        projection_id=rules[ref]['projection_id'], source_anchor=rules[ref]['rule']['source_anchor'],
        historical_review_state=rules[ref]['rule'].get('review_state'),
        execution_readiness=rules[ref]['rule'].get('execution_readiness'))
        for ref in REFERENCES]
    return c.seal(VERSION, dict(schema_version=VERSION, input=value, classification=classification,
        decision=decision, explanation=DECISIONS[decision], opportunity_findings=opportunities,
        missing_facts=sorted(set(missing)), trace=[
            dict(step='declared_characteristic_classification', outcome=classification['status'], rules=['605.1a','606.2','115.6','614.15']),
            dict(step='current_output_is_separate', outcome=state['current_mana_output'], rules=['605.2'],
                 explanation='Current output neither substitutes for potential-output evidence nor changes classification by itself.'),
            dict(step='loyalty_is_cost_based', outcome=traits['loyalty_symbol_in_cost'], rules=['606.2'],
                 explanation='Being or not being a planeswalker is not the loyalty criterion.'),
            dict(step='payment_opportunity', outcome=findings['payment']['status'], rules=['605.3a']),
            dict(step='same_ability_restriction', outcome=findings['repeat']['status'], rules=['605.3c']),
            dict(step='bounded_conclusion', outcome=decision, rules=['605.3a','605.3c'])],
        evidence=dict(context_id=retained['context_id'], release=retained['source_binding']['effective_date'],
            artifact_hash=retained['source_binding']['artifact_hash'], references=refs,
            verification_scope=retained['verification_scope'], fresh_source_verification=False,
            historical_review_states_changed=False),
        authority=dict(facts='CALLER_DECLARED_NOT_VERIFIED_CARD_OR_GAME_STATE', real_card_verified=False,
            legal_activation='NOT_ESTABLISHED', strategic_usefulness='NOT_ASSESSED', execution_authority='BLOCKED',
            canonical_admission=False, game_actions_performed=False, source_policy_clearance=retained['source_policy_clearance'],
            permissions=retained['permissions']),
        full_legality_gaps=['Current Card/Oracle verification and actual request authentication.',
            'Complete activation, cost payment, tap restrictions, priority and resource procedures.',
            'Other restrictions, interactions and executable real-card semantics.'],
        limitations=['The conclusion is conditional on the declared characteristics and state, under retained September 25, 2026 rules metadata.',
            'No Card name, Printing or caller identity string establishes verified mechanics.',
            'Retained non-executing context admission and implementation authorization do not promote historical projection states or approve real-card semantics.',
            'No simulation, mana production, source acquisition, canonical admission or external AI export occurs.']), 'report_id')


@dataclass(frozen=True, init=False)
class RulesReasoner:
    _root: Path
    _context_id: str

    def assess(self, value):
        value = _input(value)
        _require(value['evidence_context_id'] == self._context_id, 'input evidence version differs', 'EVIDENCE_VERSION_MISMATCH')
        retained, rules = _admit(self._root, self._context_id)
        return c.ReviewDocument._verified(_calculate(value, retained, rules), limit=REPORT_LIMIT)

    def validate_report(self, value):
        try:
            _require(type(value) is dict and 'input' in value, 'report input required', 'INVALID_REPORT')
            expected = self.assess(value['input'])
            c.exact(value, expected.to_dict(), limit=REPORT_LIMIT)
            return expected
        except c.PilotError as error:
            if isinstance(error, RulesReasoningError): raise
            raise RulesReasoningError('INVALID_REPORT', 'report does not reproduce from the current admitted evidence') from None

    def replay(self, raw):
        try:
            return self.validate_report(c.parse_json(raw, limit=REPORT_LIMIT))
        except c.PilotError as error:
            if isinstance(error, RulesReasoningError): raise
            raise RulesReasoningError('INVALID_REPORT', 'invalid bounded canonical report bytes') from None


def load_rules_reasoner(*, review_root, expected_context_id):
    """Admit only the existing metadata context, never Card/source acquisitions."""
    root = Path(review_root).absolute()
    _admit(root, expected_context_id)
    result = object.__new__(RulesReasoner)
    object.__setattr__(result, '_root', root)
    object.__setattr__(result, '_context_id', expected_context_id)
    return result


def render_reasoning(report):
    value = report.to_dict()
    return '\n'.join(['MTG Lab — bounded real-rules reasoning', 'Scenario: '+value['input']['scenario_id'],
        'Decision: '+value['decision'], value['explanation'], 'Report: '+value['report_id'],
        'Rules: '+', '.join(REFERENCES), 'Missing facts: '+(', '.join(value['missing_facts']) or 'none for this bounded question'),
        'Declared facts are not verified Card mechanics. Full activation legality is NOT_ESTABLISHED; execution BLOCKED.',
        'Strategic usefulness is NOT_ASSESSED. No game action or mana production occurred.'])+'\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-root', type=Path, required=True)
    parser.add_argument('--expected-context-id', required=True)
    parser.add_argument('--json', action='store_true')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('assess','validate'):
        commands.add_parser(name).add_argument('input', type=Path)
    args = parser.parse_args(argv)
    try:
        consumer = load_rules_reasoner(review_root=args.review_root, expected_context_id=args.expected_context_id)
        value = c.read_json(args.input, limit=INPUT_LIMIT if args.command=='assess' else REPORT_LIMIT)
        report = consumer.assess(value) if args.command=='assess' else consumer.validate_report(value)
        print(report.to_json() if args.json else render_reasoning(report), end='')
        return 0
    except (c.PilotError, OSError) as error:
        refused = error if isinstance(error, RulesReasoningError) else RulesReasoningError('INVALID_INPUT','input or evidence unavailable')
        print(json.dumps(refused.as_dict(), sort_keys=True), file=sys.stderr)
        return 2


if __name__ == '__main__': raise SystemExit(main())
