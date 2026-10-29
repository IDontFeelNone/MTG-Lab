"""Behavior CLI routing over one admitted snapshot; actual subprocess demo is separate.

The real publication-expanded catalog must reject without installing a historical
positive fixture. Parser/routing checks need no repeated expensive admission.
"""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from card_rules_pilot import cards, pilot
from card_rules_pilot import behavior_cli
from test_card_rules_pilot_cards import current_catalog_intact

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / 'reference-reviews'
PLAN = ROOT / 'data/review/card-rules-mana-pilot/plan.json'
SUCCESSOR = ROOT / 'data/review/mana-context-reassessment'


def arguments():
    return dict(catalog_root=ROOT, mechanical_root=ROOT, review_root=REVIEWS,
        plan_path=PLAN, successor_root=SUCCESSOR,
        expected_profile_id=cards.PROFILE_ID, expected_query_snapshot_id=cards.QUERY_ID,
        expected_plan_id=pilot.PLAN_ID)


def common():
    return ['--catalog-root', str(ROOT), '--mechanical-root', str(ROOT),
        '--plan', str(PLAN), '--successor-root', str(SUCCESSOR),
        '--expected-profile-id', cards.PROFILE_ID,
        '--expected-query-snapshot-id', cards.QUERY_ID,
        '--expected-plan-id', pilot.PLAN_ID]


class ManaBehaviorCLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from card_rules_pilot import behavior
        cls.behavior = behavior
        cls.intact = current_catalog_intact(unittest.TestCase())
        cls.context = behavior.load_behavior(**arguments()) if cls.intact else None

    def test_all_routes_preserve_actual_canonical_and_readable_api_bytes(self):
        if not self.intact:
            self.assertFalse(current_catalog_intact(self))
            with self.assertRaises(ValueError):
                self.behavior.load_behavior(**arguments())
            process = subprocess.run([sys.executable, '-m', 'card_rules_pilot.behavior_cli',
                '--review-root', str(REVIEWS), 'compare', *common(), '--json'], cwd=ROOT,
                env=dict(os.environ, PYTHONPATH=str(ROOT/'src'), PYTHONDONTWRITEBYTECODE='1'),
                capture_output=True)
            self.assertEqual(process.returncode, 2, process.stderr.decode())
            self.assertEqual(process.stdout, b'')
            return
        routes = [(['compare'], self.context.comparison()),
            (['subject', 'basalt-monolith-untap'], self.context.subject('basalt-monolith-untap')),
            (['check'], self.context.check())]
        routes += [(['priority', 'sol-ring-tap', '--prior-priority', premise],
            self.context.priority('sol-ring-tap', premise)) for premise in ('true','false','unknown')]
        for suffix, document in routes:
            for as_json in (True, False):
                with self.subTest(command=suffix, canonical=as_json):
                    out = io.StringIO()
                    with patch.object(self.behavior, 'load_behavior', return_value=self.context) as load, \
                            contextlib.redirect_stdout(out):
                        status = behavior_cli.main(['--review-root', str(REVIEWS), suffix[0],
                            *common(), *suffix[1:], *(['--json'] if as_json else [])])
                    self.assertEqual(status, 0)
                    load.assert_called_once_with(**arguments())
                    self.assertEqual(out.getvalue(), document.to_json() if as_json else
                        self.behavior.render_behavior(document))

    def test_parser_rejects_non_read_commands_and_unbounded_priority_values(self):
        invalid = [('build',), ('verify-source',), ('priority', *common(), 'sol-ring-tap'),
            ('priority', *common(), 'sol-ring-tap', '--prior-priority', '1')]
        for suffix in invalid:
            with self.subTest(command=suffix), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    behavior_cli.parser().parse_args(['--review-root', str(REVIEWS), *suffix])
                self.assertEqual(error.exception.code, 2)

    def test_failed_admission_exposes_no_partial_stdout(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(self.behavior, 'load_behavior', side_effect=ValueError('stale evidence')), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as error:
                behavior_cli.main(['--review-root', str(REVIEWS), 'compare', *common(), '--json'])
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(out.getvalue(), '')
        self.assertIn('bounded mana behavior rejected: stale evidence', err.getvalue())


if __name__ == '__main__':
    unittest.main()
