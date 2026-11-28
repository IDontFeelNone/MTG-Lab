"""Exact compatibility, immutable historical policies and owning implementation reuse."""
import copy
import hashlib
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import release_reconciliation_preservation as guard

from candidate_mana_preservation import preceding_bytes as candidate_preceding


class ReconciliationPreservationTests(unittest.TestCase):
    def test_exact_additions_and_predecessor_reversal(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT/name))
            self.assertTrue(is_addition(guard.ROOT/name))
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(guard.pin(raw),row['new'])
            old=guard.preceding_bytes(name,raw)
            self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for altered in (raw+b'future', b'X'+raw[1:],raw[:-1],bytearray(raw),None):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,altered)

    def test_changed_additions_modes_and_symlinks_fail_closed(self):
        for name in guard.ADDITIONS:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);p=root/name;p.parent.mkdir(parents=True)
                raw=(guard.ROOT/name).read_bytes();p.write_bytes(raw)
                self.assertTrue(guard.is_addition(p,root))
                p.write_bytes(raw+b'future')
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.write_bytes(raw);p.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.unlink();p.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/providers/mtgjson/future.py'))

    def test_modified_ledger_and_coherent_successor_forgery_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'ledger';p.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()
        name=next(iter(guard.REPLACEMENTS));raw=(guard.ROOT/name).read_bytes()+b'x'
        ledger=copy.deepcopy(guard.ledger());ledger['replacements'][name]['new']=guard.pin(raw)
        with patch.object(guard,'ledger',return_value=ledger),self.assertRaises(AssertionError):guard.preceding_bytes(name,raw)

    def test_every_prior_ci_pin_and_historical_chain_unchanged(self):
        import ci_workflow_preservation as previous
        self.assertEqual(previous.LEDGER_SHA256,'b5a31080d71a874532f11383b6b9c06af40168996106a786941dedfa08698af9')
        for name,row in previous.ledger()['additions'].items():
            self.assertEqual(guard.pin(candidate_preceding(name,(guard.ROOT/name).read_bytes())),row)
        for name,row in previous.ledger()['replacements'].items():
            self.assertEqual(guard.pin(previous.preceding_bytes(name,(guard.ROOT/name).read_bytes())),row['old'])

    def test_original_pipeline_mapper_validator_and_authorities_remain_exact(self):
        # Exact base pins work in the disposable publication checkout too, which
        # intentionally has unrelated Git ancestry and a different live catalog.
        for name,pin in guard.ledger()['unchanged'].items():
            self.assertEqual(guard.pin(candidate_preceding(name,(guard.ROOT/name).read_bytes())),pin,name)

    def test_new_document_links_resolve(self):
        p=guard.ROOT/'docs/RELEASE_CATALOG_RECONCILIATION_V1.md'
        for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)',p.read_text()):
            self.assertTrue((p.parent/target).is_file(),target)


if __name__=='__main__':unittest.main()
