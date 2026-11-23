"""Literal, unadmitted MTGJSON evidence. No rules or ability interpretation.

The owning reconciler calls these projections inside its bounded worker. Readers
require independently pinned native report/profile identities, never source-supplied
approval flags. Exact source replay is a separate operation from artifact inspection.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .private_policy import (ORACLE_RETENTION, PrivateResearchProfile, SourcePolicyError,
                             canonical, digest)

REPORT_VERSION = 'private-mtgjson-oracle-import-report-v1'
EVIDENCE_VERSION = 'mtgjson-candidate-oracle-evidence-v1'
MAX_REPORT_BYTES = 4 * 1024**2
MAX_EVIDENCE_LINE_BYTES = 256 * 1024
MAX_SELECTED_OCCURRENCES = 128


def replay_guarantees(mode):
    return dict(retention_mode=mode,
        original_retention='CUSTODIAN_REQUIRED' if mode == 'retained-source' else 'NOT_REQUIRED_AFTER_COMPLETION',
        full_source_replay='REQUIRES_EXACT_ORIGINAL_ARTIFACT',
        complete_source_replay_available_without_original=False,
        checkpoint_recovery_requires_original=True, automatic_source_deletion=False)


def project_text(raw, key, ordinal):
    """Retain exactly the supported provider text field, with explicit boundaries."""
    pointer = '/data/' + key.replace('~', '~0').replace('/', '~1') + '/cards/' + str(ordinal)
    result = dict(source_field='text', source_pointer=pointer+'/text', status='MISSING',
                  reason='field_absent', face_boundary={'kind': 'UNRESOLVED'})
    if type(raw) is not dict:
        return result
    layout = raw.get('layout')
    if layout == 'normal' and not any(x in raw for x in ('side', 'faceName', 'otherFaceIds')):
        result['face_boundary'] = {'kind': 'WHOLE_CARD', 'layout': layout}
    elif (type(layout) is str and layout != 'normal' and raw.get('side') in ('a', 'b', 'c')
          and type(raw.get('faceName')) is str and 0 < len(raw['faceName']) <= 256
          and type(raw.get('otherFaceIds')) is list and 0 < len(raw['otherFaceIds']) <= 128
          and all(type(x) is str and 0 < len(x) <= 256 for x in raw['otherFaceIds'])):
        result['face_boundary'] = dict(kind='EXPLICIT_FACE', layout=layout,
            side=raw['side'], face_name=raw['faceName'], related_printings=raw['otherFaceIds'])
    else:
        return dict(result, status='UNSUPPORTED', reason='missing_or_ambiguous_text_boundary')
    if 'text' not in raw:
        return result
    value = raw['text']
    if value is None:
        return dict(result, reason='provider_null')
    if type(value) is not str:
        return dict(result, status='UNSUPPORTED', reason='unsupported_text_value')
    return dict(result, status='SUPPLIED', reason='literal_source_assertion_not_verified_mechanics', value=value)


def evidence_records(db, binding):
    """Stream each source occurrence, including conflicts; never select a winner."""
    scope = binding['private_scope']['source_use_receipt']
    release = {k:v for k,v in binding.items() if k != 'private_scope'}
    for p, n, payload in db.execute('SELECT p,n,payload FROM records ORDER BY p,n'):
        row = json.loads(payload)
        text = row['oracle_evidence']
        conditions = []
        if row['status'] != 'SUPPORTED':
            conditions.append(row['status'])
        if db.execute('SELECT 1 FROM conflicts WHERE card_id=? LIMIT 1', (row['card_id'],)).fetchone():
            conditions.append('CONFLICTING_CARD_ASSERTIONS')
        if db.execute('SELECT 1 FROM duplicate_printings WHERE printing_id=?', (row['printing_id'],)).fetchone():
            conditions.append('DUPLICATE_OR_CONFLICTING_PRINTING')
        if db.execute("""SELECT 1 FROM alias_conflicts a,json_each(?,'$.identifiers') j
                         WHERE a.namespace=j.key AND a.value=lower(j.value) LIMIT 1""", (payload,)).fetchone():
            conditions.append('CONFLICTING_EXTERNAL_IDENTIFIER')
        for related in row['relationships']:
            matches = db.execute('SELECT card_id FROM records WHERE printing_id=?', (related,)).fetchall()
            if matches != [(row['card_id'],)]:
                conditions.append('UNRESOLVED_FACE_RELATIONSHIP')
        if row['exceptional']:
            conditions.append('EXCEPTIONAL_RECORD_REQUIRES_REVIEW')
        if text['status'] != 'SUPPLIED':
            conditions.append(text['reason'])
        key, partition_hash = db.execute('SELECT key,raw_hash FROM partitions WHERE seq=?', (p,)).fetchone()
        body = dict(schema_version=EVIDENCE_VERSION, card_id=row['card_id'], printing_id=row['printing_id'],
            candidate_status='WITHHELD' if conditions else 'UNADMITTED_SOURCE_EVIDENCE',
            conditions=sorted(set(conditions)), text=text,
            source_release=release, source_partition=key, source_partition_sha256=partition_hash,
            source_row=n, source_record_sha256=row['source_record_sha256'],
            provenance_sha256=scope['provenance_sha256'], notice_sha256=scope['notice_sha256'],
            source_use_profile_id=scope['profile_id'],
            canonical_admission='NOT_PERFORMED', semantic_authority='NOT_ESTABLISHED',
            current_oracle_verified=False, real_card_execution='BLOCKED')
        yield dict(body, evidence_id='sha256:'+digest(body))


def _check(condition, reason):
    if not condition:
        raise SourcePolicyError(reason)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _check(key not in result, 'duplicate evidence key')
        result[key] = value
    return result


def read_candidate_evidence(directory, *, profile, expected_report_id, card_id, printing_id):
    """Inspect importer output using trusted report/profile pins, without source IO.

    The report identity must come from the caller's independently retained import
    receipt, not be copied from newly received, untrusted artifact bytes.
    """
    _check(type(profile) is PrivateResearchProfile and profile.retention_profile == ORACLE_RETENTION,
           'explicit Oracle evidence profile required')
    profile.require_inspection()  # Before reading source-bearing artifacts.
    _check(type(expected_report_id) is str and expected_report_id.startswith('sha256:')
           and len(expected_report_id) == 71, 'independently pinned report required')
    root = Path(directory).absolute()
    _check(not any(p.is_symlink() for p in (root, *root.parents)), 'symlink evidence directory refused')
    _check(not any((p/'.git').is_file() or (p/'.git/HEAD').is_file() for p in (root,*root.parents)),
           'private evidence must remain outside Git')
    try:
        _check(root.is_dir() and root.stat().st_mode & 0o077 == 0, 'private evidence directory required')
        report_path = root/'report.json'
        _check(not report_path.is_symlink() and report_path.is_file(), 'ordinary report required')
        with report_path.open('rb') as stream:
            raw = stream.read(MAX_REPORT_BYTES+1)
        _check(len(raw) <= MAX_REPORT_BYTES, 'report exceeds bound')
        report = json.loads(raw, object_pairs_hook=_unique)
        _check(type(report) is dict and report.get('report_id') == expected_report_id
               and 'sha256:'+digest({k:v for k,v in report.items() if k!='report_id'}) == expected_report_id,
               'import report integrity mismatch')
        _check(report.get('schema_version') == REPORT_VERSION and report.get('status') == 'CANDIDATES_PREPARED'
               and report.get('retention_profile') == ORACLE_RETENTION
               and report.get('canonical_admission') == 'NOT_PERFORMED'
               and report.get('real_card_execution') == 'BLOCKED', 'incompatible or authoritative evidence refused')
        expected_release = json.loads(profile.release_json) | {'private_scope': {
            'retention_profile': ORACLE_RETENTION, 'source_use_receipt': profile.receipt()}}
        _check(report['source_release'] == expected_release, 'profile or release binding mismatch')
        pin = report['artifacts']['oracle-evidence.jsonl']
        path = root/'oracle-evidence.jsonl'
        _check(not path.is_symlink() and path.is_file(), 'ordinary evidence artifact required')
        _check(pin['bytes'] <= report['limits']['output_bytes'] <= 512*1024**2,
               'evidence exceeds supported output budget')
        selected, count, size, checksum = [], 0, 0, hashlib.sha256()
        with path.open('rb') as stream:
            while True:
                line = stream.readline(MAX_EVIDENCE_LINE_BYTES+1)
                if not line:
                    break
                size += len(line); count += 1; checksum.update(line)
                _check(len(line) <= MAX_EVIDENCE_LINE_BYTES and size <= pin['bytes'], 'evidence exceeds bound')
                item = json.loads(line, object_pairs_hook=_unique)
                _check(type(item) is dict, 'invalid evidence occurrence')
                if item.get('card_id') == card_id and item.get('printing_id') == printing_id:
                    _check(item.get('schema_version') == EVIDENCE_VERSION and
                           item.get('evidence_id') == 'sha256:'+digest({k:v for k,v in item.items() if k!='evidence_id'}),
                           'evidence occurrence integrity mismatch')
                    selected.append(item)
                    _check(len(selected) <= MAX_SELECTED_OCCURRENCES, 'selected occurrence budget exceeded')
        _check(dict(bytes=size, rows=count, sha256=checksum.hexdigest()) == pin, 'evidence artifact integrity mismatch')
        return dict(report_id=expected_report_id, source_use_profile_id=profile.receipt()['profile_id'],
                    replay=report['replay'], occurrences=selected,
                    status='IDENTITY_UNRESOLVED' if not selected else 'WITHHELD' if any(
                        x['candidate_status']=='WITHHELD' for x in selected) else 'UNADMITTED_SOURCE_EVIDENCE')
    except SourcePolicyError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise SourcePolicyError('invalid or unavailable private evidence') from None
