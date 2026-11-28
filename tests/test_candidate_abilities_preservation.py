"""Pinned predecessors and independent authority/runtime preservation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import candidate_abilities_preservation as guard
from canonical_import.mtgjson_factual import engine_binding
from card_intelligence import candidate_mana as v1


class CandidateAbilityPreservationTests(unittest.TestCase):
    def test_exact_replacements_reconstruct_canonical_predecessors(self):
        for name,row in guard.ledger()['replacements'].items():
            raw=(guard.ROOT/name).read_bytes()
            self.assertEqual(guard.pin(raw),row['new'])
            old=guard.preceding_bytes(name,raw)
            self.assertEqual(guard.pin(old),row['old'])
            self.assertEqual(guard.preceding_bytes(name,old),old)
            for altered in (raw+b'future',raw[:-1],b'X'+raw[1:],bytearray(raw)):
                with self.assertRaises(AssertionError):guard.preceding_bytes(name,altered)

    def test_finite_additions_and_tampering_mode_symlink_refusal(self):
        from draw_access_preservation import is_addition
        for name in guard.ADDITIONS:
            self.assertTrue(is_addition(guard.ROOT/name))
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);p=root/name;p.parent.mkdir(parents=True)
                original=(guard.ROOT/name).read_bytes();p.write_bytes(original)
                self.assertTrue(guard.is_addition(p,root))
                p.write_bytes(original+b'future')
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.write_bytes(original);p.chmod(0o744)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
                p.unlink();p.symlink_to(guard.ROOT/name)
                with self.assertRaises(AssertionError):guard.is_addition(p,root)
        self.assertFalse(guard.is_addition(guard.ROOT/'src/card_intelligence/future.py'))

    def test_all_v1_and_twelve_admission_binding_files_unchanged(self):
        pins=guard.ledger()['unchanged']
        for name,expected in pins.items():
            self.assertEqual(guard.pin((guard.ROOT/name).read_bytes()),expected,name)
        self.assertEqual(len(engine_binding()),12)
        for name,digest in engine_binding().items():self.assertEqual(pins['src/'+name]['sha256'],digest,name)
        self.assertEqual(v1._IMPORTED_CODE,guard.ledger()['v1_implementation_id'])
        for name in v1._CODE:self.assertIn('src/'+name,pins)

    def test_forged_ledger_and_coherent_edit_cannot_rebaseline_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/'ledger';p.write_bytes(guard.LEDGER.read_bytes()+b' ')
            with patch.object(guard,'LEDGER',p),self.assertRaises(AssertionError):guard.ledger()
        data=deepcopy(guard.ledger());name='docs/ROADMAP.md'
        data['replacements'][name]['edit']['old']='invented predecessor'
        with patch.object(guard,'ledger',return_value=data),self.assertRaises(AssertionError):
            guard.preceding_bytes(name,(guard.ROOT/name).read_bytes())

    def test_future_bridge_and_authority_holds_are_explicit(self):
        text=(guard.ROOT/'docs/CANDIDATE_ABILITY_SEGMENTATION_V1.md').read_text()
        for phrase in ('Compatibility V1','not implemented here','card_reference/uuid',
                       'Authentication is deferred','admission remains HOLD','require review',
                       'No additional cost or effect grammar'):
            self.assertIn(phrase,text)


if __name__=='__main__':unittest.main()
