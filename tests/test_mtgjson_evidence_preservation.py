"""Exact successor and negative guards; no historical rebaseline."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import mtgjson_evidence_preservation as guard


class EvidencePreservationTests(unittest.TestCase):
    def test_all_exact_successors_reconstruct_predecessors(self):
        from factual_retention_preservation import preceding_bytes as factual_preceding
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(guard.pin(factual_preceding(name,raw)),row['new'])
            self.assertEqual(guard.pin(guard.preceding_bytes(name,raw)),row['old'])
            self.assertEqual(guard.preceding_bytes(name,guard.preceding_bytes(name,raw)),guard.preceding_bytes(name,raw))
            for changed in (raw+b'future',b'X'+raw[1:],raw[:-1],bytearray(raw),None):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,changed)

    def test_unchanged_authority_and_historical_ledgers(self):
        from factual_retention_preservation import preceding_bytes as factual_preceding
        for name,pin in guard.ledger()['unchanged'].items():
            self.assertEqual(guard.pin(factual_preceding(name,(guard.ROOT/name).read_bytes())),pin,name)

    def test_additions_inventory_modes_and_symlinks_fail_closed(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(is_addition(guard.ROOT/name))
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);p=root/name;p.parent.mkdir(parents=True);raw=(guard.ROOT/name).read_bytes()
                p.write_bytes(raw);self.assertTrue(guard.is_addition(p,root))
                p.write_bytes(raw+b'x')
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.write_bytes(raw);p.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.unlink();p.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/providers/mtgjson/future.py'))

    def test_forged_edits_and_ledger_cannot_redefine_history(self):
        name='src/providers/mtgjson/private_policy.py';data=deepcopy(guard.ledger())
        data['replacements'][name]['edits'][0]['old']='forged predecessor'
        with patch.object(guard,'ledger',return_value=data),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'ledger';p.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()


if __name__=='__main__':unittest.main()
