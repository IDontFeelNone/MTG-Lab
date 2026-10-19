"""One-unit, source-verified stack-exception context; no executable rules.

Structural fixtures are project-authored and establish locator behavior only.
The optional external artifact proof never stores source bytes in the repository.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from evidence.contracts import deterministic_json
from gameplay_rules.capabilities import ENGINE_CONTRACT_VERSION, EXECUTION_PROFILE
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection import mana_stack_exception_package as pkg
from gameplay_rules.projection import mana_stack_exception_source as source
from gameplay_rules.projection.contracts import _json
from gameplay_rules.projection.mana_stack_exception_pins import PRIOR_PACKAGES, VERIFIED_ANCHORS
from gameplay_rules.projection.mana_stack_exception_reports import CANONICAL_MAIN, UNPROJECTED


ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / 'reference-reviews'
PACKAGE = REVIEWS / pkg.PACKAGE_NAME
NEW_FILES = {f'mana_stack_exception_{part}.py' for part in ('source', 'pins', 'reports', 'package')}
FAMILY = ['605.1', '605.1a', '605.1b', '605.2', '605.3', '605.3a', '605.3b',
          '605.3c', '605.4', '605.4a', '605.5', '605.5a', '605.5b']
FIXTURE = (b'405.6. Fixture parent.\n\xc2\xa0\n405.6a Fixture sibling.\n\xc2\xa0\n'
           b'405.6b Fixture sibling.\n\xc2\xa0\n405.6c Fixture selected.\n\xc2\xa0\n'
           b'405.6d Fixture terminal.\n')
HISTORICAL = 'sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53'


def retained_rules():
    """Read the eight disjoint prior projections, without modifying their records."""
    rules = {}
    for name in PRIOR_PACKAGES:
        path = REVIEWS / name / 'projection.json'
        if path.is_file():
            for rule in json.loads(path.read_bytes())['rules']:
                if rule['rule_reference'] in rules:
                    raise AssertionError('Prior projections must remain disjoint')
                rules[rule['rule_reference']] = rule
    return rules


class SourceBoundaryTests(unittest.TestCase):
    def test_exact_child_only_allowlist_and_fixed_local_family(self):
        self.assertEqual(source.SELECTED_REFERENCES, ('405.6c',))
        self.assertEqual(source.DIRECT_REFERENCES, ('605',))
        anchors = source.locate_anchors(FIXTURE)
        self.assertEqual([a['rule_reference'] for a in anchors], ['405.6c'])
        self.assertEqual(len(anchors), 1)
        self.assertEqual(set(source._MARKERS), {'405.6', '405.6a', '405.6b', '405.6c', '405.6d'})
        self.assertEqual(anchors, source.locate_anchors(bytes(FIXTURE)))

    def test_one_line_and_multiline_raw_byte_span_excludes_final_terminator(self):
        a = source.locate_anchors(FIXTURE)[0]
        self.assertEqual(a['line_count'], 1)
        data = FIXTURE.replace(b'Fixture selected.\n', b'Fixture selected.\r\n  Authored continuation.\r\n')
        a = source.locate_anchors(data)[0]
        block = data[a['byte_start']:a['byte_end']]
        self.assertIn(b'\r\n  ', block)
        self.assertFalse(block.endswith((b'\r', b'\n')))
        self.assertEqual(a['line_count'], 2)
        self.assertEqual(a['ending_physical_line'] - a['starting_physical_line'] + 1, 2)
        self.assertEqual(a['span_sha256'], 'sha256:' + hashlib.sha256(block).hexdigest())
        self.assertEqual(a['anchor_type'], 'MULTI_LINE_RULE_BLOCK_ANCHOR')
        self.assertEqual(a['span_policy'], 'EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR')

    def test_missing_duplicate_and_malformed_selected_marker_rejected(self):
        for data in (FIXTURE.replace(b'405.6c ', b'405.6e '),
                     FIXTURE + b'405.6c Duplicate fixture.\n',
                     FIXTURE.replace(b'405.6c ', b'405.6c. '),
                     FIXTURE.replace(b'405.6c Fixture selected.', b'405.6c ')):
            with self.subTest(data=data), self.assertRaises(GameplayContractError):
                source.locate_anchors(data)

    def test_ambiguous_continuation_and_termination_rejected(self):
        for extra in (b'Unowned continuation.\n', b'\xc2\xa0\n', b'\n',
                      b'Example: Unowned fixture.\n', b'405.6c1 Unexpected child.\n'):
            with self.subTest(extra=extra), self.assertRaises(GameplayContractError):
                source.locate_anchors(FIXTURE.replace(b'405.6d ', extra + b'405.6d '))
        with self.assertRaises(GameplayContractError):
            source.locate_anchors(FIXTURE.replace(b'405.6d Fixture terminal.\n', b''))
        # A continuation after a separator has no unambiguous owner.
        with self.assertRaises(GameplayContractError):
            source.locate_anchors(FIXTURE.replace(b'405.6d ', b'  Late continuation.\n405.6d '))

    def test_parent_and_adjacent_shape_required_but_not_projected(self):
        for ref in (b'405.6. ', b'405.6a ', b'405.6b ', b'405.6d '):
            with self.subTest(ref=ref), self.assertRaises(GameplayContractError):
                source.locate_anchors(FIXTURE.replace(ref, b'499.9 '))
        with self.assertRaises(GameplayContractError):
            source.locate_anchors(FIXTURE.replace(b'405.6b ', b'405.6e Unexpected sibling.\n405.6b '))
        anchors = source.locate_anchors(FIXTURE)
        for ref in ('405.6', '405.6a', '405.6b', '405.6d'):
            self.assertNotIn(ref, [a['rule_reference'] for a in anchors])

    def test_second_source_unit_overlap_and_malformed_span_rejected(self):
        anchors = source.locate_anchors(FIXTURE)
        for value in (anchors + copy.deepcopy(anchors), [],
                      [{**anchors[0], 'rule_reference': '405.6'}],
                      [{**anchors[0], 'byte_end': anchors[0]['byte_start']}],
                      [{**anchors[0], 'line_count': 2}],
                      [{**anchors[0], 'byte_start': True}]):
            with self.subTest(value=value), self.assertRaises(GameplayContractError):
                source.validate_spans(value)

    def test_actual_artifact_required_wrong_bytes_do_not_use_retained_metadata(self):
        with self.assertRaisesRegex(GameplayContractError, 'MISSING_VERIFIED_SOURCE_ARTIFACT'):
            pkg.build_package(None, review_root=REVIEWS)
        with self.assertRaisesRegex(GameplayContractError, 'VERIFIED_SOURCE_ARTIFACT_MISMATCH'):
            source.verify_bytes(FIXTURE)
        with tempfile.TemporaryDirectory() as td:
            absent = Path(td) / 'absent.txt'
            with self.assertRaisesRegex(GameplayContractError, 'MISSING_VERIFIED_SOURCE_ARTIFACT'):
                pkg.build_package(absent, review_root=REVIEWS)
            wrong = Path(td) / 'wrong.txt'
            wrong.write_bytes(FIXTURE)
            with self.assertRaisesRegex(GameplayContractError, 'VERIFIED_SOURCE_ARTIFACT_MISMATCH'):
                pkg.build_package(wrong, review_root=REVIEWS)

    def test_release_specific_locator_has_no_network_general_parser_or_engine_path(self):
        allowed = {'pathlib', 'hashlib', 're', 'json', 'collections', 'evidence', 'gameplay_rules'}
        for name in NEW_FILES:
            tree = ast.parse((ROOT / 'src/gameplay_rules/projection' / name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(a.name.split('.')[0] in allowed for a in node.names))
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    self.assertIn(node.module.split('.')[0], allowed)
                    self.assertNotIn(node.module, {'gameplay_rules.engine', 'gameplay_rules.snapshot'})
        self.assertEqual(len(source.SELECTED_REFERENCES), 1)


class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = pkg.load_package(PACKAGE, review_root=REVIEWS)
        cls.p = cls.records['projection.json']
        cls.prior = retained_rules()

    def findings(self, name):
        return self.records[name + '.json']['findings']

    def test_exact_canonical_base_one_new_unit_eighty_five_total(self):
        self.assertEqual(CANONICAL_MAIN, 'c9f46a2768cdee5e32f72e27d0255c6d4efbe175')
        self.assertEqual(self.p['canonical_base'], CANONICAL_MAIN)
        self.assertEqual(self.p['selected_references'], ['405.6c'])
        self.assertEqual(self.p['selected_rule_count'], 1)
        self.assertEqual(self.p['new_source_units_projected'], 1)
        self.assertEqual(self.p['total_projected_rule_count'], 85)
        self.assertEqual(self.p['additional_rules_projected'], [])
        self.assertEqual([r['rule_reference'] for r in self.p['rules']], ['405.6c'])
        m = pkg.manifest(self.records)
        self.assertEqual(m['projected_rule_count_before'], 84)
        self.assertEqual(m['projected_rule_count_after'], 85)
        self.assertFalse(m['historical_anchors_changed'])

    def test_nine_distinct_projection_identities_and_read_only_composite(self):
        before = copy.deepcopy(self.records)
        view = pkg.composite_view(self.records)
        self.assertEqual(before, self.records)
        self.assertEqual(view['total_projected_rule_count'], 85)
        parts = view['projection_components']
        self.assertEqual([len(p['projected_references']) for p in parts], [20,12,7,12,12,5,13,3,1])
        self.assertEqual(len({p['projection_id'] for p in parts}), 9)
        self.assertEqual(parts[-1]['package_id'], pkg.manifest(self.records)['package_id'])
        refs = view['projected_references']
        self.assertEqual(len(refs), len(set(refs)))
        self.assertEqual(len(refs), 85)
        self.assertEqual(set(refs) - set(self.prior), {'405.6c'})
        self.assertEqual(len(self.prior), 84)
        for ref in UNPROJECTED:
            self.assertNotIn(ref, refs)

    def test_single_real_anchor_exact_identity_and_explicit_broad_reference(self):
        rule = self.p['rules'][0]
        self.assertEqual(rule['source_anchor'], _json(VERIFIED_ANCHORS)[0])
        a = rule['source_anchor']
        self.assertEqual(a['artifact_hash'], 'sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca')
        self.assertEqual(a['effective_date'], '2026-09-25')
        self.assertEqual(a['anchor_type'], 'MULTI_LINE_RULE_BLOCK_ANCHOR')
        self.assertEqual(a['span_policy'], 'EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR')
        self.assertEqual((a['starting_physical_line'], a['ending_physical_line'], a['line_count']), (2059,2059,1))
        self.assertEqual((a['byte_start'], a['byte_end']), (238794,239105))
        self.assertEqual(a['span_sha256'], 'sha256:f5b86d6ad7446f5a0090739608105aabf33168403e36233806543438f122f184')
        self.assertEqual(rule['direct_dependency_references'], ['605'])
        self.assertEqual(rule['semantic_closure'], 'OPEN')
        self.assertEqual(rule['execution_readiness'], 'BLOCKED')
        self.assertNotIn('117', rule['direct_dependency_references'])

    def test_unselected_parent_siblings_large_frontiers_and_synthetic_605_absent(self):
        refs = self.findings('composite-coverage')['projected_references']
        forbidden = {'405.6', '405.6a', '405.6b', '405.6d', '405.6e', '405.6f', '405.6g', '405.6h',
                     '605', '602.2', '602.2a', '602.2b', '603', '603.7d', '603.7e', '603.7f',
                     '606', '606.3', '606.4', '606.5', '606.6', '613', '117'}
        self.assertTrue(forbidden.isdisjoint(refs))
        self.assertEqual([r for r in refs if r.startswith('405.')], ['405.6c'])

    def test_parent_is_structural_only_and_child_consumer_scope_is_coherent(self):
        parent = self.findings('parent-scope-review')
        self.assertEqual(parent['parent_reference'], '405.6')
        self.assertEqual(parent['parent_observation'], 'STRUCTURAL_PARENT_OBSERVED_NOT_PROJECTED')
        self.assertTrue(parent['parent_observed'])
        self.assertEqual(parent['scope_coherence'], 'CHILD_ONLY_COHERENT_WITH_RETAINED_605.3b_CONTEXT')
        for key in ('parent_projected', 'parent_anchor_retained', 'parent_prose_retained',
                    'parent_required_for_this_bounded_consumer_scope', 'automatic_parent_admission',
                    'broad_405.6_family_represented', 'general_non_stack_event_semantics_supplied'):
            self.assertFalse(parent[key])
        self.assertTrue(parent['siblings_inspected_as_transient_source_shape_only'])
        self.assertEqual(parent['sibling_rules_projected'], [])
        self.assertEqual(parent['general_parent_semantics'], 'UNPROJECTED')
        self.assertEqual(parent['direct_consumer']['historical_rule_id'], self.prior['605.3b']['rule_id'])
        self.assertEqual(parent['retained_consumer_knowledge'],
                         ['ACTIVATED_MANA_NO_STACK', 'ACTIVATED_MANA_IMMEDIATE_RESOLUTION'])
        self.assertNotIn('source_anchor', parent)
        self.assertNotIn('parent_anchor', parent)

    def test_immediate_resolution_and_mana_additional_effect_relationship_are_knowledge_only(self):
        rule = self.p['rules'][0]
        self.assertEqual(rule['knowledge_kind'], 'MANA_ABILITY_IMMEDIATE_RESOLUTION_CONTEXT')
        immediate = rule['immediate_resolution']
        self.assertEqual(immediate['applicability'], 'MANA_ABILITIES')
        self.assertEqual(immediate['behavior'], 'IMMEDIATE_RESOLUTION')
        self.assertTrue(immediate['knowledge_only'])
        self.assertFalse(immediate['resolver_created'])
        parts = rule['mana_plus_additional_effect']
        self.assertEqual(parts['condition'], 'MANA_ABILITY_HAS_MANA_PRODUCTION_AND_ADDITIONAL_EFFECT')
        self.assertEqual(parts['mana_production'], 'IMMEDIATE_AS_PART_OF_MANA_ABILITY_RESOLUTION')
        self.assertEqual(parts['additional_effect'], 'IMMEDIATE_AS_PART_OF_MANA_ABILITY_RESOLUTION')
        self.assertEqual(parts['relationship'], 'BOTH_PARTS_SHARE_IMMEDIATE_RESOLUTION_BEHAVIOR')
        self.assertEqual(parts['fine_grained_ordering'], 'NOT_ESTABLISHED')
        for key in ('mana_before_additional_effect_inferred', 'additional_effect_before_mana_inferred',
                    'event_sequencing_implemented'):
            self.assertFalse(parts[key])

    def test_post_resolution_priority_context_is_conditional_and_activated_only(self):
        rule = self.p['rules'][0]
        context = rule['post_mana_activation_priority_return_context']
        self.assertEqual(context['applicability'], 'ACTIVATED_MANA_ABILITY_ONLY')
        self.assertEqual(context['condition'], 'PLAYER_HELD_PRIORITY_IMMEDIATELY_BEFORE_ACTIVATION')
        self.assertEqual(context['recipient'], 'THAT_PRE_ACTIVATION_PRIORITY_HOLDER')
        self.assertEqual(context['return_context'], 'AFTER_MANA_ABILITY_RESOLUTION')
        for key in ('applied_to_triggered_mana_abilities', 'general_priority_semantics_supplied',
                    'priority_runtime_implemented'):
            self.assertFalse(context[key])
        self.assertFalse(rule['direct_117_dependency_created'])
        priority = self.findings('priority-readiness')
        self.assertEqual(priority['capability'], 'post_mana_activation_priority_return_context')
        self.assertEqual(priority['source_coverage'], ['405.6c'])
        self.assertEqual(priority['applicability'], 'ACTIVATED_MANA_ABILITY_ONLY')
        self.assertFalse(priority['triggered_priority_return_inferred'])
        self.assertEqual(priority['general_priority_semantics'], 'OPEN')
        self.assertEqual(priority['general_priority_source_coverage'], 'UNPROJECTED')
        self.assertFalse(priority['rule_117_projected'])
        self.assertFalse(priority['direct_117_dependency_created'])
        self.assertFalse(priority['priority_runtime_implemented'])
        self.assertFalse(priority['source_coverage_implies_general_priority_support'])
        self.assertEqual(priority['execution_readiness'], 'BLOCKED')
        self.assertEqual(set(priority['unrepresented_general_priority_boundaries']),
                         {'priority_ownership', 'priority_passing', 'APNAP_priority', 'response_windows', 'step_phase_progression'})

    def test_direct_broad_605_reference_binds_the_unchanged_complete_thirteen_unit_family(self):
        dep = self.findings('section-dependency-review')
        self.assertEqual(dep['exact_outgoing_numbered_references'], ['605'])
        section = dep['section_reference']
        self.assertEqual(section['from_reference'], '405.6c')
        self.assertEqual(section['source_citation'], '605')
        self.assertEqual(section['citation_kind'], 'BROAD_SECTION_REFERENCE')
        self.assertEqual(section['state'], 'SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY')
        self.assertEqual(section['concrete_family_references'], FAMILY)
        self.assertEqual(section['concrete_family_count'], 13)
        self.assertEqual(len(section['concrete_family_bindings']), 13)
        for binding in section['concrete_family_bindings']:
            old = self.prior[binding['rule_reference']]
            self.assertEqual(binding['rule_id'], old['rule_id'])
            self.assertEqual(binding['source_anchor'], old['source_anchor'])
        self.assertFalse(section['synthetic_605_rule_created'])
        self.assertFalse(section['historical_605_family_mutated'])
        self.assertEqual(section['family_source_units_reprojected'], 0)
        self.assertEqual(section['semantic_closure'], 'OPEN')
        self.assertEqual(section['execution_readiness'], 'BLOCKED')
        self.assertEqual(dep['invented_direct_numbered_references'], [])

    def test_605_3b_reference_resolves_append_only_without_semantic_or_runtime_closure(self):
        dep = self.findings('section-dependency-review')
        self.assertEqual(len(dep['direct_reference_reassessments']), 1)
        row = dep['direct_reference_reassessments'][0]
        self.assertEqual((row['from_reference'], row['target_reference']), ('605.3b', '405.6c'))
        self.assertEqual(row['reference_state'], 'DIRECT_REFERENCE_RESOLVED')
        self.assertEqual(row['historical_rule_id'], self.prior['605.3b']['rule_id'])
        self.assertEqual(row['target_rule_id'], self.p['rules'][0]['rule_id'])
        self.assertEqual(row['historical_direct_dependency_references'], ['405.6c'])
        self.assertFalse(row['historical_dependency_array_rewritten'])
        self.assertEqual(row['source_coverage_state'], 'IMPROVED')
        self.assertEqual(row['semantic_closure'], 'OPEN')
        self.assertEqual(row['execution_readiness'], 'BLOCKED')
        self.assertFalse(row['source_reference_resolution_implies_execution'])
        for key in ('source_reference_resolution_implies_semantic_closure',
                    'source_reference_resolution_implies_general_stack_support',
                    'source_reference_resolution_implies_priority_implementation'):
            self.assertFalse(dep[key])

    def test_605_4a_overlap_does_not_invent_a_citation_or_triggered_priority_rule(self):
        row = self.findings('section-dependency-review')['semantic_overlap']
        self.assertEqual(row['rule_reference'], '605.4a')
        self.assertEqual(row['historical_rule_id'], self.prior['605.4a']['rule_id'])
        self.assertEqual(row['historical_direct_dependency_references'], self.prior['605.4a']['direct_dependency_references'])
        self.assertEqual(row['relationship'], 'SEMANTIC_OVERLAP_WITHOUT_DIRECT_CR_CITATION')
        self.assertEqual(row['new_direct_cr_citations'], [])
        self.assertFalse(row['direct_405.6c_citation'])
        self.assertFalse(row['historical_rule_mutated'])
        self.assertFalse(row['historical_dependency_array_rewritten'])
        self.assertFalse(row['priority_return_from_405.6c_applied_to_triggered'])
        self.assertEqual(row['triggered_no_stack_evidence'], ['605.4a'])
        self.assertEqual(row['triggered_immediate_resolution_evidence'], ['605.4a'])

    def test_no_stack_and_immediate_resolution_evidence_have_separate_provenance(self):
        provenance = self.p['rules'][0]['no_stack_evidence_provenance']
        self.assertEqual(provenance['activated_direct_evidence'], ['605.3b'])
        self.assertEqual(provenance['triggered_direct_evidence'], ['605.4a'])
        self.assertEqual(provenance['405.6c_role'], 'IMMEDIATE_RESOLUTION_AND_ACTIVATED_PRIORITY_CONTEXT')
        self.assertFalse(provenance['general_non_stack_event_semantics_supplied'])
        stack = self.findings('stack-exception-readiness')
        self.assertEqual(stack['source_coverage'], ['605.3b', '605.4a', '405.6c'])
        self.assertEqual(stack['source_coverage_state'], 'IMPROVED')
        self.assertEqual(stack['state'], 'REPRESENTED_WITH_OPEN_DEPENDENCIES')
        activated = stack['activated_mana_abilities']
        self.assertEqual(activated['no_stack_evidence'], ['605.3b'])
        self.assertEqual(activated['immediate_resolution_evidence'], ['605.3b', '405.6c'])
        self.assertEqual(activated['post_activation_priority_evidence'], ['405.6c'])
        triggered = stack['triggered_mana_abilities']
        self.assertEqual(triggered['no_stack_evidence'], ['605.4a'])
        self.assertEqual(triggered['immediate_resolution_evidence'], ['605.4a'])
        self.assertEqual(triggered['405.6c_relationship'], 'SEMANTIC_OVERLAP_WITHOUT_DIRECT_CR_CITATION')
        self.assertFalse(triggered['direct_405.6c_citation'])
        self.assertFalse(triggered['post_activation_priority_return_inferred'])

    def test_general_stack_remains_open_and_every_runtime_boundary_is_unrepresented(self):
        stack = self.findings('stack-exception-readiness')
        self.assertEqual(stack['general_stack_semantics'], 'OPEN')
        for key in ('response_windows', 'countering', 'resolution_queue', 'semantic_closure'):
            self.assertEqual(stack[key], 'OPEN')
        self.assertEqual(stack['execution_readiness'], 'BLOCKED')
        self.assertFalse(stack['runtime_implemented'])
        self.assertFalse(stack['general_405.6_parent_projected'])
        self.assertFalse(stack['source_coverage_implies_general_stack_support'])
        self.assertEqual(set(stack['unrepresented_general_stack_boundaries']),
                         {'stack_object_model', 'object_ordering', 'stack_push_pop', 'spell_stack_placement',
                          'activated_ability_stack_placement', 'triggered_ability_stack_placement', 'resolution_queue',
                          'response_windows', 'countering', 'priority_sequencing', 'APNAP_stack_ordering'})

    def test_consumer_reassessment_preserves_identities_dependencies_and_indirect_routes(self):
        findings = self.findings('consumer-reassessment')
        rows = {r.get('rule_reference', r.get('consumer')): r for r in findings['consumers']}
        self.assertEqual(set(rows), {'605.3b', '605.4a', '601.2g', 'Madness', '109.4a'})
        self.assertEqual(findings['new_direct_cr_citations_invented'], [])
        self.assertFalse(findings['source_coverage_implies_execution'])
        for ref, row in rows.items():
            self.assertEqual(row['semantic_closure'], 'OPEN')
            self.assertEqual(row['execution_readiness'], 'BLOCKED')
            if ref != 'Madness':
                self.assertEqual(row['historical_rule_id'], self.prior[ref]['rule_id'])
                self.assertEqual(row['historical_direct_dependency_references'], self.prior[ref]['direct_dependency_references'])
                self.assertFalse(row['historical_dependency_array_rewritten'])
                self.assertFalse(row['historical_rule_mutated'])
                self.assertFalse(row['historical_anchor_changed'])
        activated = rows['605.3b']
        self.assertEqual(activated['direct_405.6c_reference'], 'DIRECT_REFERENCE_RESOLVED')
        self.assertTrue({'real_activated_ability_semantics', 'ability_classification', 'real_effect_semantics',
                         'mana_production', 'priority_semantics'}.issubset(activated['remaining_semantic_dependencies']))
        self.assertEqual(rows['601.2g']['path'], ['601.2g', '605', 'activated_mana_behavior'])
        self.assertEqual(rows['601.2g']['605_section'], 'SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY')
        self.assertFalse(rows['601.2g']['new_direct_405.6c_citation'])
        self.assertEqual(rows['Madness']['path'], ['702.35b', 'bounded_casting', '601.2g', '605'])
        self.assertEqual(rows['Madness']['relationship'], 'INDIRECT')
        self.assertFalse(rows['Madness']['new_direct_405.6c_citation'])
        self.assertFalse(rows['109.4a']['new_direct_405.6c_dependency'])
        self.assertEqual(rows['109.4a']['controller_attribution'], 'SEPARATE_UNRESOLVED_SEMANTIC_BOUNDARY')
        for ref in ('601.2g', 'Madness', '109.4a'):
            self.assertEqual(rows[ref]['new_direct_cr_citations'], [])

    def test_design_correspondence_is_append_only_and_covers_all_scope_observations(self):
        review = self.records['design-source-correspondence.json']
        self.assertEqual(review['prior_design_package_id'], 'sha256:af42a280e70618102a71381f43122fb98c5e60367f63bd33750677a9a7d9646c')
        self.assertFalse(review['historical_design_mutated'])
        findings = review['findings']
        self.assertEqual(findings['prior_authority'], 'PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED')
        self.assertFalse(findings['historical_design_rewritten'])
        self.assertEqual(findings['contradictions'], [])
        self.assertEqual(findings['discrepancies'], [])
        self.assertFalse(findings['additional_rule_required'])
        observations = {row['observation']: row for row in findings['observations']}
        expected = {'child_only_scope_coherence', 'parent_405.6_structural_context', 'immediate_mana_ability_resolution',
                    'mana_plus_additional_effect', 'post_activation_priority_return', 'direct_broad_605_citation',
                    'general_stack_semantics_not_supplied', 'general_priority_semantics_not_supplied',
                    'semantic_overlap_with_605.4a', 'parent_not_necessary_for_bounded_consumer_scope'}
        self.assertTrue(expected.issubset(observations))
        self.assertEqual({r['result'] for r in observations.values()},
                         {'VERIFIED', 'VERIFIED_WITH_REFINEMENT', 'FOUND_ADDITIONAL_BOUNDARY'})
        self.assertEqual(observations['triggered_priority_return']['result'], 'FOUND_ADDITIONAL_BOUNDARY')

    def test_original_mana_frontier_is_partly_resolved_and_real_profile_still_not_ready(self):
        readiness = self.findings('overall-readiness')
        self.assertEqual(readiness['real_execution_profile'], 'magic-comprehensive-rules-20260925-v1')
        self.assertEqual(readiness['profile_status'], 'DESIGN_ONLY / NOT EXECUTABLE')
        self.assertEqual(readiness['readiness_code'], 'REAL_EXECUTION_PROFILE_NOT_READY')
        self.assertEqual(readiness['semantic_closure'], 'OPEN')
        self.assertEqual(readiness['execution_readiness'], 'BLOCKED')
        self.assertEqual(readiness['blocked_consumers'], ['mana_abilities', 'casting', 'object_control', 'Madness'])
        self.assertEqual(readiness['general_stack_semantics'], 'OPEN')
        self.assertEqual(readiness['priority_semantics'], 'OPEN')
        frontier = readiness['original_mana_direct_dependency_frontier']
        self.assertEqual(frontier['resolved_source_units'], ['115.6', '405.6c'])
        self.assertEqual(frontier['bounded_classification_evidence'], ['606.1', '606.2'])
        self.assertEqual(frontier['broad_606'], 'PARTIALLY_REPRESENTED_NOT_SECTION_COMPLETE')
        self.assertEqual(frontier['major_unresolved_direct_subsystem_targets'], ['602.2', '603'])
        self.assertFalse(frontier['original_five_target_frontier_fully_solved'])
        self.assertFalse(readiness['fictional_mana_satisfies_real_605'])

    def test_exactly_one_next_design_is_recommended_and_unauthorized(self):
        readiness = self.findings('overall-readiness')
        self.assertEqual(readiness['next_milestone_recommendation_count'], 1)
        next_milestone = readiness['next_milestone']
        self.assertEqual(next_milestone['candidate'], 'Activated Ability Procedure Design')
        self.assertEqual(next_milestone['exact_proposed_design_scope'], ['602.2', '602.2a', '602.2b'])
        self.assertEqual(next_milestone['future_source_allowlist'], [])
        self.assertEqual(next_milestone['scope_kind'], 'DEDICATED_SUBSYSTEM_DESIGN_BEFORE_ANY_SOURCE_PROJECTION')
        self.assertTrue(next_milestone['source_txt_required'])
        self.assertFalse(next_milestone['authorized'])
        self.assertTrue({'605.3', '605.3b', '601.2g', 'Madness'}.issubset(next_milestone['target_consumers']))
        self.assertTrue({'603', 'priority_semantics', 'general_stack_semantics', 'mana_production',
                         'controller_attribution', '613'}.issubset(next_milestone['deliberately_unresolved']))
        self.assertTrue(next_milestone['rationale'])

    def test_permissions_and_real_execution_flags_remain_closed(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION, 'gameplay-kernel-v1')
        self.assertEqual(EXECUTION_PROFILE, 'fictional-two-player-v1')
        for record in self.records.values():
            flags = record['boundary_flags']
            self.assertEqual(flags['source_policy_clearance'], 'not_granted')
            for key in ('private_retention', 'redistribution', 'free_service', 'commercial_service', 'ai_export'):
                self.assertEqual(flags[key], 'NOT_ESTABLISHED')
            for key in ('real_snapshot_created', 'real_profile_activated', 'real_rules_executable',
                        'oracle_ingested', 'source_body_retained'):
                self.assertFalse(flags[key])
        self.assertEqual({p.name for p in (ROOT / 'src/simulation').iterdir() if p.name != '__pycache__'}, {'.gitkeep'})

    def test_source_prose_txt_examples_and_attachment_paths_absent(self):
        for path in PACKAGE.iterdir():
            self.assertEqual(path.suffix, '.json')
            raw = path.read_bytes()
            for forbidden in (b'/tmp/', b'attachment_path', b'\"source_prose\":', b'Example:', b'source_text',
                              b'raw_source', b'source_body\":\"'):
                self.assertNotIn(forbidden, raw)
        self.assertFalse(list(ROOT.rglob('*MagicCompRules*.txt')))


class PreservationAndIntegrityTests(unittest.TestCase):
    def test_second_rule_and_changed_projection_cannot_be_manifested_or_written(self):
        original = pkg.rebuild_package(review_root=REVIEWS)
        for change in ('second_rule', 'parent_anchor', 'invented_dependency', 'runtime_claim'):
            records = copy.deepcopy(original)
            projection = records['projection.json']
            if change == 'second_rule':
                projection['rules'].append(copy.deepcopy(projection['rules'][0]))
            elif change == 'parent_anchor':
                projection['rules'][0]['source_anchor']['rule_reference'] = '405.6'
            elif change == 'invented_dependency':
                projection['rules'][0]['direct_dependency_references'].append('117')
            else:
                projection['execution_readiness'] = 'READY'
            with self.subTest(change=change), self.assertRaises(GameplayContractError):
                pkg.manifest(records)
            with tempfile.TemporaryDirectory() as td:
                with self.assertRaises(GameplayContractError):
                    pkg.write_package(Path(td) / 'new', records, review_root=REVIEWS)

    def test_twelve_prior_packages_eighty_four_rules_and_historical_anchors_preserved(self):
        pins = pkg.verify_prior_packages(REVIEWS)
        self.assertEqual(len(pins), 12)
        self.assertEqual(pins['gameplay-rules-bounded-mana-classification-projection']['package_id'],
                         'sha256:57c9a21ec6a253ad9bfc3a650ec2edc8a389a456eb555a213c3a3f5c673eea73')
        from test_mana_ability_direct_dependency_design import RULE_IDS
        rules = retained_rules()
        self.assertEqual(len(rules), 84)
        for ref, identity in RULE_IDS.items():
            self.assertEqual(rules[ref]['rule_id'], identity)
        self.assertEqual([ref for ref in rules if ref.startswith('605.')], FAMILY)
        self.assertEqual(rules['605.3b']['direct_dependency_references'], ['405.6c'])
        self.assertNotIn('405.6c', rules['605.4a']['direct_dependency_references'])
        self.assertNotIn('405.6c', rules['601.2g']['direct_dependency_references'])
        self.assertNotIn('405.6c', rules['109.4a']['direct_dependency_references'])
        self.assertEqual(pkg.manifest(pkg.rebuild_package(review_root=REVIEWS))['historical_acquisition_identity'], HISTORICAL)

    def test_deterministic_offline_relocation_rebuild_and_append_only_write(self):
        records = pkg.load_package(PACKAGE, review_root=REVIEWS)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'reviews'
            root.mkdir()
            for name in PRIOR_PACKAGES:
                shutil.copytree(REVIEWS / name, root / name)
            target = root / pkg.PACKAGE_NAME
            m = pkg.write_package(target, records, review_root=root)
            self.assertEqual(pkg.load_package(target, review_root=root), records)
            self.assertEqual(pkg.rebuild_package(review_root=root), records)
            self.assertEqual(m, pkg.manifest(records))
            with self.assertRaises(GameplayContractError):
                pkg.write_package(target, records, review_root=root)
            old = root / 'gameplay-rules-bounded-mana-classification-projection/projection.json'
            old.write_bytes(old.read_bytes() + b' ')
            with self.assertRaisesRegex(GameplayContractError, 'PRIOR_PACKAGE_BYTES_CHANGED'):
                pkg.load_package(target, review_root=root)

    def test_tampered_noncanonical_extra_txt_symlink_and_hardlink_packages_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / 'package'
            shutil.copytree(PACKAGE, target)
            def reject():
                with self.assertRaises(GameplayContractError):
                    pkg.load_package(target, review_root=REVIEWS)
            path = target / 'overall-readiness.json'
            original = path.read_bytes()
            value = json.loads(original)
            value['findings']['execution_readiness'] = 'READY'
            path.write_text(deterministic_json(value) + '\n')
            reject()
            path.write_bytes(original + b' ')
            reject()
            path.write_bytes(original)
            for name in ('extra.json', 'source.txt'):
                extra = target / name
                extra.write_text('Project fixture')
                reject()
                extra.unlink()
            path.unlink()
            path.symlink_to(PACKAGE / 'overall-readiness.json')
            reject()
            path.unlink()
            outside = root / 'outside.json'
            outside.write_bytes(original)
            os.link(outside, path)
            reject()
            path.unlink()
            path.write_bytes(original)
            link = root / 'linked'
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(GameplayContractError):
                pkg.load_package(link, review_root=REVIEWS)
            self.assertEqual(pkg.load_package(target, review_root=REVIEWS), pkg.rebuild_package(review_root=REVIEWS))

    def test_exact_external_source_reproduction_without_source_retention(self):
        selector = os.environ.get('MTGLAB_STACK_EXCEPTION_SOURCE_ARTIFACT')
        if selector is None:
            self.assertEqual(_json(VERIFIED_ANCHORS), [r['source_anchor'] for r in pkg.projection()['rules']])
            return
        records = pkg.load_package(PACKAGE, review_root=REVIEWS)
        result = pkg.verify_source(records, selector, review_root=REVIEWS)
        self.assertEqual(result['selected_rule_count'], 1)
        self.assertFalse(result['source_body_retained'])
        data = Path(selector).read_bytes()
        self.assertEqual(len(data), 977752)
        self.assertEqual(hashlib.sha256(data).hexdigest(), '8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca')
        self.assertEqual(source.verify_bytes(data), _json(VERIFIED_ANCHORS))
        for a in _json(VERIFIED_ANCHORS):
            self.assertEqual('sha256:' + hashlib.sha256(data[a['byte_start']:a['byte_end']]).hexdigest(), a['span_sha256'])


if __name__ == '__main__':
    unittest.main()
