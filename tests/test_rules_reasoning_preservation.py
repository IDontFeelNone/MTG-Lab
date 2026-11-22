"""Fail-closed adapter tests, including historical predecessor reconstruction."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rules_reasoning_preservation as guard


class RulesReasoningPreservationTests(unittest.TestCase):
    def test_finite_additions_and_unchanged_governance(self):
        from draw_access_preservation import is_addition
        ledger=guard.ledger()
        for name in guard.ADDITIONS:
            self.assertTrue(guard.is_addition(guard.ROOT/name))
            self.assertTrue(is_addition(guard.ROOT/name))
        for name,row in ledger['unchanged'].items():
            self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),row)

    def test_exact_reversal_to_pinned_predecessor(self):
        import release_reconciliation_preservation as previous
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            old=guard.preceding_bytes(name,raw)
            self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            self.assertEqual(previous.preceding_bytes(name,raw),old)
            for changed in (raw+b'\n',raw[:-1],raw.replace(b'reasoning_preceding',b'forged_preceding')):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,changed)

    def test_additions_reject_mutation_mode_symlink_and_future_files(self):
        for name in guard.ADDITIONS:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); path=root/name;path.parent.mkdir(parents=True)
                original=(guard.ROOT/name).read_bytes();path.write_bytes(original)
                self.assertTrue(guard.is_addition(path,root))
                path.write_bytes(original+b' ')
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
                path.write_bytes(original);path.chmod(0o755)
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
                path.unlink();target=root/'target';target.write_bytes(original);path.symlink_to(target)
                with self.assertRaises(AssertionError):guard.is_addition(path,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/card_intelligence/future.py'))

    def test_forged_reversal_cannot_change_historical_bytes(self):
        ledger=deepcopy(guard.ledger());name=next(iter(guard.REPLACEMENTS))
        ledger['replacements'][name]['edits'][0]['old']='forged historical text'
        with patch.object(guard,'ledger',return_value=ledger),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())

    def test_ledger_cannot_be_broadly_rebaselined(self):
        ledger=guard.ledger();ledger['base']='forged'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ledger.json';path.write_text(json.dumps(ledger))
            with patch.object(guard,'LEDGER',path),self.assertRaises(AssertionError):guard.ledger()

    def test_all_older_reconciliation_contract_pins_still_apply(self):
        import release_reconciliation_preservation as previous
        for name,row in previous.ledger()['unchanged'].items():
            self.assertEqual(previous.pin((previous.ROOT/name).read_bytes()),row)
        for name,row in previous.ledger()['replacements'].items():
            self.assertEqual(previous.pin(previous.preceding_bytes(name,(previous.ROOT/name).read_bytes())),row['old'])
