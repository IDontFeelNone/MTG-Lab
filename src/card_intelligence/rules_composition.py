"""Compose retained rules reasoning with exact static-pool assignment.

This is a conjunction of independently declared analytical premises, not a
conversion from mana-ability classification into resources or legal actions.
"""
from dataclasses import dataclass
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys

from card_rules_pilot import contract as c
from probability import resource_assignment as resources
from . import rules_reasoning as rules

INPUT_VERSION = 'rules-reasoning-composition-input-v1'
VERSION = 'rules-reasoning-composition-report-v1'
QUESTION = 'MANA_PAYMENT_TIMING_AND_STATIC_ASSIGNMENT'
INPUT_LIMIT = 24576
REPORT_LIMIT = 65536
ASSUMPTIONS = {
    'pool': 'INDEPENDENTLY_DECLARED_STATIC_AVAILABILITY',
    'demands': 'ABSTRACT_REQUIREMENTS_NOT_VERIFIED_MAGIC_COSTS',
    'ability_output': 'NOT_INFERRED_FROM_MANA_ABILITY_CLASSIFICATION',
}
CODE_FILES = ('card_intelligence/rules_composition.py', 'card_intelligence/rules_reasoning.py',
    'card_intelligence/mana_window.py', 'probability/resource_assignment.py',
    'probability/draw_access.py', 'card_rules_pilot/contract.py', 'card_rules_pilot/land_context.py')
NEGATIVE_TIMING = ('NO_MANA_PAYMENT_EXCEPTION', 'SAME_ABILITY_REACTIVATION_PROHIBITED',
                   'NO_DECLARED_MANA_PAYMENT_OPPORTUNITY')


class CompositionError(c.PilotError):
    def __init__(self, code, reason, *, component='composition'):
        self.code, self.component = code, component
        super().__init__(reason)

    def as_dict(self):
        return dict(schema_version=VERSION, status='REFUSED', code=self.code,
            component=self.component, reason=str(self), legal_activation='NOT_ESTABLISHED',
            resource_generation='NOT_ESTABLISHED', execution_authority='BLOCKED')


def _require(value, reason, code='INVALID_INPUT'):
    if not value:
        raise CompositionError(code, reason)


def _code_binding():
    # Same selected-code compatibility pattern as portable investigations. This
    # binds packaged entry points, not authenticated authorship or all Python.
    root = Path(__file__).resolve().parents[1]
    result = {}
    try:
        for name in CODE_FILES:
            path = root/name
            _require(not path.is_symlink() and path.is_file() and path.stat().st_size <= 524288,
                     'bounded packaged component code required', 'INCOMPATIBLE_ENGINE')
            with path.open('rb') as stream:
                raw = stream.read(524289)
            _require(len(raw) <= 524288, 'component code byte bound', 'INCOMPATIBLE_ENGINE')
            result[name] = sha256(raw).hexdigest()
    except OSError:
        raise CompositionError('DEPENDENCY_UNAVAILABLE', 'packaged component code unavailable') from None
    return result


_AT_IMPORT = _code_binding()


def _engine():
    current = _code_binding()
    _require(current == _AT_IMPORT, 'packaged components changed in this session', 'INCOMPATIBLE_ENGINE')
    _require(rules.VERSION == 'real-card-rules-reasoning-report-v1'
             and resources.REPORT_VERSION == 'declared-resource-assignment-report-v1'
             and resources.METHOD == 'weighted-count-vectors-distinct-matching-v1',
             'unsupported component version', 'INCOMPATIBLE_ENGINE')
    return dict(implementation=current, rules_schema=rules.VERSION,
                resource_schema=resources.REPORT_VERSION, resource_method=resources.METHOD)


def _input(value):
    try:
        value = json.loads(c.owned(value, limit=INPUT_LIMIT))
    except (c.PilotError, ValueError, TypeError, RecursionError):
        raise CompositionError('INVALID_INPUT', 'bounded exact JSON request required') from None
    _require(type(value) is dict and set(value) == {'schema_version','question','scenario_id',
             'rules','resources','assumptions'}, 'closed composition request required')
    _require(value['schema_version'] == INPUT_VERSION, 'unsupported input version', 'UNSUPPORTED_VERSION')
    _require(value['question'] == QUESTION, 'unsupported question', 'UNSUPPORTED_QUESTION')
    key = value['scenario_id']
    _require(type(key) is str and 0 < len(key) <= 128 and key == key.strip() and key.isprintable(),
             'bounded scenario identity required')
    _require(type(value['rules']) is dict and value['rules'].get('scenario_id') == key,
             'one explicitly bound rules scenario required', 'INCONSISTENT_SCOPE')
    _require(value['assumptions'] == ASSUMPTIONS and type(value['assumptions']) is dict,
             'explicit independent-pool and abstract-demand assumptions required', 'UNSUPPORTED_ASSUMPTIONS')
    try:
        resource_input = resources.validate_resource_assignment(value['resources'])
    except resources.ResourceAssignmentError as error:
        raise CompositionError(error.code, str(error), component='resources') from None
    _require(resource_input['cards_seen'] == resource_input['population_size'],
             'complete static pool must be observed in full; draw probability is not availability',
             'UNSUPPORTED_RESOURCE_SCOPE')
    _require(resource_input['target'] == {'minimum':0,'mode':'observe'}
             and all(row['target'] is False for row in resource_input['classes']),
             'this question concerns resource jobs only; target access/reservation is not composed',
             'UNSUPPORTED_RESOURCE_SCOPE')
    _require(any(resource_input['demands'].values()), 'at least one positive abstract demand required',
             'UNSUPPORTED_RESOURCE_SCOPE')
    value['resources'] = resource_input
    return value


