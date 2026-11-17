"""Finite documentation successors preserve all existing historical contracts."""
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote

import documentation_continuity_preservation as guard


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


class DocumentationContinuityTests(unittest.TestCase):
    def test_exact_successors_reconstruct_all_twelve_predecessors(self):
        value = guard.ledger()
        self.assertEqual(value['schema_version'], 'documentation-continuity-successors-v1')
        for name, row in value['replacements'].items():
            with self.subTest(path=name):
                current = (guard.ROOT / name).read_bytes()
                self.assertEqual(pin(current), row['new'])
                old = guard.restore(name, current)
                self.assertEqual(pin(old), row['old'])
                self.assertEqual(guard.restore(name, old), old)
                if name in guard.DOCUMENTS:
                    self.assertEqual(len(row['edits']), 1)
                    self.assertEqual(row['edits'][0]['start'], 0)
                    self.assertEqual(row['edits'][0]['old'], '')
                    self.assertTrue(current.endswith(old))
                else:
                    self.assertTrue(all(edit['old'] == '' for edit in row['edits']))

    def test_every_document_predecessor_chain_has_identical_results(self):
        modules = (
            'proposed_spell_packet_analysis_preservation',
            'proposed_spell_packet_authoring_preservation',
            'proposed_spell_evidence_packet_preservation',
            'casting_permission_family_preservation',
            'casting_stage_family_completion_preservation',
            'shared_target_allocation_preservation',
            'shared_target_declaration_preservation',
            'shared_proposal_legality_preservation',
            'shared_casting_stage_preservation',
        )
        checked = 0
        for module_name in modules:
            module = importlib.import_module(module_name)
            for name, function in inspect.getmembers(module, inspect.isfunction):
                if not name.startswith('historical_document_before_') or function.__module__ != module_name:
                    continue
                for document in guard.DOCUMENTS:
                    with self.subTest(chain=module_name + '.' + name, document=document):
                        raw = (guard.ROOT / document).read_bytes()
                        old = guard.restore(document, raw)
                        if document not in module.DOCUMENT_APPENDICES:
                            for candidate in (raw, old):
                                with self.assertRaises(AssertionError):
                                    function(document, candidate)
                            continue
                        self.assertEqual(function(document, raw), function(document, old))
                        checked += 1
        self.assertEqual(checked, 87)

    def test_helper_changes_reverse_through_existing_source_chains(self):
        from overlay_preservation_support import historical_source_bytes
        from context_review_preservation_support import preceding_bytes
        for name in guard.HELPERS:
            raw = (guard.ROOT / name).read_bytes()
            old = guard.restore(name, raw)
            for function in (historical_source_bytes, preceding_bytes):
                with self.subTest(path=name, chain=function.__module__):
                    self.assertEqual(function(name, raw), function(name, old))

    def test_unknown_paths_types_and_unrecognized_edits_reject(self):
        for name in guard.DOCUMENTS | guard.HELPERS:
            raw = (guard.ROOT / name).read_bytes()
            old = guard.restore(name, raw)
            for candidate in (raw + b'future\n', raw[:-1], b'X' + raw[1:],
                              raw + raw, old + b'future\n', bytearray(raw), None, True):
                with self.subTest(path=name, kind=type(candidate).__name__):
                    with self.assertRaises(AssertionError):
                        guard.restore(name, candidate)
        for name in ('docs/future.md', 'src/gameplay_rules/engine.py', Path('README.md'), None):
            with self.subTest(path=name), self.assertRaises(AssertionError):
                guard.restore(name, b'')

    def test_unchanged_size_historical_text_and_prefix_tampering_reject(self):
        for name in guard.DOCUMENTS:
            raw = (guard.ROOT / name).read_bytes()
            boundary = guard.ledger()['replacements'][name]['edits'][0]['end']
            for index in (0, boundary, len(raw) - 1):
                altered = raw[:index] + bytes([raw[index] ^ 1]) + raw[index + 1:]
                with self.subTest(path=name, offset=index), self.assertRaises(AssertionError):
                    guard.restore(name, altered)

    def test_coherently_rehashed_ledger_is_not_an_approved_successor(self):
        value = guard.ledger()
        value['replacements']['README.md']['new'] = pin(b'forged replacement')
        raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'successors.json'
            path.write_bytes(raw)
            with patch.object(guard, 'LEDGER', path), self.assertRaises(AssertionError):
                guard.restore('README.md', b'forged replacement')

    def test_unrelated_files_remain_visible_to_original_validators(self):
        raw = b'unrecognized changed runtime bytes'
        self.assertEqual(guard.preceding_bytes('src/gameplay_rules/engine.py', raw), raw)
        with self.assertRaises(AssertionError):
            guard.preceding_bytes('README.md', bytearray(raw))

    def test_new_document_pins_and_relative_links(self):
        texts = {}
        for name, expected in guard.ledger()['additions'].items():
            raw = (guard.ROOT / name).read_bytes()
            from vision_alignment_preservation import preceding_bytes
            raw = preceding_bytes(name, raw)
            self.assertEqual(pin(raw), expected)
            texts[name] = raw.decode()
        for name in guard.DOCUMENTS:
            row = guard.ledger()['replacements'][name]
            texts[name] = row['edits'][0]['new']
        for name, text in texts.items():
            for target in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)', text):
                if target.startswith(('https://', 'http://')):
                    continue
                file, _, fragment = unquote(target).partition('#')
                path = (guard.ROOT / name).parent / file if file else guard.ROOT / name
                with self.subTest(document=name, link=target):
                    self.assertTrue(path.resolve().is_relative_to(guard.ROOT))
                    self.assertTrue(path.is_file())
                    if fragment:
                        headings = re.findall(r'^#{1,6}\s+(.+)$', path.read_text(), re.MULTILINE)
                        anchors = {re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-') for h in headings}
                        self.assertIn(fragment, anchors)

    def test_vision_is_stable_and_governance_retains_owner_control(self):
        vision = (guard.ROOT / 'VISION.md').read_text()
        governance = (guard.ROOT / 'docs/GOVERNANCE.md').read_text()
        self.assertNotRegex(vision, r'PR\s*#\d|\b\d+%|PROPOSED_NOT_AUTHORIZED|Structural Inventory V1')
        for phrase in ('First useful release', 'Ultimate research vision', 'aspirational research benchmark',
                       'separate Project Owner approval'):
            self.assertIn(phrase, vision)
        for phrase in ('Card Reseller ChatGPT', 'not a mandatory gate', 'MERGE, REVISE or HOLD',
                       'operation-specific source-use permissions', 'Update only documentation materially affected'):
            self.assertIn(phrase, governance)
        roadmap = guard.ledger()['replacements']['docs/ROADMAP.md']['edits'][0]['new']
        self.assertIn('Structural Inventory V1 — PROPOSED_NOT_AUTHORIZED', roadmap)
        self.assertIn('Whole-artifact transient structural parsing', roadmap)
        self.assertIn('Private derived metadata retention', roadmap)
        self.assertIn('Any proposed public metadata publication', roadmap)


if __name__ == '__main__':
    unittest.main()
