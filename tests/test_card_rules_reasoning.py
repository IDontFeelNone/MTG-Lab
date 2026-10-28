"""Conditional reasoning regressions; no assertion approves real Card semantics.

Synthetic policy fixtures carry no real provenance. Real public-boundary tests
use only the current attachment-backed pilot; the real expanded writer catalog
must reject instead of being replaced with a historical positive fixture.
"""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import contract as c, pilot as p, cards
from card_rules_pilot import reasoning as r, reasoning_policy as policy
from test_card_rules_pilot_cards import current_catalog_intact, evidence_copy

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'data/review/card-rules-mana-pilot/plan.json'
SUBJECTS = tuple(row[0] for row in cards.SUBJECTS)
SAT = 'SATISFIED_UNDER_AUTHORED_READINGS'
NEG = 'NOT_SATISFIED_UNDER_AUTHORED_READINGS'
IND = 'INDETERMINATE_UNDER_AUTHORED_READINGS'
POSITIVE = 'CONDITIONALLY_ELIGIBLE_UNDER_AUTHORED_READINGS'
EXCLUDED = 'CONDITIONALLY_EXCLUDED_UNDER_AUTHORED_READINGS'
INCOMPLETE = 'INCOMPLETE_ASSESSMENT_UNDER_AUTHORED_READINGS'
S = 'proposed_satisfied'
N = 'proposed_not_satisfied'


def arguments(**changes):
    value = dict(catalog_root=ROOT, mechanical_root=ROOT,
        review_root=ROOT / 'reference-reviews', plan_path=PLAN,
        expected_profile_id=cards.PROFILE_ID, expected_query_snapshot_id=cards.QUERY_ID,
        expected_plan_id=p.PLAN_ID)
    value.update(changes)
    return value


def synthetic(kind='proposed_activated_ability', **states):
    # Explicitly synthetic criterion states with policy-required rule labels;
    # no Card IDs, passage bytes, anchors, packages or evidence identity claims.
    refs = [
        ('activated_kind', ['605.1a']), ('no_target', ['605.1a', '115.6']),
        ('potential_mana', ['605.1a', '605.2']), ('not_loyalty', ['605.1a', '606.1', '606.2']),
        ('no_library_cost_movement', ['605.1a']), ('no_library_effect_movement', ['605.1a']),
        ('self_replacement_considered', ['605.1a']), ('other_replacements_disregarded', ['605.1a']),
        ('triggered_kind', ['605.1b']), ('trigger_no_target', ['605.1b', '115.6']),
        ('trigger_potential_mana', ['605.1b', '605.2']),
        ('qualifying_trigger_relationship', ['605.1b', '605.1a'])]
    active = range(8) if kind == 'proposed_activated_ability' else range(8, 12) if kind == 'proposed_triggered_ability' else ()
    return dict(proposed_kind=kind, criteria=[dict(criterion_id=name,
        state=states.get(name, S if i in active else 'inapplicable'), rule_refs=rules)
        for i, (name, rules) in enumerate(refs)],
        kind_evidence_refs=['type_line', 'rule:605.5b'] if kind == 'proposed_spell_instruction' else ['selected_passage', 'rule:605.1a' if kind == 'proposed_activated_ability' else 'rule:605.1b'])


