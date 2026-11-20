"""Exact predecessor reversal, immutable original fixtures and bounded owning API reuse."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import set_preparation_preservation as guard

class SetPreparationPreservationTests(unittest.TestCase):
    def test_additions_and_exact_reversible_hook(self):
        for name in guard.ADDITIONS:self.assertTrue(guard.is_addition(guard.ROOT/name))
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes();self.assertEqual(guard.pin(raw),row['new'])
            old=guard.preceding_bytes(name,raw);self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for bad in (raw+b'future',b'X'+raw[1:],raw[:-1],bytearray(raw),None):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,bad)
    def test_addition_tampering_modes_symlinks_and_neighbors_reject(self):
        for name in guard.ADDITIONS:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);p=root/name;p.parent.mkdir(parents=True);raw=(guard.ROOT/name).read_bytes();p.write_bytes(raw)
                self.assertTrue(guard.is_addition(p,root));p.write_bytes(raw+b'future')
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.write_bytes(raw);p.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.chmod(0o644);p.unlink();p.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/ingestion/future.py'))
    def test_coherently_rehashed_history_and_modified_ledger_refuse(self):
        v=copy.deepcopy(guard.ledger());name=next(iter(guard.REPLACEMENTS));raw=b'X'+(guard.ROOT/name).read_bytes()[1:]
        v['replacements'][name]['new']=guard.pin(raw)
        with patch.object(guard,'ledger',return_value=v),self.assertRaises(AssertionError):guard.preceding_bytes(name,raw)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger';p.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()
    def test_all_prior_addition_and_predecessor_chains_keep_their_pins(self):
        import resource_assignment_preservation as resource
        import draw_access_preservation as draw
        for name in guard.ADDITIONS:self.assertTrue(draw.is_addition(guard.ROOT/name))
        self.assertEqual(resource.LEDGER_SHA256,'0f5b49fb78d2798749c31cd4acbd73896eb430b246a58523c98a45597a1ca726')
        for name,row in resource.ledger()['additions'].items():self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),row)
    def test_no_storage_acquisition_admission_or_private_consumer_imports(self):
        source=(guard.ROOT/'src/ingestion/set_preparation.py').read_text();tree=ast.parse(source)
        allowed={'collections','copy','hashlib','json','pathlib','dataset_import.framework','external_ingestion.framework','repository.cards','repository.canonical','validation'}
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):self.assertIn(node.module,allowed)
            if isinstance(node,ast.Import):self.assertTrue(all(x.name=='json' for x in node.names))
        for bad in ('write_text(', 'write_bytes(', 'apply_import(', 'promote(', 'attach_snapshot(', 'requests.', 'subprocess', 'urllib', 'MTGJSONImportExecution('):self.assertNotIn(bad,source)
    def test_document_links_resolve(self):
        p=guard.ROOT/'docs/SET_CANDIDATE_PREPARATION_V1.md'
        for link in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)',p.read_text()):self.assertTrue((p.parent/link).exists(),link)

if __name__=='__main__':unittest.main()
