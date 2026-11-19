"""Approved single-section vision change and fail-closed historical reconstruction."""
import copy
import hashlib
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import documentation_continuity_preservation as original
import proactive_vision_preservation as guard
import vision_alignment_preservation as previous

ROOT = Path(__file__).resolve().parents[1]
PRIORITIZATION = ('The system should prioritize investigations according to their potential strategic '
    'significance, novelty, evidentiary strength, uncertainty, and expected value of further research, '
    'while recognizing when an investigation should be deferred, stopped, or revisited.')
UNCHANGED_SHA256 = {'docs/ARCHITECTURE.md': 'c4651ad45e47ff9a247151a9c4ca54e8e7dd18b23725cec0571039ef676284b3',
 'docs/DECISIONS.md': '47e1fc0e4353f251dde4fb316ec79642a3ab3d51fc0dcc6613b49a795ead73db',
 'docs/GOVERNANCE.md': 'c88e696509ab99abae60c9b8aa63e3f9d79cef92f7814989cb91c46b659fa819',
 'docs/RESEARCH_LOG_ARCHITECTURE.md': '0bcd1637e7dc29c51f510e16c38184bf57343f69d0a2faeb6b8858b15dc9d79e',
 'docs/ROADMAP.md': '2e1585cb6c6edd91d86489be55002784106b179c7e71f56e502cad087cc9417c'}


