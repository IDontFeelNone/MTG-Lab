"""Exact finite successor scope and predecessor reconstruction remain fail-closed."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import standard_envelope_preservation as guard


class StandardEnvelopePreservationTests(unittest.TestCase):
    def test_all_successors_reconstruct_exact_baseline(self):
        for name,row in guard.ledger()['replacements'].items():
            from factual_admission_preservation import preceding_bytes
            raw=preceding_bytes(name,(guard.ROOT/name).read_bytes())
            self.assertEqual(guard.pin(raw),row['new'])
            self.assertEqual(guard.pin(guard.preceding_bytes(name,raw)),row['old'])
            for altered in (raw+b'future',raw[:-1],b'X'+raw[1:],None,bytearray(raw)):
                with self.subTest(name=name),self.assertRaises(AssertionError):guard.preceding_bytes(name,altered)

    def test_authority_policy_projection_limits_and_historical_ledgers_unchanged(self):
        for name,pin in guard.ledger()['unchanged'].items():
            from factual_admission_preservation import preceding_bytes
            self.assertEqual(guard.pin(preceding_bytes(name,(guard.ROOT/name).read_bytes())),pin,name)

    def test_forged_reversal_or_ledger_is_refused(self):
        name='src/providers/mtgjson/reconciliation.py';data=deepcopy(guard.ledger())
        data['replacements'][name]['edits'][0]['old']='forged'
        with patch.object(guard,'ledger',return_value=data),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ledger';path.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',path),self.assertRaises(AssertionError):guard.ledger()

    def test_addition_scope_rejects_altered_bytes_modes_and_symlinks(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(is_addition(guard.ROOT/name))
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


if __name__=='__main__':unittest.main()
