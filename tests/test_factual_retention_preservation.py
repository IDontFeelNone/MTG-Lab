"""Exact predecessor reproduction and negative guards for this bounded repair."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import factual_retention_preservation as guard


class FactualRetentionPreservationTests(unittest.TestCase):
    def test_successors_reconstruct_exact_predecessors(self):
        from standard_envelope_preservation import preceding_bytes as envelope_preceding
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(guard.pin(envelope_preceding(name,raw)),row['new'])
            self.assertEqual(guard.pin(guard.preceding_bytes(name,raw)),row['old'])
            for invalid in (raw+b'future',raw[:-1],b'X'+raw[1:],bytearray(raw),None):
                with self.subTest(name=name),self.assertRaises(AssertionError):guard.preceding_bytes(name,invalid)

    def test_historical_authority_source_policy_and_oracle_bytes_unchanged(self):
        for name,pin in guard.ledger()['unchanged'].items():
            self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),pin,name)

    def test_forged_reversal_or_ledger_cannot_redefine_predecessor(self):
        name='src/providers/mtgjson/private_policy.py';data=deepcopy(guard.ledger())
        data['replacements'][name]['edits'][0]['old']='forged'
        with patch.object(guard,'ledger',return_value=data),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ledger';path.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',path),self.assertRaises(AssertionError):guard.ledger()

    def test_exact_additions_integrate_and_reject_future_edits_modes_and_symlinks(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(is_addition(guard.ROOT/name))
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);path=root/name;path.parent.mkdir(parents=True)
                raw=(guard.ROOT/name).read_bytes();path.write_bytes(raw)
                self.assertTrue(guard.is_addition(path,root))
                path.write_bytes(raw+b'x')
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
                path.write_bytes(raw);path.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
                path.unlink();path.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/providers/mtgjson/future.py'))


if __name__=='__main__':unittest.main()
