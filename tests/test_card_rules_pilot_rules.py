"""Exact retained-rule bindings; these tests do not establish Card semantics."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from card_rules_pilot import rules

ROOT = Path(__file__).resolve().parents[1] / "reference-reviews"


class RetainedPilotRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = rules.read_rules(ROOT)

    def test_exact_scope_full_criteria_and_exclusion_records(self):
        value = self.evidence
        by_ref = {item['rule']['rule_reference']: item['rule'] for item in value['rules']}
        self.assertEqual(len(by_ref), 17)
        activated = by_ref['605.1a']['semantic_distinctions']
        self.assertEqual(activated['ability_kind'], 'ACTIVATED')
        self.assertIs(activated['requires_target'], False)
        self.assertIs(activated['could_add_mana_to_player_pool_on_resolution'], True)
        self.assertIs(activated['is_loyalty_ability'], False)
        self.assertIs(activated['cost_moves_card_to_or_from_library'], False)
        self.assertIs(activated['effect_moves_card_to_or_from_library'], False)
        self.assertEqual(activated['applicable_replacement_effects_considered'], 'SELF_REPLACEMENT_ONLY')
        self.assertIs(activated['other_applicable_replacement_effects_ignored_for_classification'], True)
        self.assertEqual(by_ref['605.1b']['semantic_distinctions']['qualifying_trigger_relationships'],
            ['ACTIVATED_MANA_ABILITY_ACTIVATION', 'ACTIVATED_MANA_ABILITY_RESOLUTION', 'MANA_ADDED_TO_POOL'])
        self.assertEqual(by_ref['605.5a']['semantic_category'], 'EXPLICIT_NON_MANA_ABILITY_EXCLUSIONS')
        self.assertEqual(by_ref['605.5b']['semantic_category'], 'SPELL_EXCLUSION_FROM_MANA_ABILITIES')
        for row in by_ref.values():
            self.assertEqual(row['source_anchor']['artifact_hash'], rules.ARTIFACT)
            self.assertEqual(row['source_anchor']['effective_date'], rules.RELEASE)
        self.assertEqual(value['execution_authority'], 'BLOCKED')

    def test_historical_arrays_remain_separate_from_later_reviews(self):
        value = self.evidence
        by_ref = {item['rule']['rule_reference']: item['rule'] for item in value['rules']}
        self.assertTrue(any(row['reference'] == '115.6' for row in by_ref['605.1a']['unresolved_dependencies']))
        classification = value['current_dependency_reviews'][0]
        self.assertEqual(classification['findings']['direct_reference_reassessments'][0]['reference_state'],
                         'DIRECT_REFERENCE_RESOLVED')
        self.assertEqual(classification['findings']['section_reassessment']['broad_606_section_resolution'], 'OPEN')
        later = value['current_dependency_reviews'][2]
        self.assertEqual(later['schema_version'], 1)
        self.assertEqual(later['identity_domain'], 'gameplay-bounded-activated-ability-procedure-record-v1')
        self.assertEqual(later['relationship']['origin_reference'], '605.3')
        self.assertEqual(later['relationship']['target_reference'], '602.2')
        self.assertEqual(later['relationship']['state'], 'DIRECT_REFERENCE_RESOLVED')
        self.assertFalse(later['activation_engine_supplied'])
        self.assertNotIn('602.2', by_ref)
        self.assertNotIn('405.6c', by_ref['605.4a']['direct_dependency_references'])

    def test_relocation_replay_independent_views_and_no_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            relocated = Path(tmp) / 'reviews'
            shutil.copytree(ROOT, relocated)
            before = {p.relative_to(relocated): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in relocated.rglob('*') if p.is_file()}
            actual = rules.read_rules(relocated)
            self.assertEqual(actual, self.evidence)
            actual['rules'][0]['rule']['source_anchor']['effective_date'] = 'fictional mutation'
            self.assertEqual(self.evidence['rules'][0]['rule']['source_anchor']['effective_date'], rules.RELEASE)
            self.assertEqual(before, {p.relative_to(relocated): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in relocated.rglob('*') if p.is_file()})

    def test_changed_rule_anchor_release_package_and_review_bytes_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            relocated = Path(tmp) / 'reviews'
            shutil.copytree(ROOT, relocated)
            cases = [
                (rules.MANA_PACKAGE, 'projection.json', lambda d: d['rules'][0].update(rule_reference='fictional:wrong')),
                (rules.MANA_PACKAGE, 'projection.json', lambda d: d['rules'][0]['source_anchor'].update(byte_start=0)),
                (rules.classification.PACKAGE_NAME, 'projection.json', lambda d: d['source_binding'].update(effective_date='1900-01-01')),
                (rules.stack.PACKAGE_NAME, 'manifest.json', lambda d: d.update(package_id='sha256:'+'0'*64)),
                (rules.activated.PACKAGE_NAME, 'mana-relationships.json', lambda d: d.update(schema_version=True)),
            ]
            for package, filename, change in cases:
                path = relocated / package / filename
                original = path.read_bytes()
                with self.subTest(package=package, filename=filename):
                    altered = json.loads(original)
                    change(altered)
                    path.write_text(deterministic_json(altered)+'\n')
                    with self.assertRaises(GameplayContractError):
                        rules.read_rules(relocated)
                path.write_bytes(original)

    def test_rehashed_later_review_cannot_rewrite_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            relocated = Path(tmp) / 'reviews'
            shutil.copytree(ROOT / rules.activated.PACKAGE_NAME, relocated / rules.activated.PACKAGE_NAME)
            directory = relocated / rules.activated.PACKAGE_NAME
            path = directory / 'mana-relationships.json'
            value = json.loads(path.read_bytes())
            value['execution_readiness'] = 'READY'
            value['review_id'] = rules._identity(rules.activated.RECORD_DOMAIN, value, 'review_id')
            raw = (deterministic_json(value)+'\n').encode()
            path.write_bytes(raw)
            manifest_path = directory / 'manifest.json'
            manifest = json.loads(manifest_path.read_bytes())
            manifest['record_ids'][path.name] = value['review_id']
            manifest['files'][path.name] = {'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}
            manifest['package_id'] = rules._identity(manifest['schema_version'], manifest, 'package_id')
            manifest_path.write_text(deterministic_json(manifest)+'\n')
            with self.assertRaises(GameplayContractError):
                rules._activated_review(relocated)


if __name__ == '__main__':
    unittest.main()
