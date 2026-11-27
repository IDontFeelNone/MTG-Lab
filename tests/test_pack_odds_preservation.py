"""Fail-closed successor reconstruction and historical runtime/source isolation."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import pack_odds_preservation as guard


class PackOddsPreservationTests(unittest.TestCase):
    def test_exact_runtime_addition_and_four_reversible_successors(self):
        self.assertEqual(guard.ADDITIONS, {'src/probability/pack_odds.py'})
        self.assertEqual(len(guard.REPLACEMENTS), 4)
        for name, row in guard.ledger()['replacements'].items():
            raw = (guard.ROOT / name).read_bytes()
            from supplied_deck_preservation import preceding_bytes
            raw = preceding_bytes(name, raw)
            self.assertEqual(guard.pin(raw), row['new'])
            old = guard.preceding_bytes(name, raw)
            self.assertEqual(guard.pin(old), row['old'])
            self.assertEqual(guard.preceding_bytes(name, old), old)
            for invalid in (raw + b'future', b'X' + raw[1:], raw[:-1], bytearray(raw), None):
                with self.subTest(name=name), self.assertRaises(AssertionError): guard.preceding_bytes(name, invalid)

    def test_named_addition_modes_tampering_and_unrecognized_neighbors(self):
        name = 'src/probability/pack_odds.py'
        self.assertTrue(guard.is_addition(guard.ROOT / name))
        for invalid in (name + '.future', 'src/simulation/future.py', 'src/gameplay_rules/engine.py'):
            self.assertFalse(guard.is_addition(guard.ROOT / invalid))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root / name; path.parent.mkdir(parents=True)
            raw = (guard.ROOT / name).read_bytes(); path.write_bytes(raw)
            self.assertTrue(guard.is_addition(path, root))
            path.write_bytes(raw + b'future')
            with self.assertRaises(AssertionError): guard.is_addition(path, root)
            path.write_bytes(raw); path.chmod(0o744)
            with self.assertRaises(AssertionError): guard.is_addition(path, root)
            path.chmod(0o644); path.unlink(); path.symlink_to(guard.ROOT / name)
            with self.assertRaises(AssertionError): guard.is_addition(path, root)

    def test_coherently_rehashed_ledger_is_not_a_new_authorization(self):
        value = guard.ledger(); value['additions']['src/probability/pack_odds.py']['sha256'] = '0' * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.json'; path.write_text(json.dumps(value))
            with patch.object(guard, 'LEDGER', path), self.assertRaises(AssertionError): guard.ledger()

    def test_coherent_successor_hash_cannot_rewrite_historical_source(self):
        value = copy.deepcopy(guard.ledger()); name = 'src/simulation/pack.py'
        raw = b'X' + (guard.ROOT / name).read_bytes()[1:]
        value['replacements'][name]['new'] = guard.pin(raw)
        with patch.object(guard, 'ledger', return_value=value), self.assertRaises(AssertionError): guard.preceding_bytes(name, raw)

    def test_each_source_successor_uses_existing_historical_chains(self):
        from pack_simulation_preservation import preceding_bytes as pack_preceding
        from draw_access_preservation import is_addition, preceding_bytes
        for name in ('src/simulation/pack.py', 'src/probability/__main__.py'):
            raw = (guard.ROOT / name).read_bytes(); old = guard.preceding_bytes(name, raw)
            self.assertEqual(pack_preceding(name, raw), pack_preceding(name, old))
            self.assertEqual(preceding_bytes(name, raw), old)
        self.assertTrue(is_addition(guard.ROOT / 'src/probability/pack_odds.py'))
        self.assertTrue(is_addition(guard.ROOT / 'src/probability/__main__.py'))

    def test_earlier_ledgers_and_deck_calculation_source_stay_byte_exact(self):
        import draw_access_preservation as previous
        self.assertEqual(previous.LEDGER_SHA256, 'b9805847403bd97cd42a081123cc59032e5c516c2ffe62526ef640912a16ec16')
        for name in ('src/probability/draw_access.py', 'VISION.md', 'docs/ARCHITECTURE.md', 'docs/DECISIONS.md'):
            from candidate_mana_preservation import preceding_bytes as candidate_preceding
            raw = candidate_preceding(name, (guard.ROOT / name).read_bytes())
            self.assertEqual(guard.preceding_bytes(name, raw), raw)
        raw = (guard.ROOT / 'src/probability/draw_access.py').read_bytes()
        self.assertEqual(guard.pin(raw), previous.ledger()['additions']['src/probability/draw_access.py'])

    def test_probability_consumer_uses_public_view_without_competing_repository(self):
        source = (guard.ROOT / 'src/probability/pack_odds.py').read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, {'fractions', 'hashlib', 'simulation.pack', 'draw_access'})
            if isinstance(node, ast.Import): self.assertTrue(all(v.name in {'json', 're'} for v in node.names))
            if isinstance(node, ast.Attribute): self.assertNotEqual(node.attr, '_query')
        self.assertNotIn('CanonicalRepository', source)

    def test_new_document_relative_links_resolve(self):
        path = guard.ROOT / 'docs/EXACT_PACK_TARGET_ODDS_V1.md'
        for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)', path.read_text()):
            self.assertTrue((path.parent / target).is_file(), target)


if __name__ == '__main__':
    unittest.main()
