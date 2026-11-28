"""Exact successor reconstruction and authority containment, without rebaselining."""
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import candidate_mana_preservation as guard


class CandidateManaPreservationTests(unittest.TestCase):
    def test_each_successor_reconstructs_exact_canonical_predecessor(self):
        for name, row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(guard.pin(raw),row['new'],name)
            old=guard.preceding_bytes(name,raw)
            self.assertEqual(guard.pin(old),row['old'],name)
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for altered in (raw+b'future', raw[:-1], b'X'+raw[1:], bytearray(raw), None):
                with self.subTest(path=name), self.assertRaises(AssertionError):
                    guard.preceding_bytes(name,altered)

    def test_new_additions_are_finite_and_reject_tampering_modes_symlinks(self):
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
        self.assertFalse(guard.is_addition(guard.ROOT/'src/card_intelligence/future.py'))

    def test_historical_authority_and_source_contracts_are_unchanged(self):
        for name, expected in guard.ledger()['unchanged'].items():
            self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),expected,name)

    def test_forged_or_coherently_rehashed_ledger_does_not_authorize_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'ledger';p.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()
        data=deepcopy(guard.ledger());name='docs/GOVERNANCE.md'
        data['replacements'][name]['edit']['old']='forged'
        with patch.object(guard,'ledger',return_value=data),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())

    def test_product_requirements_and_deferred_authority_are_explicit(self):
        vision=(guard.ROOT/'VISION.md').read_text()
        for phrase in ('practical from an iPhone', 'selects Approve or Reject',
                       'technical\nauthorization metadata', 'bounded standing policies',
                       'cannot grant itself permissions', 'No standing-policy\nexecution'):
            self.assertIn(phrase,vision)
        governance=(guard.ROOT/'docs/GOVERNANCE.md').read_text()
        self.assertIn('Decision 017 does not already authorize standing-policy execution',governance)
        self.assertIn('independently authenticated\nexact-operation decision',governance)
        factual=(guard.ROOT/'docs/PRIVATE_FACTUAL_ADMISSION_V1.md').read_text()
        self.assertIn('cumulative private canonical\ncatalog expansion is not implemented',factual)


if __name__=='__main__':unittest.main()
