"""Finite land successor, exact inherited boundaries and owning-contract parity."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import proposed_spell_packet_analysis_preservation as guard
import proposed_spell_packet_authoring_preservation as previous

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MAIN = '121aecc20810c59ad689eaa25f23079305b3605d'
CANONICAL_TREE = '562c4074d5523b04d80f54edad829a15071f0b93'
PROTECTED_SHA256 = {'src/card_rules_pilot/__init__.py': '2093c7424b37f6106539fd705bd5f92fad3265e57f91f70b78f6f77b85a25feb',
 'src/card_rules_pilot/__main__.py': 'c8caad5badb9da31d6db5a8b45457a5c4bee4e26b63c333fa77e856b990d427d',
 'src/card_rules_pilot/contract.py': '6ab87a46c13d91b799e1c30e96323898feb08d05ec80d486c4204784d27334e5',
 'src/card_rules_pilot/pilot.py': '4556628ec9e4be09b69b0f11434a3bd1c370c3744dac1f283811d51aaa3e4c31',
 'src/card_rules_pilot/authored.py': '4b6284d25add2069a34b6d6dda37be944296c22d14409a1920225bd719881e88',
 'src/card_rules_pilot/cards.py': '02311cfad0339836064c2235237853c0e3fc39c48db3bb901d37b02e58ccc70c',
 'src/card_rules_pilot/rules.py': 'fb07585c48cb7ca303de57e13ff0817dac34ee5472b6fdd91208670a453d15d7',
 'src/card_rules_pilot/reasoning.py': 'b01435e8180923cef545b19fa713afa153eb634e3a47f950455c01bb8d324f20',
 'src/card_rules_pilot/reasoning_policy.py': '4ebb431fb265fe37223aafe7a8c6829a027019ba1cd0d5abe54f94709a9465bf',
 'src/card_rules_pilot/reassessment.py': 'a98cbc8dd8a59567cbb4a4557f189456533055181726e39ef58e61b296788892',
 'src/card_rules_pilot/reassessment_cli.py': '7a75d87676ca94fe24232498ca36a7712f4b198a47615780d7586cd730d528c1',
 'src/card_rules_pilot/behavior.py': 'aa7f9399a6aca318ec24696ffe1fffb7b85899716ef8eebb278cabf444bb7f84',
 'src/card_rules_pilot/behavior_context.py': 'aabe91a493e36a3e459fca6a3619d15c60fd5d036fdaedfc46e538b8f68ee7fa',
 'src/card_rules_pilot/behavior_policy.py': 'ac67f056df9889afe377decc13d6d54fb0c741e101e67f5f718021b0e35c6d27',
 'src/card_rules_pilot/behavior_cli.py': '6af12074fa42af9fabb0682e0c43af6ae2a1917eb7ba7173651aa56c082a12f4',
 'docs/ARCHITECTURE.md': 'c4651ad45e47ff9a247151a9c4ca54e8e7dd18b23725cec0571039ef676284b3',
 'docs/DECISIONS.md': '47e1fc0e4353f251dde4fb316ec79642a3ab3d51fc0dcc6613b49a795ead73db',
 'data/review/mechanical-card-cohort/dossiers.jsonl': '108d269bc77a36e076028c67169e351f8b5328ad27a6b060ba69f74ead2c11bf',
 'data/review/mechanical-card-cohort/manifest.json': '8405fc5b88b8eabb16d5596d567c27bc749b63e68a33af792ef6f287001c3e58',
 'data/market/acquisitions/scryfall-mb2-30754638264-1/source-mb2.json': 'c112a379a2356632f37c89f6486cd2f921eccf7a5413113d13d863383c236d47',
 '.github/workflows/python-validation.yml': '4c4c7e42ff96c59e6edbe2c4d204c50a464d907153d9caf9df9564b03430b6a2'}


class LandPreservationTests(unittest.TestCase):
    def test_finite_sources_and_no_projection_or_future_exception(self):
        names = {"src/card_rules_pilot/" + name for name in (
            "land_cards.py", "land_authored.py", "land_context.py",
            "land_effects.py", "land.py", "land_cli.py")}
        self.assertEqual(guard.LAND_MANA_SOURCE_PATHS, names)
        for name in names:
            self.assertTrue(guard.is_packet_analysis_addition(ROOT / name))
            self.assertTrue(previous.is_packet_authoring_addition(ROOT / name))
            self.assertFalse(guard.is_packet_analysis_addition(ROOT / (name + '.future')))
        for name in ('src/card_rules_pilot/land_future.py',
                     'src/gameplay_rules/projection/land.py',
                     'reference-reviews/land-mana/projection.json'):
            self.assertFalse(guard.is_packet_analysis_addition(ROOT / name))

    def test_exact_suffixes_reconstruct_canonical_main_and_reject_drift(self):
        self.assertEqual(set(guard.LAND_MANA_DOCUMENT_APPENDICES), set(guard.DOCUMENT_APPENDICES))
        for name, pin in guard.LAND_MANA_DOCUMENT_APPENDICES.items():
            with self.subTest(path=name):
                raw = (ROOT / name).read_bytes()
                old = guard.historical_document_before_land_mana_append(name, raw)
                self.assertEqual(len(raw), pin['baseline_bytes'] + pin['appendix_bytes'])
                self.assertEqual(hashlib.sha256(old).hexdigest(), pin['baseline_sha256'])
                self.assertEqual(guard.historical_document_before_land_mana_append(name, old), old)
                self.assertEqual(guard.historical_document_before_mana_behavior_append(name, raw),
                    guard.historical_document_before_mana_behavior_append(name, old))
                for changed in (raw + b'future\n', raw[:-1], b'X' + raw[1:],
                                old + b'X' + raw[len(old)+1:], bytearray(raw), True):
                    with self.assertRaises(AssertionError):
                        guard.historical_document_before_land_mana_append(name, changed)
        with self.assertRaises(AssertionError):
            guard.historical_document_before_land_mana_append('docs/future.md', b'')

    def test_inherited_modules_rules_evidence_data_and_gates_are_exact(self):
        for name, digest in PROTECTED_SHA256.items():
            with self.subTest(path=name):
                path = ROOT / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(path.stat().st_mode & 0o111, 0)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_historical_actual_owning_contract_identities_and_output_parity(self):
        from card_rules_pilot import behavior as b, behavior_policy as bp
        from card_rules_pilot import behavior_context as bc, contract as c
        from card_rules_pilot import cards, pilot, reasoning_policy as cp
        from test_card_rules_pilot_cards import current_catalog_intact
        # Publication changes the actual catalog. It must reject; a historical
        # positive fixture is never installed for either current land or pilot.
        arguments = dict(catalog_root=ROOT, mechanical_root=ROOT,
            review_root=ROOT / 'reference-reviews',
            plan_path=ROOT / 'data/review/card-rules-mana-pilot/plan.json',
            successor_root=ROOT / 'data/review/mana-context-reassessment',
            expected_profile_id=cards.PROFILE_ID,
            expected_query_snapshot_id=cards.QUERY_ID, expected_plan_id=pilot.PLAN_ID)
        self.assertEqual(c.identity(cp.POLICY_VERSION, cp.policy_document(), 'policy_id'),
            'sha256:5694ec96c5edcbe61895684c6885e556578b738f27a29154d95283542b1ed745')
        self.assertEqual(c.identity(bp.POLICY_VERSION, bp.policy_document(), 'policy_id'),
            'sha256:2b7ab1a82da6ba0f09a59d8fa39d6fcbf9f6ff4279e1348e2f4b319466b7df39')
        if not current_catalog_intact(self):
            with self.assertRaises(ValueError):
                b.load_behavior(**arguments)
            return
        captured = []
        admission = b.admit_context
        def capture(**kwargs):
            captured.append(kwargs['successor'])
            return admission(**kwargs)
        with patch.object(b, 'admit_context', side_effect=capture):
            consumer = b.load_behavior(**arguments)
        actual = consumer.comparison()
        value = actual.to_dict()
        self.assertEqual(c.identity(b.REPORT_VERSION, value, 'report_id'),
            'sha256:722c2ba02468aa1d81a2f5f7de6b43913483bfedeb7873130d14cc6634b19a0f')
        self.assertEqual(len(actual.to_json().encode()), 571141)
        self.assertEqual(hashlib.sha256(actual.to_json().encode()).hexdigest(),
            '517fdf194ccdb326e53882ea8deecefb1d15fa81e41a5240802e6802eefd7489')
        context = value['context']['retained_rules']
        self.assertEqual(c.identity(bc.CONTEXT_VERSION, context, 'context_id'),
            'sha256:bfe54406c0ed5df672dbda7b9f6a376bd823070ea301ff54595f6ab37ed2265e')
        successor = captured[0].comparison().to_dict()
        self.assertEqual(c.identity(successor['schema_version'], successor, 'report_id'),
            'sha256:51ab182ea464d9374be53cd5d77a6cc76b6cc5210af168f4eb6b2afb2a2e2cb9')
        self.assertEqual(context['historical_acquisition_identity'],
            'sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53')
        original = value['context']['original_comparison']
        for candidate in original['candidates']:
            candidate['rules_evidence'] = value['context']['shared_original_rules_evidence']
        self.assertEqual(c.identity(original['schema_version'], original, 'report_id'), original['report_id'])
        self.assertEqual(len(c.canonical(original)), 740979)
        self.assertEqual(hashlib.sha256(c.canonical(original)).hexdigest(),
            'e7f2e4b75131845e9b04a73f2cade86a225f4ec013a1797633cbb1bd669eeb70')


if __name__ == '__main__':
    unittest.main()
