"""Exact application successors, historical algorithms and source isolation."""
import ast
import copy
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import workbench_preservation as guard


class WorkbenchPreservationTests(unittest.TestCase):
    def test_exact_additions_and_reversible_predecessor(self):
        for name in guard.ADDITIONS:self.assertTrue(guard.is_addition(guard.ROOT/name))
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes();self.assertEqual(guard.pin(raw),row['new'])
            old=guard.preceding_bytes(name,raw);self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for altered in (raw+b'future',raw[:-1],b'X'+raw[1:],None,bytearray(raw)):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,altered)

    def test_tampered_additions_modes_symlinks_and_neighbor_paths_fail_closed(self):
        for name in guard.ADDITIONS:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);p=root/name;p.parent.mkdir(parents=True);raw=(guard.ROOT/name).read_bytes();p.write_bytes(raw)
                self.assertTrue(guard.is_addition(p,root));p.write_bytes(raw+b'x')
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.write_bytes(raw);p.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.chmod(0o644);p.unlink();p.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/workbench/future.py'))

    def test_coherently_changed_ledger_and_rehashed_historical_text_reject(self):
        value=copy.deepcopy(guard.ledger());name=next(iter(guard.REPLACEMENTS));raw=b'X'+(guard.ROOT/name).read_bytes()[1:]
        value['replacements'][name]['new']=guard.pin(raw)
        with patch.object(guard,'ledger',return_value=value),self.assertRaises(AssertionError):guard.preceding_bytes(name,raw)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'ledger.json';p.write_text('changed')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()

    def test_original_probability_collection_and_gameplay_files_are_untouched(self):
        import supplied_deck_preservation as supplied
        import draw_access_preservation as draw
        import pack_odds_preservation as pack
        import collection_deck_preservation as collection
        for name,row in [( 'src/probability/supplied_deck.py',supplied.ledger()['additions']['src/probability/supplied_deck.py']),
            ('src/probability/draw_access.py',draw.ledger()['additions']['src/probability/draw_access.py']),
            ('src/probability/pack_odds.py',pack.ledger()['additions']['src/probability/pack_odds.py']),
            ('src/collection/deck_analysis.py',collection.ledger()['additions']['src/collection/deck_analysis.py'])]:
            self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),row)
        for name in guard.ADDITIONS:self.assertTrue(draw.is_addition(guard.ROOT/name))

    def test_runtime_imports_are_only_stdlib_and_public_probability_consumer(self):
        allowed={'argparse','hashlib','hmac','http','json','pathlib','secrets','probability','adapter','server'}
        for name in guard.ADDITIONS:
            if not name.endswith('.py'):continue
            for node in ast.walk(ast.parse((guard.ROOT/name).read_text())):
                if isinstance(node,ast.Import):self.assertTrue(all(x.name.split('.')[0] in allowed for x in node.names))
                if isinstance(node,ast.ImportFrom):self.assertIn(node.module.split('.')[0],allowed)
        source=(guard.ROOT/'src/workbench/assets/app.js').read_text()
        for forbidden in ('innerHTML','eval(','localStorage','sessionStorage','WebSocket','XMLHttpRequest'):
            self.assertNotIn(forbidden,source)
        self.assertEqual(source.count("fetch("),1)

    def test_new_document_links_resolve(self):
        p=guard.ROOT/'docs/LOCAL_DECK_WORKBENCH_V1.md'
        for link in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)',p.read_text()):self.assertTrue((p.parent/link).exists(),link)


if __name__=='__main__':unittest.main()
