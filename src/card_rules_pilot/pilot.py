"""Read-only reproduction of seven engineer-authored pending interpretations."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .authored import PLAN_BODY, CRITERIA
from .cards import read_cards, SUBJECTS
from .rules import read_rules
from .contract import (PLAN_VERSION, CANDIDATE_VERSION, REPORT_VERSION,
    PLAN_LIMIT, CANDIDATE_LIMIT, REPORT_LIMIT, PilotError, InterpretationCandidate,
    ReviewReport, canonical, owned, seal, exact, read_json)

STATES = ('proposed_satisfied', 'proposed_not_satisfied', 'unknown',
          'unsupported', 'inapplicable', 'conflicting')
CLASSIFICATIONS = ('proposed_activated_mana_ability', 'proposed_triggered_mana_ability',
                   'proposed_exclusion', 'interpretation_unresolved')
REVIEW = {'status': 'requires_review', 'human_attestation': None,
          'canonical_admission': False}
LIMITATIONS = (
    'Source correspondence and integrity do not approve authored subject interpretation or rules classification.',
    'Historical Card observation is not current Oracle verification or a current official ruling.',
    'No classification establishes current activation eligibility, actual mana output, legality or execution.',
    'Unknown external state, applicable effects and replacement semantics remain unknown.',
    'No real Card candidate may enter fictional packets, v1/v2 evaluators or executable CardGameplaySemantics.',
    'Any displayed 605.3b activated no-stack or 405.6c immediate-resolution context is conditional on later acceptance of the pending classification. The 405.6c conditional prior-priority context is limited to activated mana abilities. Triggered 605.4a is separate; it does not directly cite 405.6c or inherit activated priority return. No live response window is established.',
)
CORRECTION = 'APPEND_ONLY_SEPARATELY_AUTHORIZED_PLAN_VERSION_PRESERVING_PRIOR_BYTES'
_PLAN_BYTES = owned(seal(PLAN_VERSION, {**PLAN_BODY,
    'criterion_definitions': CRITERIA, 'criterion_states': list(STATES),
    'classification_vocabulary': list(CLASSIFICATIONS), 'review': REVIEW,
    'execution_authority': 'BLOCKED', 'supersedes_plan_ids': [],
    'correction_boundary': CORRECTION}, 'plan_id'), limit=PLAN_LIMIT)
PLAN_ID = json.loads(_PLAN_BYTES)['plan_id']


def fixed_plan():
    """Independent view of the fixed authored input, never a semantic approval."""
    return json.loads(_PLAN_BYTES)


def _validate_plan(plan):
    exact(plan, fixed_plan(), limit=PLAN_LIMIT)
    subjects = {row['subject_id']: row for row in plan['subjects']}
    if len(subjects) != 7 or set(subjects) != {row[0] for row in SUBJECTS}:
        raise PilotError('exact seven subjects required')
    criterion_ids = [row['criterion_id'] for row in plan['criterion_definitions']]
    for subject in subjects.values():
        if [row['criterion_id'] for row in subject['criteria']] != criterion_ids:
            raise PilotError('complete ordered criterion matrix required')
        for row in subject['criteria']:
            if row['state'] not in STATES or not row['rationale'] or not row['limitations']:
                raise PilotError('explicit criterion reading and limitations required')
    return subjects


@dataclass(frozen=True, init=False)
class InterpretationReviewPilot:
    """One verified request snapshot. No mutable reader or ambient root is retained."""
    _raw: bytes

    def _material(self):
        return json.loads(self._raw)

    @property
    def plan_id(self):
        return self._material()['plan']['plan_id']

    @property
    def subject_ids(self):
        return tuple(row['subject_id'] for row in self._material()['plan']['subjects'])

    def _candidate(self, subject_id):
        material = self._material()
        selected = [row for row in material['plan']['subjects'] if row['subject_id'] == subject_id]
        if len(selected) != 1:
            raise PilotError('subject outside fixed seven-subject pilot')
        authored = selected[0]
        cards = material['cards']
        matrix = authored['criteria']
        unresolved = [row['criterion_id'] for row in matrix
                      if row['state'] in ('unknown', 'unsupported', 'conflicting')]
        value = {
            'schema_version': CANDIDATE_VERSION,
            'authority': 'ENGINEER_AUTHORED_PENDING_INTERPRETATION_ONLY',
            'plan_id': self.plan_id, 'prepared_at': material['plan']['prepared_at'],
            'subject': cards['subjects'][subject_id],
            'card_evidence': cards['cards'][authored['card_id']],
            'catalog_binding': cards['catalog_binding'],
            'acquisition_binding': cards['acquisition'],
            'rules_evidence': material['rules'],
            'authored_interpretation': authored,
            'criterion_definitions': material['plan']['criterion_definitions'],
            'material_unresolved_criteria': unresolved,
            'source_correspondence': 'EXACT_RETAINED_BINDINGS_VALIDATED',
            'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
            'review': material['plan']['review'], 'execution_authority': 'BLOCKED',
            'limitations': material['limitations'],
            'supersedes_candidate_ids': [], 'correction_boundary': material['plan']['correction_boundary'],
        }
        return seal(CANDIDATE_VERSION, value, 'candidate_id')

    def subject(self, subject_id):
        if type(subject_id) is not str:
            raise PilotError('exact local subject string required')
        return InterpretationCandidate._verified(self._candidate(subject_id), limit=CANDIDATE_LIMIT)

    def validate_candidate(self, value):
        """Validate the exact authored proposal and its evidence, without entailment."""
        value = json.loads(owned(value, limit=CANDIDATE_LIMIT))
        try:
            expected = self._candidate(value['subject']['subject_id'])
        except (KeyError, TypeError):
            raise PilotError('exact candidate subject binding required') from None
        exact(value, expected, limit=CANDIDATE_LIMIT)
        return InterpretationCandidate._verified(value, limit=CANDIDATE_LIMIT)

    def comparison(self):
        value = {'schema_version': REPORT_VERSION, 'plan_id': self.plan_id,
            'authority': 'PENDING_INTERPRETATION_COMPARISON_ONLY',
            'candidates': [self._candidate(identifier) for identifier in self.subject_ids],
            'review': self._material()['plan']['review'], 'execution_authority': 'BLOCKED',
            'limitations': self._material()['limitations'],
            'comparison_dimensions': [
                'A strategic mana-related role is separate from the rules category mana ability.',
                'Paying mana is separate from potentially producing mana: compare the two Basalt subjects.',
                'A target requirement is separate from chosen-target count: Deathrite retains its complete targeted first ability.',
                'Mana production by a spell does not make that instruction an activated or triggered ability: Dark Ritual binds its type line.',
                'The Treasure activation belongs to the created object, separate from the Plunderer host trigger.',
                'Mana Flare trigger relationship is separately authored and unresolved; no causality or event detection runs.',
                'Classification is separate from current eligibility and actual mana output; unknown criteria stay visible.',
            ]}
        return ReviewReport._verified(seal(REPORT_VERSION, value, 'report_id'), limit=REPORT_LIMIT)

    def reproduction_manifest(self):
        """Small retained proof of exact output reproduction, not stored authority."""
        candidates = [self.subject(s).to_dict() for s in self.subject_ids]
        report = self.comparison()
        outputs = {
            'candidates.jsonl': b''.join(canonical(c) for c in candidates),
            'comparison.json': report.to_json().encode(),
        }
        return seal('card-rules-mana-pilot-manifest-v1', {
            'schema_version': 'card-rules-mana-pilot-manifest-v1', 'plan_id': self.plan_id,
            'artifacts': {name: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
                          for name, raw in outputs.items()},
            'candidates': [{'subject_id': c['subject']['subject_id'],
                'card_id': c['subject']['card_id'], 'candidate_id': c['candidate_id']} for c in candidates],
            'report_id': report.to_dict()['report_id'],
            'review': self._material()['plan']['review'], 'execution_authority': 'BLOCKED',
        }, 'manifest_id')


def load_pilot(*, catalog_root, mechanical_root, review_root, plan_path,
               expected_profile_id, expected_query_snapshot_id, expected_plan_id):
    """Fresh request checks; the three evidence/plan trust domains stay separate.

    Both Card roots are repository roots; mechanical data is their data child.
    No fallback, historical catalog substitution, network request or write exists.
    """
    if type(expected_plan_id) is not str or expected_plan_id != PLAN_ID:
        raise PilotError('independently selected exact pilot plan identity required')
    plan = read_json(plan_path, limit=PLAN_LIMIT)
    _validate_plan(plan)
    cards = read_cards(catalog_root=catalog_root, mechanical_root=mechanical_root,
        expected_profile_id=expected_profile_id,
        expected_query_snapshot_id=expected_query_snapshot_id)
    rules = read_rules(review_root)
    rule_refs = {row['rule']['rule_reference'] for row in rules['rules']}
    for authored in plan['subjects']:
        if cards['subjects'][authored['subject_id']]['card_id'] != authored['card_id']:
            raise PilotError('foreign authored Card binding')
        for refs in [authored['classification_evidence_refs'],
                     *[row['evidence_refs'] for row in authored['criteria']]]:
            for ref in refs:
                if ref.startswith('rule:'):
                    if ref[5:] not in rule_refs:
                        raise PilotError('unbound authored rule reference')
                elif ref not in ('selected_passage', 'full_oracle_field', 'type_line'):
                    raise PilotError('foreign authored passage reference')
    # Detect changed authored bytes during evidence loading before owning material.
    exact(read_json(plan_path, limit=PLAN_LIMIT), plan, limit=PLAN_LIMIT)
    result = object.__new__(InterpretationReviewPilot)
    object.__setattr__(result, '_raw', owned({'plan': plan, 'cards': cards, 'rules': rules,
                                            'limitations': list(LIMITATIONS)}))
    # Enforce cumulative output budgets before returning any partial result.
    result.comparison()
    return result


def render(document):
    """Readable full-context review, keeping unresolved and contrary readings."""
    value = document.to_dict()
    candidates = value.get('candidates', [value])
    lines = ['Pending Card–rules interpretation review',
             'requires_review; human_attestation=null; canonical_admission=false; execution_authority=BLOCKED',
             'Integrity validates correspondence only; semantic interpretation remains pending.']
    if 'comparison_dimensions' in value:
        lines.extend(value['comparison_dimensions'])
    for candidate in candidates:
        subject = candidate['subject']; authored = candidate['authored_interpretation']
        card = candidate['card_evidence']
        lines += ['', subject['subject_id'] + ' — ' + card['card_identity']['name'],
            'Card: ' + subject['card_id'], 'Candidate: ' + candidate['candidate_id'],
            'Dossier: ' + subject['mechanical_dossier_id'],
            'Proposed kind: ' + authored['proposed_kind'],
            'Proposed classification: ' + authored['proposed_classification'],
            'Owner: ' + subject['owner'], 'Source field: ' + subject['source_record_pointer'],
            'Full retained Oracle field: ' + subject['complete_field_value'],
            'Selected complete passage: ' + subject['selected_passage'],
            'Retained type line: ' + subject['type_line']['value'],
            'Context limit: ' + subject['ownership_and_context_limitations'],
            'Classification rationale: ' + authored['classification_rationale'],
            'Classification evidence: ' + ', '.join(authored['classification_evidence_refs']),
            'Material unresolved criteria: ' + (', '.join(candidate['material_unresolved_criteria']) or 'none authored; semantic review still pending')]
        for row in authored['criteria']:
            lines += ['  ' + row['criterion_id'] + ': ' + row['state'],
                      '    ' + row['rationale'], '    Evidence: ' + ', '.join(row['evidence_refs'])]
            lines.extend('    Limitation: ' + text for text in row['limitations'])
        lines.extend('Counterevidence: ' + text for text in authored['counterevidence'])
        lines.extend('Missing requirement: ' + text for text in authored['missing_requirements'])
        lines += ['Comparison: ' + authored['comparison_note'],
                  'Exact Card/source context: ' + canonical(card).decode().strip()]
    # Shared evidence is identical across candidates. Display it once, complete.
    first = candidates[0]
    lines += ['', 'Complete shared catalog binding (relative retained references):',
        canonical(first['catalog_binding']).decode().strip(),
        'Complete retained CR context, anchors, historical arrays and separately bound later reviews:',
        canonical(first['rules_evidence']).decode().strip(), *first['limitations']]
    return '\n'.join(lines) + '\n'
