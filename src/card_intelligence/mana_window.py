"""Retained-proposition applicability over explicit hypothetical contexts. No execution."""
from dataclasses import dataclass
import hashlib
import json

from card_rules_pilot import contract as c
from . import semantic_closure as closure

VERSION = 'real-mana-window-report-v1'
CONTEXT_VERSION = 'real-mana-window-context-v1'
POLICY_VERSION = 'real-mana-window-policy-v1'
COMPOSITION_VERSION = 'mana-window-closure-reference-v1'
LIMIT = 32768
READABLE_LIMIT = 16384
RULE_IDS = (
    ('605.3a', 'sha256:b996ad86f817a1d69ed179f5b299c6efe56591ff363d162dba64318c98f4c562'),
    ('605.3b', 'sha256:64c8d9dffd2a31ad715d214fda4fb650c217f5bd803b72dcb65663cc03a73e04'),
    ('605.3c', 'sha256:c00f9b451db7dcce795fcfb2b1c53a192610feb2c3112a0d73bf155f4709039c'),
    ('405.6c', 'sha256:014c5bf6eb8a3b751961d28ea1e612ade7509763ecd9886fb66dd68010294941'),
)
FIELDS = {
    'classification': ('ACTIVATED_MANA', 'ACTIVATED_NONMANA', 'TRIGGERED_MANA', 'UNKNOWN', 'UNSUPPORTED'),
    'stack_use': ('YES', 'NO', 'UNKNOWN'),
    'priority_opportunity': ('YES', 'NO', 'UNKNOWN'),
    'payment_opportunity': ('ABSENT', 'SPELL_CASTING_MANA_PAYMENT', 'ABILITY_ACTIVATION_MANA_PAYMENT',
        'RULE_REQUESTED_MANA_PAYMENT', 'EFFECT_REQUESTED_MANA_PAYMENT', 'UNKNOWN', 'UNSUPPORTED'),
    'same_ability_unresolved': ('YES', 'NO', 'UNKNOWN'),
    'held_priority_before_activation': ('YES', 'NO', 'UNKNOWN'),
    'activation_resolved': ('YES', 'NO', 'UNKNOWN'),
}
MEANINGS = {
    'APPLICABLE': 'The retained conditional proposition follows under supplied hypothetical conditions; no legal action is established.',
    'INAPPLICABLE': 'A necessary condition is expressly false; no conclusion about other rules or legality follows.',
    'UNKNOWN': 'A necessary condition is unspecified or unknown.',
    'CONFLICTING': 'Submitted assumptions contradict a bound retained proposition; neither assertion is repaired.',
    'UNSUPPORTED': 'The classification or requested context exceeds this bounded assessment.',
}


