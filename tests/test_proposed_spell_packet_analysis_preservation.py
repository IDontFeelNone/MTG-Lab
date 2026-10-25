"""Four finite controls compose analysis and conditional changes with historical protections."""
import hashlib
from pathlib import Path
import unittest

import proposed_spell_packet_analysis_preservation as guard
import proposed_spell_packet_authoring_preservation as previous


class ProposedSpellPacketAnalysisPreservationTests(unittest.TestCase):
    def test_exact_document_suffixes_compose_without_hiding_tampering(self):
        for name, pin in guard.DOCUMENT_APPENDICES.items():
            with self.subTest(path=name):
                raw = guard.historical_document_before_conditional_append(
                    name, (guard.ROOT / name).read_bytes())
                old = guard.historical_document_before_analysis_append(name, raw)
                self.assertEqual(len(raw), pin['baseline_bytes'] + pin['appendix_bytes'])
                self.assertEqual(hashlib.sha256(old).hexdigest(), pin['baseline_sha256'])
                self.assertEqual(guard.historical_document_before_analysis_append(name, old), old)
                self.assertEqual(previous.historical_document_before_authoring_append(name, raw),
                                 previous.historical_document_before_authoring_append(name, old))
                for changed in (raw + b'future\n', raw[:-1], b'X' + raw[1:],
                                old + b'X' + raw[len(old)+1:], bytearray(raw), True):
                    with self.assertRaises(AssertionError):
                        guard.historical_document_before_analysis_append(name, changed)
        with self.assertRaises(AssertionError):
            guard.historical_document_before_analysis_append('docs/future.md', b'')

    def test_only_named_source_addition_and_exact_reversible_adapters(self):
        alternate = Path('/tmp/analysis-pilot-finite-control')
        self.assertEqual(guard.NEW_SOURCE_PATHS, {'src/proposed_spell_packets/analysis.py'})
        for name in guard.NEW_SOURCE_PATHS:
            self.assertTrue(guard.is_packet_analysis_addition(guard.ROOT / name))
            self.assertTrue(guard.is_packet_analysis_addition(alternate / name, alternate))
            self.assertTrue(previous.is_packet_authoring_addition(guard.ROOT / name))
            self.assertFalse(guard.is_packet_analysis_addition(guard.ROOT / (name + '.future')))
        for name in ('src/proposed_spell_packets/future.py', 'src/gameplay_rules/analysis.py'):
            self.assertFalse(previous.is_packet_authoring_addition(guard.ROOT / name))
        for name in guard.ADAPTER_PATCHES:
            raw = (guard.ROOT / name).read_bytes()
            old = guard.historical_adapter_bytes(name, raw)
            self.assertEqual(hashlib.sha256(old).hexdigest(), guard.ADAPTER_BASE_SHA256[name])
            for changed in (raw + b'future\n', raw[:-1], b'X' + raw[1:], old, bytearray(raw), True):
                with self.subTest(path=name), self.assertRaises(AssertionError):
                    guard.historical_adapter_bytes(name, changed)

    def test_exact_conditional_suffixes_and_finite_source_successor(self):
        self.assertEqual(guard.CONDITIONAL_SOURCE_PATHS,
                         {'src/proposed_spell_packets/conditions.py'})
        self.assertEqual(set(guard.CONDITIONAL_DOCUMENT_APPENDICES), set(guard.DOCUMENT_APPENDICES))
        for name in guard.CONDITIONAL_SOURCE_PATHS:
            self.assertTrue(guard.is_packet_analysis_addition(guard.ROOT / name))
            self.assertTrue(previous.is_packet_authoring_addition(guard.ROOT / name))
            self.assertFalse(previous.is_packet_authoring_addition(guard.ROOT / (name + '.future')))
        for name, pin in guard.CONDITIONAL_DOCUMENT_APPENDICES.items():
            with self.subTest(path=name):
                raw = (guard.ROOT / name).read_bytes()
                old = guard.historical_document_before_conditional_append(name, raw)
                self.assertEqual(len(raw), pin['baseline_bytes'] + pin['appendix_bytes'])
                self.assertEqual(hashlib.sha256(old).hexdigest(), pin['baseline_sha256'])
                self.assertEqual(guard.historical_document_before_conditional_append(name, old), old)
                for changed in (raw + b'future\n', raw[:-1], b'X' + raw[1:],
                                old + b'X' + raw[len(old)+1:], bytearray(raw), True):
                    with self.assertRaises(AssertionError):
                        guard.historical_document_before_conditional_append(name, changed)
        with self.assertRaises(AssertionError):
            guard.historical_document_before_conditional_append('docs/future.md', b'')

    def test_exact_cli_successor_and_original_shared_validation_bytes(self):
        self.assertEqual(set(guard.EXACT_SUCCESSORS), {'src/proposed_spell_packets/__main__.py'})
        for name, pins in guard.EXACT_SUCCESSORS.items():
            raw = (guard.ROOT / name).read_bytes()
            self.assertEqual(hashlib.sha256(guard.historical_analysis_cli_bytes(raw)).hexdigest(),
                             pins['successor_sha256'])
            for changed in (raw + b'future\n', raw[:-1], b'X' + raw[1:], bytearray(raw), True):
                with self.assertRaises(AssertionError):
                    guard.historical_analysis_cli_bytes(changed)
        # Direct pins avoid historical Git dependencies in disposable discovery.
        pins = {
            'src/proposed_spell_packets/authoring.py': '0762251886a9a02de8d06c96fe69fee9c97c3a1cafb0f71e51ea3169e76a7d7a',
            'src/proposed_spell_packets/validation.py': 'c6a7fcb28f2243448afdd3c0fb9bcff2ac9d8abe246fa736e924173812cb5e2e',
        }
        for name, digest in pins.items():
            self.assertEqual(hashlib.sha256((guard.ROOT / name).read_bytes()).hexdigest(), digest)
        self.assertEqual(hashlib.sha256(previous.historical_checker_bytes()).hexdigest(),
                         previous.CHECKER_ORIGINAL_SHA256)


if __name__ == '__main__':
    unittest.main()
