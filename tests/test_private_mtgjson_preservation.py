"""Exact predecessors, non-forgeable compatibility and unchanged authority boundaries."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import private_mtgjson_preservation as guard

from candidate_mana_preservation import preceding_bytes as candidate_preceding


class PrivateImportPreservationTests(unittest.TestCase):
    def test_exact_additions_and_prior_inventory_admission(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT/name))
            self.assertTrue(is_addition(guard.ROOT/name))
        for name,pin in guard.ledger()['unchanged'].items():
            self.assertEqual(guard.pin(candidate_preceding(name,(guard.ROOT/name).read_bytes())),pin,name)

    def test_exact_reversal_and_mutations_fail_closed(self):
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(guard.pin(guard.preceding_bytes(name,raw)),row['old'])
            for altered in (raw+b'future',raw[:-1],b'X'+raw[1:],bytearray(raw),None):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,altered)

    def test_coherent_forgery_and_ledger_changes_do_not_rebaseline_history(self):
        name='src/providers/mtgjson/reconciliation.py';data=deepcopy(guard.ledger())
        data['replacements'][name]['edits'][0]['old']='forged predecessor'
        with patch.object(guard,'ledger',return_value=data),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'ledger';p.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()

    def test_additions_reject_changed_bytes_modes_symlinks_and_future_files(self):
        for name in guard.ADDITIONS:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);p=root/name;p.parent.mkdir(parents=True)
                raw=(guard.ROOT/name).read_bytes();p.write_bytes(raw)
                self.assertTrue(guard.is_addition(p,root))
                p.write_bytes(raw+b'future')
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.write_bytes(raw);p.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.unlink();p.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/providers/mtgjson/future.py'))


if __name__=='__main__':unittest.main()
