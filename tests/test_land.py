"""Real public admission plus focused checks over the shared admitted snapshot."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import contract as c, land, land_authored, land_cards
from card_rules_pilot import reasoning_policy as classification
from land_test_support import ROOT, arguments, consumer, current_catalog_intact


class LandIntelligenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact = current_catalog_intact(unittest.TestCase())
        cls.consumer = consumer() if cls.intact else None

    def admitted(self):
        if self.intact:
            return True
        with self.assertRaises(ValueError):
            land.load_lands(**arguments())
        return False

    def test_actual_closure_complete_ownership_and_results(self):
        if not self.admitted(): return
        value = self.consumer.overview().to_dict()
        self.assertEqual(self.consumer.subject_ids, tuple(row[0] for row in land_cards.SUBJECTS))
        self.assertEqual(len(value['context']['evidence']['cards']), 6)
        self.assertEqual(len(value['assessments']), 9)
        self.assertEqual(value['context']['retained_rules']['context_id'],
            'sha256:59eb902055e8f597f9b0761ac176ad37406365c53a87098e3dcf621a1c5df478')
        expected = {'port-utility': 'CONDITIONAL_ORDINARY_ACTIVATED',
                    'city-damage-trigger': 'UNRESOLVED_ORDINARY_TRIGGERED_FRONTIER'}
        for result in value['assessments']:
            self.assertEqual(result['behavior']['branch'], expected.get(result['subject_id'], 'CONDITIONAL_ACTIVATED_MANA'))
            self.assertEqual(result['review'], {'status': 'requires_review', 'human_attestation': None, 'canonical_admission': False})
            self.assertEqual(result['execution_authority'], 'BLOCKED')
        self.assertLess(len(self.consumer.overview().to_json().encode()), land.REPORT_LIMIT)

    def test_port_owns_target_and_full_cost_without_borrowed_mana(self):
        if not self.admitted(): return
        value = self.consumer.comparison('mana-and-utility').to_dict()
        options = value['comparisons'][0]['comparison']['options']
        self.assertEqual(options[0]['negative_witnesses'], [])
        self.assertEqual(options[1]['negative_witnesses'], [])
        self.assertEqual(options[2]['negative_witnesses'], ['no_target', 'potential_mana'])
        self.assertEqual(options[2]['complete_owned_passage'], '{1}, {T}: Tap target land.')
        self.assertEqual(options[2]['written_readings']['cost']['written_cost'], '{1}, {T}')
        self.assertEqual(options[2]['written_readings']['output']['actual_output'], 'unknown')

    def test_city_trigger_and_citadel_effect_keep_distinct_procedures(self):
        if not self.admitted(): return
        results = {row['subject_id']: row for row in self.consumer.overview().to_dict()['assessments']}
        triggered = results['city-damage-trigger']
        self.assertEqual(triggered['classification']['negative_witnesses'], ['trigger_potential_mana', 'qualifying_trigger_relationship'])
        consequence = triggered['behavior']['consequences'][0]['conditional_consequence']
        self.assertEqual(consequence['placement'], 'UNSUPPORTED_603_FRONTIER')
        self.assertEqual(triggered['additional_effect_composition']['status'], 'SEPARATE_TRIGGERED_SUBJECT')
        colored = results['citadel-color-choice']['additional_effect_composition']
        self.assertEqual(colored['status'], 'CONDITIONAL_SAME_ABILITY_ADDITIONAL_EFFECT')
        self.assertIsNotNone(colored['conditional_relationship'])
        self.assertIn('no additional effect is asserted', colored['unchanged_baseline_additional_effect_context']['explanation'])
        self.assertEqual(results['citadel-colorless']['additional_effect_composition']['status'], 'PENDING_NO_ADDITIONAL_EFFECT_IN_SELECTED_SUBJECT')
        self.assertIsNone(results['citadel-colorless']['descriptive_readings']['effect_ownership']['damage_clause'])

    def test_counts_and_external_palette_remain_unknown(self):
        if not self.admitted(): return
        results = {row['subject_id']: row for row in self.consumer.overview().to_dict()['assessments']}
        for sid, dependency in (('coffers-mana', 'controlled_swamp_count'), ('tower-mana', 'commander_color_identity')):
            result = results[sid]
            self.assertEqual(result['classification']['overall_assessment'], classification.ELIGIBLE)
            self.assertIn(dependency, result['descriptive_readings']['output']['dependencies'])
            self.assertEqual(result['descriptive_readings']['output']['actual_output'], 'unknown')
            self.assertEqual(result['descriptive_readings']['conditions']['supplied_game_inputs'], [])

    def test_comparisons_project_meaningful_dimensions_not_labels(self):
        if not self.admitted(): return
        value = self.consumer.overview().to_dict()
        pairs = {row['name']: row['comparison'] for row in value['comparisons']}
        self.assertEqual(set(pairs), set(land.COMPARISONS))
        for name, required in (('variable-output', {'written_cost','dependencies','output_pattern'}),
                               ('color-context', {'dependencies','written_output'}),
                               ('damage-ownership', {'effect_ownership','effect_composition'})):
            self.assertTrue(required <= {row['dimension'] for row in pairs[name]['differences']})
        snapshot = value['context']
        candidates = snapshot['interpretations']['candidates'][:2]
        assessments = value['assessments'][:2]
        original = land._compare(candidates, assessments)
        modified = deepcopy(candidates)
        for candidate in modified:
            candidate['display_label'] = 'arbitrary label'
        self.assertEqual(original, land._compare(modified, assessments))
        self.assertEqual(original['differences'], [])

    def test_report_validation_recomputes_and_rejects_coherent_tampering(self):
        if not self.admitted(): return
        report = self.consumer.overview().to_dict()
        changes = []
        for key, value in (('schema_version', 'unsupported-v2'), ('execution_authority', 'READY'),
                           ('semantic_review_status', 'APPROVED'), ('cohort_card_count', True)):
            changed = deepcopy(report); changed[key] = value; changes.append(changed)
        changed = deepcopy(report); changed['review']['canonical_admission'] = 0; changes.append(changed)
        changed = deepcopy(report); changed['assessments'][0]['behavior']['branch'] = 'READY'; changes.append(changed)
        changed = deepcopy(report); changed['context']['interpretations']['candidates'].pop(); changes.append(changed)
        changed = deepcopy(report); changed['context']['evidence']['subjects']['citadel-color-choice']['selected_passage'] = '{T}: Add one mana of any color.'; changes.append(changed)
        changed = deepcopy(report); changed['context']['retained_rules']['rules'][0]['rule']['source_anchor']['effective_date'] = '2099-01-01'; changes.append(changed)
        for changed in changes:
            changed = c.seal(land.REPORT_VERSION, changed, 'report_id')
            with self.assertRaises(ValueError): self.consumer.validate_report(changed)
        self.assertEqual(self.consumer.validate_report(report).to_dict(), report)
        for value in ({}, {'kind': True}, {'kind':'subject','selector':'foreign'}, {'kind':'overview','selector':True}):
            with self.assertRaises(ValueError): self.consumer.validate_report(value)
        with self.assertRaises(ValueError): c.parse_json(b'{"a":1,"a":2}\n')
        with self.assertRaises(ValueError): c.owned({'float':1.0})

    def test_private_views_and_fresh_authored_admission(self):
        if not self.admitted(): return
        original = self.consumer.overview().to_json()
        view = self.consumer.overview().to_dict(); view['context'].clear()
        self.assertEqual(self.consumer.overview().to_json(), original)
        with self.assertRaises(TypeError): land.LandConsumer(b'{}')
        snapshot = json.loads(self.consumer._snapshot)
        rules = snapshot['retained_rules']
        context = {'retained_rules': rules, 'rule_facts': {row['rule']['rule_reference']:row for row in rules['rules']}}
        with tempfile.TemporaryDirectory() as directory:
            cohort = Path(directory)/'cohort'
            shutil.copytree(arguments()['cohort_root'], cohort)
            with patch.object(land_cards, 'read_cards', return_value=snapshot['evidence']), \
                    patch.object(land.land_context, 'read_context', return_value=context):
                first = land.load_lands(**arguments(cohort_root=cohort))
                path = cohort/'interpretations.json'
                content = c.read_json(path); content['candidates'][0]['review']['canonical_admission'] = True
                # Rehash candidate, collection and manifest coherently: still not
                # the exact authored pending readings, so public admission fails.
                content['candidates'][0] = c.seal(land_authored.CANDIDATE_VERSION, content['candidates'][0], 'candidate_id')
                content = c.seal(land_authored.INPUT_VERSION, content, 'interpretations_id')
                path.write_bytes(c.canonical(content))
                (cohort/'manifest.json').write_bytes(c.canonical(land_authored.build_manifest(snapshot['plan'], content)))
                self.assertEqual(first.overview().to_json(), original)
                with self.assertRaises(ValueError): land.load_lands(**arguments(cohort_root=cohort))
                path.write_bytes(c.canonical(snapshot['interpretations']))
                (cohort/'manifest.json').write_bytes(c.canonical(snapshot['manifest']))
                (cohort/'foreign.json').write_bytes(b'{}\n')
                with self.assertRaises(ValueError): land.load_lands(**arguments(cohort_root=cohort))


if __name__ == '__main__': unittest.main()