class WindowError(c.PilotError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(code + ': ' + message)


def hypothetical_context(**assumptions):
    """Missing information stays UNKNOWN, including a missing payment opportunity."""
    value = dict(schema_version=CONTEXT_VERSION, **{k: 'UNKNOWN' for k in FIELDS})
    value.update(assumptions)
    return _context(value)


def _context(value):
    value = json.loads(c.owned(value, limit=4096))
    if type(value) is not dict or set(value) != set(FIELDS) | {'schema_version'} or value['schema_version'] != CONTEXT_VERSION:
        raise WindowError('INVALID_CONTEXT', 'exact versioned context fields required')
    if any(type(value[k]) is not str or value[k] not in choices for k, choices in FIELDS.items()):
        raise WindowError('INVALID_CONTEXT', 'closed exact string assumptions required')
    return value


def _term(field, *allowed):
    return dict(field=field, allowed=list(allowed))


_TEMPLATES = c.owned([
    dict(key='ordinary-priority-opportunity',rule_reference='605.3a',conditions=[_term('priority_opportunity','YES')],
         conditional_consequence='The retained ordinary-priority opportunity category applies; other activation requirements remain unresolved.'),
    dict(key='mana-payment-opportunity',rule_reference='605.3a',conditions=[_term('payment_opportunity','$RETAINED_PAYMENT_CATEGORIES')],
         conditional_consequence='The explicitly assumed mana-payment opportunity category applies; its existence and legal procedure are not verified.'),
    dict(key='no-stack-immediate-resolution',rule_reference='605.3b',conditions=[],
         conditional_consequence='The retained activated-mana exception describes no stack entry and immediate resolution after activation; no activation or resolution occurred.'),
    dict(key='same-ability-repeat-restriction',rule_reference='605.3c',conditions=[_term('same_ability_unresolved','YES')],
         conditional_consequence='The same ability cannot be reactivated before that activation resolves; no lock or game event is executed.'),
    dict(key='post-resolution-priority-return',rule_reference='405.6c',conditions=[_term('held_priority_before_activation','YES'),_term('activation_resolved','YES')],
         conditional_consequence='The retained conditional recipient is $RETAINED_RECIPIENT; no general priority procedure is supplied.'),
])


def _propositions(rules):
    """Finite source adapter: use admitted structured semantics, not rule-number parsing."""
    a, b, lock = (rules[k]['rule']['semantic_distinctions'] for k in ('605.3a', '605.3b', '605.3c'))
    returned = rules['405.6c']['rule']['post_mana_activation_priority_return_context']
    if (a['eligibility_categories_only'] is not True or b['actual_stack_entry'] is not False
            or b['resolution_sequence'] != 'IMMEDIATELY_AFTER_ACTIVATION'
            or lock['restricted_subject'] != 'SAME_ABILITY' or lock['same_ability_reactivation_before_resolution'] is not False
            or returned['condition'] != 'PLAYER_HELD_PRIORITY_IMMEDIATELY_BEFORE_ACTIVATION'
            or returned['applicability'] != 'ACTIVATED_MANA_ABILITY_ONLY'
            or returned['return_context'] != 'AFTER_MANA_ABILITY_RESOLUTION'):
        raise WindowError('UNSUPPORTED_EVIDENCE', 'retained descriptors do not supply the supported propositions')
    windows = a['activation_opportunity_categories']
    if 'ORDINARY_PRIORITY' not in windows or set(windows) != {'ORDINARY_PRIORITY', *FIELDS['payment_opportunity'][1:5]}:
        raise WindowError('UNSUPPORTED_EVIDENCE', 'exact retained opportunity categories required')
    rows = json.loads(_TEMPLATES)
    for row in rows:
        row['rule_id'] = rules[row['rule_reference']]['rule']['rule_id']
        row['conditions'].insert(0,_term('classification','ACTIVATED_MANA'))
        for term in row['conditions']:
            if term['allowed'] == ['$RETAINED_PAYMENT_CATEGORIES']:
                term['allowed'] = [w for w in windows if w != 'ORDINARY_PRIORITY']
        row['conditional_consequence'] = row['conditional_consequence'].replace('$RETAINED_RECIPIENT',returned['recipient'])
    return rows


def evaluate_propositions(propositions, context):
    """Pure bounded conjunction evaluation; never an evidence-admission interface."""
    context = _context(context)
    props = json.loads(c.owned(propositions, limit=16384))
    if type(props) is not list or not 1 <= len(props) <= 16:
        raise WindowError('INVALID_PROPOSITIONS', 'one to sixteen structured propositions required')
    seen, findings = set(), []
    for prop in props:
        if (type(prop) is not dict or set(prop) != {'key','rule_reference','rule_id','conditions','conditional_consequence'}
                or any(type(prop[k]) is not str or not prop[k] or len(prop[k]) > 1024 for k in ('key','rule_reference','rule_id','conditional_consequence'))
                or prop['key'] in seen or type(prop['conditions']) is not list or not 1 <= len(prop['conditions']) <= 8):
            raise WindowError('INVALID_PROPOSITIONS', 'closed finite proposition fields required')
        seen.add(prop['key']); conditions = []; used = set()
        for term in prop['conditions']:
            if (type(term) is not dict or set(term) != {'field','allowed'} or type(term['field']) is not str
                    or term['field'] not in FIELDS or term['field'] in used or type(term['allowed']) is not list
                    or not term['allowed'] or any(type(v) is not str or v not in FIELDS[term['field']] or v in ('UNKNOWN','UNSUPPORTED') for v in term['allowed'])
                    or len(set(term['allowed'])) != len(term['allowed'])):
                raise WindowError('INVALID_PROPOSITIONS', 'closed unique condition terms required')
            used.add(term['field']); supplied = context[term['field']]
            state = 'UNKNOWN' if supplied == 'UNKNOWN' else 'UNSUPPORTED' if supplied == 'UNSUPPORTED' else 'SATISFIED' if supplied in term['allowed'] else 'UNSATISFIED'
            conditions.append(dict(**term, supplied=supplied, status=state))
        states = [t['status'] for t in conditions]
        status = ('INAPPLICABLE' if 'UNSATISFIED' in states else 'UNSUPPORTED' if 'UNSUPPORTED' in states
                  else 'UNKNOWN' if 'UNKNOWN' in states else 'APPLICABLE')
        if context['classification'] in ('TRIGGERED_MANA', 'UNSUPPORTED'):
            status = 'UNSUPPORTED'
        conflicts = []
        if context['classification'] == 'ACTIVATED_MANA' and context['stack_use'] == 'YES':
            conflicts.append('ACTIVATED_MANA_WITH_STACK_USE_YES')
        if context['same_ability_unresolved'] == 'YES' and context['activation_resolved'] == 'YES':
            conflicts.append('SAME_ACTIVATION_BOTH_UNRESOLVED_AND_RESOLVED')
        conflicting = bool(conflicts)
        if conflicting: status = 'CONFLICTING'
        findings.append(dict(prop, conditions=conditions, status=status,
            conflicts=conflicts,
            consequence_established=status == 'APPLICABLE'))
    return dict(findings=sorted(findings,key=lambda r:r['key']),
        authority='PURE_HYPOTHETICAL_EVALUATION_NOT_EVIDENCE_ADMISSION', legal_activation='NOT_ESTABLISHED', execution_authority='BLOCKED')


_POLICY = c.seal(POLICY_VERSION, dict(schema_version=POLICY_VERSION, fields={k:list(v) for k,v in FIELDS.items()},
    meanings=MEANINGS, templates=json.loads(_TEMPLATES), common_condition=_term('classification','ACTIVATED_MANA'),
    conjunction='KNOWN_FALSE_THEN_UNSUPPORTED_THEN_UNKNOWN_THEN_TRUE',
    conflicts=['ACTIVATED_MANA_WITH_STACK_USE_YES','SAME_ACTIVATION_BOTH_UNRESOLVED_AND_RESOLVED'], rules=dict(RULE_IDS),
    scope='HYPOTHETICAL_APPLICABILITY_ONLY', execution_authority='BLOCKED'), 'policy_id')
POLICY_ID = _POLICY['policy_id']


def _ref(document):
    raw = document.to_json().encode()
    return dict(kind='mana-window-retained-evidence', identity=document.to_dict()['evidence_id'],
        bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), route='ManaWindowConsumer.detailed(reference)')


