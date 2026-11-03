"""Actual accepted-evidence admission and compact explanation regressions.

Expanded publication catalogs must reject the fixed attachment. Tests never
substitute a historical positive catalog and add no source-dependent skips.
"""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import contract as c, land_decision as decision
from land_test_support import ROOT, current_catalog_intact
from test_land_decision import decision_arguments, cli_arguments


CARD_SUBJECTS = {
    'Snow-Covered Wastes': ('snow-wastes-mana',),
    'Rishadan Port': ('port-mana', 'port-utility'),
    'City of Brass': ('city-mana', 'city-damage-trigger'),
    'Tarnished Citadel': ('citadel-colorless', 'citadel-color-choice'),
    'Cabal Coffers': ('coffers-mana',),
    'Command Tower': ('tower-mana',),
}
GROUPS = {
    'mana-and-utility': ('snow-wastes-mana', 'port-mana', 'port-utility'),
    'damage-ownership': ('city-mana', 'city-damage-trigger', 'citadel-colorless', 'citadel-color-choice'),
    'variable-output': ('snow-wastes-mana', 'coffers-mana'),
    'color-context': ('tower-mana', 'city-mana'),
}


def values(node):
    yield node
    children = node.values() if type(node) is dict else node if type(node) is list else ()
    for child in children:
        yield from values(child)


def pointer(node, path):
    for name in path.lstrip('/').split('/'):
        name = name.replace('~1', '/').replace('~0', '~')
        node = node[int(name)] if type(node) is list else node[name]
    return node


class LandExplanationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from card_rules_pilot import land_explanation as e
        from card_rules_pilot import land_explanation_policy as policy
        cls.e, cls.policy = e, policy
        cls.intact = current_catalog_intact(unittest.TestCase())
        cls.consumer = e.load_land_explanations(**decision_arguments()) if cls.intact else None
        if cls.intact:
            cls.overview = decision.load_land_decision(**decision_arguments()).historical_overview().to_dict()

    def admitted(self):
        if self.intact:
            return True
        self.assertFalse(current_catalog_intact(self))
        with self.assertRaises(ValueError):
            self.e.load_land_explanations(**decision_arguments())
        return False

    def docs(self):
        return ([self.consumer.explain_subject(sid) for sid in decision.SUBJECT_IDS]
            + [self.consumer.explain_card(name) for name in CARD_SUBJECTS]
            + [self.consumer.compare(name) for name in GROUPS])

    def run_cli(self, command, *suffix, json_mode=True):
        return subprocess.run([sys.executable, '-m', 'card_rules_pilot.land_explanation_cli',
            '--review-root', str(ROOT / 'reference-reviews'), command,
            *cli_arguments(), *suffix, *(['--json'] if json_mode else [])],
            cwd=ROOT, capture_output=True, env=dict(os.environ,
                PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1'))

    def test_actual_nine_subjects_six_cards_four_comparisons(self):
        if not self.admitted(): return
        self.assertEqual(self.consumer.subject_ids, decision.SUBJECT_IDS)
        self.assertEqual(set(self.consumer.card_names), set(CARD_SUBJECTS))
        self.assertEqual(set(self.consumer.comparison_names), set(GROUPS))
        for document in self.docs():
            view = document.to_dict()
            self.assertEqual(view['decision_id'], decision.DECISION_ID)
            self.assertEqual(view['approved_collection_id'], decision.COLLECTION_ID)
            self.assertEqual(view['decision_status'], 'ACCEPTED_BOUNDED_RETAINED_TEXT')
            self.assertEqual(self.consumer.validate_report(view).to_json(), document.to_json())
            self.assertEqual(self.consumer.parse_report(document.to_json().encode()).to_json(), document.to_json())

    def test_unsupported_selectors_never_substitute_another_card_or_inference(self):
        if not self.admitted(): return
        for method, selectors in (
                (self.consumer.explain_subject, ('foreign', 'tower-mana-extra', True, None, [])),
                (self.consumer.explain_card, ('Nykthos', 'Command tower', 'best land', True, None)),
                (self.consumer.compare, ('best-land', 'variable-output-extra', True, None)),
                (self.consumer.provenance, ('foreign', True, None))):
            for selector in selectors:
                with self.subTest(selector=selector), self.assertRaisesRegex(ValueError, 'unsupported'):
                    method(selector)
        result = self.run_cli('card', 'Nykthos')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'unsupported', result.stderr.lower())

    def test_immutable_owned_reports_return_independent_decoded_views(self):
        if not self.admitted(): return
        document = self.consumer.explain_subject('citadel-color-choice')
        raw = document.to_json()
        view = document.to_dict(); view.clear()
        self.assertEqual(document.to_json(), raw)
        self.assertEqual(self.consumer.explain_subject('citadel-color-choice').to_json(), raw)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            self.consumer._snapshot = b'{}'
        with self.assertRaises(TypeError):
            self.e.LandExplanationConsumer(b'{}')

    def test_report_exact_reproduction_rejects_rehashed_unknown_fields_and_types(self):
        if not self.admitted(): return
        original = self.consumer.explain_subject('coffers-mana').to_dict()
        mutations = []
        for key, val in (('schema_version', 'foreign-v9'), ('decision_id', 'sha256:' + '0' * 64),
                         ('selector', 'port-mana'), ('future_claim', 'universally strongest')):
            changed = deepcopy(original); changed[key] = val; mutations.append(changed)
        for changed in mutations:
            changed = c.seal(self.e.REPORT_VERSION, changed, 'report_id')
            with self.assertRaises(ValueError): self.consumer.validate_report(changed)
        for raw in (b'{"kind":"subject","kind":"subject"}\n', b'{}', b'{"kind":NaN}\n',
                    b'{"kind":1.0}\n', b'{"kind":true}\n'):
            with self.assertRaises(ValueError): self.consumer.parse_report(raw)
        for value in ({}, True, {'kind': True}, {'kind': 'subject', 'selector': 'foreign'}):
            with self.assertRaises(ValueError): self.consumer.validate_report(value)

    def test_exact_decision_pin_and_coherently_rehashed_owner_tampering_reject(self):
        if not self.admitted(): return
        with self.assertRaises(ValueError):
            self.e.load_land_explanations(**decision_arguments(expected_decision_id='sha256:' + '0' * 64))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'decision'
            shutil.copytree(decision_arguments()['decision_root'], root)
            path = root / decision.OWNER_RECORD
            record = c.read_json(path)
            record['scope']['not_established'] = []
            record = c.seal(decision.DECISION_VERSION, record, 'decision_id')
            self.assertNotEqual(record['decision_id'], decision.DECISION_ID)
            path.write_bytes(c.canonical(record))
            with self.assertRaises(ValueError):
                self.e.load_land_explanations(**decision_arguments(decision_root=root))
            with self.assertRaises(ValueError):
                self.e.load_land_explanations(**decision_arguments(decision_root=root,
                    expected_decision_id=record['decision_id']))

    def test_fresh_admission_revalidates_retained_evidence_and_owns_prior_snapshot(self):
        if not self.admitted(): return
        before = self.consumer.explain_subject('snow-wastes-mana').to_json()
        from card_rules_pilot import land_authored
        with tempfile.TemporaryDirectory() as directory:
            cohort = Path(directory) / 'cohort'
            shutil.copytree(decision_arguments()['cohort_root'], cohort)
            first = self.e.load_land_explanations(**decision_arguments(cohort_root=cohort))
            path = cohort / 'interpretations.json'
            interpretations = c.read_json(path)
            candidate = interpretations['candidates'][0]
            candidate['descriptive_readings']['output']['written_instruction'] = 'Add {B}.'
            interpretations['candidates'][0] = c.seal(candidate['schema_version'], candidate, 'candidate_id')
            interpretations = c.seal(interpretations['schema_version'], interpretations, 'interpretations_id')
            plan = c.read_json(cohort / 'plan.json')
            path.write_bytes(c.canonical(interpretations))
            (cohort / 'manifest.json').write_bytes(c.canonical(land_authored.build_manifest(plan, interpretations)))
            with self.assertRaises(ValueError):
                self.e.load_land_explanations(**decision_arguments(cohort_root=cohort))
            self.assertEqual(first.explain_subject('snow-wastes-mana').to_json(), before)
        self.assertEqual(self.consumer.explain_subject('snow-wastes-mana').to_json(), before)

    def test_public_cli_and_api_are_deterministic_and_read_only(self):
        if not self.admitted(): return
        roots = [ROOT / 'data/review', ROOT / 'reference-reviews']
        paths = [path for root in roots for path in root.rglob('*') if path.is_file()]
        def snapshot():
            return {str(path): (path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
                    for path in paths}
        before = snapshot()
        document = self.consumer.explain_subject('coffers-mana')
        result = self.run_cli('subject', 'coffers-mana')
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result.stdout, document.to_json().encode())
        readable = self.run_cli('subject', 'coffers-mana', json_mode=False)
        self.assertEqual(readable.returncode, 0, readable.stderr.decode())
        self.assertEqual(readable.stdout.decode(), self.e.render_land_explanation(document))
        self.consumer.check()
        self.consumer.provenance('coffers-mana')
        self.assertEqual(snapshot(), before)

    def test_compact_rendering_provenance_and_generic_label_independence(self):
        if not self.admitted(): return
        for doc in self.docs():
            view = doc.to_dict()
            rendered = self.e.render_land_explanation(doc)
            self.assertLessEqual(len(doc.to_json().encode()), self.e.REPORT_LIMIT)
            self.assertLessEqual(len(rendered.encode()), self.e.READABLE_LIMIT)
            for row in view['subjects']:
                for finding in row['findings']:
                    self.assertIn(finding['text'], rendered)
                    candidate = next(c for c in self.overview['context']['interpretations']['candidates'] if c['subject']['subject_id'] == row['subject_id'])
                    assessment = next(a for a in self.overview['assessments'] if a['subject_id'] == row['subject_id'])
                    for path in finding['premise_paths']:
                        pointer({'candidate': candidate, 'assessment': assessment}, path)
            self.assertEqual(self.consumer.detailed(view['detailed']).to_dict(), self.overview)
        original = self.consumer.explain_subject('citadel-color-choice').to_dict()
        altered = deepcopy(original['detailed']); altered['sha256'] = '0' * 64
        with self.assertRaises(ValueError): self.consumer.detailed(altered)
        for candidate in self.overview['context']['interpretations']['candidates']:
            assessment = next(a for a in self.overview['assessments'] if a['subject_id'] == candidate['subject']['subject_id'])
            args = dict(readings=candidate['descriptive_readings'], classification=assessment['classification'], behavior=assessment['behavior'], composition=assessment['additional_effect_composition'], unknowns=candidate['unresolved'])
            expected = self.policy.compute(**args)
            args = deepcopy(args)
            args['readings']['effect_ownership']['owner_subject_id'] = 'unrelated-label'
            args['readings']['effect_ownership']['card_id'] = 'unrelated-card'
            args['composition']['pending_effect_ownership'] = args['readings']['effect_ownership']
            self.assertEqual(expected, self.policy.compute(**args))

    def test_cli_has_no_mutation_or_general_query_language(self):
        from card_rules_pilot import land_explanation_cli as cli
        for command in ('approve', 'write', 'ingest', 'activate', 'query', 'simulate'):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    cli.parser().parse_args(['--review-root', str(ROOT / 'reference-reviews'), command])
                self.assertEqual(raised.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
