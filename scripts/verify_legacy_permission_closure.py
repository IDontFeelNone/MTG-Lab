"""Verify review metadata against an explicitly supplied historical baseline.

Read-only governance checks, not a snapshot loader, permission or approval service.
No current-root fallback, network, writer, file generation or Git dependency.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath

OPERATIONS = ('LOCAL_PRIVATE_PROCESSING', 'PRIVATE_OPERATOR_RETENTION',
    'EXISTING_PUBLIC_GIT_COMPATIBILITY', 'NEW_PUBLIC_REPOSITORY_REDISTRIBUTION',
    'FREE_PUBLIC_APPLICATION_SERVICE', 'COMMERCIAL_OR_PAID_SERVICE', 'AI_OR_MODEL_EXPORT')
STATES = {'ESTABLISHED', 'ESTABLISHED_WITH_CONDITIONS', 'NOT_ESTABLISHED',
          'NOT_APPLICABLE', 'EXCLUDED_FROM_PROFILE', 'NEEDS_DIRECT_REVIEW'}
PACKET = 'reference-reviews/v13-legacy-profile-permission-closure'
STAGE2 = 'reference-reviews/v13-stage2-legacy-public-profile'
QUERY_ID = 'sha256:7cee417d40186169829d812c1edd4db6d6934f75f3eeb7183dae09f61bb437a7'
HISTORICAL_ID = 'sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53'
DOCUMENTS = {'capability-tiers.json', 'dependency-closure.json', 'field-inventory.json',
    'query-field-inventory.json', 'permission-matrix.json', 'source-evidence-index.json',
    'notice-requirements.json', 'ci-placement.json', 'stage3-readiness.json', 'preservation-bindings.json'}


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate review JSON key')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('non-finite review JSON')
    return json.loads(path.read_bytes(), object_pairs_hook=pairs, parse_constant=invalid)


def file_at(root, name):
    path = PurePosixPath(name)
    if (not path.parts or path.is_absolute() or '..' in path.parts or ':' in name
            or '\\' in name or path.as_posix() != name):
        raise ValueError('unsafe review dependency path')
    if root.is_symlink() or any(root.joinpath(*path.parts[:i]).is_symlink()
                                for i in range(1, len(path.parts) + 1)):
        raise ValueError('symlinked review dependency')
    target = root / path
    if not target.is_file():
        raise ValueError('missing review dependency: ' + name)
    return target


def binding(root, ref):
    target = file_at(root, ref['path'])
    raw = target.read_bytes()
    if len(raw) != ref['byte_length'] or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('review dependency integrity mismatch: ' + ref['path'])
    return target


def leaves(value, path=''):
    """Field names/types/counts only; dynamic source-valued keys never escape."""
    if isinstance(value, dict):
        if not value:
            yield path, 'empty_object'
        for key, child in value.items():
            key = '*' if path in {'/cards_reused', '/review_artifact_digests', '/evidence_files'} else key
            key = key.replace('~', '~0').replace('/', '~1')
            yield from leaves(child, path + '/' + key)
    elif isinstance(value, list):
        if not value:
            yield path, 'empty_array'
        for child in value:
            yield from leaves(child, path + '/*')
    else:
        yield path, ('null' if value is None else 'boolean' if isinstance(value, bool)
                     else 'number' if isinstance(value, (int, float)) else 'string')


def storage_fields(baseline_root, files):
    observed = defaultdict(Counter)
    for ref in files:
        document = read(binding(baseline_root, ref))
        group = ref['field_group']
        records = [(group, document)] if group != 'promoted_state' else [
            ('promoted_' + kind, record) for kind, rows in document.items() for record in rows.values()]
        for kind, record in records:
            for path, value_type in leaves(record):
                observed[kind, path][value_type] += 1
    return [{'group': group, 'field_path': path, 'leaf_occurrences': sum(types.values()),
             'types': sorted(types)} for (group, path), types in sorted(observed.items())]


def query_fields(engine):
    observed = defaultdict(Counter)
    for result in engine.snapshot().entities:
        for path, value_type in leaves(result.as_dict()):
            observed['query_' + result.entity_type, path][value_type] += 1
    return [{'group': group, 'field_path': path, 'leaf_occurrences': sum(types.values()),
             'types': sorted(types)} for (group, path), types in sorted(observed.items())]


def reader_inventory(baseline_root, expected):
    """Preflight this existing reader's exact baseline scan without reading extras."""
    games = baseline_root/'data/canonical/games'
    if {p.name for p in games.iterdir() if p.is_dir() or p.is_symlink()} != {'magic'}:
        raise ValueError('baseline game namespace changed')
    root = games/'magic'
    patterns = ('game.json', 'cards/*/card.json', 'printings/*/printing.json',
        'products/*/product.json', 'product_versions/**/*.json', 'packs/**/*.json',
        'slots/**/*.json', 'print_sheets/**/*.json', 'sheets/*.json',
        'treatments/*.json', 'finishes/*.json', 'rarities/*.json')
    actual = {p.relative_to(baseline_root).as_posix() for pattern in patterns for p in root.glob(pattern)}
    actual.update(p.relative_to(baseline_root).as_posix()
                  for p in (baseline_root/'data/audit').rglob('*.json'))
    actual.add('data/canonical/state.json')
    actual.update(r['path'] for r in expected if r['field_group'] == 'typed_source')
    if actual != {r['path'] for r in expected}:
        raise ValueError('baseline reader inventory changed before content access')
    optional = baseline_root/'data/canonical/knowledge/state.json'
    if optional.exists() or optional.is_symlink():
        raise ValueError('historical optional knowledge state is no longer absent')


