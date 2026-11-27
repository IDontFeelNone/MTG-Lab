"""Approved vision refinements and exact PR #242 predecessor compatibility."""
import copy
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import documentation_continuity_preservation as original
import vision_alignment_preservation as guard
from candidate_mana_preservation import preceding_bytes as candidate_preceding


ROOT = Path(__file__).resolve().parents[1]


class VisionAlignmentTests(unittest.TestCase):
    def test_only_two_named_successors_restore_exact_predecessors(self):
        self.assertEqual(set(guard.PINS), {'VISION.md', 'tests/test_documentation_continuity.py'})
        for name, expected in guard.PINS.items():
            with self.subTest(path=name):
                raw = (ROOT / name).read_bytes()
                from proactive_vision_preservation import preceding_bytes
                raw = preceding_bytes(name, raw)
                self.assertEqual(guard.pin(raw), expected['new'])
                old = guard.restore(name, raw)
                self.assertEqual(guard.pin(old), expected['old'])
                self.assertEqual(guard.restore(name, old), old)
                if name == 'VISION.md':
                    self.assertEqual(guard.pin(old), original.ledger()['additions'][name])

    def test_unrecognized_edits_and_malformed_inputs_reject(self):
        for name in guard.PINS:
            raw = (ROOT / name).read_bytes()
            for changed in (raw + b'future\n', raw[:-1], b'X' + raw[1:],
                            bytearray(raw), None, True):
                with self.subTest(path=name, kind=type(changed).__name__), self.assertRaises(AssertionError):
                    guard.restore(name, changed)
        for name in ('docs/GOVERNANCE.md', 'src/gameplay_rules/engine.py', Path('VISION.md'), None):
            with self.subTest(path=name), self.assertRaises(AssertionError):
                guard.restore(name, b'')

    def test_coherent_successor_rehash_cannot_change_historical_text(self):
        raw = (ROOT / 'VISION.md').read_bytes()
        changed = b'X' + raw[1:]
        forged = copy.deepcopy(guard.PINS)
        forged['VISION.md']['new'] = guard.pin(changed)
        with patch.object(guard, 'PINS', forged), self.assertRaises(AssertionError):
            guard.restore('VISION.md', changed)

    def test_exact_span_check_cannot_be_bypassed_by_a_changed_edit(self):
        raw = (ROOT / 'VISION.md').read_bytes()
        forged = copy.deepcopy(guard.PINS)
        forged['VISION.md']['edits'][-1]['start'] += 1
        with patch.object(guard, 'PINS', forged), self.assertRaises(AssertionError):
            guard.restore('VISION.md', raw)

    def test_unrelated_bytes_remain_subject_to_their_existing_contract(self):
        raw = candidate_preceding('docs/GOVERNANCE.md', (ROOT / 'docs/GOVERNANCE.md').read_bytes())
        self.assertEqual(guard.preceding_bytes('docs/GOVERNANCE.md', raw), raw)
        self.assertEqual(guard.pin(raw), original.ledger()['additions']['docs/GOVERNANCE.md'])
        with self.assertRaises(AssertionError):
            guard.preceding_bytes('VISION.md', bytearray(raw))

    def test_approved_ai_accessibility_and_product_origin_are_explicit(self):
        text = (ROOT / 'VISION.md').read_text()
        for phrase in ('analytical foundation for ChatGPT', 'booster-pack probability questions',
                       'accessible, AI-powered application', 'without programming knowledge',
                       'If ChatGPT, Untapped.gg, Moxfield,', 'requirement to reproduce those applications',
                       'ChatGPT-accessible analytical capabilities', 'built-in AI',
                       'verified knowledge and analytical', 'competing source of canonical truth',
                       'not approved implementation requirements'):
            self.assertIn(phrase, text)

    def test_gameplay_and_competitive_ambitions_are_bounded(self):
        text = (ROOT / 'VISION.md').read_text()
        for phrase in ('autonomous gameplay and full-game simulation', 'long-term research ambitions',
                       'not intended to recreate MTG Arena', 'not prerequisites for the first useful release',
                       'deck consistency, win-condition probabilities, disruption, matchup',
                       'analysis and strategy evaluation', 'format-specific',
                       'turn-six performance is not a', 'universal competitive benchmark'):
            self.assertIn(phrase, text)

    def test_research_history_and_authorization_remain_separate(self):
        text = (ROOT / 'VISION.md').read_text()
        for phrase in ('dated hypotheses, original evidence', 'experiment versions and later validation',
                       'sleeper-card discovery preceded widespread recognition',
                       'does not authorize expanding the present engineering scope',
                       'Enduring product requirements', 'proposed technical', 'deferred features',
                       'aspirational research capabilities', 'Nothing in this vision authorizes implementation'):
            self.assertIn(phrase, text)
        self.assertNotRegex(text, r'PR\s*#\d|\b\d+%|Structural Inventory V1')

    def test_current_vision_relative_links_are_valid(self):
        text = (ROOT / 'VISION.md').read_text()
        for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)', text):
            self.assertFalse(target.startswith(('http://', 'https://')))
            self.assertTrue((ROOT / target).is_file(), target)


if __name__ == '__main__':
    unittest.main()
