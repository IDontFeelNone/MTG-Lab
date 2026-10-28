"""Read-only behavior implications from freshly admitted pending interpretations.

No imported report is an admission boundary. Historical shared rule evidence is
stored once; inserting it into each compact candidate exactly reconstructs the
original public candidate and comparison, including their historical identities.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .contract import PilotError, ReviewDocument, owned, seal, exact
from .reassessment import load_reassessment
from .reasoning import _inputs
from . import behavior_policy as policy
from .behavior_context import admit_context

REPORT_VERSION = 'card-rules-mana-behavior-comparison-v1'
CHECK_VERSION = 'card-rules-mana-behavior-integrity-v1'
REPORT_LIMIT = 1_048_576
SUBJECTS = ('sol-ring-tap', 'basalt-monolith-tap', 'basalt-monolith-untap',
            'deathrite-shaman-first', 'dark-ritual-spell', 'mana-flare-trigger',
            'pitiless-plunderer-host-trigger')
LIMITATIONS = (
    'Conditional behavior implications from pending retained-text readings only; no semantic approval or execution authority.',
    'Historical provider observations are not current Oracle verification. No new Card reading or source acquisition is made.',
    'All current-game activation, casting, targeting, payment, trigger occurrence, output and legality questions remain unevaluated.',
    'Gained abilities, changed text, copies, external modifiers and arbitrary game states are outside these readings.',
    'Ordinary placement does not establish a response window, legal response, counterspell applicability or successful procedure completion.',
    'The two Basalt abilities are separate; no repeatable sequence or combo follows. A created Treasure ability is not its host trigger.',
    'Source coverage is not procedure completeness. Broad 603 and the retained outgoing procedure frontiers remain unresolved.',
)
_AUTHORITY = owned({
    'authority': 'CONDITIONAL_BEHAVIOR_IMPLICATIONS_FROM_PENDING_READINGS_ONLY',
    'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
    'review': {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False},
    'execution_authority': 'BLOCKED',
})


def _authority():
    return json.loads(_AUTHORITY)


class BehaviorReport(ReviewDocument):
    """An independent immutable derived view, never a candidate or executor."""


def _document(value):
    return BehaviorReport._verified(value, limit=REPORT_LIMIT)


def _hypothetical(premise):
    if type(premise) is not str or premise not in ('true', 'false', 'unknown'):
        raise PilotError('exact bounded priority premise true/false/unknown required')
    return {'schema_version': policy.HYPOTHETICAL_VERSION, 'prior_priority': premise.upper()}


@dataclass(frozen=True, init=False)
class ManaBehavior:
    """One privately owned admission; all questions reuse these exact bytes."""
    _raw: bytes

    def _material(self):
        return json.loads(self._raw)

    @property
    def subject_ids(self):
        return SUBJECTS

    def _report(self, subjects, hypothetical=None):
        m = self._material()
        facts = {r['rule']['rule_reference']: r for r in m['context']['retained_rules']['rules']}
        records = {r['subject_id']: r for r in m['context']['successor_input']['reassessments']}
        comparisons = []
        for candidate in m['context']['original_comparison']['candidates']:
            sid = candidate['subject']['subject_id']
            if sid not in subjects:
                continue
            record = records.get(sid)
            change = ((record['original_criterion']['criterion_id'], record['proposed_state'])
                      if record else None)
            inputs = _inputs(candidate)
            original = policy.compute(**inputs, rule_facts=facts, hypothetical=hypothetical)
            successor = policy.compute(**_inputs(candidate, change), rule_facts=facts,
                                       hypothetical=hypothetical)
            # These actual results were calculated by PR #218 through its public
            # boundary, not imported assertions. Independently reusing its inputs
            # must reproduce both classifications before behavior is exposed.
            expected = m['classifications'][sid]
            exact(original['classification'], expected['before'])
            exact(successor['classification'], expected['after'])
            comparisons.append({'subject_id': sid,
                'original_candidate_id': candidate['candidate_id'],
                'original_interpretation_id': candidate['candidate_id'],
                'successor_interpretation_id': record['reassessment_id'] if record else candidate['candidate_id'],
                'proposed_kind': inputs['proposed_kind'],
                'interpretation_relationship': ('PENDING_RETAINED_TEXT_SUCCESSOR' if record else 'UNCHANGED_ORIGINAL_PENDING_IDENTITY'),
                'original': original, 'successor': successor})
        return _document(seal(REPORT_VERSION, {'schema_version': REPORT_VERSION,
            'policy': policy.policy_document(), 'context': m['context'],
            'comparisons': comparisons, 'hypothetical': hypothetical,
            'limitations': list(LIMITATIONS), **_authority()}, 'report_id'))

    def comparison(self):
        return self._report(SUBJECTS)

    def subject(self, subject_id):
        self._subject(subject_id)
        return self._report((subject_id,))

    def _subject(self, subject_id):
        if type(subject_id) is not str or subject_id not in SUBJECTS:
            raise PilotError('exact seven-subject identity required')

    def priority(self, subject_id, premise):
        self._subject(subject_id)
        return self._report((subject_id,), _hypothetical(premise))

    def check(self):
        m = self._material()
        return _document(seal(CHECK_VERSION, {'schema_version': CHECK_VERSION,
            'policy_id': policy.POLICY_ID,
            'context_id': m['context']['retained_rules']['context_id'],
            'subject_count': 7, 'behavior_context_units': 24,
            'global_source_units': 104, 'global_projections': 16,
            'new_source_units': 0, 'new_projections': 0,
            'fresh_source_inspection': False,
            'admission': 'FRESH_RETAINED_EVIDENCE_ADMISSION_NOT_FRESH_SOURCE_VERIFICATION',
            'successor_comparison_id': m['context']['successor_comparison_id'],
            **_authority()}, 'report_id'))

    def validate_report(self, value):
        value = json.loads(owned(value, limit=REPORT_LIMIT))
        try:
            if value['schema_version'] == CHECK_VERSION:
                expected = self.check()
            else:
                rows, hypothetical = value['comparisons'], value['hypothetical']
                if type(rows) is not list or len(rows) not in (1, 7):
                    raise PilotError('individual or complete comparison required')
                subjects = tuple(r['subject_id'] for r in rows)
                for sid in subjects:
                    self._subject(sid)
                if len(rows) == 7 and subjects != SUBJECTS:
                    raise PilotError('exact ordered seven subjects required')
                if hypothetical is None:
                    expected = self._report(subjects)
                else:
                    if len(rows) != 1 or type(hypothetical) is not dict:
                        raise PilotError('one bounded hypothetical subject required')
                    premise = hypothetical['prior_priority']
                    if type(premise) is not str:
                        raise PilotError('exact hypothetical premise required')
                    expected = self.priority(subjects[0], premise.lower())
        except (KeyError, TypeError, IndexError):
            raise PilotError('closed behavior report required') from None
        exact(value, expected.to_dict(), limit=REPORT_LIMIT)
        return expected


def load_behavior(*, catalog_root, mechanical_root, review_root, plan_path,
                  expected_profile_id, expected_query_snapshot_id, expected_plan_id,
                  successor_root=None):
    """Fresh public successor admission plus one bounded retained-context admission."""
    successor = load_reassessment(catalog_root=catalog_root, mechanical_root=mechanical_root,
        review_root=review_root, plan_path=plan_path, expected_profile_id=expected_profile_id,
        expected_query_snapshot_id=expected_query_snapshot_id, expected_plan_id=expected_plan_id,
        successor_root=successor_root)
    retained = admit_context(review_root=review_root, successor=successor).to_dict()
    actual = successor.comparison().to_dict()
    original = actual['context']['original_comparison']
    if tuple(c['subject']['subject_id'] for c in original['candidates']) != SUBJECTS:
        raise PilotError('exact original seven-subject cohort required')
    shared = original['candidates'][0]['rules_evidence']
    for candidate in original['candidates']:
        exact(candidate['rules_evidence'], shared)
        del candidate['rules_evidence']
    context = {'retained_rules': retained, 'original_comparison': original,
        'shared_original_rules_evidence': shared,
        'candidate_reconstruction': 'Insert shared_original_rules_evidence as rules_evidence into each compact candidate; all other fields are unchanged. Reinsert those candidates into original_comparison to reproduce its exact historical report.',
        'successor_input': successor.input_document().to_dict(),
        'successor_manifest_id': successor.check().to_dict()['manifest_id'],
        'successor_comparison_id': actual['report_id'],
        'classification_policy_id': actual['policy_id']}
    instance = object.__new__(ManaBehavior)
    object.__setattr__(instance, '_raw', owned({'context': context,
        'classifications': {r['subject_id']: {'before': r['before'], 'after': r['after']}
                            for r in actual['comparisons']}}, limit=REPORT_LIMIT))
    instance.comparison()  # Validate the entire cumulative output before exposure.
    for premise in ('true', 'false', 'unknown'):
        instance.priority(SUBJECTS[0], premise)
    return instance


def render_behavior(document):
    """Readable complete provenance, antecedents and authority, without bare enums."""
    value = document.to_dict()
    if 'comparisons' not in value:
        return document.to_json()
    lines = ['Bounded conditional mana behavior from pending retained-text readings.',
        'semantic_review_status=PENDING_NOT_ESTABLISHED; review.status=requires_review',
        'human_attestation=null; canonical_admission=false; execution_authority=BLOCKED',
        'Report: ' + value['report_id'], 'Policy: ' + value['policy']['policy_id'],
        'Context: ' + value['context']['retained_rules']['context_id'],
        'Hypothetical: ' + json.dumps(value['hypothetical'], sort_keys=True)]
    context = value['context']
    candidates = {c['subject']['subject_id']: c for c in context['original_comparison']['candidates']}
    records = {r['subject_id']: r for r in context['successor_input']['reassessments']}
    for row in value['comparisons']:
        candidate = candidates[row['subject_id']]
        lines += ['', row['subject_id'], 'Original candidate: ' + row['original_candidate_id'],
            'Complete selected passage: ' + candidate['subject']['selected_passage'],
            'Ownership/context: ' + candidate['subject']['ownership_and_context_limitations']]
        record = records.get(row['subject_id'])
        if record:
            lines += ['Pending successor: ' + record['reassessment_id'], record['scope_explanation'],
                      record['candidate_specific_rationale']]
        for reading in ('original', 'successor'):
            result = row[reading]
            classified = result['classification']
            lines += [reading.upper() + ' interpretation: ' + row[reading + '_interpretation_id'],
                'Computed classification: ' + classified['overall_assessment'],
                'Assessment method: ' + classified['method_status'],
                'Substantive negatives: ' + ', '.join(classified['negative_witnesses']),
                'Behavior branch: ' + result['branch']]
            for consequence in result['consequences']:
                lines += ['  ' + consequence['consequence_id'],
                    *['    Antecedent: ' + item for item in consequence['antecedents']],
                    '    Conditional consequence: ' + consequence['conditional_consequence']['explanation']]
                lines += ['    ' + key + ': ' + json.dumps(item, ensure_ascii=False, sort_keys=True)
                    for key, item in consequence['conditional_consequence'].items() if key != 'explanation']
                for binding in consequence['rule_bindings']:
                    lines += ['    Evidence: ' + binding['rule_reference'] + ' / ' + binding['rule_id'],
                        '      Package: ' + binding['package_id'] + '; projection: ' + binding['projection_id'],
                        '      Retained anchor: ' + json.dumps(binding['source_anchor'], sort_keys=True)]
                lines += ['    Unknown/unsupported: ' + item for item in consequence['remaining_unknowns']]
            lines += ['  Unresolved: ' + item for item in result['remaining_unresolved']]
    lines += ['', 'Retained source context: 24 distinct units; global coverage 104/16; no new source or projection.']
    for binding in context['retained_rules']['rules']:
        rule = binding['rule']
        lines += ['  ' + rule['rule_reference'] + ': ' + rule['rule_id'] +
                  '; retained anchor ' + json.dumps(rule['source_anchor'], sort_keys=True)]
    lines += ['Unresolved procedure frontiers: ' + json.dumps(
        context['retained_rules']['unresolved_frontiers'], sort_keys=True), *LIMITATIONS]
    return '\n'.join(lines) + '\n'
