"""Exact successor reconstruction, negative preservation and golden parity."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from probability.resource_assignment import assess_resource_assignment
from probability.draw_access import canonical_json
import resource_assignment_preservation as guard


class ResourceAssignmentPreservationTests(unittest.TestCase):
    def test_exact_additions_and_three_reversible_successors(self):
        self.assertEqual(len(guard.ADDITIONS), 2)
        self.assertEqual(len(guard.REPLACEMENTS), 3)
        for name, row in guard.ledger()['replacements'].items():
            from candidate_mana_preservation import preceding_bytes as candidate_preceding
            raw = candidate_preceding(name, (guard.ROOT / name).read_bytes())
            self.assertEqual(guard.pin(raw), row['new'])
            old = guard.preceding_bytes(name, raw)
            self.assertEqual(guard.pin(old), row['old'])
            self.assertEqual(guard.preceding_bytes(name, old), old)
            for invalid in (b'X' + raw[1:], raw + b'future', raw[:-1], bytearray(raw), None):
                with self.subTest(name=name), self.assertRaises(AssertionError):
                    guard.preceding_bytes(name, invalid)

    def test_tampering_modes_symlinks_and_neighbors_fail_closed(self):
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT / name))
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory); path = root / name; path.parent.mkdir(parents=True)
                original = (guard.ROOT / name).read_bytes(); path.write_bytes(original)
                self.assertTrue(guard.is_addition(path, root))
                path.write_bytes(original + b'future')
                with self.assertRaises(AssertionError): guard.is_addition(path, root)
                path.write_bytes(original); path.chmod(0o744)
                with self.assertRaises(AssertionError): guard.is_addition(path, root)
                path.chmod(0o644); path.unlink(); path.symlink_to(guard.ROOT / name)
                with self.assertRaises(AssertionError): guard.is_addition(path, root)
        self.assertFalse(guard.is_addition(guard.ROOT / 'src/probability/future.py'))
        self.assertFalse(guard.is_addition(guard.ROOT / 'src/gameplay_rules/engine.py'))

    def test_rehashed_successor_cannot_change_historical_text(self):
        value = copy.deepcopy(guard.ledger()); name = 'src/probability/__main__.py'
        raw = b'X' + (guard.ROOT / name).read_bytes()[1:]
        value['replacements'][name]['new'] = guard.pin(raw)
        with patch.object(guard, 'ledger', return_value=value), self.assertRaises(AssertionError):
            guard.preceding_bytes(name, raw)
        value = copy.deepcopy(guard.ledger())
        value['replacements'][name]['edits'][0]['new_sha256'] = '0' * 64
        with patch.object(guard, 'ledger', return_value=value), self.assertRaises(AssertionError):
            guard.preceding_bytes(name, (guard.ROOT / name).read_bytes())

    def test_ledger_changes_are_not_new_authorization(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.json'
            path.write_bytes(guard.LEDGER.read_bytes() + b' ')
            with patch.object(guard, 'LEDGER', path), self.assertRaises(AssertionError): guard.ledger()

    def test_existing_chains_and_kernels_still_authoritative(self):
        import draw_access_preservation as draw
        import pack_odds_preservation as pack
        import supplied_deck_preservation as supplied
        import collection_deck_preservation as collection
        for name, pin in (
            ('src/probability/draw_access.py', draw.ledger()['additions']['src/probability/draw_access.py']),
            ('src/probability/pack_odds.py', pack.ledger()['additions']['src/probability/pack_odds.py']),
            ('src/probability/supplied_deck.py', supplied.ledger()['additions']['src/probability/supplied_deck.py']),
            ('src/collection/deck_analysis.py', collection.ledger()['additions']['src/collection/deck_analysis.py'])):
            self.assertEqual(guard.pin((guard.ROOT / name).read_bytes()), pin)
        for name in guard.ADDITIONS: self.assertTrue(draw.is_addition(guard.ROOT / name))
        for name in ('VISION.md', 'docs/GOVERNANCE.md', 'docs/ARCHITECTURE.md', 'docs/DECISIONS.md'):
            from candidate_mana_preservation import preceding_bytes as candidate_preceding
            raw = candidate_preceding(name, (guard.ROOT / name).read_bytes())
            self.assertEqual(guard.preceding_bytes(name, raw), raw)
        self.assertEqual(draw.LEDGER_SHA256, 'b9805847403bd97cd42a081123cc59032e5c516c2ffe62526ef640912a16ec16')
        self.assertEqual(pack.LEDGER_SHA256, 'c195d944bb7fa672207d476de919da721ec30ca901e896adcc0ca4269a0de946')

    def test_examples_replay_byte_exactly(self):
        directory = guard.ROOT / 'tests/fixtures/resource_assignment_v1'
        for name in ('fixed', 'flexible'):
            request = json.loads((directory / (name + '.input.json')).read_bytes())
            expected = (directory / (name + '.report.json')).read_bytes()
            self.assertEqual((canonical_json(assess_resource_assignment(request)) + '\n').encode(), expected)

    def test_runtime_has_only_stdlib_and_probability_serialization_dependency(self):
        tree = ast.parse((guard.ROOT / 'src/probability/resource_assignment.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom): self.assertIn(node.module, {'fractions', 'hashlib', 'math', 'draw_access'})
            if isinstance(node, ast.Import): self.assertTrue(all(alias.name == 'json' for alias in node.names))
        source = (guard.ROOT / 'src/probability/resource_assignment.py').read_text()
        for forbidden in ('/workspace/', 'CanonicalRepository', 'open(', 'subprocess', 'random'):
            self.assertNotIn(forbidden, source)

    def test_document_links_resolve(self):
        path = guard.ROOT / 'docs/DECLARED_RESOURCE_ASSIGNMENT_V1.md'
        for link in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)', path.read_text()):
            self.assertTrue((path.parent / link).exists(), link)


if __name__ == '__main__':
    unittest.main()
