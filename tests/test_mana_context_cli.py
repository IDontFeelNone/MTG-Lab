"""Actual successor public boundaries; no semantic approval or catalog fallback.

The expanded catalog created by the real publication writer must reject. These
checks never install historical positive fixtures. External-source reproduction
is separately identified and explicitly skipped when its selector is absent.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from card_rules_pilot import cards, pilot
from test_card_rules_pilot_cards import current_catalog_intact

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / 'reference-reviews'
PLAN = ROOT / 'data/review/card-rules-mana-pilot/plan.json'
SUCCESSOR = ROOT / 'data/review/mana-context-reassessment'
SOURCE_PACKAGE = REVIEWS / 'gameplay-rules-mana-classification-source-context'
SUBJECTS = tuple(row[0] for row in cards.SUBJECTS)
ENV = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')


def arguments():
    return dict(catalog_root=ROOT, mechanical_root=ROOT, review_root=REVIEWS,
        plan_path=PLAN, successor_root=SUCCESSOR,
        expected_profile_id=cards.PROFILE_ID, expected_query_snapshot_id=cards.QUERY_ID,
        expected_plan_id=pilot.PLAN_ID)


def common_arguments():
    return ['--catalog-root', str(ROOT), '--mechanical-root', str(ROOT),
        '--plan', str(PLAN), '--successor-root', str(SUCCESSOR),
        '--expected-profile-id', cards.PROFILE_ID,
        '--expected-query-snapshot-id', cards.QUERY_ID, '--expected-plan-id', pilot.PLAN_ID]


def run_cli(*suffix):
    return subprocess.run([sys.executable, '-m', 'card_rules_pilot.reassessment_cli',
        '--review-root', str(REVIEWS), *suffix], cwd=ROOT, env=ENV, capture_output=True)


def selected_snapshot():
    # Bound this observation to actual selected Card, source and review evidence.
    # The canonical profile controls its catalog file closure and namespace names.
    profile_path = ROOT / 'config/catalog_profiles/legacy-public-tier-a.json'
    profile = json.loads(profile_path.read_bytes())
    paths = {profile_path, ROOT / cards.DOSSIER_REFERENCE, ROOT / cards.MANIFEST_REFERENCE}
    paths.update(ROOT / row['path'] for row in profile['files'])
    directories = [PLAN.parent, SUCCESSOR, SOURCE_PACKAGE,
        ROOT / 'data/market/acquisitions' / cards.ACQUISITION]
    directories.extend(REVIEWS / name for name in (
        'gameplay-rules-bounded-mana-ability-projection',
        'gameplay-rules-bounded-mana-classification-projection',
        'gameplay-rules-bounded-mana-stack-exception-projection',
        'gameplay-rules-bounded-activated-ability-procedure-projection',
        'gameplay-rules-artifact-verification'))
    membership = {}
    for directory in directories:
        entries = list(directory.iterdir())
        membership[str(directory)] = tuple(sorted(p.name for p in entries))
        paths.update(p for p in entries if p.is_file())
    fingerprints = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    return membership, fingerprints


class ActualManaContextCLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from card_rules_pilot import reassessment as successor
        cls.successor = successor
        cls.intact = current_catalog_intact(unittest.TestCase())
        cls.context = successor.load_reassessment(**arguments()) if cls.intact else None

    def current(self):
        if not self.intact:
            self.assertFalse(current_catalog_intact(self))
            with self.assertRaises(ValueError):
                self.successor.load_reassessment(**arguments())
            process = run_cli('compare', *common_arguments(), '--json')
            self.assertEqual(process.returncode, 2, process.stderr.decode())
            self.assertEqual(process.stdout, b'')
            return False
        return True

    def test_actual_seven_subject_comparison_and_check_canonical_parity_read_only(self):
        if not self.current():
            return
        before = selected_snapshot()
        pairs = [(['subject', subject], self.context.subject(subject)) for subject in SUBJECTS]
        pairs += [(['compare'], self.context.comparison()), (['check'], self.context.check())]
        for suffix, document in pairs:
            with self.subTest(command=suffix):
                process = run_cli(suffix[0], *common_arguments(), *suffix[1:], '--json')
                self.assertEqual(process.returncode, 0, process.stderr.decode())
                self.assertEqual(process.stdout, document.to_json().encode())
                self.assertEqual(selected_snapshot(), before)
        process = run_cli('compare', *common_arguments())
        self.assertEqual(process.returncode, 0, process.stderr.decode())
        self.assertEqual(process.stdout.decode(), self.successor.render_reassessment(self.context.comparison()))
        self.assertEqual(selected_snapshot(), before)

    def test_actual_historical_cli_outputs_reproduce_all_six_protected_identities(self):
        if not self.current():
            return
        before = selected_snapshot()
        common = common_arguments()
        offset = common.index('--successor-root')
        del common[offset:offset + 2]
        command = [sys.executable, '-m', 'card_rules_pilot', '--review-root', str(REVIEWS), *common]
        expected = {
            'compare': ('sha256:a2b0dedc3ef68b779b5b3a36ec20f97afc348b1ce52ad79c9e4a3cd2a281da0c',
                'e7f2e4b75131845e9b04a73f2cade86a225f4ec013a1797633cbb1bd669eeb70', 740979),
            'analyze-all': ('sha256:40eeaca91627b97aaca9372d56dc7cef9ee8ef8ce60d9dff503aa1d10be941d4',
                '111474e170a02fd081aa465650a279cd812ed9e77801b94d96c10d01fc4bae7c', 814245),
            'review-impact': ('sha256:69f04d914ae6653739f2c79f1849e9b54764e475035f71d30cef556f7e9b6014',
                '28cc83693b05af29a476cf45ae16dc93548855bb3b14eb3af10434ca0f2074c3', 850692)}
        for action, (identity, digest, length) in expected.items():
            with self.subTest(command=action):
                process = subprocess.run([*command, action, '--json'], cwd=ROOT, env=ENV, capture_output=True)
                self.assertEqual(process.returncode, 0, process.stderr.decode())
                self.assertEqual(len(process.stdout), length)
                self.assertEqual(hashlib.sha256(process.stdout).hexdigest(), digest)
                value = json.loads(process.stdout)
                self.assertEqual(value['report_id'], identity)
                self.assertEqual(value['plan_id'] if action == 'compare' else
                    value['context']['original_comparison']['plan_id'], pilot.PLAN_ID)
                if action != 'compare':
                    self.assertEqual(value['policy']['policy_id'],
                        'sha256:5694ec96c5edcbe61895684c6885e556578b738f27a29154d95283542b1ed745')
        process = subprocess.run([*command, 'check'], cwd=ROOT, env=ENV, capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr.decode())
        checked = json.loads(process.stdout)
        self.assertEqual(checked['check'], 'EXACT_REPRODUCTION')
        self.assertEqual(checked['plan_id'], 'sha256:acdfc01e0645dc788a5c04824cb40948377699fe9f047441500980578fb9aa83')
        self.assertEqual(checked['manifest_id'], 'sha256:7243ed93272b488b3dd50eb6ea712ca0dda4d6ea2fec6567259455f61b5d8762')
        self.assertEqual(selected_snapshot(), before)


class ManaContextSourceCLITests(unittest.TestCase):
    def test_invalid_fictional_source_rejects_before_creating_build_output(self):
        # This is a negative boundary fixture, never source verification evidence.
        with tempfile.TemporaryDirectory(prefix='mtglab-mana-cli-negative-') as temporary:
            root = Path(temporary)
            artifact = root / 'fictional-invalid-source.txt'
            artifact.write_bytes(b'fictional negative boundary fixture\n')
            destination = root / 'must-not-be-created'
            process = run_cli('build-source', '--artifact', str(artifact), '--output', str(destination))
            self.assertEqual(process.returncode, 2, process.stderr.decode())
            self.assertEqual(process.stdout, b'')
            self.assertFalse(destination.exists())
            self.assertEqual(artifact.read_bytes(), b'fictional negative boundary fixture\n')

    def test_actual_external_source_cli_reproduction_and_conflicting_build_rejection(self):
        selector = os.environ.get('MTGLAB_MANA_CONTEXT_SOURCE')
        if not selector:
            self.skipTest('fresh owner TXT unavailable: set MTGLAB_MANA_CONTEXT_SOURCE; offline checks are separate')
        from gameplay_rules.projection import mana_context_package as source
        records = source.load_package(SOURCE_PACKAGE, review_root=REVIEWS)
        expected = source.verify_source(records, Path(selector), review_root=REVIEWS)
        if hasattr(expected, 'to_dict'):
            expected = expected.to_dict()
        process = run_cli('verify-source', '--artifact', selector, '--json')
        self.assertEqual(process.returncode, 0, process.stderr.decode())
        from card_rules_pilot.contract import canonical
        self.assertEqual(process.stdout, canonical(expected))
        with tempfile.TemporaryDirectory(prefix='mtglab-mana-cli-conflict-') as temporary:
            destination = Path(temporary) / 'occupied'
            destination.mkdir()
            sentinel = destination / 'retained-content'
            sentinel.write_bytes(b'pre-existing retained content\n')
            process = run_cli('build-source', '--artifact', selector, '--output', str(destination))
            self.assertEqual(process.returncode, 2, process.stderr.decode())
            self.assertEqual(process.stdout, b'')
            self.assertEqual({p.name: p.read_bytes() for p in destination.iterdir()},
                             {'retained-content': b'pre-existing retained content\n'})


if __name__ == '__main__':
    unittest.main()