def verify(repository_root, packet, *, baseline_root):
    """The baseline root is required: never substitute current data or live Git."""
    manifest = read(file_at(packet, 'manifest.json'))
    if manifest['document_kind'] != 'permission_closure_review_not_snapshot' or manifest['production_eligible']:
        raise ValueError('review cannot grant production authority')
    if manifest['format_version'] != 'legacy-permission-closure-v1':
        raise ValueError('unsupported review format')
    expected = {'manifest.json'}
    for ref in manifest['files']:
        if ref['path'] in expected:
            raise ValueError('duplicate review file')
        expected.add(ref['path'])
        binding(packet, ref)
    actual = {p.relative_to(packet).as_posix() for p in packet.rglob('*') if p.is_file() or p.is_symlink()}
    if actual != expected:
        raise ValueError('unexpected or missing review file')
    if expected != DOCUMENTS | {'manifest.json'}:
        raise ValueError('unsupported review dependency')
    for ref in manifest['inputs']:
        binding(repository_root, ref)
    # inspection_method and preservation source hashes describe the reviewed
    # revision. They do not freeze mutable current code/governance forever.

    closure = read(packet/'dependency-closure.json')
    stage2 = read(repository_root/STAGE2/'semantic-dependencies.json')['sets']
    for tier, source in (('A', 'current_entity_snapshot_query'),
                         ('B', 'current_full_query_api_read_surface')):
        rows = closure['tiers'][tier]['files']
        if [{k: r[k] for k in ('path', 'byte_length', 'sha256', 'role')} for r in rows] != stage2[source]['files']:
            raise ValueError('closure differs from retained Stage 2: ' + tier)
    c = stage2['canonical_tree_and_full_query_api_parity']['files'] + stage2['historical_admission_validation_additional_dependencies']['files']
    if closure['tiers']['C']['files'] != sorted(c, key=lambda r: r['path']):
        raise ValueError('historical closure differs from retained Stage 2')
    if Counter(r['placement'] for r in closure['tiers']['A']['files']) != {
            'CORE_CATALOG_CONTENT': 33, 'SOURCE_EVIDENCE_REFERENCE': 5, 'AUDIT_CONTEXT': 2}:
        raise ValueError('catalog/context boundary changed')
    for ref in closure['tiers']['A']['files']:
        placement = ('AUDIT_CONTEXT' if ref['path'].startswith('data/audit/') else
                     'SOURCE_EVIDENCE_REFERENCE' if '/sources/' in ref['path'] else 'CORE_CATALOG_CONTENT')
        if ref['placement'] != placement:
            raise ValueError('catalog/context per-path placement changed')
    reader_inventory(baseline_root, closure['tiers']['B']['files'])
    fields = read(packet/'field-inventory.json')['storage_fields']
    expected_fields = [{k:r[k] for k in ('group','field_path','leaf_occurrences','types')} for r in fields]
    if storage_fields(baseline_root, closure['tiers']['A']['files']) != expected_fields:
        raise ValueError('required field inventory differs from explicit baseline')
    # This is inspection of the existing legacy reader, not an implementation
    # of the future forty-file capability. Its present full audit scan is bound.
    for ref in closure['tiers']['B']['files']:
        binding(baseline_root, ref)
    from query import CanonicalQueryEngine
    engine = CanonicalQueryEngine('magic', data_root=baseline_root/'data',
                                  games_root=baseline_root/'data/canonical/games')
    query_inventory = read(packet/'query-field-inventory.json')
    if engine.snapshot().snapshot_id != QUERY_ID or query_fields(engine) != query_inventory['fields']:
        raise ValueError('query field inventory or historical query identity changed')

    index = read(packet/'source-evidence-index.json')
    evidence = {s['id']: s for s in index['sources']}
    if len(evidence) != len(index['sources']):
        raise ValueError('duplicate source evidence')
    for source in evidence.values():
        if source['capture']['full_capture_publicly_retained'] or source['capture']['origin_entity_sha256'] is not None:
            raise ValueError('reader response misrepresented as retained origin')
        if len(source.get('quote') or '') > 250:
            raise ValueError('policy quotation exceeds review boundary')
        previous = source.get('retained_prior_evidence')
        if previous:
            binding(repository_root, {'path': previous['payload_path'],
                'byte_length': previous['payload_byte_length'], 'sha256': previous['payload_sha256']})
            for stem in ('receipt', 'source_record'):
                raw = file_at(repository_root, previous[stem + '_path']).read_bytes()
                if hashlib.sha256(raw).hexdigest() != previous[stem + '_sha256']:
                    raise ValueError('prior policy receipt binding changed')

    matrix = read(packet/'permission-matrix.json')
    profiles = matrix['status_profiles']
    if matrix['operations'] != list(OPERATIONS):
        raise ValueError('operation matrix is incomplete')
    for profile in profiles.values():
        if set(profile['operations']) != set(OPERATIONS):
            raise ValueError('missing operation-specific status')
        for status in profile['operations'].values():
            if status['status'] not in STATES or any(k not in evidence for k in status['evidence_ids']):
                raise ValueError('invalid permission evidence/status')
            if status['status'].startswith('ESTABLISHED'):
                if not status['evidence_ids'] or any(evidence[k]['availability'] != 'AVAILABLE' for k in status['evidence_ids']):
                    raise ValueError('unavailable evidence cannot establish permission')
                if profile['scope'] != 'MTGJSON_CONTROLLED_MATERIAL_ONLY':
                    raise ValueError('mixed content cannot inherit provider permission')
    all_fields = fields + read(packet/'query-field-inventory.json')['fields']
    selected = {(r['group'], r['field_path']) for r in all_fields}
    entries = matrix['fields']
    if len(entries) != len(selected) or {(r['group'],r['field_path']) for r in entries} != selected:
        raise ValueError('required field has no permission disposition')
    for row in entries:
        if row['profile_id'] not in profiles or row['profile_id'] == 'mtgjson-controlled-only':
            raise ValueError('field silently inherits another rights layer')
        if row['profile_id'] == 'project-control' and row['lineage_category'] != 'PROJECT_AUTHORED_TECHNICAL_CONTROL':
            raise ValueError('mixed source field relabeled as project control')
    for requirement in read(packet/'notice-requirements.json')['requirements']:
        if requirement['status'].startswith('ESTABLISHED') and (not requirement['evidence_ids']
                or any(evidence[k]['availability'] != 'AVAILABLE' for k in requirement['evidence_ids'])):
            raise ValueError('notice condition has no available authoritative evidence')

    ready = read(packet/'stage3-readiness.json')
    tiers = read(packet/'capability-tiers.json')
    if (ready['decision'] != 'READY_FOR_NON_PRODUCTION_STAGE3' or ready['production_eligible']
            or ready['source_policy_clearance'] != 'not_granted' or ready['implementation_authorized']
            or ready['execution_authorized'] or ready['production_operator_profile'] != 'BLOCKED'
            or ready['approval_state'] != 'not_granted'):
        raise ValueError('review cannot authorize execution or production')
    if tiers['selected'] != 'A' or tiers['parity']['query_snapshot_id'] != QUERY_ID or tiers['parity']['bare_constructor_equivalent']:
        raise ValueError('explicit-root capability target changed')
    if tiers['incompleteness']['unresolved_finish_references'] != {'signed':21,'etched':9}:
        raise ValueError('historical incompleteness omitted')
    preserved = read(packet/'preservation-bindings.json')
    if preserved['historical_protected_identity'] != HISTORICAL_ID:
        raise ValueError('historical identity changed')
    for ref in preserved['files']:
        if ref['path'].startswith('tests/fixtures/historical_'):
            binding(repository_root, ref)
    return {'status':'verified_review_metadata', 'selected_tier':'A',
            'required_files':40, 'storage_fields':len(fields), 'permission_fields':len(entries),
            'production_eligible':False, 'source_policy_clearance':'not_granted',
            'execution_authorized':False, 'runtime_profile_implemented':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', type=Path, required=True)
    parser.add_argument('--baseline-root', type=Path, required=True)
    parser.add_argument('--packet', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.repository_root, args.packet or args.repository_root/PACKET,
                            baseline_root=args.baseline_root), sort_keys=True))


if __name__ == '__main__':
    main()
