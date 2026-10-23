"""Finite pilot preservation composition; historical evidence remains intact."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import proposed_spell_packet_authoring_preservation as guard
import proposed_spell_evidence_packet_preservation as previous


class ProposedSpellPacketAuthoringPreservationTests(unittest.TestCase):
    def test_exact_document_suffixes_compose_and_tampering_remains_visible(self):
        for name, pin in guard.DOCUMENT_APPENDICES.items():
            raw = (guard.ROOT / name).read_bytes()
            old = guard.historical_document_before_authoring_append(name, raw)
            with self.subTest(path=name):
                self.assertEqual(len(raw), pin['baseline_bytes'] + pin['appendix_bytes'])
                self.assertEqual(hashlib.sha256(old).hexdigest(), pin['baseline_sha256'])
                self.assertEqual(guard.historical_document_before_authoring_append(name, old), old)
                self.assertEqual(previous.historical_document_before_packet_append(name, raw),
                                 previous.historical_document_before_packet_append(name, old))
                for changed in (raw + b'future\n', raw[:-1], b'X' + raw[1:],
                                old + b'X' + raw[len(old)+1:], bytearray(raw), True):
                    with self.assertRaises(AssertionError):
                        guard.historical_document_before_authoring_append(name, changed)
        with self.assertRaises(AssertionError):
            guard.historical_document_before_authoring_append('docs/future.md', b'')

    def test_exact_finite_paths_and_adapter_reversals_preserve_original_assertions(self):
        for name in guard.NEW_SOURCE_PATHS:
            self.assertTrue(guard.is_packet_authoring_addition(guard.ROOT / name))
            self.assertTrue(previous.is_proposed_spell_evidence_packet_addition(guard.ROOT / name))
            self.assertFalse(guard.is_packet_authoring_addition(guard.ROOT / (name + '.future')))
        for name in ('src/proposed_spell_packets/future.py', 'src/gameplay_rules/engine.py',
                     'reference-reviews/gameplay-rules-proposed-spell-evidence-packet-design/future.json'):
            self.assertFalse(guard.is_packet_authoring_addition(guard.ROOT / name))
        for name in guard.ADAPTER_PATCHES:
            raw = (guard.ROOT / name).read_bytes()
            old = guard.historical_adapter_bytes(name, raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(), guard.ADAPTER_BASE_SHA256[name])
            for changed in (raw + b'future\n', raw[:-1], b'X' + raw[1:], old, bytearray(raw), True):
                with self.subTest(path=name), self.assertRaises(AssertionError):
                    guard.historical_adapter_bytes(name, changed)

    def test_promoted_checker_reproduces_exact_inherited_bytes_without_a_second_copy(self):
        old = guard.historical_checker_bytes()
        self.assertEqual(hashlib.sha256(old).hexdigest(), guard.CHECKER_ORIGINAL_SHA256)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('tests/proposed_spell_evidence_packet_validation.py',
                         'src/proposed_spell_packets/validation.py'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                raw = (guard.ROOT / name).read_bytes()
                path.write_bytes(raw)
            self.assertEqual(guard.historical_checker_bytes(root), old)
            for name in ('tests/proposed_spell_evidence_packet_validation.py',
                         'src/proposed_spell_packets/validation.py'):
                path = root / name
                raw = path.read_bytes()
                path.write_bytes(b'X' + raw[1:])
                with self.assertRaises(AssertionError):
                    guard.historical_checker_bytes(root)
                path.write_bytes(raw)


if __name__ == '__main__':
    unittest.main()
