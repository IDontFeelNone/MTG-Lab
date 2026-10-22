"""Bounded source extraction, immutable lineage, readiness and integrity proofs."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from activated_ability_preservation import is_design_addition
from query_attachment_performance_preservation import assert_hash_row
from evidence.contracts import deterministic_json
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection import mana_classification_package as pkg
from gameplay_rules.projection import mana_classification_source as source
from gameplay_rules.projection.mana_classification_reports import UNPROJECTED, RULE_CONTENT, CANONICAL_MAIN
from gameplay_rules.projection.mana_classification_pins import PRIOR_PACKAGES, VERIFIED_ANCHORS
from gameplay_rules.projection.contracts import _json
from gameplay_rules.capabilities import ENGINE_CONTRACT_VERSION, EXECUTION_PROFILE

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT/'reference-reviews'
PACKAGE = REVIEWS/pkg.PACKAGE_NAME
NEW_FILES = {f'mana_classification_{part}.py' for part in ('source','pins','reports','package')}
FIXTURE = (b'115.6. Project authored target distinction fixture.\n\xc2\xa0\n115.7. Boundary fixture.\n'
    b'606. Loyalty Abilities\n\xc2\xa0\n606.1. Project authored category fixture.\n\xc2\xa0\n'
    b'606.2. Project authored criterion fixture.\n\xc2\xa0\n606.3. Boundary fixture.\n')


class SourceBoundaryTests(unittest.TestCase):
    def test_one_line_and_multiline_physical_bytes(self):
        anchors = source.locate_anchors(FIXTURE)
        self.assertEqual([a['rule_reference'] for a in anchors], ['115.6','606.1','606.2'])
        self.assertEqual([a['line_count'] for a in anchors], [1,1,1])
        data = FIXTURE.replace(b'distinction fixture.\n', b'distinction fixture.\r\n  Authored continuation.\r\n')
        a = source.locate_anchors(data)[0]
        block = data[a['byte_start']:a['byte_end']]
        self.assertIn(b'\r\n  ',block)
        self.assertFalse(block.endswith((b'\r',b'\n')))
        self.assertEqual(a['line_count'],2)
        self.assertEqual(a['span_sha256'],'sha256:'+hashlib.sha256(block).hexdigest())
        self.assertEqual(a['anchor_type'],source.ANCHOR_TYPE)
        self.assertEqual(a['span_policy'],source.SPAN_POLICY)

    def test_missing_duplicate_malformed_markers(self):
        for data in (FIXTURE.replace(b'606.2. ',b'606.9. '), FIXTURE+ b'606.1. Duplicate.\n',
                     FIXTURE.replace(b'115.6. ',b'115.6 ')):
            with self.subTest(data=data), self.assertRaises(GameplayContractError):
                source.locate_anchors(data)

    def test_ambiguous_continuation_termination_examples_and_family(self):
        for extra in (b'Unowned continuation.\n', b'\xc2\xa0\n', b'Example: Unowned.\n', b'606.1a Unexpected child.\n'):
            with self.subTest(extra=extra), self.assertRaises(GameplayContractError):
                source.locate_anchors(FIXTURE.replace(b'606.2. ',extra+b'606.2. '))
        with self.assertRaises(GameplayContractError):
            source.locate_anchors(FIXTURE.replace(b'606. Loyalty Abilities',b'606. Wrong context'))
        with self.assertRaises(GameplayContractError):
            source.locate_anchors(FIXTURE.replace(b'606.3. Boundary fixture.\n',b''))

    def test_overlap_and_fourth_rule_rejected(self):
        anchors = source.locate_anchors(FIXTURE)
        anchors[1]['byte_start'] = anchors[0]['byte_start']
        with self.assertRaisesRegex(GameplayContractError,'OVERLAPPING'):
            source.validate_spans(anchors)
        with self.assertRaises(GameplayContractError):
            source.validate_spans([*_json(VERIFIED_ANCHORS),_json(VERIFIED_ANCHORS)[0]])

    def test_verified_artifact_required_and_wrong_artifact_rejected(self):
        with self.assertRaisesRegex(GameplayContractError,'MISSING_VERIFIED_SOURCE_ARTIFACT'):
            pkg.build_package(None,review_root=REVIEWS)
        with self.assertRaisesRegex(GameplayContractError,'VERIFIED_SOURCE_ARTIFACT_MISMATCH'):
            source.verify_bytes(FIXTURE)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'wrong.txt';path.write_bytes(FIXTURE)
            with self.assertRaises(GameplayContractError):
                pkg.build_package(path,review_root=REVIEWS)

    def test_no_general_parser_network_or_runtime_imports(self):
        allowed = {'pathlib','hashlib','re','json','evidence','gameplay_rules'}
        for name in NEW_FILES:
            tree=ast.parse((ROOT/'src/gameplay_rules/projection'/name).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    self.assertTrue(all(a.name.split('.')[0] in allowed for a in node.names))
                if isinstance(node,ast.ImportFrom) and node.level == 0:
                    self.assertIn(node.module.split('.')[0],allowed)
        self.assertEqual(set(source._MARKERS), {'115.6','115.7','606.1','606.2','606.3'})


class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = pkg.load_package(PACKAGE,review_root=REVIEWS)
        cls.p = cls.records['projection.json']

    def findings(self,name):
        return self.records[name+'.json']['findings']

    def test_exact_canonical_base_three_new_units_and_eighty_four_total(self):
        self.assertEqual(CANONICAL_MAIN,'7082d7c048ef764d5e5ec8d5ea42e2ab9d3dbb28')
        self.assertEqual(self.p['canonical_base'],CANONICAL_MAIN)
        self.assertEqual(self.p['selected_references'],['115.6','606.1','606.2'])
        self.assertEqual(len(self.p['rules']),3)
        self.assertEqual(self.p['new_source_units_projected'],3)
        self.assertEqual(self.p['total_projected_rule_count'],84)
        self.assertEqual(self.p['additional_rules_projected'],[])
        refs=self.findings('composite-coverage')['projected_references']
        self.assertEqual(len(refs),len(set(refs)))
        for ref in UNPROJECTED:
            self.assertNotIn(ref,refs)
        self.assertNotIn('606',refs)

    def test_eight_distinct_projections_read_only_composite(self):
        before=copy.deepcopy(self.records)
        view=pkg.composite_view(self.records)
        self.assertEqual(self.records,before)
        self.assertEqual(view['total_projected_rule_count'],84)
        parts=view['projection_components']
        self.assertEqual([len(c['projected_references']) for c in parts],[20,12,7,12,12,5,13,3])
        self.assertEqual(len({c['projection_id'] for c in parts}),8)
        self.assertEqual(parts[-1]['package_id'],pkg.manifest(self.records)['package_id'])

    def test_three_rule_anchors_and_no_outgoing_citations(self):
        for rule,anchor in zip(self.p['rules'],_json(VERIFIED_ANCHORS)):
            self.assertEqual(rule['source_anchor'],anchor)
            self.assertEqual(anchor['anchor_type'],'MULTI_LINE_RULE_BLOCK_ANCHOR')
            self.assertEqual(anchor['line_count'],1)
            self.assertEqual(rule['direct_dependency_references'],[])
            self.assertEqual(rule['dependency_frontier'],'NO_EXPLICIT_OUTGOING_NUMBERED_REFERENCES')

    def test_target_requirement_count_status_and_legality_remain_distinct(self):
        rule=self.p['rules'][0]
        self.assertFalse(rule['zero_selected_implies_no_target_requirement'])
        self.assertTrue(rule['target_requirement_distinct_from_legality'])
        self.assertFalse(rule['recognizes_arbitrary_ability_target_requirements'])
        self.assertEqual(len({rule[k] for k in ('target_requirement','chosen_target_count','targeted_status')}),3)
        target=self.findings('target-readiness')
        self.assertEqual(target['source_coverage'],['115.6'])
        dims=copy.deepcopy(target['dimensions'])
        self.assertEqual(dims.pop('requirement_vs_selected_count_distinction'),'BOUNDED_SOURCE_COVERAGE')
        self.assertEqual(set(dims.values()),{'BLOCKED_UNPROJECTED'})
        self.assertFalse(target['general_targeting_supported'])
        self.assertEqual(target['semantic_closure'],'OPEN')

    def test_loyalty_category_criterion_context_and_execution_separate(self):
        self.assertEqual(self.p['rules'][1]['knowledge_kind'],'LOYALTY_CATEGORY_CONTEXT')
        rule=self.p['rules'][2]
        self.assertEqual(rule['knowledge_kind'],'LOYALTY_CLASSIFICATION_CRITERION')
        self.assertFalse(rule['only_planeswalkers_can_have_loyalty_abilities'])
        self.assertFalse(rule['loyalty_symbol_parser_supplied'])
        loyalty=self.findings('loyalty-readiness')
        self.assertFalse(loyalty['classification_implies_execution'])
        a,b=loyalty['capabilities']
        self.assertEqual(a['source_coverage'],['606.1','606.2'])
        self.assertEqual(a['state'],'REPRESENTED_WITH_OPEN_SEMANTIC_DEPENDENCIES')
        self.assertEqual(b['unprojected_references'],['606.3','606.4','606.5','606.6'])
        self.assertEqual(b['execution_readiness'],'BLOCKED')
        self.assertIn('negative_cost_sufficiency',b['missing'])

    def test_direct_115_6_resolved_but_target_semantic_closure_open(self):
        dep=self.findings('classification-dependency-review')
        rows=dep['direct_reference_reassessments']
        self.assertEqual([r['from_reference'] for r in rows],['605.1a','605.1b'])
        for row in rows:
            self.assertEqual(row['reference_state'],'DIRECT_REFERENCE_RESOLVED')
            self.assertEqual(row['ability_target_requirement_semantic_closure'],'OPEN')
            self.assertEqual(row['real_classification_execution'],'BLOCKED')

    def test_broad_606_partial_derived_evidence_without_invented_citations(self):
        dep=self.findings('classification-dependency-review')
        section=dep['section_reassessment']
        self.assertEqual(section['broad_606_section_resolution'],'OPEN')
        self.assertEqual(section['state'],'SECTION_DEPENDENCY_PARTIALLY_REPRESENTED_FOR_CLASSIFICATION')
        self.assertEqual(section['classification_specific_relationship'],'REPRESENTED')
        self.assertEqual(section['execution_behavior_scope'],'UNPROJECTED')
        self.assertFalse(section['historical_dependency_array_rewritten'])
        self.assertFalse(section['historical_605.1a_rule_mutated'])
        evidence=dep['derived_classification_evidence']
        self.assertEqual(evidence['source_citation'],'606')
        self.assertEqual(evidence['evidence_references'],['606.1','606.2'])
        self.assertEqual(evidence['new_direct_cr_citations'],[])

    def test_mana_classification_improved_source_open_semantics_blocked_execution(self):
        findings=self.findings('overall-readiness')
        self.assertEqual(findings['source_coverage'],['605.1','605.1a','605.1b','605.2','605.5','605.5a','605.5b','115.6','606.1','606.2'])
        self.assertEqual(findings['semantic_closure'],'OPEN')
        self.assertEqual(findings['execution_readiness'],'BLOCKED')
        self.assertGreaterEqual(len(findings['missing_semantic_evidence']),8)
        dep=self.findings('classification-dependency-review')
        for key in ('activated_classification','triggered_classification'):
            self.assertEqual(dep[key]['execution_readiness'],'BLOCKED')
            self.assertEqual(dep[key]['semantic_closure'],'OPEN')
            self.assertFalse(dep[key]['historical_dependency_array_rewritten'])

    def test_consumer_601_2g_unchanged_and_madness_indirect(self):
        consumers=self.findings('consumer-reassessment')['consumers']
        self.assertEqual(consumers[2]['605_section'],'SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY')
        self.assertFalse(consumers[2]['new_direct_source_dependency'])
        self.assertEqual(consumers[3]['relationship'],'INDIRECT')
        self.assertEqual(consumers[3]['path'],['702.35b','bounded_casting','601.2g','605'])
        self.assertEqual(consumers[3]['new_direct_cr_citations'],[])

    def test_correspondence_classifications_and_immutable_design(self):
        review=self.records['design-source-correspondence.json']
        self.assertEqual(review['prior_design_package_id'],'sha256:af42a280e70618102a71381f43122fb98c5e60367f63bd33750677a9a7d9646c')
        self.assertFalse(review['historical_design_mutated'])
        findings=review['findings']
        self.assertEqual(findings['contradictions'],[])
        self.assertEqual({r['result'] for r in findings['observations']},{'VERIFIED','VERIFIED_WITH_REFINEMENT','FOUND_ADDITIONAL_BOUNDARY'})

    def test_exactly_one_next_milestone_not_authorized(self):
        next_milestone=self.findings('overall-readiness')['next_milestone']
        self.assertEqual(next_milestone['candidate'],'Bounded Mana Stack-Exception Projection')
        self.assertEqual(next_milestone['exact_proposed_scope'],['405.6c'])
        self.assertTrue(next_milestone['source_txt_required'])
        self.assertFalse(next_milestone['authorized'])

    def test_permissions_profile_snapshot_and_runtime_absent(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION,'gameplay-kernel-v1')
        self.assertEqual(EXECUTION_PROFILE,'fictional-two-player-v1')
        for record in self.records.values():
            flags=record['boundary_flags']
            self.assertEqual(flags['source_policy_clearance'],'not_granted')
            for key in ('private_retention','redistribution','free_service','commercial_service','ai_export'):
                self.assertEqual(flags[key],'NOT_ESTABLISHED')
            for key in ('real_snapshot_created','real_profile_activated','real_rules_executable','oracle_ingested','source_body_retained'):
                self.assertFalse(flags[key])
        self.assertEqual({p.name for p in (ROOT/'src/simulation').iterdir() if p.name != '__pycache__'},{'.gitkeep'})

    def test_no_source_prose_examples_txt_or_attachment_paths(self):
        for p in PACKAGE.iterdir():
            self.assertEqual(p.suffix,'.json')
            raw=p.read_bytes()
            for forbidden in (b'/tmp/',b'attachment_path',b'source_prose',b'Example:',b'A spell or ability that requires targets may allow',b'Normally, only planeswalkers'):
                self.assertNotIn(forbidden,raw)
        self.assertFalse(list(ROOT.rglob('*MagicCompRules*.txt')))


class PreservationAndIntegrityTests(unittest.TestCase):
    def test_historical_source_inventory_and_authorized_current_implementations_match_pins(self):
        raw=(ROOT/'tests/fixtures/mana-classification-protected-source.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'e21f4a50990577e46ddc36ffb21bf16852fa9efa4f2800ecd30b54ef17e3d784')
        inventory=json.loads(raw)
        expected={row['path'] for row in inventory}
        for row in inventory:
            with self.subTest(path=row['path']):
                assert_hash_row(row)
        actual={str(p.relative_to(ROOT))
            for p in (ROOT/'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'
            and not is_design_addition(p)
            # The successor guard pins every byte in this canonical inventory
            # and permits only these four append-only source files.
            and not (p.parent == ROOT/'src/gameplay_rules/projection' and p.name in NEW_FILES | {
                'mana_stack_exception_source.py','mana_stack_exception_pins.py',
                'mana_stack_exception_reports.py','mana_stack_exception_package.py'})}
        self.assertEqual(actual,expected)

    def test_all_eleven_prior_packages_and_historical_anchors_preserved(self):
        pins=pkg.verify_prior_packages(REVIEWS)
        self.assertEqual(len(pins),11)
        self.assertEqual(pins['gameplay-rules-mana-direct-dependency-design']['package_id'],
            'sha256:af42a280e70618102a71381f43122fb98c5e60367f63bd33750677a9a7d9646c')
        from test_mana_ability_direct_dependency_design import prior_rules, RULE_IDS
        rules=prior_rules()
        self.assertEqual(len(rules),81)
        for ref,identity in RULE_IDS.items():
            self.assertEqual(rules[ref]['rule_id'],identity)
        self.assertEqual(rules['605.1a']['direct_dependency_references'],['115.6','606'])
        self.assertEqual(rules['605.1b']['direct_dependency_references'],['115.6','605.1a'])
        self.assertEqual(pkg.manifest(pkg.rebuild_package(review_root=REVIEWS))['historical_acquisition_identity'],
            'sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53')

    def test_deterministic_offline_relocation_and_append_only_write(self):
        records=pkg.load_package(PACKAGE,review_root=REVIEWS)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'reviews'
            root.mkdir()
            for name in PRIOR_PACKAGES:
                shutil.copytree(REVIEWS/name,root/name)
            target=root/pkg.PACKAGE_NAME
            m=pkg.write_package(target,records,review_root=root)
            self.assertEqual(pkg.load_package(target,review_root=root),records)
            self.assertEqual(pkg.rebuild_package(review_root=root),records)
            self.assertEqual(m,pkg.manifest(records))
            with self.assertRaises(GameplayContractError):
                pkg.write_package(target,records,review_root=root)
            old=root/'gameplay-rules-mana-direct-dependency-design/classification-dependencies.json'
            old.write_bytes(old.read_bytes()+b' ')
            with self.assertRaisesRegex(GameplayContractError,'PRIOR_PACKAGE_BYTES_CHANGED'):
                pkg.load_package(target,review_root=root)

    def test_tampering_extra_source_noncanonical_symlink_and_hardlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            target=root/'package'
            shutil.copytree(PACKAGE,target)
            def reject():
                with self.assertRaises(GameplayContractError):
                    pkg.load_package(target,review_root=REVIEWS)
            p=target/'overall-readiness.json';original=p.read_bytes()
            value=json.loads(original);value['findings']['execution_readiness']='READY'
            p.write_text(deterministic_json(value)+'\n');reject()
            p.write_bytes(original+b' ');reject()
            p.write_bytes(original)
            for name in ('extra.json','source.txt'):
                extra=target/name;extra.write_text('fixture');reject();extra.unlink()
            p.unlink();p.symlink_to(PACKAGE/'overall-readiness.json');reject();p.unlink()
            outside=root/'outside.json';outside.write_bytes(original);os.link(outside,p);reject();p.unlink()
            p.write_bytes(original)
            link=root/'linked';link.symlink_to(target,target_is_directory=True)
            with self.assertRaises(GameplayContractError):
                pkg.load_package(link,review_root=REVIEWS)
            self.assertEqual(pkg.load_package(target,review_root=REVIEWS),pkg.rebuild_package(review_root=REVIEWS))

    def test_exact_source_reproduction_when_explicit_external_artifact_supplied(self):
        # CI remains offline: an explicit environment selector enables the actual
        # owner artifact proof without retaining its bytes or path in the package.
        selector=os.environ.get('MTGLAB_CLASSIFICATION_SOURCE_ARTIFACT')
        if selector is None:
            self.assertEqual(_json(VERIFIED_ANCHORS),[r['source_anchor'] for r in pkg.projection()['rules']])
            return
        records=pkg.load_package(PACKAGE,review_root=REVIEWS)
        self.assertEqual(pkg.verify_source(records,selector,review_root=REVIEWS)['selected_rule_count'],3)
        data=Path(selector).read_bytes()
        self.assertEqual(source.verify_bytes(data),_json(VERIFIED_ANCHORS))
        for anchor in _json(VERIFIED_ANCHORS):
            raw=data[anchor['byte_start']:anchor['byte_end']]
            self.assertEqual('sha256:'+hashlib.sha256(raw).hexdigest(),anchor['span_sha256'])


if __name__ == '__main__':
    unittest.main()