@dataclass(frozen=True, init=False)
class ManaWindowConsumer:
    _closure: closure.SemanticClosureConsumer
    _evidence: bytes
    _closure_report: bytes

    def assess(self, context):
        context = _context(context); evidence = json.loads(self._evidence); original = json.loads(self._closure_report)
        rules = {r['rule']['rule_reference']:r for r in evidence['rules']}
        result = evaluate_propositions(_propositions(rules), context)
        report = dict(schema_version=VERSION, policy_id=POLICY_ID,
            context=c.seal(CONTEXT_VERSION,context,'context_id'), assumptions_authority='CALLER_SUPPLIED_HYPOTHETICAL_NOT_OBSERVED_OR_VERIFIED',
            findings=result['findings'], status_meanings=MEANINGS,
            disposition='NON_EXECUTING_APPLICABILITY_ASSESSMENT', legal_activation='NOT_ESTABLISHED',
            canonical_admission=False, execution_authority='BLOCKED',
            source_policy_clearance=original['authority']['source_policy_clearance'], permissions=original['authority']['permissions'],
            composition=dict(schema_version=COMPOSITION_VERSION, closure_report_id=original['report_id'],
                accepted_candidate_id=original['input']['candidate_id'], owner_decision_id=original['input']['decision_id'],
                scope='REFERENCE_ONLY_NO_REQUIREMENT_OR_CARD_SEMANTIC_PROMOTION', closure_unchanged=True,
                stronger_consumer='DEFERRED_REQUIRES_EXPLICIT_VERSIONED_ADMISSION_NOT_AUTOMATIC'),
            evidence_id=evidence['evidence_id'], references=[dict(reference=r['rule']['rule_reference'],rule_id=r['rule']['rule_id'],
                package_id=r['package_id'],projection_id=r['projection_id'],source_anchor=r['rule']['source_anchor']) for r in evidence['rules']],
            detailed_reference=_ref(c.ReviewDocument._verified(evidence,limit=LIMIT)),
            missing_dependencies=['General priority establishment and passing are not admitted.',
                'Actual payment requests, complete activation legality, tap costs, mana-pool changes, checkpoints and illegal-action recovery remain unestablished.',
                'No general 117 procedure or missing dependency body is inferred from a citation.'],
            limitations=['APPLICABLE is conditional on hypothetical assumptions, not a legal action, observed event or complete procedure.',
                'An INAPPLICABLE proposition supplies no opposite permission or conclusion about other rules.',
                'Retained projection/dependency review is not executable semantic approval or current source verification.',
                'No triggered procedure, targets, additional-effect ordering or real-card execution is established.',
                'Fictional gameplay supplies no real-rules evidence or execution authority.'])
        return c.ReviewDocument._verified(c.seal(VERSION, report,'report_id'),limit=LIMIT)

    def check(self):
        return self.assess(hypothetical_context())

    def validate_report(self, value, *, expected_context=None):
        if type(value) is not dict or type(value.get('context')) is not dict:
            raise WindowError('INVALID_REPORT','submitted context required')
        context = dict(value['context']); claimed = context.pop('context_id',None)
        if claimed != c.identity(CONTEXT_VERSION,context,'context_id'):
            raise WindowError('INVALID_REPORT','exact context identity required')
        if expected_context is not None:
            c.exact(context,_context(expected_context),limit=4096)
        expected = self.assess(context); c.exact(value, expected.to_dict(), limit=LIMIT)
        return expected

    def parse_report(self, raw):
        return self.validate_report(c.parse_json(raw,limit=LIMIT))

    def detailed(self, reference):
        doc = c.ReviewDocument._verified(json.loads(self._evidence),limit=LIMIT)
        if reference == doc.to_dict()['historical_reference']:
            return self._closure.detailed(reference)
        c.exact(reference,_ref(doc),limit=4096)
        return doc


