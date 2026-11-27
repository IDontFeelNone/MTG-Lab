"""Exact finite source changes, unchanged authority and historical reconstruction."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import factual_admission_preservation as guard


class FactualAdmissionPreservationTests(unittest.TestCase):
    def test_every_successor_reconstructs_exact_reviewed_base(self):
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(guard.pin(raw),row['new'],name)
            old=guard.preceding_bytes(name,raw)
            self.assertEqual(guard.pin(old),row['old'],name)
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for altered in (raw+b'future',raw[:-1],b'X'+raw[1:],None,bytearray(raw)):
                with self.subTest(name=name),self.assertRaises(AssertionError):
                    guard.preceding_bytes(name,altered)

    def test_authority_importer_rules_transactions_and_prior_ledgers_unchanged(self):
        for name,pin in guard.ledger()['unchanged'].items():
            self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),pin,name)

    def test_foreign_edits_cannot_redefine_predecessors_or_ledger(self):
        name='src/query/engine.py';data=deepcopy(guard.ledger())
        data['replacements'][name]['edits'][0]['old']='fabricated'
        with patch.object(guard,'ledger',return_value=data),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'ledger';path.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',path),self.assertRaises(AssertionError):guard.ledger()

    def test_additions_are_finite_regular_and_exact(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(is_addition(guard.ROOT/name))
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
        self.assertFalse(guard.is_addition(guard.ROOT/'src/canonical_import/future.py'))

    def test_all_historical_successors_still_reconstruct(self):
        from mtgjson_evidence_preservation import preceding_bytes
        for name in ('src/query/engine.py','src/card_intelligence/mechanics.py'):
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(preceding_bytes(name,raw),preceding_bytes(name,guard.preceding_bytes(name,raw)))

    def test_current_query_inventory_row_uses_exact_predecessor_view(self):
        import query_attachment_performance_preservation as previous
        name='src/query/engine.py';raw=(guard.ROOT/name).read_bytes()
        current={'path':name,**guard.pin(raw)}
        expected=next(row['original'] for row in previous.ledger()['replacements'] if row['path']==name)
        self.assertEqual(previous.historical_inventory_row(current),
            {'path':name,'bytes':expected['bytes'],'sha256':expected['sha256']})
        with self.assertRaises(AssertionError):previous.historical_inventory_row({**current,'sha256':'0'*64})


if __name__=='__main__':unittest.main()
