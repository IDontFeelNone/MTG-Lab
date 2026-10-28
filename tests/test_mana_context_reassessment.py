"""Source-backed successor boundaries, not assertions of approved Card semantics."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import cards, pilot, reasoning_policy as policy
from card_rules_pilot import reassessment as r, contract as c
from gameplay_rules.projection import mana_context_package as source
from test_card_rules_pilot_cards import current_catalog_intact

ROOT = Path(__file__).resolve().parents[1]
SUCCESSOR = ROOT / 'data/review/mana-context-reassessment'


def arguments(**changes):
    args = dict(catalog_root=ROOT, mechanical_root=ROOT,
        review_root=ROOT / 'reference-reviews',
        plan_path=ROOT / 'data/review/card-rules-mana-pilot/plan.json',
        expected_profile_id=cards.PROFILE_ID, expected_query_snapshot_id=cards.QUERY_ID,
        expected_plan_id=pilot.PLAN_ID)
    args.update(changes)
    return args


class ReassessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Real publication-expanded input must reject, never load an old fixture.
        cls.consumer = r.load_reassessment(**arguments()) if current_catalog_intact(unittest.TestCase()) else None

    def current(self):
        if self.consumer is None:
            self.assertFalse(current_catalog_intact(self))
            with self.assertRaises(ValueError):
                r.load_reassessment(**arguments())
            return False
        return True

    def records(self):
        return self.consumer.input_document().to_dict()['reassessments']

    def test_exact_five_new_records_and_seven_original_subjects(self):
        if not self.current():
            return
        records = self.records()
        self.assertEqual(tuple(v['subject_id'] for v in records), r.SUBJECTS)
        self.assertEqual(len({v['reassessment_id'] for v in records}), 5)
        comparison = self.consumer.comparison().to_dict()
        originals = comparison['context']['original_comparison']['candidates']
        self.assertEqual(len(originals), 7)
        self.assertEqual({v['subject_id'] for v in comparison['comparisons']}, {v[0] for v in cards.SUBJECTS})
        for record in records:
            candidate = next(v for v in originals if v['subject']['subject_id'] == record['subject_id'])
            self.assertEqual(record['original_candidate_id'], candidate['candidate_id'])
            self.assertNotEqual(record['reassessment_id'], candidate['candidate_id'])
            self.assertEqual(record['original_plan_id'], pilot.PLAN_ID)
            self.assertEqual(record['original_subject'], candidate['subject'])
            self.assertEqual(record['card_evidence_binding'], candidate['card_evidence'])
            self.assertEqual(record['original_criterion']['state'], 'unknown')
            self.assertTrue(record['original_criterion']['rationale'])
            self.assertTrue(record['original_counterevidence'])
            self.assertEqual(record['historical_context_count'], 17)
            self.assertEqual(record['enriched_context_count'], 21)

    def test_scope_narrowing_exposes_original_universal_unknown(self):
        if not self.current():
            return
        for record in self.records():
            self.assertTrue(record['universal_question_remaining_unknown'])
            self.assertEqual(record['proposed_state'], 'proposed_satisfied')
            self.assertTrue(record['counterevidence'])
            self.assertFalse(record['hypothetical_cases_used_as_evidence'])
            if record['subject_id'] != 'mana-flare-trigger':
                self.assertEqual(record['scope_change'], 'NARROWED_TO_COMPLETE_RETAINED_CARD_TEXT')
                self.assertIn('does not resolve the original universal question', record['scope_explanation'])
            else:
                self.assertEqual(record['scope_change'], 'CLARIFIED_RETAINED_TRIGGER_WORDING_RELATIONSHIP_ONLY')
        readable = r.render_reassessment(self.consumer.comparison())
        self.assertIn('original universal questions remain UNKNOWN', readable)
        self.assertIn('not verbatim CR content or an official Card ruling', readable)

    def test_basalt_context_is_accounted_for_without_borrowing_mana(self):
        if not self.current():
            return
        records = {v['subject_id']: v for v in self.records()}
        tap = records['basalt-monolith-tap']; untap = records['basalt-monolith-untap']
        self.assertEqual(tap['original_subject']['complete_field_value'], untap['original_subject']['complete_field_value'])
        self.assertNotEqual(tap['original_subject']['selected_passage'], untap['original_subject']['selected_passage'])
        for record in (tap, untap):
            self.assertIn('static restriction', record['candidate_specific_rationale'])
            self.assertIn('untap step', record['candidate_specific_rationale'])
            self.assertIn('separate', record['candidate_specific_rationale'])
            self.assertEqual([v['rule_reference'] for v in record['new_source_support']], ['614.15'])
        self.assertIn('paid activation', tap['candidate_specific_rationale'])
        self.assertIn('replacing part or all', untap['candidate_specific_rationale'])
        rows = {v['criterion_id']: v for v in untap['rechecked_criteria']}
        self.assertEqual(rows['potential_mana']['proposed_state'], 'proposed_not_satisfied')
        self.assertIn('borrow', rows['potential_mana']['rationale'])

    def test_deathrite_complete_exile_and_other_abilities_remain_context(self):
        if not self.current():
            return
        record = next(v for v in self.records() if v['subject_id'] == 'deathrite-shaman-first')
        subject = record['original_subject']
        self.assertEqual(subject['selected_passage'], '{T}: Exile target land card from a graveyard. Add one mana of any color.')
        self.assertIn('Each opponent loses 2 life.', subject['complete_field_value'])
        self.assertIn('You gain 2 life.', subject['complete_field_value'])
        self.assertIn('both', record['assessment_question'])
        self.assertIn('without classifying either as a new subject', record['candidate_specific_rationale'])
        rows = {v['criterion_id']: v for v in record['rechecked_criteria']}
        self.assertEqual(rows['no_target']['proposed_state'], 'proposed_not_satisfied')
        self.assertEqual(rows['potential_mana']['proposed_state'], 'proposed_satisfied')
        self.assertIn('graveyard-to-exile', rows['no_library_effect_movement']['rationale'])

    def test_mana_flare_support_is_resolution_not_an_execution_claim(self):
        if not self.current():
            return
        record = self.records()[-1]
        self.assertEqual(record['original_subject']['selected_passage'], 'Whenever a player taps a land for mana, that player adds one mana of any type that land produced.')
        self.assertEqual([v['rule_reference'] for v in record['new_source_support']], ['106.12', '106.12a', '106.12b'])
        argument = record['candidate_specific_rationale']
        self.assertIn('resolution-of-an-activated-mana-ability alternative', argument)
        self.assertIn('not a literal citation', argument)
        self.assertIn('106.12b instead concerns replacement effects', record['counterevidence'])
        self.assertIn('not a trigger for every activation', record['counterevidence'])
        inactive = [v for v in record['rechecked_criteria'] if v['original_state'] == 'inapplicable']
        self.assertEqual(len(inactive), 8)
        self.assertTrue(all('inapplicable' in v['rationale'] for v in inactive))

    def test_rechecked_full_matrices_have_only_the_primary_state_change(self):
        if not self.current():
            return
        for record in self.records():
            rows = record['rechecked_criteria']
            self.assertEqual([v['criterion_id'] for v in rows], [v['criterion_id'] for v in pilot.fixed_plan()['criterion_definitions']])
            changed = [v for v in rows if v['state_changed']]
            self.assertEqual(len(changed), 1)
            self.assertEqual(changed[0]['criterion_id'], record['original_criterion']['criterion_id'])
            self.assertTrue(all(v['rationale'] for v in rows))
            self.assertEqual(record['associated_state_changes'], [])
            self.assertTrue(record['associated_revision_explanation'])

    def test_actual_calculations_and_original_control_identities(self):
        if not self.current():
            return
        rows = {v['subject_id']: v for v in self.consumer.comparison().to_dict()['comparisons']}
        for sid in ('sol-ring-tap', 'basalt-monolith-tap'):
            self.assertEqual(rows[sid]['before']['overall_assessment'], policy.INCOMPLETE)
            self.assertEqual(rows[sid]['after']['overall_assessment'], policy.ELIGIBLE)
        for sid, negative in (('basalt-monolith-untap', 'potential_mana'), ('deathrite-shaman-first', 'no_target')):
            self.assertEqual(rows[sid]['before']['overall_assessment'], policy.INCOMPLETE)
            self.assertEqual(rows[sid]['before']['negative_witnesses'], [negative])
            self.assertEqual(rows[sid]['after']['negative_witnesses'], [negative])
            self.assertEqual(rows[sid]['after']['overall_assessment'], policy.EXCLUDED)
        flare = rows['mana-flare-trigger']
        self.assertEqual(flare['before']['overall_assessment'], policy.INDETERMINATE)
        self.assertEqual(flare['after']['overall_assessment'], policy.ELIGIBLE)
        for sid in ('dark-ritual-spell', 'pitiless-plunderer-host-trigger'):
            self.assertEqual(rows[sid]['before'], rows[sid]['after'])
            self.assertEqual(rows[sid]['after']['overall_assessment'], policy.EXCLUDED)
            self.assertEqual(rows[sid]['interpretation_input_id'], rows[sid]['original_candidate_id'])
            self.assertIsNone(rows[sid]['reassessment_id'])
            self.assertEqual(rows[sid]['proposed_changes'], [])

    def test_new_authority_and_rehashed_substitutions_reject(self):
        if not self.current():
            return
        original = self.records()[0]
        for mutation in ('authority', 'attestation', 'type', 'matrix', 'source', 'parent', 'extra', 'narrowing', 'hypothetical'):
            value = deepcopy(original)
            if mutation == 'authority': value['execution_authority'] = 'READY'
            elif mutation == 'attestation': value['review']['human_attestation'] = {'approved': True}
            elif mutation == 'type': value['review']['canonical_admission'] = 0
            elif mutation == 'matrix': value['rechecked_criteria'].pop()
            elif mutation == 'source': value['new_source_support'][0]['source_anchor']['byte_start'] += 1
            elif mutation == 'parent': value['original_candidate_id'] = value['reassessment_id']
            elif mutation == 'extra': value['official_ruling'] = True
            elif mutation == 'narrowing': value['universal_question_remaining_unknown'] = False
            else: value['source_package_id'] = 'sha256:' + '0' * 64
            value = c.seal(r.REASSESSMENT_VERSION, value, 'reassessment_id')
            with self.subTest(mutation=mutation), self.assertRaises(c.PilotError):
                self.consumer.validate_reassessment(value)
        report = self.consumer.comparison().to_dict()
        report['comparisons'][0]['after']['overall_assessment'] = policy.EXCLUDED
        report = c.seal(r.REPORT_VERSION, report, 'report_id')
        with self.assertRaises(c.PilotError):
            self.consumer.validate_report(report)
        # A genuinely computed old hypothetical is still not new source evidence.
        from card_rules_pilot.reasoning import ManaEvidenceReasoning
        historical = object.__new__(ManaEvidenceReasoning)
        object.__setattr__(historical, '_raw', c.owned(
            self.consumer.comparison().to_dict()['context']['original_comparison']))
        actual_case = historical.review_impact().to_dict()['cases'][0]
        self.assertEqual(actual_case['schema_version'], 'card-rules-mana-hypothetical-case-v1')
        with self.assertRaises(c.PilotError):
            self.consumer.validate_reassessment(actual_case)

    def test_immutable_owned_canonical_views_and_report_validation(self):
        if not self.current():
            return
        document = self.consumer.comparison(); raw = document.to_json()
        view = document.to_dict(); view.clear()
        self.assertEqual(document.to_json(), raw)
        self.assertLessEqual(len(raw.encode()), r.REPORT_LIMIT)
        self.assertEqual(self.consumer.validate_report(json.loads(raw)).to_json(), raw)
        for record in self.records():
            self.assertEqual(record['review'], {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False})
            self.assertEqual(record['semantic_review_status'], 'PENDING_NOT_ESTABLISHED')
            self.assertEqual(record['execution_authority'], 'BLOCKED')
            self.assertEqual(record['reassessment_id'], c.identity(r.REASSESSMENT_VERSION, record, 'reassessment_id'))
        with self.assertRaises((AttributeError, FrozenInstanceError)):
            self.consumer._raw = b'{}\n'
        with self.assertRaises(c.PilotError):
            self.consumer.validate_reassessment({'subject_id': 1.0})
        for invalid in ('', None, True, 'new-subject'):
            with self.assertRaises(c.PilotError):
                self.consumer.subject(invalid)

    def test_one_current_evidence_admission_per_invocation_no_success_cache(self):
        if not self.current():
            return
        with patch.object(pilot, 'read_cards', wraps=pilot.read_cards) as card_reader, \
                patch.object(pilot, 'read_rules', wraps=pilot.read_rules) as rule_reader, \
                patch.object(source, 'load_package', wraps=source.load_package) as source_reader:
            first = r.load_reassessment(**arguments())
            first.comparison(); first.check(); first.input_document()
            for sid in first.subject_ids:
                first.subject(sid)
            self.assertEqual((card_reader.call_count, rule_reader.call_count, source_reader.call_count), (1, 1, 1))
            r.load_reassessment(**arguments())
            self.assertEqual((card_reader.call_count, rule_reader.call_count, source_reader.call_count), (2, 2, 2))

    def test_current_files_checked_and_private_snapshot_survives_drift(self):
        if not self.current():
            return
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'successor'
            shutil.copytree(SUCCESSOR, destination)
            loaded = r.load_reassessment(**arguments(successor_root=destination))
            original = loaded.comparison().to_json()
            p = destination / 'reassessments.json'
            p.write_bytes(p.read_bytes() + b' ')
            self.assertEqual(loaded.comparison().to_json(), original)
            with self.assertRaises(c.PilotError):
                r.load_reassessment(**arguments(successor_root=destination))
            p.write_bytes(b'{"schema_version":"fictional","schema_version":"duplicate"}\n')
            with self.assertRaises(c.PilotError):
                r.load_reassessment(**arguments(successor_root=destination))

    def test_explicit_builder_rejects_unvalidated_inputs_before_output(self):
        if not self.current():
            return
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'must-not-exist'
            with self.assertRaises(c.PilotError):
                r.write_reassessments(destination, object(), {}, review_root=ROOT/'reference-reviews')
            self.assertFalse(destination.exists())
            p = pilot.load_pilot(**arguments())
            package = source.load_package(ROOT/'reference-reviews'/r.PACKAGE_NAME, review_root=ROOT/'reference-reviews')
            result = r.write_reassessments(destination, p, package, review_root=ROOT/'reference-reviews')
            self.assertEqual(result.to_json(), self.consumer.input_document().to_json())
            with self.assertRaises(c.PilotError):
                r.write_reassessments(destination, p, package, review_root=ROOT/'reference-reviews')
            data = (destination/'reassessments.json').read_bytes()
            self.assertEqual(data, (SUCCESSOR/'reassessments.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