def _compose(value, rule_report, resource_report, engine):
    decision = rule_report['decision']
    _require(decision in ('PAYMENT_TIMING_EXCEPTION_APPLIES','NEEDS_FACTS',*NEGATIVE_TIMING),
             'unsupported rules conclusion', 'INCOMPATIBLE_ENGINE')
    p = resource_report['probability']
    # Full-pool sampling has precisely one physical hand. Read the owning exact
    # answer, never run a second matching/assignment solver or round a decimal.
    _require(resource_report['total_physical_hands'] == '1'
             and p['denominator'] == '1' and p['numerator'] in ('0','1'),
             'component did not establish exact full-pool feasibility', 'INCOMPATIBLE_ENGINE')
    feasible = p['numerator'] == '1'
    negative = []
    if decision in NEGATIVE_TIMING: negative.append(decision)
    if not feasible: negative.append('STATIC_RESOURCE_ASSIGNMENT_INFEASIBLE')
    status = ('NOT_SUPPORTED_UNDER_DECLARATIONS' if negative else
              'SUPPORTED_UNDER_DECLARATIONS' if decision == 'PAYMENT_TIMING_EXCEPTION_APPLIES' else 'UNRESOLVED')
    findings = {r['key']:r['status'] for r in rule_report['opportunity_findings']}
    return c.seal(VERSION, dict(schema_version=VERSION, input=value,
        input_id=c.identity(INPUT_VERSION,value,'input_id'), engine=engine,
        components=dict(rules=rule_report, resources=resource_report),
        component_references=dict(rules=dict(operation='card_intelligence.rules_reasoning.RulesReasoner.assess',
            report_id=rule_report['report_id']), resources=dict(operation='probability.resource_assignment.assess_resource_assignment',
            report_id=resource_report['report_id'], input_id=resource_report['input_id'])),
        evidence_reference=dict(context_id=rule_report['evidence']['context_id'],
            location='components.rules.evidence', source_scope='UNCHANGED_RETAINED_METADATA_ONLY'),
        conclusion=dict(status=status, negative_reasons=negative,
            mana_classification=rule_report['classification']['status'],
            payment_opportunity=findings['payment'], same_ability_restriction=findings['repeat'],
            static_assignment='FEASIBLE' if feasible else 'INFEASIBLE',
            meaning='Conjunction of the bounded mana-payment timing finding, absence of its same-ability restriction, and independent static-pool assignment; not a legal activation.'),
        steps=[dict(component='rules', premise='mana classification', result=rule_report['classification']['status']),
               dict(component='rules', premise='payment opportunity', result=findings['payment']),
               dict(component='rules', premise='same-ability restriction', result=findings['repeat']),
               dict(component='resources', premise='exact full-pool assignment', result='FEASIBLE' if feasible else 'INFEASIBLE'),
               dict(component='composition', premise='known-negative, then unknown, then supported conjunction', result=status)],
        missing_facts=['rules.'+item for item in rule_report['missing_facts']],
        unresolved_dependencies=list(rule_report['full_legality_gaps']) + [
            'Actual current resource availability and generation are declarations, not verified game-state facts.',
            'Abstract demands are not a verified Magic cost, and one-unit memberships are not admitted mana-production semantics.',
            'No causal link from the selected ability to any pool copy or resource unit is established.'],
        authority=dict(facts='CALLER_DECLARED', canonical_admission=False, real_card_verified=False,
            legal_activation='NOT_ESTABLISHED', resource_generation='NOT_ESTABLISHED',
            actual_payment='NOT_ESTABLISHED', strategic_usefulness='NOT_ASSESSED',
            execution_authority='BLOCKED', game_actions_performed=False,
            source_policy_clearance=rule_report['authority']['source_policy_clearance'],
            permissions=rule_report['authority']['permissions']),
        limitations=[
            'Rules and resource findings remain separate; neither component supplies the other component\'s premises.',
            'The resource pool is fully observed and independently declared static, with no sampling uncertainty or inferred draws.',
            'A positive conjunction establishes neither casting feasibility nor activation legality, actual output, payment, a winning interaction or strategic superiority.',
            'A negative conjunction does not decide unrelated permissions; unknown rules facts remain unknown even if resources already defeat the conjunction.',
            'Historical projection states, source-use observations and real-card execution gates remain unchanged.',
            'No Card source, new acquisition, private collection, production snapshot or external provider is accessed.']), 'report_id')


