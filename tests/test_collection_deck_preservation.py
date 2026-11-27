"""Exact successor proofs, source isolation and reproducible fictional reports."""
import ast
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import collection_deck_preservation as guard


class CollectionDeckPreservationTests(unittest.TestCase):
    def test_exact_named_additions_and_four_source_successors(self):
        self.assertEqual(len(guard.ADDITIONS),3);self.assertEqual(len(guard.REPLACEMENTS),4)
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes();old=guard.preceding_bytes(name,raw)
            self.assertEqual(guard.pin(raw),row['new']);self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for altered in (raw+b'future',raw[:-1],b'X'+raw[1:],bytearray(raw),None):
                with self.subTest(name=name),self.assertRaises(AssertionError):guard.preceding_bytes(name,altered)

    def test_hash_mode_symlink_and_neighbor_guards_fail_closed(self):
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT/name))
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);path=root/name;path.parent.mkdir(parents=True)
                raw=(guard.ROOT/name).read_bytes();path.write_bytes(raw)
                self.assertTrue(guard.is_addition(path,root));path.write_bytes(raw+b'future')
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
                path.write_bytes(raw);path.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
                path.chmod(0o644);path.unlink();path.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/collection/unapproved.py'))

    def test_coherent_new_hash_cannot_replace_historical_bytes(self):
        value=copy.deepcopy(guard.ledger());name='src/mtglab/__main__.py'
        raw=b'X'+(guard.ROOT/name).read_bytes()[1:];value['replacements'][name]['new']=guard.pin(raw)
        with patch.object(guard,'ledger',return_value=value),self.assertRaises(AssertionError):guard.preceding_bytes(name,raw)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'ledger.json';path.write_text(json.dumps(value))
            with patch.object(guard,'LEDGER',path),self.assertRaises(AssertionError):guard.ledger()

    def test_existing_pin_chains_and_original_algorithms_remain_authoritative(self):
        import supplied_deck_preservation as prior
        import draw_access_preservation as draw
        import pack_odds_preservation as pack
        self.assertEqual(prior.LEDGER_SHA256,'0703ef4afbc95d0ac0877807236e967a1b4e54c374fd7ed2cc768ef96004d019')
        self.assertEqual(guard.pin((guard.ROOT/'src/probability/supplied_deck.py').read_bytes()),prior.ledger()['additions']['src/probability/supplied_deck.py'])
        self.assertEqual(guard.pin((guard.ROOT/'src/probability/draw_access.py').read_bytes()),draw.ledger()['additions']['src/probability/draw_access.py'])
        self.assertEqual(guard.pin((guard.ROOT/'src/probability/pack_odds.py').read_bytes()),pack.ledger()['additions']['src/probability/pack_odds.py'])
        for name in guard.ADDITIONS:self.assertTrue(draw.is_addition(guard.ROOT/name))
        for name in ('VISION.md','docs/GOVERNANCE.md','docs/ARCHITECTURE.md','docs/DECISIONS.md'):
            from candidate_mana_preservation import preceding_bytes as candidate_preceding
            raw=candidate_preceding(name,(guard.ROOT/name).read_bytes());self.assertEqual(guard.preceding_bytes(name,raw),raw)

    def test_consumer_calls_owners_without_probability_or_allocation_reconstruction(self):
        source=(guard.ROOT/'src/collection/deck_analysis.py').read_text();tree=ast.parse(source)
        self.assertNotIn('comb(',source);self.assertNotIn('remaining[',source);self.assertNotIn('CanonicalRepository',source)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                self.assertIn(node.module,{'collections','hashlib','pathlib','probability.draw_access','probability.supplied_deck','query','audit','intelligence'})
        pure=(guard.ROOT/'src/probability/supplied_deck.py').read_text()
        self.assertNotIn('collection.',pure)

    def test_complete_fictional_example_reproduces_json_text_and_source_bindings(self):
        from test_collection_deck_analysis import CollectionDeckAnalysisTests
        from collection.deck_analysis import render_collection_decks
        case=CollectionDeckAnalysisTests();case.setUp()
        try:
            p=guard.ROOT/'tests/fixtures/collection_deck_analysis_v1';r=case.run_analysis()
            self.assertEqual(render_collection_decks(r),(p/'example-report.json').read_text())
            self.assertEqual(render_collection_decks(r,readable=True),(p/'example-report.txt').read_text())
            self.assertEqual(case.source.read_bytes(),(p/case.source.name).read_bytes())
        finally:case.doCleanups()

    def test_direct_document_links_resolve(self):
        p=guard.ROOT/'docs/COLLECTION_DECK_ANALYSIS_V1.md'
        for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)',p.read_text()):self.assertTrue((p.parent/target).exists(),target)


if __name__=='__main__':unittest.main()
