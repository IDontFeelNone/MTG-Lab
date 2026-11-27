"""Narrow reversible historical view; no arbitrary additions or rebaselining."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import draw_access_preservation as guard


class DrawAccessPreservationTests(unittest.TestCase):
    def test_exact_two_new_source_files_and_original_probability_init(self):
        self.assertEqual(guard.ADDITIONS, {'src/probability/draw_access.py', 'src/probability/__main__.py'})
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT / name))
            self.assertFalse(guard.is_addition(guard.ROOT / (name + '.future')))
        raw = (guard.ROOT / 'src/probability/__init__.py').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), 'fc77acf2a428b69fcd8bb38e4ba6cb900b6f269effa38a78c0bd618e435e0c6f')
        self.assertFalse(guard.is_addition(guard.ROOT / 'src/gameplay_rules/engine.py'))

    def test_source_tampering_modes_and_symlinks_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); name = sorted(guard.ADDITIONS)[0]
            path = root / name; path.parent.mkdir(parents=True)
            raw = (guard.ROOT / name).read_bytes(); path.write_bytes(raw)
            self.assertTrue(guard.is_addition(path, root))
            path.write_bytes(raw + b'future')
            with self.assertRaises(AssertionError): guard.is_addition(path, root)
            path.write_bytes(raw); path.chmod(0o744)
            with self.assertRaises(AssertionError): guard.is_addition(path, root)
            path.chmod(0o644); path.unlink(); path.symlink_to(guard.ROOT / name)
            with self.assertRaises(AssertionError): guard.is_addition(path, root)

    def test_five_successors_reverse_to_exact_canonical_baselines(self):
        for name, row in guard.ledger()['replacements'].items():
            raw = (guard.ROOT / name).read_bytes()
            from mtgjson_evidence_preservation import preceding_bytes as evidence_preceding
            self.assertEqual(guard.pin(evidence_preceding(name, raw)), row['new'])
            original = guard.preceding_bytes(name, raw)
            self.assertEqual(guard.pin(original), row['old'])
            self.assertEqual(guard.preceding_bytes(name, original), original)
            for invalid in (raw + b'future', b'X' + raw[1:], raw[:-1], bytearray(raw), None):
                with self.subTest(name=name), self.assertRaises(AssertionError): guard.preceding_bytes(name, invalid)

    def test_coherently_rehashed_manifest_is_not_authorized(self):
        value = guard.ledger()
        value['additions']['src/probability/draw_access.py']['sha256'] = '0' * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.json'; path.write_text(json.dumps(value))
            with patch.object(guard, 'LEDGER', path), self.assertRaises(AssertionError): guard.ledger()

    def test_coherent_successor_rehash_cannot_rewrite_historical_text(self):
        value = copy.deepcopy(guard.ledger())
        name = 'tests/test_rules_card_integration_design.py'
        raw = b'X' + (guard.ROOT / name).read_bytes()[1:]
        value['replacements'][name]['new'] = guard.pin(raw)
        with patch.object(guard, 'ledger', return_value=value), self.assertRaises(AssertionError): guard.preceding_bytes(name, raw)

    def test_existing_predecessor_contracts_still_receive_their_exact_bytes(self):
        from documentation_continuity_preservation import preceding_bytes
        from pack_simulation_preservation import preceding_bytes as pack_preceding
        name = 'tests/test_rules_card_integration_design.py'
        raw = (guard.ROOT / name).read_bytes()
        old = guard.preceding_bytes(name, raw)
        self.assertEqual(pack_preceding(name, raw), pack_preceding(name, old))
        self.assertEqual(preceding_bytes(name, raw), old)
        for name in ('src/query/engine.py', 'VISION.md', 'docs/ARCHITECTURE.md'):
            from factual_admission_preservation import preceding_bytes as admission_preceding
            raw = admission_preceding(name, (guard.ROOT / name).read_bytes())
            self.assertEqual(guard.preceding_bytes(name, raw), raw)

    def test_new_runtime_imports_only_standard_library_and_own_package(self):
        for name in guard.ADDITIONS:
            from pack_odds_preservation import preceding_bytes
            tree = ast.parse(preceding_bytes(name, (guard.ROOT / name).read_bytes()).decode())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(x.name.split('.')[0] in {'argparse', 'json', 'sys'} for x in node.names))
                if isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module, {'decimal', 'fractions', 'hashlib', 'itertools', 'math', 'pathlib', 'draw_access'})

    def test_new_document_relative_links_resolve(self):
        import re
        path = guard.ROOT / 'docs/EXACT_DECK_DRAW_ACCESS_V1.md'
        for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)', path.read_text()):
            self.assertTrue((path.parent / target).is_file(), target)


if __name__ == '__main__':
    unittest.main()
