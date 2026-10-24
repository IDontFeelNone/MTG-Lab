"""Three bounded preservation checks; source and historical assertions stay intact."""
import hashlib
from proposed_spell_packet_authoring_preservation import historical_document_before_authoring_append
from pathlib import Path
import unittest

import proposed_spell_evidence_packet_preservation as guard
import casting_permission_family_preservation as previous


class ProposedSpellEvidencePacketPreservationTests(unittest.TestCase):
    def test_exact_successor_paths_keep_unknown_neighbors_visible(self):
        alternate = Path('/tmp/packet-design-finite-inventory')
        for name in guard.NEW_REVIEW_PATHS:
            with self.subTest(path=name):
                self.assertTrue(guard.is_proposed_spell_evidence_packet_addition(guard.ROOT / name))
                self.assertTrue(guard.is_proposed_spell_evidence_packet_addition(alternate / name, alternate))
                self.assertTrue(previous.is_casting_permission_family_addition(guard.ROOT / name))
                self.assertFalse(guard.is_proposed_spell_evidence_packet_addition(guard.ROOT / (name + '.future')))
        for name in ('reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/future.json',
                     'reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/projection.json',
                     'src/gameplay_rules/proposed_spell_evidence_packet_design/__init__.py'):
            self.assertFalse(previous.is_casting_permission_family_addition(guard.ROOT / name))

    def test_complete_inherited_documents_and_exact_suffixes_remain_distinct(self):
        for name, pin in guard.DOCUMENT_APPENDICES.items():
            raw = historical_document_before_authoring_append(name, (guard.ROOT / name).read_bytes())
            old = guard.historical_document_before_packet_append(name, raw)
            with self.subTest(path=name):
                self.assertEqual(len(raw), pin['baseline_bytes'] + pin['appendix_bytes'])
                self.assertEqual(hashlib.sha256(old).hexdigest(), pin['baseline_sha256'])
                self.assertEqual(guard.historical_document_before_packet_append(name, old), old)
                prior = previous.historical_document_before_casting_permission_append(name, raw)
                self.assertEqual(prior, old[:previous.DOCUMENT_APPENDICES[name]['baseline_bytes']])
                for changed in (raw + b'future\n', raw[:-1], b'X' + raw[1:],
                                old + b'X' + raw[len(old)+1:], bytearray(raw), True):
                    with self.subTest(kind=type(changed).__name__), self.assertRaises(AssertionError):
                        guard.historical_document_before_packet_append(name, changed)
        with self.assertRaises(AssertionError):
            guard.historical_document_before_packet_append('docs/future.md', b'')

    def test_finite_adapter_reversal_preserves_every_original_assertion(self):
        for name in guard.ADAPTER_PATCHES:
            raw = (guard.ROOT / name).read_bytes()
            with self.subTest(path=name):
                old = guard.historical_adapter_bytes(name, raw)
                self.assertEqual(hashlib.sha256(old).hexdigest(), guard.ADAPTER_BASE_SHA256[name])
                for changed in (raw + b'future changes\n', b'X' + raw[1:], raw[:-1], old,
                                bytearray(raw), True):
                    with self.subTest(kind=type(changed).__name__), self.assertRaises(AssertionError):
                        guard.historical_adapter_bytes(name, changed)
        with self.assertRaises(AssertionError):
            guard.historical_adapter_bytes('tests/future.py', b'')


if __name__ == '__main__':
    unittest.main()
