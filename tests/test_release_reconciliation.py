"""Original provider-shaped release -> owning mapper -> disk reconciliation."""
from copy import deepcopy
from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import os
import time

from providers.mtgjson.mapper import map_dataset
from providers.mtgjson.parser import parse_dataset
from providers.mtgjson.reconciliation import (
    reconcile_release, ReconciliationLimits, ReconciliationError, VERSION, OPERATION,
)

FIXTURE = Path(__file__).parent / 'fixtures/release_reconciliation_v1/original-release.json'


def _interrupt_child(connection, source, root, binding, limits, stop_after):
    from providers.mtgjson import reconciliation as implementation
    original = implementation._row
    def interrupted(meta, key, source_set, raw, cap):
        if key == 'QRB':
            os._exit(9)  # Actual process death during the second SQLite transaction.
        return original(meta, key, source_set, raw, cap)
    with patch.object(implementation, '_row', interrupted):
        implementation._worker(connection, source, root, binding, limits, stop_after)


def _limited_child(connection, source, root, binding, limits, stop_after):
    from providers.mtgjson import reconciliation as implementation
    def constrained(*args):
        if binding['release_id'] == 'memory-test':
            return bytearray(1024**3)
        while True:
            if binding['release_id'] == 'wall-test':
                time.sleep(.1)
    with patch.object(implementation, '_run', constrained):
        implementation._worker(connection, source, root, binding, limits, stop_after)


class ReleaseReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.document = json.loads(FIXTURE.read_bytes())
        self.source = self.root / 'original.json'
        self.workspace = self.root / 'private'
        self.seen_bindings = []

    def prepare(self, doc=None, raw=None):
        doc = self.document if doc is None else doc
        self.source.write_bytes(raw if raw is not None else json.dumps(doc).encode())
        self.release = dict(provider='MTGJSON', release_id='original-project-fixture-v1',
            version='5.2.1', date='2026-11-20', artifact_sha256=hashlib.sha256(self.source.read_bytes()).hexdigest(),
            provenance_reference='original-project-authorship-fixture', notice_reference='project-fixture-notices')

    def authorize_original_fixture(self, binding):
        self.seen_bindings.append(deepcopy(binding))
        # Test host authorization is for these original fixture bytes only.
        return (binding['operation'] == OPERATION and binding['release'] == self.release
                and binding['whole_artifact_read'] is True and binding['public_export'] is False)

    def run_release(self, **kwargs):
        return reconcile_release(self.source, self.workspace, self.release,
            authorize_source=self.authorize_original_fixture, **kwargs)

    def lines(self, name):
        return [json.loads(x) for x in (self.workspace/'output'/name).read_text().splitlines()]

    def error(self, code, call):
        with self.assertRaises(ReconciliationError) as context:
            call()
        self.assertEqual(context.exception.code, code, context.exception)
        self.assertEqual(context.exception.as_dict()['status'], 'REFUSED')

    def test_complete_end_to_end_two_sets_share_card_keep_distinct_printings(self):
        self.prepare()
        before = deepcopy(self.release)
        mapped = map_dataset(parse_dataset(self.source))
        result = self.run_release()
        self.assertEqual(result['schema_version'], VERSION)
        self.assertEqual(result['total_source_rows'], 4)
        self.assertEqual(result['unique_supported_card_identities'], 3)
        self.assertEqual(result['distinct_printing_identities'], 4)
        self.assertEqual(result['source_processing_completeness'], 'ALL_ROWS_ACCOUNTED_FOR')
        self.assertEqual(result['catalog_population_completeness'], 'NOT_ESTABLISHED')
        self.assertEqual(result['canonical_admission'], 'NOT_PERFORMED')
        cards = self.lines('cards.jsonl')
        rivet = next(x for x in cards if x['card_id'] == 'fixture-card-rivet')
        self.assertTrue(rivet['cross_set_relationship'])
        self.assertEqual(rivet['source_occurrences'], 2)
        expected = {x['candidate_identifier'] for x in mapped if x['entity_type'] == 'printing'}
        self.assertEqual({x['mapped_candidate']['candidate_identifier'] for x in self.lines('printings.jsonl')}, expected)
        self.assertEqual(self.release, before)
        self.assertEqual(len(self.seen_bindings), 1)
        self.assertNotIn(str(self.root), json.dumps(result))
        for name, evidence in result['artifacts'].items():
            raw = (self.workspace/'output'/name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence['sha256'])
            self.assertEqual(len(raw), evidence['bytes'])

    def test_cross_set_assertions_actually_compared_and_dependent_printings_withheld(self):
        self.document['data']['QRB']['cards'][0]['manaCost'] = '{9}'
        self.document['data']['QRB']['cards'][0]['text'] = 'An original fixture assertion.'
        self.prepare(); result = self.run_release()
        self.assertEqual(result['conflicting_card_fields'], 1)
        self.assertEqual(self.lines('conflicts.jsonl')[0]['field'], 'manaCost')
        cards = self.lines('cards.jsonl')
        self.assertEqual(next(x for x in cards if x['card_id']=='fixture-card-rivet')['candidate_status'], 'WITHHELD')
        rows = [x for x in self.lines('printings.jsonl') if x['card_id']=='fixture-card-rivet']
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(x['mapped_candidate'] is None for x in rows))
        self.assertEqual(len(self.lines('assertions.jsonl')), 4)

    def test_name_equality_is_not_identity_and_name_change_is_an_assertion(self):
        self.document['data']['QRB']['cards'][1]['name'] = 'Quiet Rivet Archivist'
        self.document['data']['QRB']['cards'][0]['name'] = 'An Altered Fixture Label'
        self.prepare(); report = self.run_release()
        self.assertEqual(report['unique_supported_card_identities'], 3)
        self.assertEqual(report['conflicting_card_fields'], 1)

    def test_duplicate_and_conflicting_printings_preserve_all_occurrences(self):
        row = deepcopy(self.document['data']['QRA']['cards'][0])
        self.document['data']['QRA']['cards'].append(row)
        self.document['data']['QRB']['cards'][0]['uuid'] = row['uuid']
        self.prepare(); report = self.run_release()
        self.assertEqual(report['total_source_rows'], 5)
        self.assertEqual(report['duplicate_printing_identities'], 1)
        self.assertEqual(report['conflicting_printing_identities'], 1)
        self.assertEqual(self.lines('duplicates.jsonl')[0]['occurrences'], 3)
        candidate = next(x for x in self.lines('printings.jsonl') if x['printing_id']==row['uuid'])
        self.assertIsNone(candidate['mapped_candidate']); self.assertIsNone(candidate['card_id'])

    def test_identical_duplicate_is_reported_not_insert_or_ignore(self):
        self.document['data']['QRA']['cards'] *= 2
        self.prepare(); report = self.run_release()
        self.assertEqual(report['total_source_rows'], 6)
        self.assertEqual(report['duplicate_printing_identities'], 2)
        self.assertEqual(report['conflicting_printing_identities'], 0)
        self.assertTrue(all(x['classification']=='DUPLICATE' for x in self.lines('duplicates.jsonl')))

    def test_strict_alias_collision_crossing_partitions(self):
        self.document['data']['QRB']['cards'][0]['identifiers']['scryfallId'] = 'fixture-external-rivet-a'
        self.prepare(); report = self.run_release()
        self.assertEqual(report['conflicting_external_identifiers'], 1)
        candidates = [x for x in self.lines('printings.jsonl') if x['card_id']=='fixture-card-rivet']
        self.assertTrue(all(x['candidate_status']=='WITHHELD' for x in candidates))

    def test_missing_and_ambiguous_oracle_ids_never_fall_back_to_names(self):
        a,b = self.document['data']['QRA']['cards']
        a['identifiers'] = {}
        b['identifiers']['oracleId'] = 'different-fixture-identity'
        self.prepare(); report = self.run_release()
        self.assertEqual(report['unresolved_identity_records'], 2)
        unresolved = [x for x in self.lines('assertions.jsonl') if x['status']=='IDENTITY_UNRESOLVED']
        self.assertTrue(all(x['card_id'] is None and x['mapped_card'] is None for x in unresolved))
        self.assertEqual(len(self.lines('unresolved.jsonl')), 2)

    def test_multiface_relations_preserved_and_missing_relations_reported(self):
        a,b = self.document['data']['QRA']['cards']
        a.update(layout='transform', side='a', faceName='Original Front', otherFaceIds=[b['uuid']])
        b.update(layout='transform', side='b', faceName='Original Back', otherFaceIds=['missing-original-face'])
        self.prepare(); report = self.run_release()
        self.assertEqual(report['exceptional_records'], 2)
        exceptional = self.lines('exceptional.jsonl')
        self.assertEqual(exceptional[0]['related_printings'], [b['uuid']])
        self.assertEqual(exceptional[1]['missing_related_printings'], ['missing-original-face'])
        self.assertTrue(all(x['candidate_status']=='WITHHELD' for x in self.lines('printings.jsonl') if x['printing_id'] in (a['uuid'],b['uuid'])))

    def test_unsupported_records_and_missing_identifiers_are_accounted_not_fabricated(self):
        self.document['data']['QRA']['cards'] += [None, {'identifiers': {'scryfallOracleId':'fixture-broken'}}]
        self.prepare(); report = self.run_release()
        self.assertEqual(report['total_source_rows'], 6)
        self.assertEqual(report['unsupported_records'], 2)
        self.assertEqual(len(self.lines('assertions.jsonl')), 6)

    def test_deterministic_replay_validates_checkpoint_and_emits_identical_artifacts(self):
        self.prepare(); first = self.run_release()
        contents = {x:p.read_bytes() for x in first['artifacts'] for p in [self.workspace/'output'/x]}
        second = self.run_release()
        self.assertEqual(first, second)
        self.assertEqual(contents, {x:(self.workspace/'output'/x).read_bytes() for x in contents})

    def test_pause_resume_does_not_remap_completed_partitions_as_new(self):
        self.prepare(); paused = self.run_release(stop_after_partitions=1)
        self.assertEqual(paused['status'], 'PAUSED')
        self.assertEqual(paused['completed_partitions'], 1)
        self.assertFalse((self.workspace/'output/report.json').exists())
        resumed = self.run_release()
        original = self.workspace; self.workspace = self.root/'fresh'
        fresh = self.run_release(); self.workspace = original
        self.assertEqual(resumed, fresh)

    def test_actual_worker_death_rolls_back_partial_partition_and_resumes(self):
        self.prepare()
        with patch('providers.mtgjson.reconciliation._worker', _interrupt_child):
            self.error('RESOURCE_BUDGET', self.run_release)
        with sqlite3.connect(self.workspace/'index.sqlite3') as db:
            self.assertEqual(db.execute('SELECT count(*) FROM partitions').fetchone()[0], 1)
        resumed = self.run_release()
        self.assertEqual(resumed['total_source_rows'], 4)
        self.assertEqual(resumed['distinct_printing_identities'], 4)

    def test_actual_cpu_memory_and_wall_limits_are_refusals_not_success(self):
        self.prepare()
        for name, limits in (
            ('cpu-test', replace(ReconciliationLimits(),cpu_seconds=1)),
            ('memory-test', ReconciliationLimits()),
            ('wall-test', replace(ReconciliationLimits(),wall_seconds=1))):
            self.release['release_id'] = name; self.workspace=self.root/name
            with patch('providers.mtgjson.reconciliation._worker', _limited_child):
                self.error('RESOURCE_BUDGET', lambda:self.run_release(limits=limits))
            self.assertFalse((self.workspace/'output/report.json').exists())

    def test_tampered_and_coherently_rehashed_checkpoint_rows_rejected(self):
        self.prepare(); self.run_release(stop_after_partitions=1)
        with sqlite3.connect(self.workspace/'index.sqlite3') as db:
            payload = json.loads(db.execute('SELECT payload FROM records WHERE p=0 AND n=0').fetchone()[0])
            payload['assertions']['manaCost'] = '{8}'
            db.execute('UPDATE records SET payload=? WHERE p=0 AND n=0', (json.dumps(payload,sort_keys=True,separators=(',',':')),))
            db.execute("UPDATE assertions SET value='\"{8}\"' WHERE p=0 AND n=0 AND field='manaCost'")
        self.error('INTEGRITY_MISMATCH', self.run_release)

    def test_altered_index_assertion_and_extra_rows_rejected(self):
        self.prepare(); self.run_release(stop_after_partitions=1)
        with sqlite3.connect(self.workspace/'index.sqlite3') as db:
            db.execute("UPDATE assertions SET value='\"{8}\"' WHERE p=0 AND n=0 AND field='manaCost'")
        self.error('INTEGRITY_MISMATCH', self.run_release)

    def test_extra_index_rows_rejected_even_with_valid_known_rows(self):
        self.prepare(); self.run_release(stop_after_partitions=1)
        with sqlite3.connect(self.workspace/'index.sqlite3') as db:
            row=list(db.execute('SELECT * FROM records LIMIT 1').fetchone());row[1]=999
            db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?)', row)
        self.error('INTEGRITY_MISMATCH', self.run_release)

    def test_source_hash_metadata_and_workspace_bindings_rejected(self):
        self.prepare(); original = deepcopy(self.release)
        self.release['artifact_sha256']='0'*64
        self.error('INTEGRITY_MISMATCH', self.run_release)
        self.release=original; self.release['version']='5.2.2'
        self.error('INTEGRITY_MISMATCH', self.run_release)

    def test_source_authorization_refuses_before_read_or_workspace_creation(self):
        self.prepare()
        with patch.object(Path, 'open', side_effect=AssertionError('source must not be read')):
            self.error('SOURCE_POLICY_REFUSAL', lambda: reconcile_release(
                self.source,self.workspace,self.release))
            self.error('SOURCE_POLICY_REFUSAL', lambda: reconcile_release(
                self.source,self.workspace,self.release,authorize_source=lambda _:False))
        self.assertFalse(self.workspace.exists())

    def test_license_and_approved_flags_are_not_authorization(self):
        self.prepare(); self.release['approved']=True
        self.error('INVALID_INPUT', self.run_release)
        self.release.pop('approved')
        def unavailable(_): raise RuntimeError('PRIVATE_SECRET')
        with self.assertRaises(ReconciliationError) as context:
            reconcile_release(self.source,self.workspace,self.release,authorize_source=unavailable)
        self.assertNotIn('PRIVATE_SECRET', str(context.exception))

    def test_resource_row_and_partition_limits_refuse_without_complete_report(self):
        self.prepare()
        self.error('RESOURCE_BUDGET', lambda:self.run_release(limits=replace(ReconciliationLimits(),rows=3)))
        self.assertFalse((self.workspace/'output/report.json').exists())
        self.workspace=self.root/'partition-limit'
        self.error('RESOURCE_BUDGET', lambda:self.run_release(limits=replace(ReconciliationLimits(),partitions=1)))

    def test_resource_row_size_and_output_limits(self):
        self.prepare()
        self.error('RESOURCE_BUDGET', lambda:self.run_release(limits=replace(ReconciliationLimits(),row_bytes=50)))
        self.workspace=self.root/'output-limit'
        self.error('RESOURCE_BUDGET', lambda:self.run_release(limits=replace(ReconciliationLimits(),output_bytes=20)))
        self.assertFalse((self.workspace/'output/report.json').exists())

    def test_source_and_decoded_byte_budgets(self):
        self.prepare()
        self.error('RESOURCE_BUDGET',lambda:self.run_release(limits=replace(ReconciliationLimits(),source_bytes=10)))
        self.error('RESOURCE_BUDGET',lambda:self.run_release(limits=replace(ReconciliationLimits(),decoded_bytes=10)))

    def test_resource_partition_accumulation_is_bounded_before_decode(self):
        self.document['data']['QRA']['padding']='x'*10000
        self.prepare()
        self.error('RESOURCE_BUDGET', lambda:self.run_release(limits=replace(ReconciliationLimits(),partition_bytes=1024)))

    def test_disk_limit_is_enforced(self):
        for index in range(500):
            row=deepcopy(self.document['data']['QRA']['cards'][0])
            row['uuid']='fixture-large-'+str(index)
            row['identifiers']={'scryfallOracleId':'fixture-card-'+str(index)}
            row['original-fixture-padding']='z'*2000
            self.document['data']['QRA']['cards'].append(row)
        self.prepare()
        self.error('RESOURCE_BUDGET',lambda:self.run_release(limits=replace(ReconciliationLimits(),disk_bytes=1024**2)))
        self.assertFalse((self.workspace/'output/report.json').exists())

    def test_many_partition_path_stays_streamed_and_reconciles_global_identities(self):
        self.document['data']={}
        for index in range(12):
            code='ORIGINAL'+str(index)
            cards=[]
            for i in range(100):
                cards.append(dict(uuid='fixture-print-'+str(index)+'-'+str(i),name='Original '+str(i),
                    number=str(i),layout='normal',colors=[],manaCost='{1}',
                    identifiers={'scryfallOracleId':'fixture-card-'+str(i)}))
            self.document['data'][code]=dict(code=code,name='Original Fixture '+str(index),cards=cards)
        self.prepare(); report=self.run_release()
        self.assertEqual(report['total_source_rows'],1200)
        self.assertEqual(report['unique_supported_card_identities'],100)
        self.assertEqual(report['distinct_printing_identities'],1200)
        self.assertTrue(all(x['partition_count']==12 for x in self.lines('cards.jsonl')))
        measurement=json.loads((self.workspace/'last-run.json').read_text())
        self.assertLess(measurement['peak_memory_kib'],512*1024)

    def test_workspace_lock_refuses_concurrent_execution(self):
        import fcntl
        self.prepare();self.workspace.mkdir(mode=0o700)
        with (self.workspace/'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.error('WORKSPACE_BUSY',self.run_release)

    def test_invalid_limit_types_and_enlargements_refuse(self):
        self.prepare()
        for limits in (replace(ReconciliationLimits(),rows=True), replace(ReconciliationLimits(),rows=1_000_001),
                       replace(ReconciliationLimits(),memory_bytes=1), replace(ReconciliationLimits(),cpu_seconds=0)):
            self.error('INVALID_INPUT', lambda:self.run_release(limits=limits))

    def test_malformed_envelope_duplicate_keys_and_trailing_data_rejected(self):
        for i,raw in enumerate((b'{}', b'{"meta":{},"meta":{},"data":{}}',
            json.dumps(self.document).encode()+b' false',
            json.dumps(self.document).replace('"cards": [','"cards": [NaN,',1).encode())):
            self.prepare(raw=raw); self.workspace=self.root/('bad'+str(i))
            with self.assertRaises(ReconciliationError): self.run_release()

    def test_duplicate_partition_case_and_unrecognized_envelope_rejected(self):
        self.document['data']['qra']=deepcopy(self.document['data']['QRA'])
        self.prepare(); self.error('INVALID_INPUT', self.run_release)

    def test_gzip_uses_same_semantics_without_loading_the_corpus(self):
        self.prepare(); plain=self.run_release()
        raw=self.source.read_bytes(); self.source=self.root/'original.json.gz'
        self.source.write_bytes(gzip.compress(raw,mtime=0))
        self.release['artifact_sha256']=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.workspace=self.root/'zipped'; zipped=self.run_release()
        for key in ('total_source_rows','unique_supported_card_identities','distinct_printing_identities','partition_inventory'):
            self.assertEqual(plain[key], zipped[key])

    def test_unsafe_paths_unrelated_workspace_and_symlink_checkpoint_refused(self):
        self.prepare(); linked=self.root/'link.json'; linked.symlink_to(self.source)
        self.error('INVALID_INPUT', lambda:reconcile_release(linked,self.workspace,self.release,
            authorize_source=self.authorize_original_fixture))
        self.workspace.mkdir(mode=0o700); (self.workspace/'unrelated').write_text('preserve')
        self.error('INVALID_INPUT', self.run_release)
        (self.workspace/'unrelated').unlink()
        (self.workspace/'index.sqlite3').symlink_to(self.source)
        self.error('INVALID_INPUT', self.run_release)

    def test_report_schema(self):
        from jsonschema import Draft202012Validator
        self.prepare(); report=self.run_release()
        schema=json.loads((Path(__file__).parents[1]/'src/schemas/v1/release-catalog-reconciliation-report.schema.json').read_text())
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(report)
        changed=deepcopy(report);changed['invented_authority']=True
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(changed)))


if __name__=='__main__': unittest.main()
