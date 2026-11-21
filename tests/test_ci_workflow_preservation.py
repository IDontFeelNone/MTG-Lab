"""Exact workflow successor compatibility without changing historical baselines."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import ci_workflow_preservation as guard


class CIWorkflowPreservationTests(unittest.TestCase):
    def test_exact_reversal_and_every_historical_pin(self):
        from overlay_preservation_support import historical_source_bytes
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(guard.pin(raw),row['new'])
            old=guard.preceding_bytes(name,raw)
            self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            if name.endswith('python-validation.yml'):
                self.assertEqual(hashlib.sha256(historical_source_bytes(name,raw)).hexdigest(),
                                 '4c4c7e42ff96c59e6edbe2c4d204c50a464d907153d9caf9df9564b03430b6a2')

    def test_unrecognized_edits_types_and_coherent_ledger_forgery_reject(self):
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            for changed in (raw+b'future',b'X'+raw[1:],raw[:-1],bytearray(raw),None):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,changed)
            value=copy.deepcopy(guard.ledger());value['replacements'][name]['new']=guard.pin(raw+b'x')
            with patch.object(guard,'ledger',return_value=value),self.assertRaises(AssertionError):
                guard.preceding_bytes(name,raw+b'x')

    def test_ledger_hash_and_exact_scope_reject_alterations(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'ledger';path.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',path),self.assertRaises(AssertionError):guard.ledger()

    def test_new_files_and_all_predecessor_addition_chains(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT/name))
            self.assertTrue(is_addition(guard.ROOT/name))
        self.assertFalse(guard.is_addition(guard.ROOT/'scripts/future_ci.py'))

    def test_original_retained_workflow_row_and_controlled_inventory_digest(self):
        from query_attachment_performance_preservation import assert_retained_row, historical_inventory_row
        name='.github/workflows/python-validation.yml';row=guard.ledger()['replacements'][name]
        old=dict(path=name,**row['old']);current=dict(path=name,**row['new'])
        assert_retained_row(old)
        self.assertEqual(historical_inventory_row(current),old)
        for bad in (dict(old,bytes=old['bytes']+1),dict(old,sha256='f'*64)):
            with self.assertRaises(AssertionError):assert_retained_row(bad)
        with self.assertRaises(AssertionError):historical_inventory_row(old)
        from test_real_rules_execution_design_boundaries import PROTECTED_GROUPS,controlled_inventory
        import json
        roots,count,expected=PROTECTED_GROUPS['writer_admission_evidence_and_transport']
        rows=controlled_inventory(roots)
        self.assertEqual(len(rows),count)
        self.assertEqual(hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest(),expected)

    def test_added_file_bytes_modes_and_symlinks_fail_closed(self):
        for name in guard.ADDITIONS:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);path=root/name;path.parent.mkdir(parents=True)
                raw=(guard.ROOT/name).read_bytes();path.write_bytes(raw)
                self.assertTrue(guard.is_addition(path,root))
                path.write_bytes(raw+b'future')
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
                path.write_bytes(raw);path.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
                path.unlink();path.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(path,root)


if __name__=='__main__':unittest.main()