class SyntheticReasoningPolicyTests(unittest.TestCase):
    def test_separate_substantive_and_method_dimensions(self):
        value = policy.compute(**synthetic(self_replacement_considered='unknown'))
        self.assertEqual(value['substantive_result'], SAT)
        self.assertEqual(value['method_status'], 'INCOMPLETE')
        self.assertEqual(value['overall_assessment'], INCOMPLETE)
        self.assertEqual(value['negative_witnesses'], [])
        self.assertEqual(value['unresolved_requirements'], [])
        for row in ('self_replacement_considered', 'other_replacements_disregarded'):
            with self.subTest(method=row):
                value = policy.compute(**synthetic(**{row: N}))
                self.assertEqual(value['substantive_result'], SAT)
                self.assertEqual(value['method_status'], 'UNMET')
                self.assertEqual(value['overall_assessment'], INCOMPLETE)
                self.assertEqual(value['negative_witnesses'], [])

    def test_decisive_negative_preserves_unresolved_requirement_and_method_gap(self):
        value = policy.compute(**synthetic(potential_mana=N, no_target='unknown', self_replacement_considered='unknown'))
        self.assertEqual(value['substantive_result'], NEG)
        self.assertIn('potential_mana', value['negative_witnesses'])
        self.assertIn({'criterion_id': 'no_target', 'state': 'unknown'}, value['unresolved_requirements'])
        self.assertEqual(value['method_status'], 'INCOMPLETE')
        self.assertEqual(value['overall_assessment'], INCOMPLETE)

    def test_unknown_unsupported_conflicting_and_required_inapplicable_remain_distinct(self):
        for state in ('unknown', 'unsupported', 'conflicting', 'inapplicable'):
            with self.subTest(state=state):
                value = policy.compute(**synthetic(no_target=state))
                self.assertEqual(value['substantive_result'], IND)
                self.assertIn({'criterion_id': 'no_target', 'state': state}, value['unresolved_requirements'])
        value = policy.compute(**synthetic(self_replacement_considered='conflicting'))
        self.assertEqual(value['method_status'], 'CONFLICTING')
        self.assertEqual(value['overall_assessment'], INCOMPLETE)

    def test_trigger_branch_has_no_activated_method_obligations(self):
        value = policy.compute(**synthetic('proposed_triggered_ability', qualifying_trigger_relationship='unknown'))
        self.assertEqual(value['substantive_result'], IND)
        self.assertEqual(value['method_status'], 'NOT_APPLICABLE')
        self.assertEqual(value['method_findings'], [])
        for state, outcome in ((S, POSITIVE), (N, EXCLUDED)):
            value = policy.compute(**synthetic('proposed_triggered_ability', qualifying_trigger_relationship=state))
            self.assertEqual(value['overall_assessment'], outcome)

    def test_spell_requires_explicit_kind_and_exclusion_binding_without_vacuity(self):
        fixture = synthetic('proposed_spell_instruction')
        value = policy.compute(**fixture)
        self.assertEqual(value['substantive_result'], NEG)
        self.assertEqual(value['overall_assessment'], EXCLUDED)
        self.assertEqual(value['method_status'], 'NOT_APPLICABLE')
        for invalid in ('missing-type', 'missing-rule', 'empty-criteria', 'activated-kind'):
            row = deepcopy(fixture)
            if invalid == 'missing-type':
                row['kind_evidence_refs'].remove('type_line')
            elif invalid == 'missing-rule':
                row['kind_evidence_refs'].remove('rule:605.5b')
            elif invalid == 'empty-criteria':
                row['criteria'] = []
            else:
                row['proposed_kind'] = 'proposed_activated_ability'
            with self.subTest(invalid=invalid), self.assertRaises(c.PilotError):
                policy.compute(**row)

    def test_complete_validation_does_not_stop_at_negative(self):
        for mutation in ('missing', 'duplicate', 'foreign-id', 'foreign-state', 'wrong-rules', 'boolean-state', 'inactive-row'):
            row = synthetic(potential_mana=N)
            if mutation == 'missing':
                row['criteria'].pop()
            elif mutation == 'duplicate':
                row['criteria'][-1] = deepcopy(row['criteria'][0])
            elif mutation == 'foreign-id':
                row['criteria'][-1]['criterion_id'] = 'synthetic_unknown_criterion'
            elif mutation == 'foreign-state':
                row['criteria'][-1]['state'] = 'accepted'
            elif mutation == 'wrong-rules':
                row['criteria'][-1]['rule_refs'] = ['602.2']
            elif mutation == 'boolean-state':
                row['criteria'][-1]['state'] = True
            else:
                row['criteria'][-1]['state'] = S
            with self.subTest(mutation=mutation), self.assertRaises(c.PilotError):
                policy.compute(**row)

    def test_synthetic_display_names_and_proposal_labels_cannot_drive_calculation(self):
        first = dict(display_name='Synthetic fixture Alpha', proposed_classification='proposed_exclusion', **synthetic())
        second = deepcopy(first)
        second.update(display_name='Synthetic fixture Beta', proposed_classification='interpretation_unresolved')
        def project(row):
            return {key: row[key] for key in ('proposed_kind', 'criteria', 'kind_evidence_refs')}
        self.assertEqual(policy.compute(**project(first)), policy.compute(**project(second)))
        self.assertEqual(policy.compute(**project(second))['overall_assessment'], POSITIVE)


class ActualReasoningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact = current_catalog_intact(unittest.TestCase())
        cls.reasoning = r.load_reasoning(**arguments()) if cls.intact else None

    def current(self):
        if not self.intact:
            self.assertFalse(current_catalog_intact(self))
            # This assertion exercises the actual reasoning boundary against the
            # real 654-Card writer expansion, without a replacement catalog.
            with self.assertRaises(ValueError):
                r.load_reasoning(**arguments())
            return False
        return True

    def analysis(self, subject):
        return self.reasoning.subject(subject).to_dict()['analyses'][0]

    def test_all_seven_actual_baseline_results(self):
        if not self.current():
            return
        expected = {
            'sol-ring-tap': (SAT, 'INCOMPLETE', INCOMPLETE, []),
            'basalt-monolith-tap': (SAT, 'INCOMPLETE', INCOMPLETE, []),
            'basalt-monolith-untap': (NEG, 'INCOMPLETE', INCOMPLETE, ['potential_mana']),
            'deathrite-shaman-first': (NEG, 'INCOMPLETE', INCOMPLETE, ['no_target']),
            'dark-ritual-spell': (NEG, 'NOT_APPLICABLE', EXCLUDED, []),
            'mana-flare-trigger': (IND, 'NOT_APPLICABLE', IND, []),
            'pitiless-plunderer-host-trigger': (NEG, 'NOT_APPLICABLE', EXCLUDED,
                ['trigger_potential_mana', 'qualifying_trigger_relationship'])}
        for subject, (substantive, method, overall, negative) in expected.items():
            with self.subTest(subject=subject):
                result = self.analysis(subject)['result']
                self.assertEqual(result['substantive_result'], substantive)
                self.assertEqual(result['method_status'], method)
                self.assertEqual(result['overall_assessment'], overall)
                if subject != 'dark-ritual-spell':
                    self.assertEqual(result['negative_witnesses'], negative)
        comparison = self.reasoning.comparison().to_dict()
        self.assertEqual([row['subject_id'] for row in comparison['analyses']], list(SUBJECTS))

    def test_exact_ten_bounded_hypotheticals_hold_other_readings_unchanged(self):
        if not self.current():
            return
        cases = self.reasoning.review_impact().to_dict()['cases']
        self.assertEqual(len(cases), 10)
        self.assertEqual(len({row['case_id'] for row in cases}), 10)
        expected_subjects = set(SUBJECTS[:4]) | {'mana-flare-trigger'}
        self.assertEqual({row['subject_id'] for row in cases}, expected_subjects)
        for case in cases:
            with self.subTest(case=case['case_id']):
                subject = case['subject_id']
                original = self.analysis(subject)
                self.assertEqual(case['candidate_id'], original['candidate_id'])
                self.assertEqual(case['plan_id'], p.PLAN_ID)
                self.assertEqual(case['original_state'], 'unknown')
                self.assertIn(case['hypothetical_state'], (S, N))
                self.assertTrue(case['unchanged_input_assumption'])
                self.assertEqual(case['analysis']['candidate_id'], original['candidate_id'])
                before = {row['criterion_id']: row['state'] for row in original['premises']}
                after = {row['criterion_id']: row['state'] for row in case['analysis']['premises']}
                self.assertEqual([name for name in before if before[name] != after[name]], [case['criterion_id']])
                self.assertEqual(after[case['criterion_id']], case['hypothetical_state'])
                result = case['analysis']['result']
                if subject == 'mana-flare-trigger':
                    self.assertEqual(case['criterion_id'], 'qualifying_trigger_relationship')
                    self.assertEqual(result['overall_assessment'], POSITIVE if case['hypothetical_state'] == S else EXCLUDED)
                else:
                    self.assertEqual(case['criterion_id'], 'self_replacement_considered')
                    self.assertIn('Completing this assessment may require revising other criterion readings. This hypothetical holds those readings unchanged.', case['assessment_caveat'])
                    self.assertEqual(result['substantive_result'], original['result']['substantive_result'])
                    self.assertEqual(result['method_status'], 'PROPOSED_SATISFIED' if case['hypothetical_state'] == S else 'UNMET')
                    complete = POSITIVE if subject in SUBJECTS[:2] else EXCLUDED
                    self.assertEqual(result['overall_assessment'], complete if case['hypothetical_state'] == S else INCOMPLETE)
        for subject in expected_subjects:
            self.assertEqual({row['hypothetical_state'] for row in cases if row['subject_id'] == subject}, {S, N})

    def test_original_candidate_comparison_plan_and_manifest_identities_preserved(self):
        if not self.current():
            return
        old = p.load_pilot(**arguments())
        self.assertEqual(old.plan_id, 'sha256:acdfc01e0645dc788a5c04824cb40948377699fe9f047441500980578fb9aa83')
        original = old.comparison()
        self.assertEqual(original.to_dict()['report_id'], 'sha256:a2b0dedc3ef68b779b5b3a36ec20f97afc348b1ce52ad79c9e4a3cd2a281da0c')
        self.assertEqual(old.reproduction_manifest()['manifest_id'], 'sha256:7243ed93272b488b3dd50eb6ea712ca0dda4d6ea2fec6567259455f61b5d8762')
        self.assertEqual(old.reproduction_manifest(), c.read_json(PLAN.parent / 'manifest.json'))
        for document in (self.reasoning.comparison(), self.reasoning.review_impact()):
            self.assertEqual(c.canonical(document.to_dict()['context']['original_comparison']), original.to_json().encode())
        for subject in SUBJECTS:
            candidate = self.reasoning.subject(subject).to_dict()['context']['candidate']
            self.assertEqual(c.canonical(candidate), old.subject(subject).to_json().encode())

    def test_full_provenance_for_every_premise_question_and_case(self):
        if not self.current():
            return
        old = p.load_pilot(**arguments())
        for subject in SUBJECTS:
            analysis = self.analysis(subject)
            candidate = old.subject(subject).to_dict()
            rows = candidate['authored_interpretation']['criteria']
            self.assertEqual(len(analysis['premises']), 13 if subject == 'dark-ritual-spell' else 12)
            for premise, original in zip(analysis['premises'], rows):
                self.assertEqual(premise['criterion_id'], original['criterion_id'])
                self.assertEqual(premise['original_state'], original['state'])
                self.assertEqual(premise['state'], original['state'])
                self.assertEqual(premise['evidence_refs'], original['evidence_refs'])
                self.assertTrue(premise['rule_refs'])
                self.assertIn(premise['role'], ('substantive', 'method', 'inapplicable'))
            for question in analysis['review_questions']:
                self.assertEqual(question['candidate_id'], candidate['candidate_id'])
                self.assertEqual(question['subject_id'], subject)
                self.assertEqual(question['plan_id'], p.PLAN_ID)
                self.assertTrue(question['evidence_refs'])
                self.assertIn(question['category'], ('substantive', 'method'))
            self.assertTrue(analysis['result']['trace'])
            self.assertTrue(analysis['proposal_relationship'])

    def test_pending_authority_immutable_views_and_rehashed_claims_reject(self):
        if not self.current():
            return
        authority_view = r._authority()
        authority_view['review']['canonical_admission'] = True
        descriptor = policy.policy_document()
        descriptor['review']['canonical_admission'] = True
        self.assertFalse(r._authority()['review']['canonical_admission'])
        self.assertFalse(policy.policy_document()['review']['canonical_admission'])
        for document in (self.reasoning.subject(SUBJECTS[0]), self.reasoning.comparison(), self.reasoning.review_impact()):
            original = document.to_json()
            value = document.to_dict()
            self.assertEqual(value['review'], {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False})
            self.assertEqual(value['semantic_review_status'], 'PENDING_NOT_ESTABLISHED')
            self.assertEqual(value['execution_authority'], 'BLOCKED')
            self.assertEqual(value['report_id'], c.identity(value['schema_version'], value, 'report_id'))
            self.assertLessEqual(len(original.encode()), r.REASONING_LIMIT)
            for case in value.get('cases', []):
                self.assertEqual(case['case_id'], c.identity(case['schema_version'], case, 'case_id'))
                self.assertEqual(case['review'], value['review'])
                self.assertEqual(case['analysis']['review'], value['review'])
                self.assertEqual(case['semantic_review_status'], 'PENDING_NOT_ESTABLISHED')
                self.assertEqual(case['execution_authority'], 'BLOCKED')
            transforms = ('review', 'authority', 'type', 'extra', 'result', 'source')
            if 'cases' in value:
                transforms += ('case-authority-rehashed',)
            for transform in transforms:
                changed = deepcopy(value)
                if transform == 'review':
                    changed['review']['canonical_admission'] = True
                elif transform == 'authority':
                    changed['execution_authority'] = 'READY'
                elif transform == 'type':
                    changed['review']['canonical_admission'] = 0
                elif transform == 'extra':
                    changed['official_ruling'] = True
                elif transform == 'case-authority-rehashed':
                    case = changed['cases'][0]
                    case['review']['canonical_admission'] = True
                    changed['cases'][0] = c.seal(case['schema_version'], case, 'case_id')
                elif transform == 'source':
                    context = changed['context']
                    candidate = context['candidate'] if 'candidate' in context else context['original_comparison']['candidates'][0]
                    candidate['rules_evidence']['rules'][0]['rule']['source_anchor']['effective_date'] = '2099-01-01'
                else:
                    analysis = changed.get('analyses', [changed.get('cases', [{}])[0].get('analysis')])[0]
                    analysis['result']['overall_assessment'] = 'UNAUTHORIZED_RESULT'
                changed = c.seal(value['schema_version'], changed, 'report_id')
                with self.subTest(version=value['schema_version'], transform=transform), self.assertRaises(c.PilotError):
                    self.reasoning.validate_report(changed)
            self.assertEqual(self.reasoning.validate_report(value).to_json(), original)
            value.clear()
            self.assertEqual(document.to_json(), original)
            with self.assertRaises((FrozenInstanceError, AttributeError)):
                document._raw = b'{}\n'

    def test_one_admitted_snapshot_for_all_reports_and_no_success_cache(self):
        if not self.current():
            return
        with patch.object(p, 'read_cards', wraps=p.read_cards) as card_reader, patch.object(p, 'read_rules', wraps=p.read_rules) as rule_reader:
            first = r.load_reasoning(**arguments())
            first.comparison()
            first.review_impact()
            for subject in SUBJECTS:
                first.subject(subject)
            self.assertEqual(card_reader.call_count, 1)
            self.assertEqual(rule_reader.call_count, 1)
            r.load_reasoning(**arguments())
            self.assertEqual(card_reader.call_count, 2)
            self.assertEqual(rule_reader.call_count, 2)

    def test_loaded_snapshot_survives_filesystem_drift_new_invocation_rejects(self):
        if not self.current():
            return
        with tempfile.TemporaryDirectory(prefix='mtglab-reasoning-drift-') as temp:
            mechanical = evidence_copy(Path(temp))
            initial = r.load_reasoning(**arguments(mechanical_root=mechanical))
            before = initial.comparison().to_json()
            path = mechanical / cards.DOSSIER_REFERENCE
            path.write_bytes(path.read_bytes() + b' ')
            self.assertEqual(initial.comparison().to_json(), before)
            with self.assertRaises(ValueError):
                r.load_reasoning(**arguments(mechanical_root=mechanical))

    def test_actual_cli_api_canonical_readable_parity_and_read_only(self):
        if not self.current():
            return
        command = [sys.executable, '-m', 'card_rules_pilot', '--catalog-root', str(ROOT),
            '--mechanical-root', str(ROOT), '--review-root', str(ROOT / 'reference-reviews'),
            '--plan', str(PLAN), '--expected-profile-id', cards.PROFILE_ID,
            '--expected-query-snapshot-id', cards.QUERY_ID, '--expected-plan-id', p.PLAN_ID]
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')
        before = {path.name: path.read_bytes() for path in PLAN.parent.iterdir() if path.is_file()}
        pairs = [(['analyze', subject], self.reasoning.subject(subject)) for subject in SUBJECTS]
        pairs += [(['analyze-all'], self.reasoning.comparison()), (['review-impact'], self.reasoning.review_impact())]
        for suffix, document in pairs:
            for json_output in (True, False):
                result = subprocess.run(command + suffix + (['--json'] if json_output else []),
                    cwd=ROOT, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, document.to_json() if json_output else r.render_reasoning(document))
        self.assertEqual(before, {path.name: path.read_bytes() for path in PLAN.parent.iterdir() if path.is_file()})


if __name__ == '__main__':
    unittest.main()
