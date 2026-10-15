"""Review metadata and fictional read-side proofs, never real snapshot admission."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.review_legacy_catalog import inspect, encoded, personal, ROLES
from historical_catalog import historical_repository
from repository.snapshots import attach_snapshot, attach_legacy_public, SnapshotError
from query import CanonicalQueryEngine
from collection.intelligence import CanonicalCollectionResolver
from snapshot_fixture_builder import FIXTURES, read, save

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'reference-reviews/v13-stage2-legacy-public-profile'
BASE = '83e832e3105ddb1c65252b5946387651c49685e4'


def hashes(paths):
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


class LegacyPublicProfileReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.census = read(REVIEW/'census.json')
        cls.current = inspect(ROOT, baseline_revision=BASE)
        cls.engine = CanonicalQueryEngine('magic', data_root=ROOT/'data',
                                         games_root=ROOT/'data/canonical/games')

    def test_review_manifest_binds_exact_review_files(self):
        manifest = read(REVIEW/'review-manifest.json')
        expected = set()
        for ref in manifest['files']:
            name = ref['path']
            self.assertEqual(Path(name).name, name)
            self.assertNotIn(name, expected)
            expected.add(name)
            raw = (REVIEW/name).read_bytes()
            self.assertEqual(len(raw), ref['byte_length'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), ref['sha256'])
        self.assertEqual(expected, {p.name for p in REVIEW.iterdir() if p.name != 'review-manifest.json'})
        self.assertEqual(manifest['document_kind'], 'review_not_snapshot')
        self.assertFalse(manifest['production_eligible'])

    def test_current_inspection_repeats_deterministically_without_writes(self):
        protected = [ROOT/r['path'] for r in read(REVIEW/'preservation-bindings.json')['files']]
        protected += [ROOT/r['path'] for r in self.current['files']]
        before = hashes(protected)
        with patch('socket.create_connection', side_effect=AssertionError('no network')):
            repeated = inspect(ROOT, baseline_revision=BASE)
        self.assertEqual(encoded(repeated), encoded(self.current))
        self.assertEqual(hashes(protected), before)

    def test_frozen_baseline_census_stays_historical_not_current(self):
        frozen = historical_repository()
        from production_evidence.promotion_readiness import canonical_state_digest
        self.assertEqual(canonical_state_digest(frozen/'data'), self.census['canonical_tree_digest'])
        state = read(frozen/'data/canonical/state.json')
        self.assertEqual({k:len(v) for k,v in state.items()},
                         {k:v['count'] for k,v in self.census['promoted_state'].items()})
        retained = read(REVIEW/'file-inventory.json')['files']
        for ref in retained:
            if ref['path'].startswith('data/canonical/'):
                raw = (frozen/ref['path']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), ref['sha256'])
        # No current caller is rerouted to this original fixture.
        self.assertEqual(self.engine.data_root, ROOT/'data')

    def test_actual_current_query_counts_match_observation_even_after_future_expansion(self):
        observed = Counter(x.entity_type for x in self.engine.snapshot().entities)
        state = read(ROOT/'data/canonical/state.json')
        self.assertEqual({k:len(v) for k,v in state.items()},
                         {k:v['count'] for k,v in self.current['promoted_state'].items()})
        for kind in ('card', 'printing'):
            typed = self.current['games']['magic'][kind]['count']
            self.assertEqual(observed[kind], typed + len(state.get(kind, {})) -
                             self.current['typed_state_overlap']['magic'][kind])
        self.assertEqual(observed['identifier'], len(state.get('identifier', {})))
        retained = read(REVIEW/'consumer-dependencies.json')['query_observations']['both_roots']
        if self.current['canonical_tree_digest'] == self.census['canonical_tree_digest']:
            self.assertEqual(dict(observed), retained['counts_by_type'])
        else:
            # A new current state is deliberately not asserted to be the old census.
            self.assertNotEqual(self.engine.snapshot().snapshot_id, retained['query_snapshot_id'])
        self.assertFalse(self.current['production_eligible'])

    def test_classified_families_and_consumer_source_paths_exist(self):
        for family in read(REVIEW/'layer-inventory.json')['families']:
            self.assertTrue((ROOT/family['path']).exists(), family['path'])
            self.assertIn(family['primary_role'], ROLES)
        for component in read(REVIEW/'consumer-dependencies.json')['components']:
            for path in component['source_paths']:
                self.assertTrue((ROOT/path).is_file(), path)

    def test_current_path_hash_inventory_matches_actual_selected_bytes(self):
        for ref in self.current['files']:
            self.assertFalse(personal(ref['path']))
            raw = (ROOT/ref['path']).read_bytes()
            self.assertEqual(len(raw), ref['byte_length'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), ref['sha256'])
            self.assertIn(ref['role'], ROLES)
            self.assertEqual(set(ref), {'path','sha256','byte_length','role'})

    def test_packet_contains_metadata_not_provider_or_personal_payload(self):
        inv = read(REVIEW/'file-inventory.json')
        for ref in inv['files']:
            self.assertFalse(personal(ref['path']))
            self.assertEqual(set(ref), {'path','sha256','byte_length','role'})
        self.assertTrue(all(p.suffix == '.json' for p in REVIEW.iterdir()))
        self.assertEqual(read(REVIEW/'layer-inventory.json')['personal_file_details_retained'], False)
        decision = read(REVIEW/'review-decision.json')
        self.assertEqual(decision['stage3_feasibility'], 'NOT READY')
        self.assertFalse(decision['implementation_authorized'])
        self.assertFalse(decision['source_policy_clearance'])
        self.assertEqual(decision['approval_state'], 'not_granted')

    def test_dependency_sets_are_complete_references_not_copied_values(self):
        inventory = {r['path']:r for r in read(REVIEW/'file-inventory.json')['files']}
        sets = read(REVIEW/'semantic-dependencies.json')['sets']
        self.assertEqual({k:v['count'] for k,v in sets.items()}, {
            'current_entity_snapshot_query':40,'current_full_query_api_read_surface':68,
            'canonical_tree_and_full_query_api_parity':82,
            'historical_admission_validation_additional_dependencies':17})
        for value in sets.values():
            self.assertEqual(len(value['files']), value['count'])
            for ref in value['files']:
                self.assertEqual(ref, inventory[ref['path']])
        self.assertTrue(set(r['path'] for r in sets['current_entity_snapshot_query']['files']) <=
                        set(r['path'] for r in sets['current_full_query_api_read_surface']['files']))

    def test_original_auxiliary_identity_is_not_re_pinned(self):
        ref = read(REVIEW/'preservation-bindings.json')
        self.assertEqual(ref['historical_protected_identity'],
            'sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53')
        fixture = ROOT/'tests/fixtures/historical_replay/card-acquisition-pilot/docs/ARCHITECTURE.md'
        self.assertEqual(hashlib.sha256(fixture.read_bytes()).hexdigest(), ref['historical_auxiliary_architecture_sha256'])


class FictionalLegacyClosureProofTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root/'data'
        shutil.copytree(FIXTURES/'lantern/data', self.data)
        self.state = {
            'card': {'unit-1':{'values':{'name':'Must Not Override Typed'}},
                     'annex':{'values':{'name':'Original Annex'},'promotion_id':'fictional-history'}},
            'printing': {'annex-print':{'values':{'card_id':'annex','set_id':'fictional',
                'collector_number':'annex','language':'en','finish_ids':['nonfoil']},'promotion_id':'fictional-history'}},
            'identifier': {'alias':{'values':{'namespace':'fictional','value':'annex-alias','printing_uuid':'annex-print'}}},
            'finish': {'nonfoil':{'values':{'value':'nonfoil'}}}}
        save(self.data/'canonical/state.json', self.state)
        save(self.data/'audit/review.json', {'schema_version':'fictional-review-only',
            'promotion_id':'fictional-history','promoted_entities':['annex','annex-print'],
            'result':'fictional-history-only'})

    def engine(self, data=None):
        return CanonicalQueryEngine.from_attachment(attach_legacy_public(
            game='lantern', data_root=data or self.data))

    def test_actual_stage1_seam_still_accepts_only_unchanged_fictional_profile(self):
        root=FIXTURES/'lantern'
        release=read(root/'release-manifest.json')
        attached=attach_snapshot(root,game='lantern',expected_snapshot_id=release['snapshot_id'])
        self.assertEqual(len(CanonicalQueryEngine.from_attachment(attached).entities(entity_type='card')),2)
        mixed=self.root/'mixed'
        shutil.copytree(root,mixed)
        save(mixed/'data/canonical/state.json',self.state)
        with self.assertRaises(SnapshotError):
            attach_snapshot(mixed,game='lantern',expected_snapshot_id=release['snapshot_id'])

    def test_typed_precedence_alias_relationship_and_separate_collection(self):
        engine=self.engine()
        self.assertEqual(engine.entity('unit-1').canonical_values['name'],'Lantern Unit')
        self.assertEqual(len(engine.entities(entity_type='card')),3)
        resolver=CanonicalCollectionResolver.from_attachment(attach_legacy_public(game='lantern',data_root=self.data))
        result=resolver.resolve({'entries':[{'external_identifiers':{'fictional':'annex-alias'},'quantity':1}]})
        self.assertEqual(result['results'][0]['status'],'resolved')
        self.assertEqual(result['results'][0]['card_id'],'annex')
        self.assertEqual(result['canonical_snapshot_id'],engine.snapshot().snapshot_id)
        self.assertEqual(result['catalog_attachment']['profile'],'legacy-public-v1')
        self.assertFalse((self.data/'collections').exists())

    def test_relocation_preserves_legacy_query_and_resolution_semantics(self):
        relocated=self.root/'elsewhere/data'
        shutil.copytree(self.data,relocated)
        self.assertEqual(self.engine().snapshot().as_dict(),self.engine(relocated).snapshot().as_dict())
        imported={'entries':[{'printing_id':'annex-print','quantity':1}]}
        def result(data):
            return CanonicalCollectionResolver.from_attachment(attach_legacy_public(game='lantern',data_root=data)).resolve(imported)
        self.assertEqual(result(self.data),result(relocated))

    def test_audit_bytes_bind_query_but_unrelated_audit_api_is_separate(self):
        original=self.engine().snapshot().snapshot_id
        audit=read(self.data/'audit/review.json');audit['note']='Original fictional revision'
        save(self.data/'audit/review.json',audit)
        self.assertNotEqual(self.engine().snapshot().snapshot_id,original)
        before=self.engine().snapshot().snapshot_id
        save(self.data/'audit/unrelated.json',{'promotion_id':'fictional-unrelated','promoted_entities':[],
            'rejected_entities':['unselected-fictional'],'validation_results':{'valid':False}})
        query=self.engine()
        self.assertEqual(query.snapshot().snapshot_id,before)
        self.assertEqual(len(query.validation('rejected')),1)
        self.assertEqual(len(query.related('fictional-unrelated','promotion_audits')),1)

    def test_knowledge_facts_and_market_not_loaded_as_catalog(self):
        original=self.engine().snapshot().as_dict()
        save(self.data/'knowledge/facts/lantern/annex/original.json',{'original_fictional_fact':True})
        save(self.data/'market/observations/original.json',{'original_fictional_observation':True})
        self.assertEqual(self.engine().snapshot().as_dict(),original)
        save(self.data/'canonical/knowledge/state.json',{'fixture_role':{'annex-role':{'values':{'role':'fixture-only'}}}})
        self.assertNotEqual(self.engine().snapshot().as_dict(),original)

    def test_untracked_canonical_file_is_rejected_without_reading_its_contents(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        subprocess.run(['git','-C',str(self.root),'add','data'],check=True)
        extra = self.data/'canonical/untracked-fictional.json'
        extra.write_bytes(b'PRIVATE_FICTIONAL_MARKER')
        original = Path.read_bytes
        def guarded(path):
            if path == extra:
                raise AssertionError('untracked content was read')
            return original(path)
        with patch.object(Path, 'read_bytes', guarded):
            with self.assertRaisesRegex(ValueError, 'untracked or missing canonical input'):
                inspect(self.root, baseline_revision='fictional-review-only')
        self.assertEqual(extra.read_bytes(), b'PRIVATE_FICTIONAL_MARKER')

    def test_untracked_canonical_symlink_fails_without_following_it(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        subprocess.run(['git','-C',str(self.root),'add','data'],check=True)
        target = self.root/'fictional-private.txt'
        target.write_text('Original fictional private fixture')
        (self.data/'canonical/linked').symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'symlinked canonical input'):
            inspect(self.root, baseline_revision='fictional-review-only')

    def test_generic_inspector_reads_other_game_and_does_not_mutate(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        subprocess.run(['git','-C',str(self.root),'add','data'],check=True)
        before=hashes(p for p in self.data.rglob('*') if p.is_file())
        result=inspect(self.root,baseline_revision='fictional-review-only')
        self.assertEqual(result['games']['lantern']['card']['count'],2)
        self.assertEqual(result['promoted_state']['card']['count'],2)
        self.assertEqual(result['typed_state_overlap']['lantern']['card'],1)
        self.assertEqual(hashes(p for p in self.data.rglob('*') if p.is_file()),before)


if __name__ == '__main__':
    unittest.main()