def load_mana_window(**closure_arguments):
    """Revalidate actual owning admission once per public load. Never admit copied reports."""
    try:
        admitted = closure.load_semantic_closure(**closure_arguments)
        original = admitted.check().to_dict()
        history = admitted.detailed(original['detailed_references']['historical']).to_dict()
        retained = history['context']['retained_rules']
        if retained['context_id'] != closure.CONTEXT_ID or original['policy_id'] != closure.policy.POLICY_ID:
            raise WindowError('EVIDENCE_BINDING','exact historical admission required')
        rules = {r['rule']['rule_reference']:r for r in retained['rules']}
        selected = []
        for reference, identity in RULE_IDS:
            row = rules[reference]
            if row['rule']['rule_id'] != identity:
                raise WindowError('EVIDENCE_BINDING','exact admitted rule identity required')
            selected.append(row)
        _propositions(rules)
        evidence = c.seal('mana-window-retained-evidence-v1',dict(schema_version='mana-window-retained-evidence-v1',
            historical_report_id=history['report_id'],context_id=retained['context_id'],
            rules=selected,dependency_reviews=[{k:r[k] for k in ('package','package_id','record','review_id','schema_version','identity_domain')}
                for r in retained['current_dependency_reviews']],
            historical_reference=original['detailed_references']['historical'],
            review_scope='RETAINED_METADATA_INTEGRITY_AND_BOUNDED_DEPENDENCY_REVIEW_NOT_EXECUTABLE_APPROVAL',
            verification_scope=retained['verification_scope'],permissions=retained['permissions'],
            source_policy_clearance=retained['source_policy_clearance']), 'evidence_id')
        result = object.__new__(ManaWindowConsumer)
        object.__setattr__(result,'_closure',admitted)
        object.__setattr__(result,'_closure_report',c.owned(original,limit=closure.REPORT_LIMIT))
        object.__setattr__(result,'_evidence',c.owned(evidence,limit=LIMIT))
        result.check()
        return result
    except (ValueError,OSError,KeyError,TypeError) as error:
        raise WindowError('EVIDENCE_ADMISSION_REJECTED',str(error)) from None


