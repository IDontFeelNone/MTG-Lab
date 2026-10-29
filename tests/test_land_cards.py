"""Actual six-land evidence and complete authored boundaries; no synthetic Cards.

The unchanged publication writer's real expanded catalog must reject. It is
never replaced with a historical catalog for these evidence checks.
"""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence.mechanics import MechanicalCardIntelligence
from card_rules_pilot import land_cards as lands
from test_card_rules_pilot_cards import current_catalog_intact, evidence_copy


ROOT = Path(__file__).resolve().parents[1]


def arguments():
    return dict(catalog_root=ROOT, mechanical_root=ROOT,
                expected_profile_id=lands.PROFILE_ID,
                expected_query_snapshot_id=lands.QUERY_ID)


def read(mechanical=ROOT):
    return lands.read_cards(catalog_root=ROOT, mechanical_root=mechanical,
        expected_profile_id=lands.PROFILE_ID, expected_query_snapshot_id=lands.QUERY_ID)


class LandCardEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intact = current_catalog_intact(unittest.TestCase())
        cls.evidence = read() if cls.intact else None

    def current(self):
        if not self.intact:
            with self.assertRaises(ValueError):
                read()
        return self.intact

    def test_exact_six_card_nine_subject_closure_and_all_own_bindings(self):
        if not self.current():
            return
        result = self.evidence
        self.assertEqual(len(result['cards']), 6)
        self.assertEqual(len(result['subjects']), 9)
        self.assertEqual(set(result['cards']), {r[0] for r in lands.CARD_BINDINGS})
        self.assertEqual(set(result['subjects']), {r[0] for r in lands.SUBJECTS})
        self.assertEqual(result['canonical_snapshot_id'], lands.QUERY_ID)
        expected_indices = (91, 32, 29, 250, 19, 230)
        for (cid, name, dossier), record_index in zip(lands.CARD_BINDINGS, expected_indices):
            card = result['cards'][cid]
            self.assertEqual(card['card_identity'], {'game_id':'magic', 'card_id':cid, 'name':name})
            self.assertEqual(card['mechanical_dossier_id'], dossier)
            self.assertEqual(card['source']['source_record_index'], record_index)
            self.assertEqual(card['canonical_values']['card_reference'], cid)
            self.assertEqual(card['source']['oracle_id'], cid)
            self.assertEqual(card['source']['resolution'], 'unique')
        self.assertFalse(result['catalog_binding']['production_eligible'])
        self.assertEqual(result['catalog_binding']['source_policy_clearance'], 'not_granted')

    def test_complete_ownership_and_offsets_preserve_retained_this_land_text(self):
        if not self.current():
            return
        subjects = self.evidence['subjects']
        for sid, cid, passage, owner, _ in lands.SUBJECTS:
            subject = subjects[sid]
            self.assertEqual(subject['card_id'], cid)
            self.assertEqual(subject['selected_passage'], passage)
            self.assertEqual(subject['owner'], owner)
            self.assertEqual(subject['identity_scope'], 'local_review_subject_only')
            self.assertEqual(subject['complete_field_value'],
                subject['surrounding_before'] + passage + subject['surrounding_after'])
            self.assertEqual(subject['complete_field_value'][subject['passage_start']:subject['passage_end']], passage)
            self.assertEqual(subject['source_record_pointer'],
                '/' + str(self.evidence['cards'][cid]['source']['source_record_index']) + '/oracle_text')
        self.assertNotIn('target', subjects['port-mana']['selected_passage'])
        self.assertEqual(subjects['port-utility']['selected_passage'], '{1}, {T}: Tap target land.')
        self.assertEqual(subjects['city-damage-trigger']['selected_passage'],
            'Whenever this land becomes tapped, it deals 1 damage to you.')
        self.assertEqual(subjects['citadel-color-choice']['selected_passage'],
            '{T}: Add one mana of any color. This land deals 3 damage to you.')
        self.assertNotIn('damage', subjects['citadel-colorless']['selected_passage'])
        self.assertIn('{2}, {T}', subjects['coffers-mana']['selected_passage'])
        self.assertIn("in your commander's color identity", subjects['tower-mana']['selected_passage'])

    def test_one_actual_mechanical_reader_without_dossier_or_cohort_reconstruction(self):
        if not self.current():
            return
        with patch.object(MechanicalCardIntelligence, 'from_attachment',
                wraps=MechanicalCardIntelligence.from_attachment) as factory, \
             patch.object(MechanicalCardIntelligence, 'dossier', side_effect=AssertionError('no reconstruction')), \
             patch.object(MechanicalCardIntelligence, 'cohort_report', side_effect=AssertionError('no cohort')):
            self.assertEqual(read(), self.evidence)
        factory.assert_called_once()

    def test_new_admission_checks_changed_actual_evidence_and_prior_view_is_owned(self):
        if not self.current():
            return
        expected = deepcopy(self.evidence)
        with tempfile.TemporaryDirectory(prefix='mtglab-land-evidence-') as temp:
            copied = evidence_copy(temp)
            snapshot = read(copied)
            path = copied / lands.DOSSIER_REFERENCE
            path.write_bytes(path.read_bytes() + b' ')
            with self.assertRaises(ValueError):
                read(copied)
            self.assertEqual(snapshot, expected)
            snapshot['subjects'].clear()
            self.assertEqual(self.evidence, expected)

    def test_expected_profile_and_query_identity_cannot_be_substituted(self):
        for key in ('expected_profile_id', 'expected_query_snapshot_id'):
            for value in (True, 1, None, 'sha256:' + '0' * 64):
                kwargs = arguments()
                kwargs[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    lands.read_cards(**kwargs)


if __name__ == '__main__':
    unittest.main()
