"""Exact successor rejection and unchanged analytical/application predecessors."""
import ast
import copy
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import portable_research_preservation as guard


class PortableResearchPreservationTests(unittest.TestCase):
    def test_exact_additions_and_reversible_hook(self):
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT/name))
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes();self.assertEqual(guard.pin(raw),row['new'])
            old=guard.preceding_bytes(name,raw);self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for bad in (raw+b'future',b'X'+raw[1:],raw[:-1],bytearray(raw),None):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,bad)

    def test_finite_scope_addition_modes_and_symlinks(self):
        for name in guard.ADDITIONS:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);p=root/name;p.parent.mkdir(parents=True)
                raw=(guard.ROOT/name).read_bytes();p.write_bytes(raw)
                self.assertTrue(guard.is_addition(p,root));p.write_bytes(raw+b'x')
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.write_bytes(raw);p.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.chmod(0o644);p.unlink();p.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/workbench/future.py'))

    def test_coherent_ledger_change_and_altered_predecessor_fail(self):
        name=next(iter(guard.REPLACEMENTS));raw=b'X'+(guard.ROOT/name).read_bytes()[1:]
        value=copy.deepcopy(guard.ledger());value['replacements'][name]['new']=guard.pin(raw)
        with patch.object(guard,'ledger',return_value=value),self.assertRaises(AssertionError):guard.preceding_bytes(name,raw)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'ledger';p.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()

    def test_every_predecessor_chain_recognizes_exact_new_additions(self):
        import draw_access_preservation as draw
        import set_preparation_preservation as preparation
        for name in guard.ADDITIONS:
            self.assertTrue(draw.is_addition(guard.ROOT/name))
        for name,row in preparation.ledger()['additions'].items():
            self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),row)
        self.assertEqual(preparation.LEDGER_SHA256,'41c0375340930dbc0fdd95165a264171b7c187d0658d0f2735d2e03faf6b1126')

    def test_existing_editor_and_analytical_owners_remain_exact(self):
        import workbench_preservation as workbench
        import supplied_deck_preservation as supplied
        import resource_assignment_preservation as resource
        for owner in (workbench,supplied,resource):
            for name,row in owner.ledger()['additions'].items():
                if name.startswith('src/'):
                    self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),row)

    def test_new_runtime_has_no_private_consumers_storage_or_model_execution(self):
        allowed={'copy','datetime','hashlib','json','pathlib','re','argparse','hmac','secrets','probability',
                 'server','adapter','investigations','research_example'}
        for name in guard.ADDITIONS:
            if not name.startswith('src/') or not name.endswith('.py'):continue
            source=(guard.ROOT/name).read_text()
            for node in ast.walk(ast.parse(source)):
                if isinstance(node,ast.Import):self.assertTrue(all(x.name.split('.')[0] in allowed for x in node.names))
                if isinstance(node,ast.ImportFrom):self.assertIn(node.module.split('.')[0],allowed)
            for bad in ('write_text(', 'write_bytes(', 'subprocess', 'os.system', 'eval(', 'exec(', 'requests.', 'urllib'):
                self.assertNotIn(bad,source)
        source=(guard.ROOT/'src/workbench/assets/research.js').read_text()
        for bad in ('innerHTML','eval(','localStorage','sessionStorage','WebSocket','XMLHttpRequest'):
            self.assertNotIn(bad,source)

    def test_new_document_links_exist(self):
        p=guard.ROOT/'docs/PORTABLE_DECK_RESEARCH_V1.md'
        for link in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)',p.read_text()):
            self.assertTrue((p.parent/link).exists(),link)


if __name__=='__main__':unittest.main()
