"""Durable, bounded factual publication; source custody/deletion stays external.

The report identity must be independently retained from the successful importer,
not copied from newly received artifacts. Hashes establish integrity, not rights.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path

from jsonschema import Draft202012Validator

from .private_policy import PrivateResearchProfile, RETENTION, SourcePolicyError, canonical, digest

REPORT_VERSION = 'private-mtgjson-factual-limited-report-v1'
PUBLICATION_VERSION = 'private-mtgjson-factual-publication-v1'
PUBLICATION_NAMES = frozenset(('provenance.json', 'notice.txt', 'publication.json',
    'provenance.json.tmp', 'notice.txt.tmp', 'publication.json.tmp'))
MAX_REPORT_BYTES = 4 * 1024**2
BLOCK_BYTES = 64 * 1024


def replay_guarantees():
    return dict(retention_mode='limited-retention',
        original_retention='CUSTODIAN_UNTIL_VERIFIED_PUBLICATION',
        full_source_replay='REQUIRES_EXACT_ORIGINAL_ARTIFACT',
        complete_source_replay_available_without_original=False,
        checkpoint_recovery_requires_original=True, automatic_source_deletion=False)


def _require(condition, reason):
    if not condition:
        raise SourcePolicyError(reason)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'duplicate factual publication key')
        result[key] = value
    return result


def _json_file(path, limit):
    from .private_import import _private_path
    path = _private_path(path)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    _require(len(raw) <= limit, 'factual publication control exceeds bound')
    return json.loads(raw, object_pairs_hook=_unique)


@contextmanager
def _locked(workspace, profile):
    _require(type(profile) is PrivateResearchProfile and profile.retention_profile == RETENTION
             and profile.retention_mode == 'limited-retention', 'explicit factual limited profile required')
    profile.require_supported()  # Before any private artifact read.
    root = Path(workspace).absolute()
    _require(not any(p.is_symlink() for p in (root, *root.parents)), 'symlink publication directory refused')
    _require(not any((p/'.git').is_file() or (p/'.git/HEAD').is_file() for p in (root,*root.parents)),
             'private factual publication must remain outside Git')
    _require(root.is_dir() and root.stat().st_mode & 0o077 == 0, 'private publication directory required')
    _require({p.name for p in root.iterdir()} <= {'index.sqlite3', 'index.sqlite3-journal',
             'output', 'last-run.json', '.lock'}, 'dedicated factual publication workspace required')
    _require(not any(p.is_symlink() for p in root.rglob('*')), 'symlink in publication workspace refused')
    from .private_import import _private_path
    lock = _private_path(root/'.lock')
    with lock.open('rb') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SourcePolicyError('factual publication workspace busy') from None
        try:
            output = root/'output'
            _require(not output.is_symlink() and output.is_dir() and output.stat().st_mode & 0o077 == 0,
                     'private factual output required')
            yield root, output
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _verified_report(output, profile, expected_report_id):
    from .reconciliation import ReconciliationLimits
    _require(type(expected_report_id) is str and len(expected_report_id) == 71
             and expected_report_id.startswith('sha256:'), 'independently pinned report identity required')
    report = _json_file(output/'report.json', MAX_REPORT_BYTES)
    _require(type(report) is dict and report.get('report_id') == expected_report_id
             and 'sha256:'+digest({k:v for k,v in report.items() if k!='report_id'}) == expected_report_id,
             'factual report integrity mismatch')
    schema = json.loads((Path(__file__).parents[2]/'schemas/v1/private-mtgjson-factual-limited-report.schema.json').read_bytes())
    _require(Draft202012Validator(schema).is_valid(report), 'incompatible factual report')
    _require(report['source_release'] == json.loads(profile.release_json) | {'private_scope': {
        'retention_profile': RETENTION, 'source_use_receipt': profile.receipt()}}, 'factual profile or release mismatch')
    _require(report['replay'] == replay_guarantees(), 'incompatible factual replay guarantees')
    limits = ReconciliationLimits(**report['limits']); limits.validate()
    _require({p.name for p in output.iterdir()} <= set(report['artifacts']) | {'report.json'} | PUBLICATION_NAMES,
             'unexpected factual publication artifact')
    from .private_import import _private_path
    for path in output.iterdir():
        _private_path(path)  # Includes interrupted temporary controls; never follow them.
    total = 0
    for name, pin in report['artifacts'].items():
        path = _private_path(output/name)
        checksum, size, rows, last = hashlib.sha256(), 0, 0, b''
        with path.open('rb') as stream:
            while block := stream.read(BLOCK_BYTES):
                size += len(block); total += len(block); rows += block.count(b'\n'); last = block[-1:]
                _require(size <= pin['bytes'] and total <= limits.output_bytes, 'factual artifact exceeds bound')
                checksum.update(block)
        _require(dict(bytes=size, rows=rows, sha256=checksum.hexdigest()) == pin and
                 (not size or last == b'\n'), 'factual artifact integrity mismatch')
    return report, limits


def _body(profile, report):
    return dict(schema_version=PUBLICATION_VERSION, report_id=report['report_id'],
        source_use_profile_id=profile.receipt()['profile_id'], source_artifact_sha256=report['source_release']['artifact_sha256'],
        provenance_sha256=profile.provenance_sha256, notice_sha256=profile.notice_sha256,
        status='FACTUAL_RESULTS_DURABLY_PUBLISHED', cleanup_eligible=True, cleanup_performed=False,
        cleanup_authority='SEPARATE_CUSTODIAN_AUTHORIZATION_REQUIRED',
        canonical_admission='NOT_PERFORMED', production_activation='NOT_PERFORMED',
        semantic_authority='NOT_ESTABLISHED', real_card_execution='BLOCKED', external_ai_export=False,
        replay=replay_guarantees())


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _sync_ancestry(output):
    # mkdir(parents=True) may have created more than the immediate parent.
    # Persist each link before eligibility; a checksum cannot repair lost paths.
    for directory in (output, *output.parents):
        _sync_directory(directory)


def _write_control(path, raw):
    temporary = path.with_name(path.name+'.tmp')
    _require(not temporary.is_symlink(), 'symlink publication control refused')
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


def publish_factual_results(workspace, *, profile, expected_report_id, provenance, notice):
    """Publish controls/receipt after validating every output; never delete source.

    A failed publication raises without granting cleanup eligibility. An already
    completed factual report remains evidence; retry with the original available.
    """
    from .private_import import _control, _private_path
    from .reconciliation import _disk
    try:
        with _locked(workspace, profile) as (root, output):
            report, limits = _verified_report(output, profile, expected_report_id)
            controls = {'provenance.json': _control(provenance, profile.provenance_sha256),
                        'notice.txt': _control(notice, profile.notice_sha256)}
            body = _body(profile, report)
            receipt = dict(body, publication_id='sha256:'+digest(body))
            raw = (canonical(receipt)+'\n').encode()
            # Enforce existing ceilings including retained controls and marker.
            projected = sum(pin['bytes'] for pin in report['artifacts'].values())
            projected += (output/'report.json').stat().st_size + sum(map(len, controls.values())) + len(raw)
            _require(projected <= limits.output_bytes, 'factual publication exceeds output budget')
            for name, value in controls.items():
                _write_control(output/name, value)
            for name in (*report['artifacts'], 'report.json'):
                with _private_path(output/name).open('rb') as stream:
                    os.fsync(stream.fileno())
            _disk(root, limits)
            _require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) + len(raw) <= limits.disk_bytes,
                     'factual publication exceeds disk budget')
            # Establish directory durability before publishing the final marker.
            _sync_ancestry(output)
            _write_control(output/'publication.json', raw)
            _sync_directory(output)
            return receipt
    except SourcePolicyError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise SourcePolicyError('factual publication unavailable or incomplete; source cleanup not authorized') from None


def verify_factual_publication(workspace, *, profile, expected_report_id):
    """Verify retained factual artifacts after custody cleanup, with no source IO.

    This does not replay the source, authenticate permission, or perform cleanup.
    Requires the successful import's independently retained report identity.
    """
    from .private_import import _control, _private_path, CONTROL_BYTES
    from .reconciliation import _disk
    try:
        with _locked(workspace, profile) as (root, output):
            report, limits = _verified_report(output, profile, expected_report_id)
            _control(output/'provenance.json', profile.provenance_sha256)
            _control(output/'notice.txt', profile.notice_sha256)
            body = _body(profile, report)
            expected = dict(body, publication_id='sha256:'+digest(body))
            _require(_json_file(output/'publication.json', CONTROL_BYTES) == expected,
                     'factual publication receipt mismatch')
            _require(sum(p.stat().st_size for p in output.iterdir()) <= limits.output_bytes,
                     'factual publication exceeds output budget')
            _disk(root, limits)
            # Re-establish durability even after an earlier failed final sync.
            for name in (*report['artifacts'], 'report.json', 'provenance.json', 'notice.txt', 'publication.json'):
                with _private_path(output/name).open('rb') as stream:
                    os.fsync(stream.fileno())
            _sync_ancestry(output)
            return expected
    except SourcePolicyError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise SourcePolicyError('factual publication unavailable or incomplete') from None
