"""Real replay builders use the supplied catalog's repository config paths."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from card_intelligence.comparison import ContextualComparisonError
from card_intelligence.roles import FunctionalRoleError
from historical_catalog import historical_repository
from scripts.build_contextual_card_comparison import build_artifacts as comparison_artifacts
from scripts.build_functional_role_pilot import build_artifacts as role_artifacts


class ReplayBuilderPathTests(unittest.TestCase):
    def replay_from_original_and_relocated_root(self, builder, directory, plan_name, error_type):
        historical = historical_repository()
        retained = {p.name: p.read_bytes() for p in (historical / 'data/review' / directory).iterdir()
                    if p.is_file()}
        # The loaded implementation may live in a different checkout (as in the
        # publication gate). Explicit data/config roots must still retain the
        # same historical bytes; neither module globals nor a fallback root can
        # stand in for these inputs.
        self.assertEqual(builder(historical / 'data'), retained)
        with tempfile.TemporaryDirectory() as name:
            relocated = Path(name)
            shutil.copytree(historical / 'data', relocated / 'data')
            shutil.copytree(historical / 'config', relocated / 'config')
            protected = {p.relative_to(relocated).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in relocated.rglob('*') if p.is_file()}
            artifacts = builder(relocated / 'data')
            self.assertEqual(artifacts, retained)
            manifest = json.loads(artifacts['manifest.json'])
            for path, ref in manifest['input_files'].items():
                source = relocated / path
                self.assertFalse(Path(path).is_absolute())
                self.assertEqual(source.stat().st_size, ref['bytes'])
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), ref['sha256'])
            self.assertEqual(protected, {p.relative_to(relocated).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                         for p in relocated.rglob('*') if p.is_file()})
            plan = relocated / 'config/card_intelligence' / plan_name
            original = plan.read_bytes()
            document = json.loads(original)
            document['canonical_snapshot_id'] = 'sha256:' + '0' * 64
            plan.write_text(json.dumps(document))
            with self.assertRaisesRegex(error_type, 'snapshot'):
                builder(relocated / 'data')
            # Missing supplied config must not fall back to the unchanged
            # implementation checkout's plan either.
            plan.unlink()
            with self.assertRaises(FileNotFoundError):
                builder(relocated / 'data')

    def test_functional_role_replay_paths_and_retained_snapshot_rejection(self):
        self.replay_from_original_and_relocated_root(role_artifacts, 'functional-role-pilot',
            'functional-role-pilot-v1.json', FunctionalRoleError)

    def test_contextual_replay_paths_and_retained_snapshot_rejection(self):
        self.replay_from_original_and_relocated_root(comparison_artifacts, 'contextual-card-comparison',
            'contextual-comparison-pilot-v1.json', ContextualComparisonError)


if __name__ == '__main__':
    unittest.main()
