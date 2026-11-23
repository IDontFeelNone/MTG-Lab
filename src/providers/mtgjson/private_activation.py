"""Prepare private controls and invoke the existing importer under host-reviewed pins.

The CLI prepares requests, never authority. Running requires trusted Python code
to supply an independently reviewed plan identity and existing SourceUseBasis
objects. No dataset/policy JSON can approve itself or select executable code.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from .private_import import import_private_release, _control, _private_path, CONTROL_BYTES
from .private_policy import (PrivateResearchProfile, SourcePolicyError,
                             OPERATIONS, RETENTION, canonical, digest)
from .validator import validate_document, MTGJSONValidationError

VERSION = 'private-mtgjson-activation-plan-v1'
RELEASE_FIELDS = frozenset(('provider', 'release_id', 'version', 'date', 'artifact_sha256',
                          'provenance_reference', 'notice_reference'))
CONTROL_NAMES = frozenset(('activation-plan.json', 'provenance.json', 'notice.txt'))


def _require(condition, reason):
    if not condition:
        raise SourcePolicyError(reason)


def _sha(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value)


def plan_private_activation(release, *, source_url, acquired_at, notice_sha256):
    """Build an untrusted request without opening the source, notice or network.

    Hashes/URLs here are declarations. A host must independently review and pin
    the returned plan_id before it can be used to construct an import profile.
    """
    _require(type(release) is dict and set(release) == RELEASE_FIELDS,
             'closed release declaration required')
    _require(release['provider'] == 'MTGJSON' and _sha(release['artifact_sha256'])
             and all(type(v) is str and 0 < len(v) <= 256 and v.isprintable()
                     for v in release.values()), 'invalid bounded release declaration')
    try:
        validate_document({'meta':{'version':release['version'],'date':release['date']},'data':{}})
    except MTGJSONValidationError:
        raise SourcePolicyError('unsupported release metadata') from None
    _require(_sha(notice_sha256), 'exact notice checksum required')
    _require(type(source_url) is str and 0 < len(source_url) <= 2048,
             'bounded acquisition locator required')
    try:
        url = urlsplit(source_url)
        official = (url.scheme == 'https' and url.hostname in ('mtgjson.com', 'data.mtgjson.com')
            and url.port in (None, 443) and not url.username and not url.password
            and not url.fragment and not url.query)
        _require(official or source_url.startswith('urn:mtglab:original:'),
                 'official MTGJSON or original-fixture locator required')
        _require(type(acquired_at) is str and len(acquired_at) <= 40 and acquired_at.endswith('Z'),
                 'UTC manual acquisition timestamp required')
        datetime.fromisoformat(acquired_at[:-1] + '+00:00')
    except (ValueError, TypeError):
        raise SourcePolicyError('invalid acquisition locator or timestamp') from None
    body = dict(schema_version=VERSION, release=deepcopy(release), source_url=source_url,
        acquired_at=acquired_at, acquisition_method='MANUALLY_SUPPLIED', notice_sha256=notice_sha256,
        requested_operations=list(OPERATIONS), retention_profile=RETENTION,
        authority='UNREVIEWED_REQUEST_NOT_AUTHORIZATION', canonical_admission=False,
        real_card_execution=False, public_export=False, external_ai_export=False)
    return dict(body, plan_id='sha256:' + digest(body))


def validate_activation_plan(plan):
    """Return an owned closed plan; structural validity grants no authorization."""
    _require(type(plan) is dict and set(plan) == {'schema_version', 'release', 'source_url',
        'acquired_at', 'acquisition_method', 'notice_sha256', 'requested_operations', 'retention_profile',
        'authority', 'canonical_admission', 'real_card_execution', 'public_export', 'external_ai_export',
        'plan_id'}, 'closed activation plan required')
    expected = plan_private_activation(plan['release'], source_url=plan['source_url'],
        acquired_at=plan['acquired_at'], notice_sha256=plan['notice_sha256'])
    _require(plan == expected, 'altered or incompatible activation plan')
    # Canonical comparison also rejects bool/int aliases in the authority fields.
    try:
        _require(canonical(plan) == canonical(expected), 'altered or incompatible activation plan')
    except (ValueError, TypeError, RecursionError):
        raise SourcePolicyError('invalid activation plan') from None
    return expected


def load_activation_plan(path):
    """Load only a bounded private request, never a Python module or approval file."""
    try:
        path = _private_path(path)
        _require(path.stat().st_size <= CONTROL_BYTES, 'activation plan exceeds byte bound')
        raw = path.read_bytes()
        _require(len(raw) <= CONTROL_BYTES, 'activation plan exceeds byte bound')
        def unique(pairs):
            result = {}
            for key, value in pairs:
                _require(key not in result, 'duplicate activation plan key')
                result[key] = value
            return result
        return validate_activation_plan(json.loads(raw, object_pairs_hook=unique))
    except SourcePolicyError:
        raise
    except (ValueError, TypeError, OSError, RecursionError):
        raise SourcePolicyError('invalid private activation plan') from None


def _provenance(plan):
    release = plan['release']
    return (canonical({k: release[k] for k in ('provider', 'release_id', 'version', 'date',
        'artifact_sha256')} | dict(source_url=plan['source_url'], acquired_at=plan['acquired_at'],
        acquisition_method='MANUALLY_SUPPLIED')) + '\n').encode()


def _capsule_root(path):
    root = Path(path).absolute()
    _require(not any(p.is_symlink() for p in (root, *root.parents)), 'symlink activation directory refused')
    _require(not any((p/'.git').is_file() or (p/'.git/HEAD').is_file()
                     for p in (root, *root.parents)), 'activation directory must be outside Git')
    if root.exists():
        _require(root.is_dir(), 'activation directory must be an ordinary directory')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    _require(root.stat().st_mode & 0o077 == 0, 'owner-only activation directory required')
    _require({p.name for p in root.iterdir()} <= CONTROL_NAMES | {'candidates'},
             'dedicated activation directory required')
    _require(not any(p.is_symlink() for p in root.iterdir()), 'symlink activation control refused')
    candidates = root/'candidates'
    if candidates.exists():
        _require(candidates.is_dir() and candidates.stat().st_mode & 0o077 == 0,
                 'ordinary private candidate directory required')
    return root


def _retain_control(path, raw):
    """Create once with owner-only mode; an altered existing control is a refusal."""
    if path.exists() or path.is_symlink():
        _control(path, digest(raw))
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())


def activate_private_release(plan, source, directory, *, expected_plan_id,
        reviewed_bases, basis_files, internal_decision_reference, material, notice,
        limits=None, stop_after_partitions=None):
    """Prepare controls, construct the existing profile, then invoke the importer.

    AUTHORITY INPUTS are supplied by trusted host code, not loaded from the plan:
    expected_plan_id, reviewed_bases, internal_decision_reference and material.
    Pin the plan only after independently verifying acquisition and scope; never
    copy the incoming plan_id into expected_plan_id automatically. Hashes verify
    bytes, not issuer authenticity or legal conclusions. No real profile is built in.
    """
    _require(sys.platform == 'linux', 'private activation requires the existing Linux bounded worker')
    plan = validate_activation_plan(plan)
    _require(type(expected_plan_id) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', expected_plan_id)
             and expected_plan_id == plan['plan_id'], 'independently reviewed plan identity required')
    provenance = _provenance(plan)
    profile = PrivateResearchProfile.for_release(plan['release'],
        provenance_sha256=digest(provenance), notice_sha256=plan['notice_sha256'],
        bases=reviewed_bases, internal_decision_reference=internal_decision_reference, material=material)
    profile.require_supported()  # Before any evidence, source or notice file reads/writes.
    _require(type(basis_files) is dict and set(basis_files) == {b.reference for b in profile.bases},
             'exact independently reviewed evidence file inventory required')
    try:
        # Reuse the owning private-control checks. Never interpret document text
        # as approval instructions, or load executable paths from the request.
        for basis in profile.bases:
            _control(basis_files[basis.reference], basis.sha256)
        notice_raw = _control(notice, plan['notice_sha256'])
        _require(bool(notice_raw.strip()), 'complete applicable notice required')
        source = _private_path(source)
        root = Path(directory).absolute()
        _require(root != source and root not in source.parents, 'source must remain outside activation directory')
        root = _capsule_root(root)
        for name, raw in (('activation-plan.json', (canonical(plan)+'\n').encode()),
                          ('provenance.json', provenance), ('notice.txt', notice_raw)):
            _retain_control(root/name, raw)
    except SourcePolicyError:
        raise
    except (OSError, TypeError, ValueError, RecursionError):
        raise SourcePolicyError('private activation controls unavailable or conflicting') from None
    # The owning bounded worker verifies the complete source hash before parsing
    # and again before a complete report. No extra source checksum/copy pass here.
    return import_private_release(source, root/'candidates', profile=profile,
        provenance=root/'provenance.json', notice=root/'notice.txt',
        limits=limits, stop_after_partitions=stop_after_partitions)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Prepare a private MTGJSON request; no CLI approval or import bypass.')
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('plan', help='Print an UNREVIEWED request without reading a dataset')
    for name in ('release-id', 'version', 'date', 'source-sha256', 'source-url', 'acquired-at',
                 'notice-sha256', 'provenance-reference', 'notice-reference'):
        prepare.add_argument('--'+name, required=True)
    inspect = commands.add_parser('inspect', help='Validate a request, not its source or authorization')
    inspect.add_argument('plan')
    args = parser.parse_args(argv)
    try:
        if args.command == 'inspect':
            result = load_activation_plan(args.plan)
        else:
            release = dict(provider='MTGJSON', release_id=args.release_id, version=args.version, date=args.date,
                artifact_sha256=args.source_sha256, provenance_reference=args.provenance_reference,
                notice_reference=args.notice_reference)
            result = plan_private_activation(release, source_url=args.source_url,
                acquired_at=args.acquired_at, notice_sha256=args.notice_sha256)
        print(canonical(result))
        return 0
    except SourcePolicyError as error:
        print(canonical(dict(schema_version=VERSION, status='REFUSED', code=error.code, reason=str(error))), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
