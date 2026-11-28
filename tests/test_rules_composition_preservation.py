"""Exact additions, reverse compatibility and unchanged analytical owners."""
from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import rules_composition_preservation as guard

from candidate_mana_preservation import preceding_bytes as candidate_preceding


class CompositionPreservationTests(unittest.TestCase):
    def test_exact_additions_and_owning_implementations_unchanged(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT/name))
            self.assertTrue(is_addition(guard.ROOT/name))
        for name,row in guard.ledger()['unchanged'].items():
            self.assertEqual(guard.pin(candidate_preceding(name,(guard.ROOT/name).read_bytes())),row,name)

    def test_only_exact_predecessor_reconstruction_is_accepted(self):
        import rules_reasoning_preservation as previous
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes();old=guard.preceding_bytes(name,raw)
            self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            self.assertEqual(previous.preceding_bytes(name,raw),old)
            for changed in (raw+b'future',raw[:-1],b'X'+raw[1:],bytearray(raw),None):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,changed)

    def test_addition_mutations_modes_symlinks_and_unknown_paths_rejected(self):
        for name in guard.ADDITIONS:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);p=root/name;p.parent.mkdir(parents=True)
                raw=(guard.ROOT/name).read_bytes();p.write_bytes(raw)
                self.assertTrue(guard.is_addition(p,root))
                p.write_bytes(raw+b' ')
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.write_bytes(raw);p.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.unlink();p.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/card_intelligence/future.py'))

    def test_coherent_rehash_cannot_forge_historical_predecessor(self):
        ledger=deepcopy(guard.ledger());name=next(iter(guard.REPLACEMENTS))
        ledger['replacements'][name]['edits'][0]['old']='forged history'
        with patch.object(guard,'ledger',return_value=ledger),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'ledger';p.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()

    def test_all_preceding_reasoning_and_reconciliation_pins_still_apply(self):
        import rules_reasoning_preservation as previous
        self.assertEqual(previous.LEDGER_SHA256,'747750e5698fd6efda6cd44459135458dcae0238aea1e8cae611af3bea1fc25d')
        for name,row in previous.ledger()['additions'].items():
            self.assertEqual(previous.pin(candidate_preceding(name,(previous.ROOT/name).read_bytes())),row)
        for name,row in previous.ledger()['replacements'].items():
            self.assertEqual(previous.pin(previous.preceding_bytes(name,(previous.ROOT/name).read_bytes())),row['old'])

    def test_document_links(self):
        doc=guard.ROOT/'docs/RULES_REASONING_COMPOSITION_V1.md'
        for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)',doc.read_text()):
            self.assertTrue((doc.parent/target).is_file(),target)
