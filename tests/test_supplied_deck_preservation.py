"""Exact compatibility, owning boundaries and golden analytical workflow."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import supplied_deck_preservation as guard


class SuppliedDeckPreservationTests(unittest.TestCase):
    def test_only_three_additions_and_three_exact_reversible_successors(self):
        self.assertEqual(len(guard.ADDITIONS),3);self.assertEqual(len(guard.REPLACEMENTS),3)
        for name,row in guard.ledger()['replacements'].items():
            from resource_assignment_preservation import preceding_bytes as resource_preceding
            raw=resource_preceding(name,(guard.ROOT/name).read_bytes());old=guard.preceding_bytes(name,raw)
            self.assertEqual(guard.pin(raw),row['new']);self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for invalid in (b'X'+raw[1:],raw+b'future',raw[:-1],bytearray(raw),None):
                with self.subTest(name=name),self.assertRaises(AssertionError):guard.preceding_bytes(name,invalid)

    def test_each_addition_is_hash_pinned_and_neighbors_stay_visible(self):
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT/name))
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);p=root/name;p.parent.mkdir(parents=True)
                raw=(guard.ROOT/name).read_bytes();p.write_bytes(raw)
                self.assertTrue(guard.is_addition(p,root))
                p.write_bytes(raw+b'future')
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.write_bytes(raw);p.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.chmod(0o644);p.unlink();p.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/probability/future.py'))
        self.assertFalse(guard.is_addition(guard.ROOT/'src/gameplay_rules/engine.py'))

    def test_coherent_ledger_changes_and_predecessor_rewrites_refuse(self):
        value=copy.deepcopy(guard.ledger());name='src/probability/__main__.py'
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'ledger.json';p.write_text(json.dumps(value)+' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()
        raw=b'X'+(guard.ROOT/name).read_bytes()[1:];value['replacements'][name]['new']=guard.pin(raw)
        with patch.object(guard,'ledger',return_value=value),self.assertRaises(AssertionError):guard.preceding_bytes(name,raw)

    def test_prior_compatibility_ledgers_and_probability_kernels_remain_exact(self):
        import pack_odds_preservation as previous
        import draw_access_preservation as draw
        self.assertEqual(previous.LEDGER_SHA256,'c195d944bb7fa672207d476de919da721ec30ca901e896adcc0ca4269a0de946')
        self.assertEqual(draw.LEDGER_SHA256,'b9805847403bd97cd42a081123cc59032e5c516c2ffe62526ef640912a16ec16')
        self.assertEqual(guard.pin((guard.ROOT/'src/probability/pack_odds.py').read_bytes()),previous.ledger()['additions']['src/probability/pack_odds.py'])
        self.assertEqual(guard.pin((guard.ROOT/'src/probability/draw_access.py').read_bytes()),draw.ledger()['additions']['src/probability/draw_access.py'])
        for name in ('VISION.md','docs/GOVERNANCE.md','docs/ARCHITECTURE.md','docs/DECISIONS.md'):
            raw=(guard.ROOT/name).read_bytes();self.assertEqual(guard.preceding_bytes(name,raw),raw)
        for name in guard.ADDITIONS:self.assertTrue(draw.is_addition(guard.ROOT/name))

    def test_consumer_has_no_repository_collection_source_or_gameplay_access(self):
        tree=ast.parse((guard.ROOT/'src/probability/supplied_deck.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):self.assertIn(node.module,{'fractions','hashlib','draw_access'})
            if isinstance(node,ast.Import):self.assertTrue(all(x.name=='json' for x in node.names))
        source=(guard.ROOT/'src/probability/supplied_deck.py').read_text()
        self.assertNotIn('comb(',source);self.assertNotIn('CanonicalRepository',source)

    def test_complete_fictional_example_and_golden_json_text_are_reproduced(self):
        from probability.supplied_deck import parse_supplied_decks,assess_supplied_decks,render_supplied_decks
        p=guard.ROOT/'tests/fixtures/supplied_deck_consistency_v1'
        r=assess_supplied_decks(parse_supplied_decks((p/'example-input.json').read_bytes()))
        self.assertEqual(render_supplied_decks(r),(p/'example-report.json').read_text())
        self.assertEqual(render_supplied_decks(r,readable=True),(p/'example-report.txt').read_text())

    def test_new_capability_document_links_resolve(self):
        p=guard.ROOT/'docs/SUPPLIED_DECK_CONSISTENCY_V1.md'
        for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)',p.read_text()):
            self.assertTrue((p.parent/target).exists(),target)


if __name__=='__main__':unittest.main()
