"""Land CLI parity, exact routing and rejection without partial output."""
import contextlib
import io
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from card_rules_pilot import land_cli
from land_test_support import ROOT, arguments, common, consumer, current_catalog_intact


class LandCLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from card_rules_pilot import land
        cls.land = land
        cls.intact = current_catalog_intact(unittest.TestCase())
        cls.context = consumer() if cls.intact else None

    def test_all_routes_match_complete_canonical_and_readable_api(self):
        if not self.intact:
            self.assertFalse(current_catalog_intact(self))
            with self.assertRaises(ValueError):
                self.land.load_lands(**arguments())
            command = [sys.executable, '-m', 'card_rules_pilot.land_cli',
                '--review-root', str(ROOT / 'reference-reviews'),
                'overview', *common(), '--json']
            actual = subprocess.run(command, cwd=ROOT, capture_output=True,
                env=dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1'))
            self.assertEqual(actual.returncode, 2, actual.stderr.decode())
            self.assertEqual(actual.stdout, b'')
            self.assertIn(b'bounded land mana intelligence rejected:', actual.stderr)
            return
        routes = [(['overview'], self.context.overview()),
            (['check'], self.context.check())]
        routes.extend((['subject', sid], self.context.subject(sid))
            for sid in self.context.subject_ids)
        routes.extend((['compare', name], self.context.comparison(name))
            for name in land_cli.COMPARISONS)
        for suffix, document in routes:
            for as_json in (True, False):
                with self.subTest(command=suffix, canonical=as_json):
                    out = io.StringIO()
                    with patch.object(self.land, 'load_lands', return_value=self.context) as load, \
                            contextlib.redirect_stdout(out):
                        status = land_cli.main(['--review-root', str(ROOT / 'reference-reviews'),
                            suffix[0], *common(), *suffix[1:], *(['--json'] if as_json else [])])
                    self.assertEqual(status, 0)
                    load.assert_called_once_with(**arguments())
                    self.assertEqual(out.getvalue(), document.to_json() if as_json
                        else self.land.render_lands(document))

    def test_closed_parser_rejects_mutations_arbitrary_comparisons_and_missing_bindings(self):
        invalid = [('build',), ('approve',), ('verify-source',),
            ('compare', *common(), 'strictly-better'),
            ('overview', '--catalog-root', str(ROOT))]
        for suffix in invalid:
            with self.subTest(command=suffix), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    land_cli.parser().parse_args([
                        '--review-root', str(ROOT / 'reference-reviews'), *suffix])
                self.assertEqual(raised.exception.code, 2)

    def test_admission_and_unknown_subject_rejections_publish_no_partial_stdout(self):
        for args, replacement in ((['overview'], ValueError('changed evidence')),
                                 (['subject', 'foreign-subject'], self.context)):
            if replacement is None:
                # The expanded catalog path is already exercised by the actual
                # process above; rejection routing needs no positive substitute.
                replacement = ValueError('expanded current catalog')
            out, err = io.StringIO(), io.StringIO()
            patch_args = ({'side_effect': replacement} if isinstance(replacement, Exception)
                else {'return_value': replacement})
            with patch.object(self.land, 'load_lands', **patch_args), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as raised:
                    land_cli.main(['--review-root', str(ROOT / 'reference-reviews'),
                        args[0], *common(), *args[1:], '--json'])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(out.getvalue(), '')
            self.assertIn('bounded land mana intelligence rejected:', err.getvalue())


if __name__ == '__main__':
    unittest.main()