class ProactiveResearchVisionTests(unittest.TestCase):
    def test_single_section_in_exact_approved_location(self):
        text = (ROOT/'VISION.md').read_text()
        title = '### Proactive Research Intelligence\n'
        self.assertEqual(text.count(title), 1)
        self.assertLess(text.index('## Ultimate research vision'), text.index(title))
        self.assertLess(text.index('### AI Tutoring and Interactive Laboratory'), text.index(title))
        self.assertLess(text.index(title), text.index('### Research and Experimentation'))
        section = text[text.index(title):text.index('### Research and Experimentation')]
        self.assertEqual(section.count(PRIORITIZATION), 1)
        self.assertEqual(text[text.index('### AI Tutoring and Interactive Laboratory'):text.index(title)].count('### '), 1)

    def test_complete_requirement_and_non_authorization_boundaries(self):
        text = (ROOT/'VISION.md').read_text()
        section = text[text.index('### Proactive Research Intelligence'):text.index('### Research and Experimentation')]
        for phrase in ('New cards and set previews', 'Emerging interactions and strategies',
            'Format and rules changes', 'Tournament results and metagame shifts',
            'Reprints, product releases and market developments', 'previously recorded research hypotheses',
            'Detecting and verifying', 'Card identities, mechanics and evidence', 'testable hypotheses',
            'authorized analytical tools', 'investigating counterexamples', 'own preliminary conclusions',
            'evidence, experiments and reassessments', 'Research Log architecture',
            'findings and uncertainties', 'research interests', 'notification preferences', 'frequency',
            'significance thresholds', 'privacy and authorized external actions',
            'AI-generated hypotheses', 'verified facts and supported', 'competing canonical authority',
            'deterministic analytical results', 'source-use permissions', 'computational budgets',
            'privacy restrictions, stopping conditions and publication controls',
            'cards,\ninteractions or strategies before widespread recognition',
            'verifiable\nevidence and later real-world validation', 'not a present capability',
            'not a present capability, a\nprerequisite', 'implementation authorization',
            'does not claim that the\ncapability already exists or authorize'):
            self.assertIn(phrase, section)

    def test_removing_exact_insertion_preserves_every_prior_vision_byte(self):
        raw = (ROOT/'VISION.md').read_bytes();old = guard.restore('VISION.md', raw)
        self.assertEqual(guard.pin(old), dict(bytes=7094,
            sha256='66a345656e2c51506d01dd458e83971b492792fda0fb74e241eb0013e975268e'))
        edit = guard.PINS['VISION.md']['edit']
        self.assertTrue(raw[edit['start']:edit['end']].startswith(b'### Proactive Research Intelligence\n'))
        self.assertEqual(raw[:edit['start']]+raw[edit['end']:], old)

    def test_exact_three_successors_and_old_bytes_are_idempotent(self):
        self.assertEqual(set(guard.PINS), {'VISION.md', 'tests/vision_alignment_preservation.py',
                                         'tests/test_vision_alignment.py'})
        for name, expected in guard.PINS.items():
            raw = (ROOT/name).read_bytes();self.assertEqual(guard.pin(raw), expected['new'])
            old = guard.restore(name, raw);self.assertEqual(guard.pin(old), expected['old'])
            self.assertEqual(guard.restore(name, old), old)
            self.assertEqual(expected['new']['bytes']-expected['old']['bytes'],
                             expected['edit']['end']-expected['edit']['start'])

    def test_original_pins_and_predecessor_chain_remain_authoritative(self):
        self.assertEqual(original.LEDGER_SHA256,
            '1028116c72b31751ac6e4aba4d5ae4fe477d43264b928225603f332fb0985057')
        self.assertEqual(previous.PINS['VISION.md']['new'], guard.PINS['VISION.md']['old'])
        current = (ROOT/'VISION.md').read_bytes();old = guard.restore('VISION.md', current)
        self.assertEqual(previous.restore('VISION.md', current), previous.restore('VISION.md', old))
        self.assertEqual(guard.pin(previous.restore('VISION.md', current)), original.ledger()['additions']['VISION.md'])
        ancestor = previous.restore('VISION.md', old)
        self.assertEqual(guard.restore('VISION.md', ancestor), ancestor)
        with self.assertRaises(AssertionError):guard.restore('VISION.md', ancestor+b'future')

    def test_unrecognized_edits_old_and_new_bytes_and_bad_types_reject(self):
        for name, expected in guard.PINS.items():
            raw = (ROOT/name).read_bytes();old = guard.restore(name, raw)
            for value in (raw+b'future', raw[:-1], b'X'+raw[1:], raw+raw,
                          old+b'future', b'X'+old[1:], bytearray(raw), None, True):
                with self.subTest(path=name), self.assertRaises(AssertionError):guard.restore(name, value)
            start = expected['edit']['start'];bad = raw[:start]+b'X'+raw[start+1:]
            with self.assertRaises(AssertionError):guard.restore(name, bad)

    def test_coherently_rehashed_or_expanded_pins_are_not_approval(self):
        name = 'VISION.md';raw = (ROOT/name).read_bytes();forged = copy.deepcopy(guard.PINS)
        start = forged[name]['edit']['start'];bad = raw[:start]+b'X'+raw[start+1:]
        forged[name]['new'] = guard.pin(bad)
        edit = forged[name]['edit'];edit['new_sha256'] = hashlib.sha256(bad[edit['start']:edit['end']]).hexdigest()
        with patch.object(guard, 'PINS', forged), self.assertRaises(AssertionError):guard.restore(name, bad)
        forged = copy.deepcopy(guard.PINS);forged['docs/GOVERNANCE.md'] = forged[name]
        with patch.object(guard, 'PINS', forged), self.assertRaises(AssertionError):guard.restore(name, raw)
        with patch.object(guard, 'PINS_SHA256', '0'*64), self.assertRaises(AssertionError):guard.restore(name, raw)

    def test_unrelated_sources_cannot_be_exempted(self):
        for name in ('docs/GOVERNANCE.md', 'src/gameplay_rules/engine.py', 'docs/ROADMAP.md'):
            raw = (ROOT/name).read_bytes();self.assertEqual(guard.preceding_bytes(name, raw), raw)
            with self.assertRaises(AssertionError):guard.restore(name, raw)
        for name in (None, Path('VISION.md')):
            with self.assertRaises(AssertionError):guard.preceding_bytes(name, b'')

    def test_governing_documents_and_research_log_are_byte_identical(self):
        for name, expected in UNCHANGED_SHA256.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(len(UNCHANGED_SHA256), 5)

    def test_relative_links_and_enduring_scope_are_preserved(self):
        text = (ROOT/'VISION.md').read_text()
        for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)', text):self.assertTrue((ROOT/target).is_file(), target)
        for phrase in ('## First useful release', 'separate Project Owner approval',
                       '### Evidence-Backed Discovery', '## Enduring boundaries',
                       'Nothing in this vision authorizes implementation'):
            self.assertIn(phrase, text)
        self.assertNotRegex(text, r'PR\s*#\d|\b\d+%|Structural Inventory V1')


if __name__ == '__main__':unittest.main()