@dataclass(frozen=True, init=False)
class RulesComposition:
    _rules: rules.RulesReasoner

    def assess(self, request):
        value, engine = _input(request), _engine()
        try:
            rule_report = self._rules.assess(value['rules']).to_dict()
        except rules.RulesReasoningError as error:
            raise CompositionError(error.code, str(error), component='rules') from None
        try:
            resource_report = resources.assess_resource_assignment(value['resources'])
        except resources.ResourceAssignmentError as error:
            raise CompositionError(error.code, str(error), component='resources') from None
        return c.ReviewDocument._verified(_compose(value,rule_report,resource_report,engine), limit=REPORT_LIMIT)

    def validate_report(self, value):
        try:
            _require(type(value) is dict and 'input' in value, 'report input required', 'INVALID_REPORT')
            expected = self.assess(value['input'])
            c.exact(value,expected.to_dict(),limit=REPORT_LIMIT)
            return expected
        except c.PilotError as error:
            if isinstance(error,CompositionError): raise
            raise CompositionError('INVALID_REPORT','composition does not reproduce from current components and evidence') from None

    def replay(self, raw):
        try:
            return self.validate_report(c.parse_json(raw,limit=REPORT_LIMIT))
        except c.PilotError as error:
            if isinstance(error,CompositionError): raise
            raise CompositionError('INVALID_REPORT','bounded canonical report bytes required') from None

    def record_reference(self, artifact, report, *, branch_id, parent_id, metadata):
        """Explicit note-only revision in the EXISTING investigation format.

        The caller retains the full composition separately. Native investigation
        replay does not fetch/replay external references or bless their claims.
        """
        verified = self.validate_report(report).to_dict()
        from workbench.investigations import append_revision, InvestigationError
        try:
            meta = json.loads(c.owned(metadata,limit=65536))
            _require(type(meta) is dict and type(meta.get('evidence_references')) is list,
                     'explicit research metadata required')
            meta['evidence_references'].append(dict(relation='qualifying',
                label='Conditional rules/static-resource composition; replay separately', reference=verified['report_id']))
            return append_revision(artifact,branch_id=branch_id,parent_id=parent_id,metadata=meta,
                                   analytical_input=None,calculate=False)
        except (c.PilotError,InvestigationError) as error:
            if isinstance(error,CompositionError): raise
            raise CompositionError('RESEARCH_REFERENCE_REFUSED', str(error), component='research') from None


def load_rules_composition(*, review_root, expected_context_id):
    _engine()
    try:
        admitted = rules.load_rules_reasoner(review_root=review_root,expected_context_id=expected_context_id)
    except rules.RulesReasoningError as error:
        raise CompositionError(error.code,str(error),component='rules') from None
    result = object.__new__(RulesComposition)
    object.__setattr__(result,'_rules',admitted)
    return result


def render_composition(report):
    value=report.to_dict(); conclusion=value['conclusion']; native=value['components']
    return '\n'.join(['MTG Lab — rules/resource composition', 'Scenario: '+value['input']['scenario_id'],
        'Conclusion: '+conclusion['status'], 'Mana classification: '+conclusion['mana_classification'],
        'Payment opportunity: '+conclusion['payment_opportunity'],
        'Same-ability restriction: '+conclusion['same_ability_restriction'],
        'Declared static assignment: '+conclusion['static_assignment'],
        'Exact full-pool result: '+native['resources']['probability']['numerator']+'/1 (not a casting probability)',
        'Negative reasons: '+(', '.join(conclusion['negative_reasons']) or 'none'),
        'Missing facts: '+(', '.join(value['missing_facts']) or 'none for the bounded conjunction'),
        'Rules report: '+native['rules']['report_id'], 'Resource report: '+native['resources']['report_id'],
        'Composition report: '+value['report_id'],
        'Actual activation legality, resource generation and payment: NOT_ESTABLISHED. Execution: BLOCKED.'])+'\n'


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-root',type=Path,required=True)
    parser.add_argument('--expected-context-id',required=True)
    parser.add_argument('--json',action='store_true')
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('assess','validate'): commands.add_parser(name).add_argument('input',type=Path)
    args=parser.parse_args(argv)
    try:
        consumer=load_rules_composition(review_root=args.review_root,expected_context_id=args.expected_context_id)
        value=c.read_json(args.input,limit=INPUT_LIMIT if args.command=='assess' else REPORT_LIMIT)
        report=consumer.assess(value) if args.command=='assess' else consumer.validate_report(value)
        print(report.to_json() if args.json else render_composition(report),end='')
        return 0
    except (c.PilotError,OSError) as error:
        refusal=error if isinstance(error,CompositionError) else CompositionError('INVALID_INPUT','input or retained evidence unavailable')
        print(json.dumps(refusal.as_dict(),sort_keys=True),file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
