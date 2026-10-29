"""Actual finite retained-package admission without the historical Card loader."""
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from card_rules_pilot import behavior_policy, land_context as context
from card_rules_pilot.contract import PilotError, canonical, seal
from gameplay_rules.errors import GameplayContractError

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / 'reference-reviews'


class LandContextTests(unittest.TestCase):
    def test_exact_closure_own_identity_and_single_enclosing_validation(self):
        with patch.object(context, '_package', wraps=context._package) as packages, \
                patch.object(context, 'validate_retained_stage', wraps=context.validate_retained_stage) as stages, \
                patch('card_rules_pilot.pilot.load_pilot', side_effect=AssertionError('historical cohort forbidden')), \
                patch('card_rules_pilot.reassessment.load_reassessment', side_effect=AssertionError('historical cohort forbidden')):
            value = context.read_context(REVIEWS)
        self.assertEqual(packages.call_count, 4)
        self.assertEqual(stages.call_count, 2)
        self.assertEqual(len({call.args[1] for call in packages.call_args_list}), 4)
        self.assertEqual(len({call.kwargs['name'] for call in stages.call_args_list}), 2)
        retained, facts = value['retained_rules'], value['rule_facts']
        self.assertEqual(tuple(facts), context.CONTEXT_REFERENCES)
        self.assertEqual(len(set(facts)), 24)
        self.assertEqual(behavior_policy._facts(facts), facts)
        self.assertEqual(retained['context_id'], seal(context.CONTEXT_VERSION, retained, 'context_id')['context_id'])
        self.assertNotEqual(retained['context_id'], 'sha256:bfe54406c0ed5df672dbda7b9f6a376bd823070ea301ff54595f6ab37ed2265e')
        self.assertEqual((retained['new_source_units'], retained['new_projections']), (0, 0))
        self.assertEqual((retained['global_source_units'], retained['global_projections']), (104, 16))
        self.assertLess(len(canonical(retained)), context.CONTEXT_LIMIT)
        self.assertEqual(len(retained['packages']), 6)

    def test_fresh_invocation_and_complete_enclosing_packages_fail_closed(self):
        # Even a member that supplies no selected rule must pass its own bound
        # package contract. No historical positive copy replaces a failed read.
        with tempfile.TemporaryDirectory(prefix='mtglab-land-rules-') as temp:
            root = Path(temp)
            names = set(context.PACKAGE_IDS) | {
                'gameplay-rules-artifact-verification',
                'gameplay-rules-source-versioning',
                'gameplay-rules-release-discovery-closure'}
            for name in names:
                shutil.copytree(REVIEWS / name, root / name)
            before = context.read_context(root)
            path = root / context.casting.PACKAGE_NAME / 'projection.json'
            raw = path.read_bytes()
            path.write_bytes(raw + b' ')
            self.assertEqual(len(before['rule_facts']), 24)
            with self.assertRaises((ValueError, GameplayContractError)):
                context.read_context(root)
            path.write_bytes(raw)
            review = root / context.source_context.PACKAGE_NAME / 'dependency-review.json'
            original = context.read_json(review)
            altered = deepcopy(original)
            altered['execution_authority'] = 'ALLOWED'
            review.write_bytes(canonical(seal(altered['schema_version'], altered, 'review_id')))
            with self.assertRaises((ValueError, GameplayContractError)):
                context.read_context(root)

    def test_duplicate_keys_and_coherently_rehashed_manifest_are_rejected(self):
        name = context.source_context.PACKAGE_NAME
        with tempfile.TemporaryDirectory(prefix='mtglab-land-context-reject-') as temp:
            root = Path(temp)
            shutil.copytree(REVIEWS / name, root / name)
            path = root / name / 'manifest.json'
            raw = path.read_bytes()
            schemas = context._schemas(context.source_context.RECORD_NAMES,
                'gameplay-mana-classification-source-context-')
            def load():
                return context._package(root, name, context.source_context.PACKAGE_SCHEMA,
                    schemas, lambda value: context.exact(value, context.context_projection()))
            path.write_bytes(b'{"schema_version":"x","schema_version":"x"}\n')
            with self.assertRaises(PilotError):
                load()
            path.write_bytes(raw)
            original = context.read_json(path)
            for replacement in (True, 1.0, 'unsupported-v999'):
                altered = deepcopy(original)
                altered['schema_version'] = replacement
                altered = seal('foreign-land-context-schema-v1', altered, 'package_id') if type(replacement) is not float else altered
                path.write_bytes(canonical(altered))
                with self.assertRaises(PilotError):
                    load()


if __name__ == '__main__':
    unittest.main()
