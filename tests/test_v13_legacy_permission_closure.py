"""Retained governance contract, explicitly historical inputs, no runtime profile."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from historical_catalog import historical_repository
from query import CanonicalQueryEngine
from production_evidence.promotion_readiness import canonical_state_digest
from scripts.verify_legacy_permission_closure import (
    OPERATIONS, PACKET, QUERY_ID, HISTORICAL_ID, read, verify,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT/PACKET


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n')


class LegacyPermissionClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = historical_repository()
        cls.closure = read(REVIEW/'dependency-closure.json')
        cls.matrix = read(REVIEW/'permission-matrix.json')
        cls.sources = read(REVIEW/'source-evidence-index.json')

    def check(self, packet=REVIEW, baseline=None):
        return verify(ROOT, packet, baseline_root=baseline or self.baseline)

    def packet_copy(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return Path(shutil.copytree(REVIEW, Path(temporary.name)/'review'))

    def baseline_copy(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        # Explicit existing historical dependencies only; never a production bundle.
        for ref in self.closure['tiers']['B']['files']:
            target = root/ref['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.baseline/ref['path'], target)
        return root

    def alter(self, packet, name, change):
        document = read(packet/name)
        change(document)
        save(packet/name, document)
        # Adversarial temporary metadata only; never repin retained evidence.
        manifest = read(packet/'manifest.json')
        for ref in manifest['files']:
            if ref['path'] == name:
                raw = (packet/name).read_bytes()
                ref.update(byte_length=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        save(packet/'manifest.json', manifest)

    def test_full_review_verifier_is_read_only_and_never_authorizes(self):
        protected = [ROOT/r['path'] for r in read(REVIEW/'preservation-bindings.json')['files']]
        protected += [ROOT/'data/canonical/state.json', *REVIEW.iterdir()]
        before = {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        canonical_before = canonical_state_digest(ROOT/'data')
        with patch('socket.create_connection', side_effect=AssertionError('no network')):
            result = self.check()
        self.assertEqual(result['permission_fields'], 689)
        self.assertEqual(result['storage_fields'], 354)
        self.assertFalse(result['production_eligible'])
        self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['runtime_profile_implemented'])
        self.assertEqual(result['source_policy_clearance'], 'not_granted')
        self.assertEqual(before, {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected})
        self.assertEqual(canonical_state_digest(ROOT/'data'), canonical_before)

    def test_exact_tiers_are_not_one_monolithic_snapshot(self):
        self.assertEqual({k:v['count'] for k,v in self.closure['tiers'].items()}, {'A':40,'B':68,'C':99})
        self.assertEqual(Counter(r['placement'] for r in self.closure['tiers']['A']['files']),
                         {'CORE_CATALOG_CONTENT':33,'SOURCE_EVIDENCE_REFERENCE':5,'AUDIT_CONTEXT':2})
        self.assertEqual(self.closure['tiers']['C']['canonical_and_full_query'], 82)
        self.assertEqual(self.closure['tiers']['C']['additional_historical_admission'], 17)
        for ref in self.closure['tiers']['A']['files']:
            self.assertFalse(ref['copies_values'])
            self.assertEqual(ref['retention_action'], 'REFERENCE_EXISTING_TRACKED_BYTES_IN_PLACE')
            if ref['placement'] == 'CORE_CATALOG_CONTENT':
                self.assertTrue(ref['path'].startswith('data/canonical/'))
                self.assertNotIn('/sources/', ref['path'])
        for domain in ('TEMPORAL_MARKET_EVIDENCE','PERSONAL_USER_DATA','DERIVED_INTELLIGENCE',
                       'PENDING_MB2_CANDIDATES','RAW_PROVIDER_CORPORA'):
            self.assertIn(domain, self.closure['excluded_domains'])

    def test_every_required_field_has_seven_explicit_operations_without_provider_inheritance(self):
        fields = read(REVIEW/'field-inventory.json')['storage_fields'] + read(REVIEW/'query-field-inventory.json')['fields']
        self.assertEqual({(r['group'],r['field_path']) for r in fields},
                         {(r['group'],r['field_path']) for r in self.matrix['fields']})
        for row in self.matrix['fields']:
            self.assertNotEqual(row['profile_id'], 'mtgjson-controlled-only')
            profile = self.matrix['status_profiles'][row['profile_id']]
            self.assertEqual(set(profile['operations']), set(OPERATIONS))
            for status in profile['operations'].values():
                self.assertIn(status['status'], {'NOT_ESTABLISHED','NOT_APPLICABLE'})
        hidden = [r['field_path'] for r in fields if r['group'] == 'promoted_card']
        self.assertIn('/unknown_values/text', hidden)
        self.assertIn('/unknown_values/edhrecRank', hidden)
        self.assertIn('/unknown_values/purchaseUrls/tcgplayer', hidden)

    def test_established_conditional_layers_and_notices_bind_available_authoritative_evidence(self):
        evidence = {r['id']:r for r in self.sources['sources']}
        statuses = [s for p in self.matrix['status_profiles'].values() for s in p['operations'].values()]
        statuses += read(REVIEW/'notice-requirements.json')['requirements']
        self.assertTrue(any(s['status'] == 'ESTABLISHED_WITH_CONDITIONS' for s in statuses))
        for status in statuses:
            if status['status'].startswith('ESTABLISHED'):
                self.assertTrue(status['evidence_ids'])
                for name in status['evidence_ids']:
                    self.assertEqual(evidence[name]['availability'], 'AVAILABLE')
                    self.assertTrue(evidence[name]['url'].startswith('https://'))
        unavailable = [s for s in evidence.values() if s['availability'] == 'EVIDENCE_UNAVAILABLE']
        self.assertEqual(len(unavailable), 3)
        self.assertTrue(all(s['observed_http_status'] == 403 for s in unavailable))
        self.assertTrue(all(s['capture']['origin_entity_sha256'] is None for s in evidence.values()))

    def test_permission_neutral_design_is_distinct_from_production_authority(self):
        ready = read(REVIEW/'stage3-readiness.json')
        self.assertEqual(ready['decision'], 'READY_FOR_NON_PRODUCTION_STAGE3')
        self.assertEqual(ready['production_operator_profile'], 'BLOCKED')
        for key in ('production_eligible','execution_authorized','implementation_authorized',
                    'data_processing_permission_established'):
            self.assertFalse(ready[key])
        for state in self.matrix['complete_mixed_closure'].values():
            self.assertEqual(state['status'], 'NOT_ESTABLISHED')
        self.assertEqual(ready['next_milestone_authorization'], 'NOT AUTHORIZED')

    def test_explicit_root_target_does_not_redefine_bare_constructor_or_query_snapshot(self):
        target = read(REVIEW/'capability-tiers.json')['parity']
        self.assertEqual(target['target'], 'EXPLICIT_BOTH_ROOTS')
        self.assertEqual(target['query_snapshot_id'], QUERY_ID)
        self.assertEqual(target['counts_by_type'], {'card':399,'printing':928,'identifier':235,
                                                   'finish':2,'game':1,'product':1})
        self.assertFalse(target['bare_constructor_equivalent'])
        self.assertEqual(target['bare_constructor_entity_count'], 32)
        self.assertNotEqual(target['bare_constructor_query_snapshot_id'], QUERY_ID)
        self.assertFalse(target['tier_A_verifies_whole_canonical_prestate'])
        # A future changed current catalog must not be mislabeled as this baseline.
        current = CanonicalQueryEngine('magic', data_root=ROOT/'data', games_root=ROOT/'data/canonical/games')
        prestate = canonical_state_digest(ROOT/'data')
        if prestate == target['whole_canonical_prestate_historical_reference']:
            self.assertEqual(current.snapshot().snapshot_id, QUERY_ID)
        # Non-output canonical bytes can change pre-state without changing the
        # query identity; never infer one digest from the other.
        self.assertEqual(current.data_root, ROOT/'data')

    def test_incompleteness_and_historical_replay_identity_remain_exact(self):
        gaps = read(REVIEW/'capability-tiers.json')['incompleteness']
        self.assertEqual(gaps['unresolved_finish_references'], {'signed':21,'etched':9})
        self.assertEqual(gaps['typed_materialization'], 'incomplete')
        self.assertEqual(gaps['product_slots'], 0)
        self.assertEqual(gaps['gameplay_rules'], 'unsupported')
        preserved = read(REVIEW/'preservation-bindings.json')
        self.assertEqual(preserved['historical_protected_identity'], HISTORICAL_ID)
        self.assertEqual(canonical_state_digest(self.baseline/'data'), preserved['canonical_prestate'])

    def test_package_is_only_metadata_without_private_captures_or_provider_corpus(self):
        for p in REVIEW.rglob('*'):
            self.assertEqual(p.suffix, '.json')
            raw = p.read_bytes()
            for marker in (b'/workspace/private', b'Authorization: Bearer ', b'BEGIN PRIVATE KEY', b'<html'):
                self.assertNotIn(marker, raw)
        for source in self.sources['sources']:
            self.assertLessEqual(len(source.get('quote') or ''), 250)
            self.assertFalse(source['capture']['full_capture_publicly_retained'])
        ci = read(REVIEW/'ci-placement.json')
        self.assertFalse(ci['protected_ci_required_for_contributor_tests'])
        self.assertFalse(ci['production_eligibility_from_ci'])

    def test_relocated_packet_verifies_actual_supplied_bytes(self):
        self.assertEqual(self.check(self.packet_copy()), self.check())

    def test_missing_or_altered_packet_file_is_rejected_without_checkout_fallback(self):
        for mode in ('missing','altered'):
            with self.subTest(mode=mode):
                packet = self.packet_copy()
                p = packet/'capability-tiers.json'
                if mode == 'missing': p.unlink()
                else: p.write_bytes(p.read_bytes() + b' ')
                with self.assertRaisesRegex(ValueError, 'missing review dependency|integrity mismatch'):
                    self.check(packet)

    def test_false_authorization_claim_fails_even_when_temporary_manifest_is_rehashed(self):
        changes = {'execution_authorized':True,'production_eligible':True,
                   'implementation_authorized':True,'approval_state':'approved',
                   'source_policy_clearance':'cleared'}
        for key, value in changes.items():
            with self.subTest(key=key):
                packet = self.packet_copy()
                self.alter(packet, 'stage3-readiness.json', lambda d:d.update({key:value}))
                with self.assertRaisesRegex(ValueError, 'cannot authorize execution or production'):
                    self.check(packet)

    def test_unavailable_evidence_cannot_be_relabelled_as_permission(self):
        packet = self.packet_copy()
        def change(d):
            d['status_profiles']['mtgjson-controlled-only']['operations']['LOCAL_PRIVATE_PROCESSING']['evidence_ids'] = ['closure-scryfall-terms']
        self.alter(packet, 'permission-matrix.json', change)
        with self.assertRaisesRegex(ValueError, 'unavailable evidence cannot establish permission'):
            self.check(packet)

    def test_required_upstream_identifier_cannot_inherit_mtgjson_controlled_only_grant(self):
        packet = self.packet_copy()
        def change(d):
            row = next(r for r in d['fields'] if r['group']=='promoted_identifier' and r['field_path']=='/values/value')
            row['profile_id'] = 'mtgjson-controlled-only'
        self.alter(packet, 'permission-matrix.json', change)
        with self.assertRaisesRegex(ValueError, 'field silently inherits another rights layer'):
            self.check(packet)

    def test_swapped_catalog_source_placement_fails_despite_same_aggregate_counts(self):
        packet = self.packet_copy()
        def change(d):
            rows=d['tiers']['A']['files']
            core=next(r for r in rows if r['placement']=='CORE_CATALOG_CONTENT')
            source=next(r for r in rows if r['placement']=='SOURCE_EVIDENCE_REFERENCE')
            core['placement'],source['placement']=source['placement'],core['placement']
        self.alter(packet, 'dependency-closure.json', change)
        with self.assertRaisesRegex(ValueError, 'per-path placement changed'):
            self.check(packet)

    def test_missing_operation_or_required_field_is_rejected(self):
        for kind in ('operation','field'):
            packet = self.packet_copy()
            def change(d):
                if kind=='operation': del d['status_profiles']['mixed-upstream']['operations']['AI_OR_MODEL_EXPORT']
                else: d['fields'].pop()
            self.alter(packet, 'permission-matrix.json', change)
            with self.assertRaisesRegex(ValueError, 'missing operation|no permission disposition'):
                self.check(packet)

    def test_extra_baseline_audit_or_readable_entity_is_rejected_before_content_read(self):
        for name in ('data/audit/unbound.json','data/canonical/games/magic/slots/unbound.json'):
            with self.subTest(name=name):
                baseline = self.baseline_copy()
                extra=baseline/name;extra.parent.mkdir(parents=True,exist_ok=True);extra.write_text('PRIVATE_FICTIONAL_PROBE')
                original=Path.read_bytes
                def guarded(path):
                    if path == extra: raise AssertionError('extra contents were read')
                    return original(path)
                with patch.object(Path,'read_bytes',guarded):
                    with self.assertRaisesRegex(ValueError,'baseline reader inventory changed before content access'):
                        self.check(baseline=baseline)

    def test_optional_state_and_undeclared_game_are_rejected_before_consumer_construction(self):
        for name in ('data/canonical/knowledge/state.json','data/canonical/games/fictional-other'):
            with self.subTest(name=name):
                baseline=self.baseline_copy();extra=baseline/name
                if name.endswith('.json'): extra.parent.mkdir(parents=True);extra.write_text('{}')
                else: extra.mkdir()
                with self.assertRaisesRegex(ValueError,'optional knowledge state|game namespace changed'):
                    self.check(baseline=baseline)

    def test_unread_sidecars_unused_sources_and_personal_files_do_not_enter_selected_closure(self):
        baseline=self.baseline_copy()
        paths=[baseline/p for p in ('data/canonical/games/magic/products/mystery_booster_2/metadata.json',
            'data/canonical/games/magic/sources/unreferenced.json','data/collections/private-fixture.json')]
        for p in paths: p.parent.mkdir(parents=True,exist_ok=True);p.write_text('PRIVATE_FICTIONAL_PROBE')
        original=Path.open
        def guarded(path, *args, **kwargs):
            if path in paths: raise AssertionError('out-of-scope contents were read')
            return original(path, *args, **kwargs)
        with patch.object(Path,'open',guarded):
            self.assertEqual(self.check(baseline=baseline)['required_files'],40)

    def test_changed_historical_input_cannot_use_another_copy(self):
        baseline=self.baseline_copy()
        path=baseline/'data/canonical/state.json'
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'dependency integrity mismatch'):
            self.check(baseline=baseline)

    def test_path_escape_extra_payload_and_duplicate_json_are_rejected(self):
        packet=self.packet_copy();manifest=read(packet/'manifest.json')
        manifest['files'][0]['path']='../escape.json';save(packet/'manifest.json',manifest)
        with self.assertRaisesRegex(ValueError,'unsafe review dependency path'): self.check(packet)
        packet=self.packet_copy();(packet/'provider-payload.bin').write_bytes(b'fictional extra')
        with self.assertRaisesRegex(ValueError,'unexpected or missing review file'): self.check(packet)
        packet=self.packet_copy();(packet/'manifest.json').write_text('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError,'duplicate review JSON key'): self.check(packet)

    def test_symlinked_review_dependency_cannot_borrow_checkout_bytes(self):
        packet=self.packet_copy();target=packet/'capability-tiers.json';target.unlink()
        target.symlink_to(REVIEW/'capability-tiers.json')
        with self.assertRaisesRegex(ValueError,'symlinked review dependency'):
            self.check(packet)


if __name__ == '__main__':
    unittest.main()