def render_window(document):
    v = document.to_dict()
    lines = ['Real-mana activation-window applicability — hypothetical only',
        'Legal activation: '+v['legal_activation']+'; execution: '+v['execution_authority'],
        'Assumptions: '+json.dumps(v['context'],sort_keys=True)]
    for r in v['findings']:
        lines.append(r['key']+' ['+r['status']+'] — '+r['rule_reference']+' / '+r['rule_id'])
        lines.append('  '+(r['conditional_consequence'] if r['consequence_established'] else 'No consequence established; inspect the individual condition findings.'))
    lines += [*v['missing_dependencies'],*v['limitations'],'Evidence: '+v['evidence_id'], 'Report: '+v['report_id']]
    raw='\n'.join(lines)+'\n'
    if len(raw.encode())>READABLE_LIMIT: raise WindowError('OUTPUT_BOUND','readable bound exceeded')
    return raw


def main(argv=None):
    import argparse
    from pathlib import Path
    import sys
    parser=argparse.ArgumentParser(description='Read-only hypothetical real-mana applicability; never legality or execution')
    for name in ('catalog-root','mechanical-root','review-root','cohort-root','decision-root'):
        parser.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-profile-id','expected-query-snapshot-id','expected-plan-id','expected-decision-id'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--json',action='store_true')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('assess','validate','detail'): sub.add_parser(name).add_argument('file',type=Path)
    sub.add_parser('check');args=parser.parse_args(argv)
    try:
        consumer=load_mana_window(**{k:getattr(args,k) for k in ('catalog_root','mechanical_root','review_root','cohort_root',
            'decision_root','expected_profile_id','expected_query_snapshot_id','expected_plan_id','expected_decision_id')})
        if args.command=='assess': doc=consumer.assess(c.read_json(args.file,limit=4096))
        elif args.command=='validate': doc=consumer.validate_report(c.read_json(args.file,limit=LIMIT))
        elif args.command=='detail': doc=consumer.detailed(c.read_json(args.file,limit=4096))
        else: doc=consumer.check()
        sys.stdout.write(doc.to_json() if args.json or args.command=='detail' else render_window(doc));return 0
    except (ValueError,OSError) as error:
        sys.stderr.write(json.dumps(dict(code=getattr(error,'code','EVIDENCE_REJECTED'),message=str(error)),sort_keys=True)+'\n');return 2


if __name__=='__main__':
    raise SystemExit(main())
