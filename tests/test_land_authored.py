"""Pending reading ownership and uncertainty regressions without readmission.

The public integration tests admit current evidence. These checks inspect the
finite retained input's semantic boundaries, independent of result generation.
"""
import hashlib
from pathlib import Path
import unittest

from card_rules_pilot import contract as c
from card_rules_pilot import land_authored as a
from card_rules_pilot import reasoning_policy as p

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'data/review/land-mana-utility'


class AuthoredLandReadingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = c.read_json(PACKAGE / 'plan.json')
        cls.collection = c.read_json(PACKAGE / 'interpretations.json')
        cls.candidates = {row['subject']['subject_id']: row for row in cls.collection['candidates']}

    def test_own_contract_identities_and_manifest_bind_canonical_bytes(self):
        self.assertEqual(self.plan['plan_id'], a.PLAN_ID)
        self.assertEqual(c.identity(a.PLAN_VERSION, self.plan, 'plan_id'), a.PLAN_ID)
        self.assertEqual(self.collection['interpretations_id'],
            c.identity(a.INPUT_VERSION, self.collection, 'interpretations_id'))
        manifest = c.read_json(PACKAGE / 'manifest.json')
        self.assertEqual(manifest, a.build_manifest(self.plan, self.collection))
        for filename, binding in manifest['files'].items():
            raw = (PACKAGE / filename).read_bytes()
            self.assertEqual(binding['bytes'], len(raw))
            self.assertEqual(binding['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(self.plan['card_count'], 6)
        self.assertEqual(self.plan['subject_count'], 9)
        self.assertEqual(len(self.candidates), 9)
        self.assertEqual(len({row['subject']['card_id'] for row in self.candidates.values()}), 6)

    def test_every_reading_retains_explicit_methods_evidence_and_authority(self):
        for sid, candidate in self.candidates.items():
            with self.subTest(subject=sid):
                self.assertEqual(candidate['candidate_id'],
                    c.identity(a.CANDIDATE_VERSION, candidate, 'candidate_id'))
                rows = candidate['criteria']
                self.assertEqual([r['criterion_id'] for r in rows], [r[0] for r in p._DEFINITIONS])
                for row in rows:
                    for field in ('evidence_refs', 'rationale', 'absence_scope', 'counterevidence', 'unresolved'):
                        self.assertTrue(row[field], (sid, row['criterion_id'], field))
                activated = candidate['proposed_kind'] == 'proposed_activated_ability'
                self.assertEqual([r['state'] for r in rows[-4:]],
                    ['inapplicable'] * 4 if activated else
                    ['proposed_satisfied', 'proposed_satisfied', 'proposed_not_satisfied', 'proposed_not_satisfied'])
                if activated:
                    self.assertEqual(rows[6]['state'], 'proposed_satisfied')
                    self.assertEqual(rows[6]['absence_scope'], 'complete_retained_card_text_only_not_universal_game_state')
                    self.assertIn('rule:614.15', rows[6]['evidence_refs'])
                    self.assertEqual(rows[7]['absence_scope'], 'no_absence_finding_methodological_disregard_only')
                self.assertEqual(candidate['semantic_review_status'], 'PENDING_NOT_ESTABLISHED')
                self.assertEqual(candidate['review'], {'status': 'requires_review',
                    'human_attestation': None, 'canonical_admission': False})
                self.assertEqual(candidate['execution_authority'], 'BLOCKED')

    def test_damage_and_target_readings_stay_with_the_complete_owner(self):
        city = self.candidates['city-damage-trigger']
        self.assertEqual(city['subject']['selected_passage'],
            'Whenever this land becomes tapped, it deals 1 damage to you.')
        self.assertEqual(city['descriptive_readings']['effect_ownership']['state'], 'separate_triggered_ability')
        citadel = self.candidates['citadel-color-choice']
        self.assertEqual(citadel['subject']['selected_passage'],
            '{T}: Add one mana of any color. This land deals 3 damage to you.')
        self.assertEqual(citadel['descriptive_readings']['effect_ownership']['state'], 'same_ability_additional_effect')
        self.assertEqual(citadel['descriptive_readings']['effect_ownership']['damage_clause'],
            'This land deals 3 damage to you.')
        for sid in ('citadel-colorless', 'city-mana'):
            effect = self.candidates[sid]['descriptive_readings']['effect_ownership']
            self.assertEqual(effect['state'], 'no_additional_effect')
            self.assertIsNone(effect['damage_clause'])
        port = self.candidates['port-utility']
        self.assertEqual(port['subject']['selected_passage'], '{1}, {T}: Tap target land.')
        self.assertEqual(port['criteria'][1]['state'], 'proposed_not_satisfied')
        self.assertEqual(port['criteria'][2]['state'], 'proposed_not_satisfied')
        self.assertEqual(self.candidates['port-mana']['criteria'][1]['state'], 'proposed_satisfied')
        self.assertEqual(self.candidates['port-mana']['criteria'][2]['state'], 'proposed_satisfied')

    def test_unknown_count_and_commander_context_are_not_filled(self):
        coffers = self.candidates['coffers-mana']
        tower = self.candidates['tower-mana']
        self.assertEqual(coffers['descriptive_readings']['cost']['written_cost'], '{2}, {T}')
        self.assertEqual(coffers['descriptive_readings']['output']['written_instruction'],
            'Add {B} for each Swamp you control.')
        self.assertEqual(tower['descriptive_readings']['output']['written_instruction'],
            "Add one mana of any color in your commander's color identity.")
        for candidate, dependency in ((coffers, 'controlled_swamp_count'), (tower, 'commander_color_identity')):
            self.assertEqual(candidate['descriptive_readings']['output']['actual_output'], 'unknown')
            self.assertIn(dependency, candidate['descriptive_readings']['output']['dependencies'])
            self.assertEqual(candidate['descriptive_readings']['conditions']['supplied_game_inputs'], [])
            self.assertEqual(candidate['criteria'][2]['state'], 'proposed_satisfied')


if __name__ == '__main__':
    unittest.main()
