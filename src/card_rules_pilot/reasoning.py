"""Bounded conditional reasoning from one freshly verified pending pilot.

The original comparison supplies shared, complete provenance. Local premise refs
resolve only within that exact original candidate; hypothetical states never
replace its bytes or candidate identity.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .contract import (PilotError, ReviewDocument, owned, seal, exact)
from .pilot import load_pilot
from . import reasoning_policy as policy

ANALYSIS_VERSION = 'card-rules-mana-evidence-analysis-v1'
COMPARISON_VERSION = 'card-rules-mana-evidence-comparison-v1'
IMPACT_VERSION = 'card-rules-mana-review-impact-v1'
CASE_VERSION = 'card-rules-mana-hypothetical-case-v1'
REASONING_LIMIT = 1_048_576
CASE_LIMIT = 65_536
_AUTHORITY_BYTES = owned({
    'authority': 'DERIVED_FROM_PENDING_AUTHORED_READINGS_ONLY',
    'input_authority': 'ENGINEER_AUTHORED_PENDING_INTERPRETATION_ONLY',
    'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
    'review': {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False},
    'execution_authority': 'BLOCKED',
})


def _authority():
    return json.loads(_AUTHORITY_BYTES)
UNCHANGED = 'Only the named unknown row is assumed changed; every other authored reading and all evidence bindings remain unchanged.'
SELF_CAVEAT = 'Completing this assessment may require revising other criterion readings. This hypothetical holds those readings unchanged.'
LIMITATIONS = (
    'Every calculation, including a complete hypothetical, remains pending semantic review.',
    'No current activation eligibility, actual mana output, event causality, legal action, response window or official Card ruling is established.',
    'Source correspondence, code review, PM approval and owner merge do not approve Card semantics.',
    'No canonical admission, fictional evaluation or gameplay execution authority is supplied.',
)


class ReasoningReport(ReviewDocument):
    """Separately identified derived report, never an interpretation candidate."""


def _inputs(candidate, change=None):
    authored = candidate['authored_interpretation']
    definitions = candidate['criterion_definitions']
    rows = []
    for reading, definition in zip(authored['criteria'], definitions, strict=True):
        if reading['criterion_id'] != definition['criterion_id']:
            raise PilotError('criterion definition correspondence mismatch')
        rows.append({'criterion_id': reading['criterion_id'],
            'state': change[1] if change and reading['criterion_id'] == change[0] else reading['state'],
            'rule_refs': definition['rule_refs']})
    return dict(proposed_kind=authored['proposed_kind'], criteria=rows,
                kind_evidence_refs=authored['classification_evidence_refs'])


def _relationship(result, proposal):
    overall = result['overall_assessment']
    if overall == 'INCOMPLETE_ASSESSMENT_UNDER_AUTHORED_READINGS':
        return 'INCOMPLETE: substantive findings are preserved, but method obligations prevent completing the original proposal; the proposal remains unchanged.'
    if overall == 'INDETERMINATE_UNDER_AUTHORED_READINGS':
        return ('AGREEMENT: both remain unresolved under the authored readings.' if proposal == 'interpretation_unresolved'
                else 'TENSION: unresolved substantive inputs prevent completing the original proposal.')
    expected = ('proposed_exclusion' if overall == 'CONDITIONALLY_EXCLUDED_UNDER_AUTHORED_READINGS'
                else 'proposed_' + result['branch'] + '_mana_ability')
    return ('AGREEMENT: conditional calculation matches the original proposal; semantic review remains pending.'
            if proposal == expected else 'TENSION: conditional calculation differs from the unchanged original proposal; this supplies no corrected interpretation.')


def _analysis(candidate, change=None):
    inputs = _inputs(candidate, change)
    result = policy.compute(**inputs)
    authored = candidate['authored_interpretation']
    substantive = set(policy.policy_document()['activated_substantive'] if result['branch'] == 'activated'
                      else policy.policy_document()['triggered_substantive'] if result['branch'] == 'triggered' else ())
    methods = set(policy.policy_document()['activated_method_obligations'] if result['branch'] == 'activated' else ())
    binding = {key: candidate[key] for key in ('plan_id', 'candidate_id')}
    binding['subject_id'] = candidate['subject']['subject_id']
    premises, questions = [], []
    for reading, row in zip(authored['criteria'], inputs['criteria'], strict=True):
        criterion = reading['criterion_id']
        role = 'substantive' if criterion in substantive else 'method' if criterion in methods else 'inapplicable'
        premise = {**binding, 'criterion_id': criterion, 'original_state': reading['state'],
            'state': row['state'], 'role': role, 'evidence_refs': reading['evidence_refs'],
            'rule_refs': row['rule_refs']}
        premises.append(premise)
        if role != 'inapplicable' and row['state'] != 'proposed_satisfied':
            questions.append({**binding, 'criterion_id': criterion, 'state': row['state'],
                'category': role, 'evidence_refs': reading['evidence_refs'],
                'question': ('Review the assessment method' if role == 'method' else 'Review the substantive requirement') +
                    ' for this exact candidate; retain its original rationale, limitations and contrary evidence.'})
    if result['branch'] == 'spell':
        premises.append({**binding, 'criterion_id': 'spell_exclusion', 'original_state': authored['proposed_kind'],
            'state': authored['proposed_kind'], 'role': 'substantive',
            'evidence_refs': authored['classification_evidence_refs'], 'rule_refs': ['605.5b']})
    return {**binding, 'proposed_kind': authored['proposed_kind'],
        'original_proposal': authored['proposed_classification'], 'result': result,
        'premises': premises, 'review_questions': questions,
        'proposal_relationship': _relationship(result, authored['proposed_classification']), **_authority()}


def _document(version, context, **payload):
    questions = payload.get('review_questions', [])
    summary = {
        'substantive_gaps': [q for q in questions if q['category'] == 'substantive' and q['state'] != 'proposed_not_satisfied'],
        'methodological_gaps': [q for q in questions if q['category'] == 'method'],
        'negative_substantive_findings': [q for q in questions if q['category'] == 'substantive' and q['state'] == 'proposed_not_satisfied'],
    }
    value = seal(version, {'schema_version': version, 'policy': policy.policy_document(),
        'context': context, 'review_question_summary': summary, **payload, **_authority(), 'limitations': list(LIMITATIONS)}, 'report_id')
    return ReasoningReport._verified(value, limit=REASONING_LIMIT)


@dataclass(frozen=True, init=False)
class ManaEvidenceReasoning:
    """Private immutable original comparison; no filesystem reader escapes."""
    _raw: bytes

    def _original(self):
        return json.loads(self._raw)

    @property
    def subject_ids(self):
        return tuple(c['subject']['subject_id'] for c in self._original()['candidates'])

    def subject(self, subject_id):
        if type(subject_id) is not str or subject_id not in self.subject_ids:
            raise PilotError('exact fixed pilot subject required')
        candidate = next(c for c in self._original()['candidates'] if c['subject']['subject_id'] == subject_id)
        analysis = _analysis(candidate)
        return _document(ANALYSIS_VERSION, {'candidate': candidate}, analyses=[analysis],
                         review_questions=analysis['review_questions'])

    def comparison(self):
        original = self._original()
        analyses = [_analysis(c) for c in original['candidates']]
        return _document(COMPARISON_VERSION, {'original_comparison': original}, analyses=analyses,
            review_questions=[q for a in analyses for q in a['review_questions']])

    def review_impact(self):
        original = self._original()
        cases = []
        for candidate in original['candidates']:
            for row in candidate['authored_interpretation']['criteria']:
                if row['state'] != 'unknown':
                    continue
                for assumed in ('proposed_satisfied', 'proposed_not_satisfied'):
                    analysis = _analysis(candidate, (row['criterion_id'], assumed))
                    cases.append(seal(CASE_VERSION, {
                        'schema_version': CASE_VERSION, 'plan_id': candidate['plan_id'],
                        'candidate_id': candidate['candidate_id'], 'subject_id': candidate['subject']['subject_id'],
                        'criterion_id': row['criterion_id'], 'original_state': row['state'],
                        'hypothetical_state': assumed, 'policy_id': policy.POLICY_ID,
                        'policy_version': policy.POLICY_VERSION,
                        'unchanged_input_assumption': UNCHANGED,
                        'assessment_caveat': SELF_CAVEAT if row['criterion_id'] == 'self_replacement_considered'
                            else 'This assumed trigger-relationship reading supplies no new event or causality evidence.',
                        'hypothetical_only': True, 'analysis': analysis, **_authority()}, 'case_id'))
        for case in cases:
            owned(case, limit=CASE_LIMIT)
        if len(cases) != 10:
            raise PilotError('fixed five unknown rows and exactly ten cases required')
        return _document(IMPACT_VERSION, {'original_comparison': original}, cases=cases,
            review_questions=[q for c in original['candidates'] for q in _analysis(c)['review_questions']])

    def validate_report(self, value):
        """Exact recomputation from owned verified inputs, never hash-only trust."""
        value = json.loads(owned(value, limit=REASONING_LIMIT))
        try:
            version = value['schema_version']
            if version == ANALYSIS_VERSION:
                expected = self.subject(value['context']['candidate']['subject']['subject_id'])
            elif version == COMPARISON_VERSION:
                expected = self.comparison()
            elif version == IMPACT_VERSION:
                expected = self.review_impact()
            else:
                raise PilotError('unknown derived report domain')
        except (KeyError, TypeError):
            raise PilotError('closed derived report required') from None
        exact(value, expected.to_dict(), limit=REASONING_LIMIT)
        return expected


def _from_pilot(pilot):
    # All seven originals and every binding validate before any derived output.
    comparison = pilot.comparison()
    for candidate in comparison.to_dict()['candidates']:
        pilot.validate_candidate(candidate)
    result = object.__new__(ManaEvidenceReasoning)
    object.__setattr__(result, '_raw', comparison.to_json().encode('utf-8'))
    # Validate all layouts and cumulative bounds before returning partial reports.
    result.comparison()
    result.review_impact()
    return result


def load_reasoning(**arguments):
    """Freshly admit actual catalog, mechanics, rules and plan exactly once."""
    return _from_pilot(load_pilot(**arguments))


def render_reasoning(document):
    value = document.to_dict()
    lines = ['Bounded mana-classification evidence reasoning',
        'Pending authored inputs; semantic review not established; requires_review; human_attestation=null;',
        'canonical_admission=false; execution_authority=BLOCKED',
        'Policy: ' + value['policy']['schema_version'] + ' / ' + value['policy']['policy_id']]
    context = value['context']
    originals = context['original_comparison']['candidates'] if 'original_comparison' in context else [context['candidate']]
    by_id = {c['candidate_id']: c for c in originals}
    entries = value.get('analyses', []) or [c['analysis'] for c in value['cases']]
    for index, a in enumerate(entries):
        c = by_id[a['candidate_id']]
        lines += ['', a['subject_id'] + ' — ' + c['card_evidence']['card_identity']['name'],
            'Candidate: ' + a['candidate_id'], 'Selected passage: ' + c['subject']['selected_passage'],
            'Owner/context: ' + c['subject']['owner'] + '; ' + c['subject']['ownership_and_context_limitations'],
            'Complete retained field: ' + c['subject']['complete_field_value'],
            'Retained type line: ' + c['subject']['type_line']['value'],
            'Authored kind/classification rationale: ' + c['authored_interpretation']['classification_rationale']]
        if 'cases' in value:
            case = value['cases'][index]
            lines += ['HYPOTHETICAL ' + case['criterion_id'] + ': ' + case['original_state'] + ' -> ' + case['hypothetical_state'],
                case['unchanged_input_assumption'], case['assessment_caveat']]
        r = a['result']
        lines += ['Substantive: ' + r['substantive_result'], 'Assessment method: ' + r['method_status'],
            'Overall: ' + r['overall_assessment'], 'Original proposal: ' + a['original_proposal'], a['proposal_relationship']]
        for premise in a['premises']:
            if premise['role'] == 'inapplicable':
                continue
            lines += ['  ' + premise['role'] + ' ' + premise['criterion_id'] + ': ' + premise['state'] +
                '; evidence: ' + ', '.join(premise['evidence_refs'])]
            reading = next((row for row in c['authored_interpretation']['criteria'] if row['criterion_id'] == premise['criterion_id']), None)
            if reading:
                lines.append('    Authored rationale: ' + reading['rationale'])
        for text in c['authored_interpretation']['counterevidence']:
            lines.append('Counterevidence: ' + text)
        for q in a['review_questions']:
            lines.append('Next ' + q['category'] + ' review: ' + q['criterion_id'] + ' (' + q['state'] + '). ' + q['question'])
    lines += ['', 'Review-question summary (each question retains its own candidate provenance):']
    for category, questions in value['review_question_summary'].items():
        lines.append(category.replace('_', ' ') + ': ' + ('; '.join(
            q['subject_id'] + ' / ' + q['criterion_id'] + ' (' + q['state'] + ')' for q in questions) or 'none under these readings'))
    lines += ['', 'Exact rule identities, anchors, source dates, dossier bindings and full original matrices are available in canonical JSON.', *LIMITATIONS]
    return '\n'.join(lines) + '\n'
