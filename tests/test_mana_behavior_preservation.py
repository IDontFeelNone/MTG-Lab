"""Finite consumer additions and exact historical predecessor preservation.

Pins are actual canonical-base Git blobs; this guard admits no new source
package and does not infer source reproduction or semantic authority.
"""
import hashlib
from pathlib import Path
import unittest

import proposed_spell_packet_analysis_preservation as guard
import proposed_spell_packet_authoring_preservation as previous

CANONICAL_MAIN = '2e4f9daef9c9fb18a9b5ec0ab3b35600632face4'
CANONICAL_TREE = '5d007d4e6d05349200f04f64cf2575f5e0693f92'
HISTORICAL_PUBLIC_BOUNDARIES = {'src/card_rules_pilot/__init__.py': '2093c7424b37f6106539fd705bd5f92fad3265e57f91f70b78f6f77b85a25feb',
 'src/card_rules_pilot/__main__.py': 'c8caad5badb9da31d6db5a8b45457a5c4bee4e26b63c333fa77e856b990d427d',
 'src/card_rules_pilot/contract.py': '6ab87a46c13d91b799e1c30e96323898feb08d05ec80d486c4204784d27334e5',
 'src/card_rules_pilot/pilot.py': '4556628ec9e4be09b69b0f11434a3bd1c370c3744dac1f283811d51aaa3e4c31',
 'src/card_rules_pilot/authored.py': '4b6284d25add2069a34b6d6dda37be944296c22d14409a1920225bd719881e88',
 'src/card_rules_pilot/cards.py': '02311cfad0339836064c2235237853c0e3fc39c48db3bb901d37b02e58ccc70c',
 'src/card_rules_pilot/rules.py': 'fb07585c48cb7ca303de57e13ff0817dac34ee5472b6fdd91208670a453d15d7',
 'src/card_rules_pilot/reasoning.py': 'b01435e8180923cef545b19fa713afa153eb634e3a47f950455c01bb8d324f20',
 'src/card_rules_pilot/reasoning_policy.py': '4ebb431fb265fe37223aafe7a8c6829a027019ba1cd0d5abe54f94709a9465bf',
 'src/card_rules_pilot/reassessment.py': 'a98cbc8dd8a59567cbb4a4557f189456533055181726e39ef58e61b296788892',
 'src/card_rules_pilot/reassessment_cli.py': '7a75d87676ca94fe24232498ca36a7712f4b198a47615780d7586cd730d528c1'}


class ManaBehaviorPreservationTests(unittest.TestCase):
    def test_consumer_additions_are_exact_files_without_source_admission(self):
        self.assertEqual(guard.MANA_BEHAVIOR_SOURCE_PATHS, {
            'src/card_rules_pilot/behavior.py',
            'src/card_rules_pilot/behavior_context.py',
            'src/card_rules_pilot/behavior_policy.py',
            'src/card_rules_pilot/behavior_cli.py'})
        for name in guard.MANA_BEHAVIOR_SOURCE_PATHS:
            self.assertTrue(guard.is_packet_analysis_addition(guard.ROOT / name))
            self.assertTrue(previous.is_packet_authoring_addition(guard.ROOT / name))
            self.assertFalse(guard.is_packet_analysis_addition(guard.ROOT / (name + '.future')))
        for name in ('src/card_rules_pilot/behavior_future.py',
                     'src/gameplay_rules/projection/behavior.py',
                     'reference-reviews/mana-behavior/projection.json'):
            self.assertFalse(guard.is_packet_analysis_addition(guard.ROOT / name))

    def test_exact_suffixes_reconstruct_canonical_base_and_reject_drift(self):
        self.assertEqual(set(guard.MANA_BEHAVIOR_DOCUMENT_APPENDICES), set(guard.DOCUMENT_APPENDICES))
        for name, pin in guard.MANA_BEHAVIOR_DOCUMENT_APPENDICES.items():
            with self.subTest(path=name):
                raw = guard.historical_document_before_land_mana_append(
                    name, (guard.ROOT / name).read_bytes())
                old = guard.historical_document_before_mana_behavior_append(name, raw)
                self.assertEqual(len(raw), pin['baseline_bytes'] + pin['appendix_bytes'])
                self.assertEqual(hashlib.sha256(old).hexdigest(), pin['baseline_sha256'])
                self.assertEqual(guard.historical_document_before_mana_behavior_append(name, old), old)
                self.assertEqual(guard.historical_document_before_mana_context_append(name, raw),
                                 guard.historical_document_before_mana_context_append(name, old))
                for altered in (raw + b'future\n', raw[:-1], b'X' + raw[1:],
                                old + b'X' + raw[len(old)+1:], bytearray(raw), True):
                    with self.assertRaises(AssertionError):
                        guard.historical_document_before_mana_behavior_append(name, altered)
        with self.assertRaises(AssertionError):
            guard.historical_document_before_mana_behavior_append('docs/future.md', b'')

    def test_historical_public_boundaries_remain_exact_canonical_blobs(self):
        for name, digest in HISTORICAL_PUBLIC_BOUNDARIES.items():
            with self.subTest(path=name):
                path = guard.ROOT / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(path.stat().st_mode & 0o111, 0)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
