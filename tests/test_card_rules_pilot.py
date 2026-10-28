"""Fixed retained-evidence review contract; no test asserts real semantic truth."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import contract as c
from card_rules_pilot import pilot as p
from card_rules_pilot import cards
from test_card_rules_pilot_cards import current_catalog_intact


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'data/review/card-rules-mana-pilot/plan.json'
SUBJECTS = tuple(row[0] for row in cards.SUBJECTS)


def load(**changes):
    arguments = dict(catalog_root=ROOT, mechanical_root=ROOT,
        review_root=ROOT / 'reference-reviews', plan_path=PLAN,
        expected_profile_id=cards.PROFILE_ID, expected_query_snapshot_id=cards.QUERY_ID,
        expected_plan_id=p.PLAN_ID)
    arguments.update(changes)
    return p.load_pilot(**arguments)


class ReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Actual publication validates the live expanded writer catalog. The
        # fixed attachment must reject that input, never substitute old data.
        cls.pilot = load() if current_catalog_intact(unittest.TestCase()) else None

    def current(self):
        if self.pilot is None:
            self.assertFalse(current_catalog_intact(self))
            return False
        return True

    def candidate(self, subject=SUBJECTS[0]):
        return self.pilot.subject(subject).to_dict()

    def reject(self, value):
        value = c.seal(c.CANDIDATE_VERSION, value, 'candidate_id')
        with self.assertRaises(c.PilotError):
            self.pilot.validate_candidate(value)

    def test_exact_seven_local_subjects_and_six_card_bindings(self):
        if not self.current():
            return
        expected_cards = {row[0] for row in cards.CARD_BINDINGS}
        documents = [self.candidate(subject) for subject in SUBJECTS]
        self.assertEqual(len(documents), 7)
        self.assertEqual(len(expected_cards), 6)
        self.assertEqual({row['subject']['card_id'] for row in documents}, expected_cards)
        self.assertEqual(len({row['candidate_id'] for row in documents}), 7)
        for subject in ('Sol Ring', 'unknown-subject', cards.CARD_BINDINGS[0][0], '', None, 1, True):
            with self.subTest(subject=subject), self.assertRaises(c.PilotError):
                self.pilot.subject(subject)

    def test_rehashed_authority_upgrades_and_foreign_fields_reject(self):
        if not self.current():
            return
        for field, value in (('canonical_admission', True), ('execution_authority', 'READY'),
                             ('is_mana_ability', True), ('legal', True), ('can_activate', True)):
            with self.subTest(field=field):
                row = self.candidate()
                row[field] = value
                self.reject(row)
        for status, attestation in (('approved', None), ('requires_review', 'owner-approved'),
                                    ('requires_review', {})):
            row = self.candidate()
            row['review'] = dict(status=status, human_attestation=attestation, canonical_admission=False)
            self.reject(row)
        row = self.candidate()
        row['review']['canonical_admission'] = True
        self.reject(row)

    def test_strict_scalar_types_are_not_repaired(self):
        for value in (float('nan'), float('inf'), float('-inf'), 1.0, (1,), {1: 'fictional'},
                      {'fictional': 2**63}, {'fictional': object()}):
            with self.subTest(value=type(value).__name__), self.assertRaises(c.PilotError):
                c.owned(value)
        if not self.current():
            return
        for value in (1, 0, 1.0, 0.0, 'false', None):
            with self.subTest(value=value):
                row = self.candidate()
                row['review']['canonical_admission'] = value
                if type(value) is float:
                    with self.assertRaises(c.PilotError):
                        c.seal(c.CANDIDATE_VERSION, row, 'candidate_id')
                else:
                    self.reject(row)

    def test_duplicate_json_noncanonical_and_bounded_inputs(self):
        # Clearly fictional representation fixtures, without source authority.
        for raw in (b'{"fictional":1,"fictional":2}\n', b'{"fictional":NaN}\n',
                    b'{"fictional":Infinity}\n', b'{ "fictional":true}\n', b'[]',
                    b'{"fictional":1.0}\n', b'\xff\n'):
            with self.subTest(raw=raw), self.assertRaises(c.PilotError):
                c.parse_json(raw)
        with self.assertRaises(c.PilotError):
            c.parse_json(b'{}\n', limit=2)
        node = None
        for _ in range(22):
            node = [node]
        with self.assertRaises(c.PilotError):
            c.owned(node)
        for value in ({'x' * 129: 'fictional'}, {'fictional': 'x' * 16385}, [None] * 100_001):
            with self.assertRaises(c.PilotError):
                c.owned(value)

    def test_input_file_symlink_hardlink_and_read_only_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular = root / 'fictional.json'
            regular.write_bytes(c.canonical({'fictional': True}))
            before = regular.read_bytes()
            self.assertEqual(c.read_json(regular), {'fictional': True})
            alias = root / 'alias.json'
            alias.symlink_to(regular)
            with self.assertRaises(c.PilotError):
                c.read_json(alias)
            alias.unlink()
            os.link(regular, alias)
            with self.assertRaises(c.PilotError):
                c.read_json(regular)
            self.assertEqual(regular.read_bytes(), before)

    def test_canonical_identity_domain_and_owned_views(self):
        if not self.current():
            return
        original = self.pilot.subject(SUBJECTS[0])
        before = original.to_json()
        row = original.to_dict()
        own = row['candidate_id']
        self.assertEqual(own, c.identity(c.CANDIDATE_VERSION, row, 'candidate_id'))
        self.assertNotEqual(own, c.identity(c.REPORT_VERSION, row, 'candidate_id'))
        row['canonical_admission'] = True
        row.clear()
        self.assertEqual(original.to_json(), before)
        caller = json.loads(before)
        validated = self.pilot.validate_candidate(caller)
        caller['subject']['selected_passage'] = 'fictional caller mutation'
        self.assertEqual(validated.to_json(), before)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            original._raw = b'{}\n'
        report = self.pilot.comparison()
        report_before = report.to_json()
        decoded = report.to_dict()
        decoded.clear()
        self.assertEqual(report.to_json(), report_before)

    def test_pending_envelope_always_visible(self):
        if not self.current():
            return
        for subject in SUBJECTS:
            with self.subTest(subject=subject):
                row = self.candidate(subject)
                self.assertEqual(row['review'], {'status': 'requires_review', 'human_attestation': None,
                                                 'canonical_admission': False})
                self.assertIs(row['review']['canonical_admission'], False)
                self.assertEqual(row['execution_authority'], 'BLOCKED')
                self.assertNotIn('is_mana_ability', row)
                self.assertNotIn('legal', row)
                self.assertNotIn('can_activate', row)

    def test_exact_plan_drift_rehashed_plan_and_wrong_expected_identity_reject(self):
        for expected in ('sha256:' + '0' * 64, cards.QUERY_ID, True, 1):
            with self.subTest(expected=expected), self.assertRaises(c.PilotError):
                load(expected_plan_id=expected)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.json'
            for change in ('timestamp', 'duplicate-subject', 'extra-field', 'foreign-card', 'criterion'):
                row = p.fixed_plan()
                if change == 'timestamp':
                    row['prepared_at'] = '2026-10-27T00:00:00Z'
                elif change == 'duplicate-subject':
                    row['subjects'].append(deepcopy(row['subjects'][0]))
                elif change == 'extra-field':
                    row['approval'] = True
                elif change == 'foreign-card':
                    row['subjects'][0]['card_id'] = cards.CARD_BINDINGS[1][0]
                else:
                    row['subjects'][0]['criteria'].pop()
                path.write_bytes(c.canonical(c.seal(c.PLAN_VERSION, row, 'plan_id')))
                with self.subTest(change=change), self.assertRaises(c.PilotError):
                    load(plan_path=path)

    def test_every_2026_criterion_and_material_unknown_is_retained(self):
        if not self.current():
            return
        expected = ['activated_kind', 'no_target', 'potential_mana', 'not_loyalty',
            'no_library_cost_movement', 'no_library_effect_movement',
            'self_replacement_considered', 'other_replacements_disregarded',
            'triggered_kind', 'trigger_no_target', 'trigger_potential_mana',
            'qualifying_trigger_relationship']
        for subject in SUBJECTS:
            row = self.candidate(subject)
            matrix = row['authored_interpretation']['criteria']
            self.assertEqual([cell['criterion_id'] for cell in matrix], expected)
            self.assertEqual(row['material_unresolved_criteria'], [cell['criterion_id'] for cell in matrix
                if cell['state'] in ('unknown', 'unsupported', 'conflicting')])
            for cell in matrix:
                self.assertTrue(cell['rationale'])
                self.assertTrue(cell['limitations'])
                self.assertTrue(cell['evidence_refs'])
            if subject in ('sol-ring-tap', 'basalt-monolith-tap', 'deathrite-shaman-first'):
                self.assertIn('self_replacement_considered', row['material_unresolved_criteria'])

    def test_missing_duplicate_criteria_and_unsupported_upgrades_reject(self):
        if not self.current():
            return
        for transform in ('missing', 'duplicate', 'upgrade', 'erase-unresolved'):
            row = self.candidate()
            matrix = row['authored_interpretation']['criteria']
            if transform == 'missing':
                matrix.pop()
            elif transform == 'duplicate':
                matrix.append(deepcopy(matrix[0]))
            elif transform == 'upgrade':
                matrix[6]['state'] = 'proposed_satisfied'
                matrix[6]['limitations'] = []
            else:
                row['material_unresolved_criteria'] = []
            with self.subTest(transform=transform):
                self.reject(row)

    def test_wrong_card_source_field_passage_dossier_rule_anchor_package_release_reject(self):
        if not self.current():
            return
        operations = {
            'card': lambda r: r['subject'].__setitem__('card_id', cards.CARD_BINDINGS[1][0]),
            'row': lambda r: r['card_evidence']['source'].__setitem__('source_record_index', 0),
            'row-type': lambda r: r['card_evidence']['source'].__setitem__('source_record_index', True),
            'field': lambda r: r['subject'].__setitem__('source_field_pointer', '/produced_mana'),
            'passage': lambda r: r['subject'].__setitem__('selected_passage', '{3}: Untap this artifact.'),
            'field-identity': lambda r: r['subject'].__setitem__('source_field_identity', 'sha256:' + '0' * 64),
            'dossier': lambda r: r['subject'].__setitem__('mechanical_dossier_id', cards.CARD_BINDINGS[1][2]),
            'provider-record': lambda r: r['card_evidence']['source'].__setitem__('record_content_identity', 'sha256:' + '1' * 64),
            'rule': lambda r: r['rules_evidence']['rules'][0]['rule'].__setitem__('rule_reference', '605.6'),
            'anchor': lambda r: r['rules_evidence']['rules'][0]['rule']['source_anchor'].__setitem__('rule_reference', '605.6'),
            'package': lambda r: r['rules_evidence']['packages'][0].__setitem__('package_id', 'sha256:' + '2' * 64),
            'release': lambda r: r['rules_evidence']['source_binding'].__setitem__('effective_date', '2026-10-26'),
            'target-count': lambda r: r['authored_interpretation']['criteria'][1].__setitem__('chosen_target_count', 0),
        }
        for name, operation in operations.items():
            with self.subTest(binding=name):
                row = self.candidate()
                operation(row)
                self.reject(row)

    def test_ownership_and_complete_context_are_not_borrowed(self):
        if not self.current():
            return
        tap = self.candidate('basalt-monolith-tap')
        untap = self.candidate('basalt-monolith-untap')
        self.assertEqual(tap['subject']['card_id'], untap['subject']['card_id'])
        self.assertNotEqual(tap['subject']['selected_passage'], untap['subject']['selected_passage'])
        tap['subject']['selected_passage'] = untap['subject']['selected_passage']
        self.reject(tap)
        plunderer = self.candidate('pitiless-plunderer-host-trigger')
        self.assertNotIn('Sacrifice', plunderer['subject']['selected_passage'])
        self.assertIn('Sacrifice', plunderer['subject']['complete_field_value'])
        self.assertEqual(plunderer['subject']['owner'], 'host_card')
        plunderer['subject']['owner'] = 'created_treasure'
        self.reject(plunderer)
        deathrite = self.candidate('deathrite-shaman-first')
        self.assertIn('target land card', deathrite['subject']['selected_passage'])
        self.assertNotEqual(deathrite['subject']['selected_passage'], deathrite['subject']['complete_field_value'])
        ritual = self.candidate('dark-ritual-spell')
        self.assertEqual(ritual['subject']['owner'], 'host_spell')
        self.assertEqual(ritual['subject']['type_line']['value'], 'Instant')

    def test_readable_comparison_keeps_every_candidate_context_and_limit(self):
        if not self.current():
            return
        from card_rules_pilot.pilot import render
        report = self.pilot.comparison()
        text = render(report)
        self.assertEqual(len(report.to_dict()['candidates']), 7)
        for subject in SUBJECTS:
            row = self.candidate(subject)
            self.assertIn(subject, text)
            self.assertIn(row['subject']['complete_field_value'], text)
            for limitation in row['authored_interpretation']['missing_requirements']:
                self.assertIn(limitation, text)
        self.assertIn('2026-09-25', text)
        self.assertIn('2026-08-02', text)
        self.assertIn('requires_review', text)
        self.assertIn('execution_authority=BLOCKED', text)

    def test_actual_cli_subject_comparison_deterministic_and_read_only(self):
        if not self.current():
            return
        command = [sys.executable, '-m', 'card_rules_pilot',
            '--catalog-root', str(ROOT), '--mechanical-root', str(ROOT),
            '--review-root', str(ROOT / 'reference-reviews'), '--plan', str(PLAN),
            '--expected-profile-id', cards.PROFILE_ID,
            '--expected-query-snapshot-id', cards.QUERY_ID, '--expected-plan-id', p.PLAN_ID]
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')
        review = PLAN.parent
        before = {path.name: path.read_bytes() for path in review.iterdir() if path.is_file()}
        manifest = self.pilot.reproduction_manifest()
        checked = c.canonical({'check': 'EXACT_REPRODUCTION', 'plan_id': self.pilot.plan_id,
            'report_id': manifest['report_id'], 'manifest_id': manifest['manifest_id'],
            'subjects': 7, 'review_status': 'requires_review', 'execution_authority': 'BLOCKED'}).decode()
        for suffix, expected in ((['subject', SUBJECTS[0], '--json'], self.pilot.subject(SUBJECTS[0]).to_json()),
                                 (['compare', '--json'], self.pilot.comparison().to_json()), (['check'], checked)):
            result = subprocess.run(command + suffix, cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, expected)
        after = {path.name: path.read_bytes() for path in review.iterdir() if path.is_file()}
        self.assertEqual(before, after)

    def test_real_candidates_cannot_cross_into_facts_or_fictional_models(self):
        if not self.current():
            return
        from card_intelligence.models import KnowledgeValidationError
        from card_intelligence.repository import KnowledgeRepository
        from gameplay_rules.errors import GameplayContractError
        from proposed_spell_packets.validation import validate_packet
        from proposed_spell_packets.conditions import ConditionModel as V1
        from proposed_spell_packets.conditions_v2 import ConditionModel as V2
        document = self.pilot.subject(SUBJECTS[0])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(KnowledgeValidationError):
                KnowledgeRepository(Path(directory)).append(document)
            self.assertEqual(list(Path(directory).rglob('*')), [])
        for consume in (validate_packet, V1, V2):
            with self.subTest(consumer=consume), self.assertRaises(GameplayContractError):
                consume(document.to_dict())

    def test_loaded_snapshot_is_independent_of_mutable_module_authoring_inputs(self):
        if not self.current():
            return
        before = self.pilot.subject(SUBJECTS[0]).to_json()
        report_before = self.pilot.comparison().to_json()
        with patch.object(p, 'REVIEW', {'status': 'approved', 'human_attestation': 'fictional',
                                      'canonical_admission': True}), \
             patch.object(p, 'LIMITATIONS', ('fictional module mutation',)), \
             patch.object(p, 'PLAN_BODY', {'fictional': True}):
            self.assertEqual(self.pilot.subject(SUBJECTS[0]).to_json(), before)
            self.assertEqual(self.pilot.comparison().to_json(), report_before)

    def test_small_manifest_exactly_binds_complete_reproduced_outputs(self):
        if not self.current():
            return
        manifest = self.pilot.reproduction_manifest()
        self.assertEqual(manifest, c.read_json(PLAN.parent / 'manifest.json', limit=c.PLAN_LIMIT))
        candidates = b''.join(self.pilot.subject(subject).to_json().encode() for subject in SUBJECTS)
        report = self.pilot.comparison().to_json().encode()
        for name, raw in (('candidates.jsonl', candidates), ('comparison.json', report)):
            self.assertEqual(manifest['artifacts'][name],
                             {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        self.assertEqual(manifest['report_id'], self.pilot.comparison().to_dict()['report_id'])
        before = deepcopy(manifest)
        manifest['artifacts'].clear()
        self.assertEqual(self.pilot.reproduction_manifest(), before)
        self.assertLess(len(c.canonical(before)), c.PLAN_LIMIT)


if __name__ == '__main__':
    unittest.main()
