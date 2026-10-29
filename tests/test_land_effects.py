"""Synthetic ownership algebra, kept separate from real Card evidence admission."""
from copy import deepcopy
import hashlib
import unittest

from card_rules_pilot import behavior_policy, land_effects as effects
from card_rules_pilot.contract import PilotError, canonical, seal
from test_mana_behavior import retained_policy_facts, synthetic


def content_identity(value):
    return 'sha256:' + hashlib.sha256(canonical(value)[:-1]).hexdigest()


def subject(label='fictional-subject', text='Fictional mana instruction. Fictional complete effect clause.'):
    field = {'source_pointer': '/oracle_text', 'status': 'known', 'value': text}
    type_line = {'source_pointer': '/type_line', 'status': 'known', 'value': 'Fictional retained label'}
    return dict(subject_id=label, identity_scope='local_review_subject_only',
        card_id='fictional-card', mechanical_dossier_id='sha256:' + '1' * 64,
        owner='host_card', source_field_pointer='/oracle_text',
        source_record_pointer='/0/oracle_text', source_field_identity=content_identity(field),
        complete_field_value=text, selected_passage=text, passage_start=0,
        passage_end=len(text), surrounding_before='', surrounding_after='',
        unselected_context_assessment='outside_this_subject',
        ownership_and_context_limitations='Synthetic policy inputs only; not real Card evidence.',
        type_line={**type_line, 'field_identity': content_identity(type_line)})


def reading(value, state='same_ability_additional_effect'):
    return dict(state=state, owner_subject_id=value['subject_id'], card_id=value['card_id'],
        damage_clause='Fictional complete effect clause.' if state in (
            'same_ability_additional_effect', 'separate_triggered_ability') else None,
        other_subject_ids=[], evidence_refs=['selected_passage', 'full_oracle_field'] + (
            ['rule:405.6c'] if state == 'same_ability_additional_effect' else []),
        rationale='Explicit synthetic ownership premise; no text recognition.',
        counterevidence=['The premise has no real-Card semantic attestation.'],
        unresolved=['Actual game inputs remain unknown.'])


def bind_candidate(inputs):
    """Seal synthetic premises; this is never a real-Card admission fixture."""
    selected, effect, baseline = inputs['subject'], inputs['reading'], inputs['behavior']
    rows = [{**row, 'evidence_refs': ['selected_passage'],
        'rationale': 'Explicit synthetic criterion premise.',
        'absence_scope': 'synthetic_complete_selected_subject_only',
        'counterevidence': ['Synthetic data has no real-Card semantic authority.'],
        'unresolved': ['Human semantic review remains pending.']}
        for row in baseline['input_readings']['criteria']]
    candidate = seal(effects.CANDIDATE_VERSION, {
        'schema_version': effects.CANDIDATE_VERSION, 'prepared_at': '2026-10-29T00:00:00Z',
        'plan_id': 'sha256:' + '3' * 64, 'context_id': 'sha256:' + '4' * 64,
        'subject': selected, 'source_binding': {'card_id': selected['card_id'],
            'mechanical_dossier_id': selected['mechanical_dossier_id'],
            'source_field_identity': selected['source_field_identity'],
            'canonical_snapshot_id': 'sha256:' + '5' * 64,
            'provider_record_id': 'fictional-provider-record',
            'record_content_identity': 'sha256:' + '6' * 64},
        'proposed_kind': baseline['proposed_kind'],
        'kind_evidence_refs': baseline['input_readings']['kind_evidence_refs'],
        'criteria': rows, 'descriptive_readings': {'cost': {}, 'output': {},
            'conditions': {}, 'effect_ownership': effect},
        'counterevidence': ['Synthetic interpretation only.'],
        'unresolved': ['Actual game inputs remain unknown.'],
        'classification_present_usability_distinct': True,
        'limitations': ['Not real Card evidence.'],
        'authority': 'ENGINEER_AUTHORED_SOURCE_BOUND_PENDING_LAND_READINGS_ONLY',
        'semantic_review_status': 'PENDING_NOT_ESTABLISHED',
        'review': {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False},
        'execution_authority': 'BLOCKED'}, 'candidate_id')
    inputs['candidate'], inputs['candidate_id'] = candidate, candidate['candidate_id']
    return inputs


class SyntheticLandEffectCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = retained_policy_facts()

    def inputs(self, state='same_ability_additional_effect', matrix=None, facts=None):
        selected = subject()
        facts = deepcopy(self.facts if facts is None else facts)
        baseline = behavior_policy.compute(**(matrix or synthetic()), rule_facts=facts)
        return bind_candidate(dict(subject=selected,
            classification=baseline['classification'], behavior=baseline,
            reading=reading(selected, state), rule_facts=facts))

    def test_same_ability_positive_uses_explicit_ownership_and_keeps_baseline(self):
        inputs = self.inputs()
        before = deepcopy(inputs)
        result = effects.compute(**inputs)
        self.assertEqual(result['status'], 'CONDITIONAL_SAME_ABILITY_ADDITIONAL_EFFECT')
        relation = result['conditional_relationship']
        self.assertEqual(relation['relationship'], 'BOTH_PARTS_SHARE_IMMEDIATE_RESOLUTION_BEHAVIOR')
        self.assertEqual(relation['fine_grained_ordering'], 'NOT_ESTABLISHED')
        self.assertFalse(relation['actual_effect_executed'])
        self.assertIn('no additional effect is asserted',
            result['unchanged_baseline_additional_effect_context']['explanation'])
        self.assertEqual(inputs, before)
        self.assertEqual(result['rule_evidence'][0]['rule_reference'], '405.6c')
        self.assertEqual(result['execution_authority'], 'BLOCKED')
        self.assertFalse(result['review']['canonical_admission'])
        self.assertIsNone(result['review']['human_attestation'])

    def test_same_computation_follows_structured_inputs_under_other_labels_and_text(self):
        original = effects.compute(**self.inputs())
        inputs = self.inputs()
        inputs['subject'] = subject('another-fictional-label', 'Unrelated fictional prose. Fictional complete effect clause.')
        inputs['reading'] = reading(inputs['subject'])
        bind_candidate(inputs)
        result = effects.compute(**inputs)
        self.assertEqual(result['status'], original['status'])
        self.assertEqual(result['conditional_relationship'], original['conditional_relationship'])
        self.assertNotEqual(result['composition_id'], original['composition_id'])

    def test_negative_missing_conflicting_and_nonqualifying_inputs_supply_no_shared_effect(self):
        for state in ('no_additional_effect', 'unknown', 'conflicting'):
            with self.subTest(state=state):
                result = effects.compute(**self.inputs(state))
                self.assertIsNone(result['conditional_relationship'])
        missing = dict(self.facts)
        missing.pop('405.6c')
        result = effects.compute(**self.inputs(facts=missing))
        self.assertEqual(result['status'], 'UNRESOLVED_EFFECT_OWNERSHIP')
        self.assertIsNone(result['conditional_relationship'])
        self.assertIn('405.6c', ' '.join(result['remaining_unknowns']))
        excluded = self.inputs(matrix=synthetic(potential_mana='proposed_not_satisfied'))
        self.assertIsNone(effects.compute(**excluded)['conditional_relationship'])
        incomplete = self.inputs(matrix=synthetic(self_replacement_considered='unknown'))
        self.assertIsNone(effects.compute(**incomplete)['conditional_relationship'])

    def test_unresolved_triggered_kind_supplies_no_separate_triggered_conclusion(self):
        for state in ('unknown', 'unsupported', 'conflicting', 'proposed_not_satisfied'):
            inputs = self.inputs('separate_triggered_ability', matrix=synthetic(
                'proposed_triggered_ability', triggered_kind=state,
                trigger_potential_mana='proposed_not_satisfied',
                qualifying_trigger_relationship='proposed_not_satisfied'))
            with self.subTest(state=state):
                result = effects.compute(**inputs)
                self.assertEqual(result['status'], 'UNRESOLVED_EFFECT_OWNERSHIP')
                self.assertIsNone(result['conditional_relationship'])

    def test_complete_candidate_and_authored_clause_cannot_be_substituted(self):
        changes = []
        value = self.inputs(); value['reading']['damage_clause'] = 'Foreign sibling effect.'
        bind_candidate(value); changes.append(value)
        value = self.inputs(); value['candidate']['subject']['owner'] = 'foreign-owner'
        value['candidate'] = seal(effects.CANDIDATE_VERSION, value['candidate'], 'candidate_id')
        value['candidate_id'] = value['candidate']['candidate_id']; changes.append(value)
        value = self.inputs(); value['candidate']['criteria'][0]['state'] = 'conflicting'
        value['candidate'] = seal(effects.CANDIDATE_VERSION, value['candidate'], 'candidate_id')
        value['candidate_id'] = value['candidate']['candidate_id']; changes.append(value)
        value = self.inputs(); value['candidate']['review']['canonical_admission'] = True
        value['candidate'] = seal(effects.CANDIDATE_VERSION, value['candidate'], 'candidate_id')
        value['candidate_id'] = value['candidate']['candidate_id']; changes.append(value)
        value = self.inputs(); value['candidate']['schema_version'] = 'unsupported-v999'
        value['candidate'] = seal(effects.CANDIDATE_VERSION, value['candidate'], 'candidate_id')
        value['candidate_id'] = value['candidate']['candidate_id']; changes.append(value)
        for index, value in enumerate(changes):
            with self.subTest(index=index), self.assertRaises(PilotError):
                effects.compute(**value)

    def test_separate_trigger_retains_unresolved_603_frontier_without_borrowed_output(self):
        inputs = self.inputs('separate_triggered_ability', matrix=synthetic(
            'proposed_triggered_ability', trigger_potential_mana='proposed_not_satisfied',
            qualifying_trigger_relationship='proposed_not_satisfied'))
        result = effects.compute(**inputs)
        self.assertEqual(result['status'], 'SEPARATE_TRIGGERED_SUBJECT')
        self.assertEqual(result['behavior_branch'], 'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER')
        self.assertIn('603', ' '.join(result['remaining_unknowns']))
        self.assertIsNone(result['conditional_relationship'])

    def test_foreign_ownership_missing_readings_types_and_rehashed_labels_reject(self):
        changes = []
        for key in ('owner_subject_id', 'card_id'):
            value = self.inputs(); value['reading'][key] = 'foreign'; changes.append(value)
        value = self.inputs(); value['reading'].pop('counterevidence'); changes.append(value)
        value = self.inputs(); value['reading']['evidence_refs'].append('subject:foreign'); changes.append(value)
        value = self.inputs(); value['reading']['state'] = True; changes.append(value)
        value = self.inputs(); value['subject']['passage_start'] = False; changes.append(value)
        value = self.inputs(); value['subject']['selected_passage'] += ' altered'; changes.append(value)
        value = self.inputs(); value['candidate_id'] = 'unsupported'; changes.append(value)
        value = self.inputs(); value['behavior']['branch'] = 'CONDITIONAL_ORDINARY_ACTIVATED'
        value['behavior'] = seal(behavior_policy.RESULT_VERSION, value['behavior'], 'calculation_id'); changes.append(value)
        value = self.inputs(); value['classification']['overall_assessment'] = 'foreign'; changes.append(value)
        value = self.inputs(); value['rule_facts']['405.6c']['rule']['mana_plus_additional_effect']['fine_grained_ordering'] = 'invented'; changes.append(value)
        for index, value in enumerate(changes):
            with self.subTest(index=index), self.assertRaises(PilotError):
                effects.compute(**value)


if __name__ == '__main__':
    unittest.main()
