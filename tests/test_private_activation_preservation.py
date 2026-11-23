"""Exact successor boundaries preserve the owning importer and prior evidence."""
from copy import deepcopy
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import private_activation_preservation as guard


class ActivationPreservationTests(unittest.TestCase):
    def test_exact_additions_and_historical_inventory(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT/name))
            self.assertTrue(is_addition(guard.ROOT/name))
        for name,pin in guard.ledger()['unchanged'].items():
            self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),pin,name)

    def test_exact_reversal_and_negative_preservation(self):
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(guard.pin(guard.preceding_bytes(name,raw)),row['old'])
            for altered in (raw+b'future',raw[:-1],b'X'+raw[1:],bytearray(raw),None):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,altered)

    def test_ledger_mutations_and_coherent_forgery_cannot_rewrite_predecessor(self):
        name=next(iter(guard.REPLACEMENTS));ledger=deepcopy(guard.ledger())
        ledger['replacements'][name]['edits'][0]['old']='forged predecessor'
        with patch.object(guard,'ledger',return_value=ledger),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'ledger';p.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()

    def test_additions_modes_symlinks_and_future_paths_fail_closed(self):
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

    def test_document_local_links_resolve(self):
        p=guard.ROOT/'docs/PRIVATE_MTGJSON_ACTIVATION_V1.md'
        for link in re.findall(r'\[[^]]+\]\(([^)]+)\)',p.read_text()):
            if not link.startswith('https://'):self.assertTrue((p.parent/link).is_file(),link)


if __name__=='__main__':unittest.main()
